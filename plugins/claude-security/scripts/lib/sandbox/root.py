"""The sandbox's file system: a new root with the system's programs and what the plan names."""

from __future__ import annotations

import errno
import os
import stat
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from . import kernel
from .kernel import Mount
from .landlock import Access
from .plan import HOME, HOST_NAME, SandboxError, refuse_a_swap
from .results import NEW, ON_THE_WAY

if TYPE_CHECKING:
    from collections.abc import Mapping

    from .plan import Plan

_STAGE = "/run"
_SCRATCH = "scratch"
_QUIET = Mount.NO_SETUID | Mount.NO_DEVICES
_READ_ONLY = _QUIET | Mount.READ_ONLY
_SYSTEM = ("/usr", "/bin", "/sbin", "/lib", "/lib32", "/lib64", "/libx32")
_ETC = (
    "alternatives",
    "fonts",
    "java-*",
    "ld.so.cache",
    "ld.so.conf",
    "ld.so.conf.d",
    "ld-musl-*",
    "localtime",
    "mime.types",
    "os-release",
    "protocols",
    "python3*",
    "services",
)
_DEVICES = ("/dev/null", "/dev/zero", "/dev/full", "/dev/random", "/dev/urandom")
_LINKS = {
    "/dev/fd": "/proc/self/fd",
    "/dev/stdin": "/proc/self/fd/0",
    "/dev/stdout": "/proc/self/fd/1",
    "/dev/stderr": "/proc/self/fd/2",
}
_PRIVATE = {"/tmp": _QUIET, HOME: _QUIET, "/dev/shm": _QUIET | Mount.NO_EXEC}  # noqa: S108
_SOCKET_FOLDER = "/tmp/cc-socks"  # noqa: S108
_MASKED_IN_PROC = (
    "acpi",
    "asound",
    "bootconfig",
    "bus",
    "cmdline",
    "config.gz",
    "driver",
    "dynamic_debug",
    "fs",
    "interrupts",
    "iomem",
    "ioports",
    "irq",
    "kallsyms",
    "kcore",
    "key-users",
    "keys",
    "kmsg",
    "kpagecgroup",
    "kpagecount",
    "kpageflags",
    "latency_stats",
    "locks",
    "modules",
    "pagetypeinfo",
    "sched_debug",
    "schedstat",
    "scsi",
    "slabinfo",
    "softirqs",
    "sysrq-trigger",
    "timer_list",
    "tty",
    "vmallocinfo",
    "zoneinfo",
)


class Shown(NamedTuple):
    """A folder or file of the plan, as it was when it was opened."""

    status: os.stat_result
    tree: int


def upper(index: int) -> str:
    """Where the changes to the writable folder `index` lie."""
    return f"{_SCRATCH}/upper{index}"


def stage(plan: Plan) -> None:
    """Mount the stage, in a mount namespace of the caller's own, and enter it."""
    kernel.mount("", "/", Mount.RECURSIVE | Mount.SLAVE)
    kernel.mount("tmpfs", _STAGE, _QUIET, "mode=0700")
    os.chdir(_STAGE)
    for name in ("root", "empty", _SCRATCH):
        Path(name).mkdir()
    size = plan["memory"] // 2
    kernel.mount("tmpfs", _SCRATCH, _QUIET, f"mode=0700,size={size},nr_inodes={size // 2048}")


def open_shown(plan: Plan) -> dict[str, Shown]:
    """Open each path that the plan shows, following no link, and take a copy of its mount. Needs
    the stage's mount namespace: what comes later sees only these, and never looks at the names."""
    shown: dict[str, Shown] = {}
    for path in {*plan["writable"], *plan["readable"]}:
        place = kernel.no_link(path)
        status = os.fstat(place)
        refuse_a_swap(plan, path, status)
        if not (stat.S_ISDIR(status.st_mode) or stat.S_ISREG(status.st_mode)):
            msg = f"{path} is not a file or a folder"
            raise SandboxError(msg)
        try:
            shown[path] = Shown(status, kernel.clone(place, recursive=False))
        except OSError as error:
            if error.errno != errno.EINVAL:
                raise
            raise OSError(error.errno, "it holds a mount: use --sudo", path) from error
        kernel.set_attributes(shown[path].tree, Mount(0))
        os.close(place)
    return shown


def build(
    plan: Plan, ids: int | None, shown: Mapping[str, Shown], id_map: int
) -> dict[str, Access]:
    """Build the root from the stage and enter it. `ids` is the user and group that will run in it,
    or None for the caller's own; `shown` is what open_shown gave; `id_map` shows that user as the
    owner of the scanned folder. Returns the access that each part of the new root allows."""
    kernel.mount("", "/", Mount.RECURSIVE | Mount.PRIVATE)
    kernel.mount("tmpfs", "root", _QUIET, "mode=0755,size=1m")
    system = [path for path in _SYSTEM if _show_system(Path(path))]
    for pattern in _ETC:
        for path in Path("/etc").glob(pattern):
            _show_system(path)
    for name, text in {**_etc_files(ids or os.getuid(), ids or os.getgid()), **plan["etc"]}.items():
        _write_inside(f"/etc/{name}", text)
    for device in _DEVICES:
        flags = Mount.READ_ONLY | Mount.NO_SETUID | Mount.NO_EXEC
        kernel.bind(device, point_for(device, folder=False), flags)
    for link, target in _LINKS.items():
        _inside(link).symlink_to(target)
    for index, (path, flags) in enumerate(_PRIVATE.items()):
        own = _owned(Path(_SCRATCH, f"private{index}"), ids)
        kernel.bind(str(own), point_for(path, folder=True), flags)
    owner = shown[plan["writable"][0]].status.st_uid
    for index, path in enumerate(sorted(shown)):
        status, tree = shown[path]
        mapped = id_map if path in plan["writable"] or status.st_uid == owner != 0 else 0
        _set_attributes(tree, path, mapped)
        if stat.S_ISDIR(status.st_mode):
            lower = f"lower{index}"
            Path(lower).mkdir()
            kernel.attach(tree, kernel.no_link(lower))
            layers = f"{_replacements(path, plan, f'over{index}', lower, ids)}:{lower}"
            if path in plan["writable"]:
                changes = _owned(Path(upper(plan["writable"].index(path))), ids)
                changes.chmod(status.st_mode & 0o777)
                layers += f",upperdir={changes},workdir={_owned(Path(_SCRATCH, str(index)), None)}"
            flags = _QUIET if path in plan["writable"] else _READ_ONLY
            _overlay(path, layers, flags)
        else:
            kernel.attach(tree, point_for(path, folder=False))
    for path in (_SOCKET_FOLDER, f"{_SOCKET_FOLDER}-{ids or os.getuid()}"):
        kernel.bind("empty", point_for(path, folder=True), _READ_ONLY)
    _mount_proc()
    _seal("root")
    kernel.enter_root("root")
    return (
        {"/": Access.READ_DIR}
        | dict.fromkeys((*system, "/etc", "/proc", *plan["readable"]), Access.READ)
        | dict.fromkeys(_DEVICES, Access.DEVICE)
        | dict.fromkeys((*_PRIVATE, *plan["writable"]), Access.WRITE)
    )


def _inside(path: str | Path) -> Path:
    return Path("root", str(path).lstrip("/"))


def _enter(above: int, name: str) -> int:
    """The folder `name` in the descriptor `above`, which this closes, made if it is not there."""
    with suppress(FileExistsError):
        os.mkdir(name, 0o755, dir_fd=above)
    inner = os.open(name, ON_THE_WAY, dir_fd=above)
    os.close(above)
    return inner


def _folder_inside(path: str | Path) -> tuple[int, str]:
    """A descriptor of the folder that holds `path` in the new root, made if it is not there, and
    the last name of `path`. The way follows no link."""
    *way, name = _inside(path).parts
    above = os.open(".", ON_THE_WAY)
    for part in way:
        above = _enter(above, part)
    return above, name


def _write_inside(path: str, text: str) -> None:
    """Write the file `path` in the new root through no link. A link there goes first."""
    above, name = _folder_inside(path)
    try:
        with suppress(FileNotFoundError):
            os.unlink(name, dir_fd=above)
        file = os.open(name, NEW, 0o644, dir_fd=above)
    finally:
        os.close(above)
    with os.fdopen(file, "w", encoding="utf-8") as written:
        written.write(text)


def point_for(path: str | Path, *, folder: bool) -> int:
    """A descriptor of the mount point for `path` in the new root, made if it is not there. The way
    can run through a folder of the user's, so it follows no link and takes only the kind asked."""
    above, name = _folder_inside(path)
    if folder:
        return _enter(above, name)
    with suppress(FileExistsError):
        os.close(os.open(name, NEW, 0o644, dir_fd=above))
    point = os.open(name, os.O_PATH | os.O_NOFOLLOW, dir_fd=above)
    os.close(above)
    if not stat.S_ISREG(os.fstat(point).st_mode):
        msg = f"{path} is no file to mount on"
        raise SandboxError(msg)
    return point


def _owned(folder: Path, ids: int | None) -> Path:
    folder.mkdir(exist_ok=True)
    if ids is not None:
        os.chown(folder, ids, ids)
    return folder


def _show_system(path: Path) -> bool:
    """Show a system path as the host has it. True if it is mounted, and not a link or absent."""
    if path.is_symlink():
        _inside(path).parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        _inside(path).symlink_to(path.readlink())
    elif path.is_dir() or path.is_file():
        kernel.bind(str(path), point_for(path, folder=path.is_dir()), _READ_ONLY)
        return True
    return False


def _etc_files(user: int, group: int) -> dict[str, str]:
    return {
        "passwd": f"root:x:0:0::/:/bin/false\nsandbox:x:{user}:{group}::{HOME}:/bin/bash\n",
        "group": f"root:x:0:\nsandbox:x:{group}:\n",
        "hosts": f"127.0.0.1 localhost {HOST_NAME}\n::1 localhost\n",
        "nsswitch.conf": "passwd: files\ngroup: files\nhosts: files\n",
        "gitconfig": "[safe]\n\tdirectory = *\n",
    }


def _replacements(path: str, plan: Plan, layer: str, lower: str, ids: int | None) -> str:
    """A layer to lie over `path`, which `lower` shows, with the files that the plan replaces there.
    What it holds takes the form of what it covers."""
    _owned(Path(layer), ids)
    entries = {Path()}
    for name, text in plan["replaced"].items():
        if Path(name).is_relative_to(path):
            below = Path(name).relative_to(path)
            entries.update((below, *below.parents))
            for folder in reversed(below.parents):
                _owned(layer / folder, ids)
            (layer / below).write_text(text, encoding="utf-8")
            if ids is not None:
                os.chown(layer / below, ids, ids)
    for entry in sorted(entries, reverse=True):
        _take_form(Path(layer, entry), f"{lower}/{entry}", ids)
    return layer


def _take_form(entry: Path, real: str, ids: int | None) -> None:
    """Give `entry` the mode of `real`, and the sandbox user as owner and group only where `real`
    shows them. Where `real` is no entry of this kind, the layer hides it, and `entry` stays."""
    try:
        place = kernel.no_link(real)
    except OSError as error:
        if error.errno in {errno.ENOENT, errno.ENOTDIR, errno.ELOOP, errno.EACCES}:
            return
        raise
    status = os.fstat(place)
    os.close(place)
    if stat.S_IFMT(status.st_mode) == stat.S_IFMT(entry.stat().st_mode):
        if ids is not None:
            os.chown(entry, ids if status.st_uid == ids else 0, ids if status.st_gid == ids else 0)
        entry.chmod(status.st_mode & 0o777)


def _set_attributes(tree: int, path: str, id_map: int) -> None:
    try:
        kernel.set_attributes(tree, _READ_ONLY, id_map)
    except OSError as error:
        if error.errno != errno.EINVAL:
            raise
        why = "its file system has no id-mapped mounts: copy the folder, or run without root"
        raise OSError(error.errno, why, path) from error


def _overlay(path: str, layers: str, flags: Mount) -> None:
    features = "redirect_dir=nofollow,metacopy=off,index=off" if os.getuid() == 0 else "userxattr"
    point = point_for(path, folder=True)
    try:
        kernel.mount("overlay", f"/proc/self/fd/{point}", flags, f"lowerdir={layers},{features}")
    except OSError as error:
        raise OSError(error.errno, error.strerror, path) from error
    os.close(point)


def _mount_proc() -> None:
    # The kernel allows a new /proc only while the old one is still in view.
    proc = _inside("/proc")
    proc.mkdir(mode=0o755)
    kernel.mount("proc", str(proc), _READ_ONLY | Mount.NO_EXEC)
    for path in (proc / name for name in _MASKED_IN_PROC):
        if path.is_dir():
            kernel.bind("empty", kernel.no_link(str(path)), _READ_ONLY)
        elif path.exists():
            kernel.bind("/dev/null", kernel.no_link(str(path)), Mount.READ_ONLY | Mount.NO_SETUID)


def _seal(folder: str) -> None:
    """Make the mount at `folder`, but none below it, read-only."""
    place = os.open(folder, os.O_PATH)
    kernel.set_attributes(place, Mount.READ_ONLY, recursive=False)
    os.close(place)
