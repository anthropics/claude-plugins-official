#!/usr/bin/env python3
"""Build one sandbox, watch over it, and hand out its results. sandbox.py starts this program,
as the user or through sudo, or sandbox_guest.py does in a virtual machine, and sends it the plan.

Usage:
  sandbox_keeper.py <the name of the supervisor's socket>

Python 3.9-compatible, stdlib only. Linux only.
"""

from __future__ import annotations

import errno
import grp
import mmap
import os
import pwd
import resource
import select
import signal
import socket
import stat
import subprocess
import sys
import threading
from contextlib import contextmanager, suppress
from pathlib import Path
from queue import SimpleQueue
from typing import TYPE_CHECKING, NoReturn

# Under -I, which starts this program, Python leaves its folder, with lib/, off the import path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.plugin import REPORT_DIR_RE
from lib.sandbox import kernel, landlock, root, seccomp
from lib.sandbox.kernel import Call, Namespace, Prctl
from lib.sandbox.plan import (
    BROKEN,
    FREE_IDS,
    HOST_NAME,
    RELAY,
    TIMED_OUT,
    Plan,
    SandboxError,
    receive_plan,
    send,
)
from lib.sandbox.results import DEEPEST, FOLDER

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable, Iterator, Mapping

_CGROUPS = Path("/sys/fs/cgroup")
_PROCESSES = 4096
_fault = mmap.mmap(-1, 200)
_GONE = frozenset({errno.ENOTCONN, errno.ENOENT, errno.EBADF, errno.ESRCH})
_ENDING_SECONDS = 1
_IGNORED = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT, signal.SIGTSTP)


def _said(error: BaseException) -> str:
    """What the supervisor is told of `error`."""
    return str(error) if isinstance(error, (OSError, SandboxError)) else repr(error)


def _fork(channel: socket.socket, child: Callable[[], int]) -> int:
    """Run `child` in a process that dies with this one. Its faults go to the supervisor."""
    alive, held = os.pipe()
    if pid := os.fork():
        os.close(alive)
        return pid
    try:
        os.close(held)
        _die_with_parent(alive)
        code = child()
    except BaseException as error:
        code = BROKEN
        with suppress(OSError):
            send(channel, "error", _said(error))
    os._exit(code)


def _die_with_parent(alive: int) -> None:
    kernel.prctl(Prctl.PARENT_DEATH_SIGNAL, signal.SIGKILL)
    if select.select([alive], [], [], 0)[0]:
        os._exit(BROKEN)
    os.close(alive)


def _exit_code(status: int) -> int:
    code = os.waitstatus_to_exitcode(status)
    return code if code >= 0 else 128 - code


def _is_known(number: int) -> bool:
    for look_up in (pwd.getpwuid, grp.getgrgid):
        with suppress(KeyError):
            look_up(number)
            return True
    return False


def _claim_id() -> int:
    """The first free id. A socket named for it, open until this process ends, keeps it from other
    keepers in this network namespace."""
    for number in FREE_IDS:
        if not _is_known(number):
            claim = socket.socket(socket.AF_UNIX)
            try:
                claim.bind(f"\0claude-sandbox-id-{number}")
            except OSError as error:
                claim.close()
                if error.errno != errno.EADDRINUSE:
                    raise
            else:
                claim.detach()
                return number
    msg = "no user id is free for the sandbox"
    raise SandboxError(msg)


def _map_ids(pid: int | str, user: str, group: str) -> None:
    for name, text in (("setgroups", "deny"), ("uid_map", user), ("gid_map", group)):
        Path(f"/proc/{pid}/{name}").write_text(text, encoding="ascii")


def _id_map(channel: socket.socket, owner: os.stat_result, ids: int) -> int:
    """A user namespace with no process in it, which maps `owner`'s user and group to `ids`."""
    ours, theirs = socket.socketpair()

    def hold() -> int:
        kernel.unshare(Namespace.USER)
        theirs.send(b".")
        return len(theirs.recv(1))

    pid = _fork(channel, hold)
    theirs.close()
    if not ours.recv(1):
        msg = "no user namespace could be made for the id map"
        raise SandboxError(msg)
    _map_ids(pid, f"{owner.st_uid} {ids} 1", f"{owner.st_gid} {ids} 1")
    namespace = os.open(f"/proc/{pid}/ns/user", os.O_RDONLY)
    os.kill(pid, signal.SIGKILL)
    os.waitpid(pid, 0)
    return namespace


def _make_cgroup(group: Path, plan: Plan) -> None:
    offered = _CGROUPS / "cgroup.subtree_control"
    if not (offered.is_file() and {"memory", "pids"} <= {*offered.read_text("ascii").split()}):
        msg = "no cgroup v2 can cap memory and processes here: pass --no-cgroup to run without"
        raise SandboxError(msg)
    group.mkdir()
    (group / "memory.max").write_text(str(plan["memory"]), encoding="ascii")
    (group / "pids.max").write_text(str(_PROCESSES), encoding="ascii")
    if (swap := group / "memory.swap.max").exists():
        swap.write_text("0", encoding="ascii")


def _enter_namespaces() -> None:
    shared = Namespace.MOUNT | Namespace.NET | Namespace.IPC | Namespace.UTS
    user, group = os.geteuid(), os.getegid()
    if user == 0:
        kernel.unshare(shared)
        return
    try:
        kernel.unshare(shared | Namespace.USER)
        _map_ids("self", f"{user} {user} 1", f"{group} {group} 1")
    except OSError as error:
        msg = f"a user without root cannot make namespaces here ({error.strerror}): pass --sudo"
        raise SandboxError(msg) from error


def _limit() -> None:
    Path("/proc/self/oom_score_adj").write_text("1000", encoding="ascii")
    os.nice(10)
    try:
        # At 1, and not at 0, the kernel starts no core dump program of the host. seccomp keeps it.
        resource.setrlimit(resource.RLIMIT_CORE, (1, 1))
    except ValueError as error:
        msg = "the limit on core dumps cannot be set here"
        raise SandboxError(f"{msg}: pass --sudo" if os.geteuid() else msg) from error
    limits = {
        resource.RLIMIT_NPROC: _PROCESSES,
        resource.RLIMIT_NICE: 0,
        resource.RLIMIT_RTPRIO: 0,
        resource.RLIMIT_MEMLOCK: 1 << 16,
    }
    for name, wanted in limits.items():
        hard = resource.getrlimit(name)[1]
        value = wanted if hard == resource.RLIM_INFINITY else min(wanted, hard)
        resource.setrlimit(name, (value, value))


def _verify() -> None:
    """Look at the main thread from inside, and refuse to go on if a wall is not there."""
    lines = Path("/proc/self/status").read_text(encoding="utf-8").splitlines()
    status = dict(line.split(":\t", 1) for line in lines if ":\t" in line)
    sets = ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb")
    walls = {
        "capabilities": not any(int(status[name], 16) for name in sets),
        "no_new_privs": status["NoNewPrivs"] == "1",
        "seccomp": status["Seccomp"] == "2",
        "user": "0" not in status["Uid"].split() + status["Gid"].split(),
        "network": kernel.devices_up() == ["lo"],
        "root": bool(os.statvfs("/").f_flag & os.ST_RDONLY),
        "processes": os.getpid() == 1,
    }
    if missing := [name for name, holds in walls.items() if not holds]:
        msg = f"the sandbox does not hold: {', '.join(missing)}"
        raise SandboxError(msg)


@contextmanager
def _unless_gone() -> Generator[None, None, None]:
    try:
        yield
    except OSError as error:
        if error.errno not in _GONE:
            raise


def _names_a_socket(link: Path) -> bool:
    try:
        return str(link.readlink()).startswith("socket:")
    except OSError as error:
        if error.errno != errno.ENAMETOOLONG:
            raise
        return False


def _copies(pid: int, pidfd: int) -> Iterator[int]:
    """A copy of what the process holds under each number that named a socket a moment ago, while
    it lets this one take them."""
    with suppress(PermissionError):
        for link in Path(f"/proc/{pid}/fd").iterdir():
            with _unless_gone():
                if _names_a_socket(link):
                    yield kernel.syscall(Call.PIDFD_GETFD, pidfd, int(link.name), 0)


def _is_among(copies: Iterable[int], call: socket.socket) -> bool:
    """Whether the other end of `call`, an IPv4 socket, is among `copies`, which this closes.
    OSError if the call is gone, or `copies` fails."""
    ends = (call.getpeername(), RELAY, socket.SOCK_STREAM)
    held = False
    for copy in copies:
        try:
            end = socket.socket(fileno=copy)
        except OSError:
            os.close(copy)
            continue
        with suppress(OSError), end:
            held = held or (end.getsockname(), end.getpeername(), end.type) == ends
    call.getpeername()
    return held


def _first_look(pidfd: int) -> None:
    """PermissionError if a look at the process is refused, as some hosts do and an unreadable
    program does, unless the process ends within _ENDING_SECONDS."""
    try:
        with _unless_gone():
            os.close(kernel.syscall(Call.PIDFD_GETFD, pidfd, 0, 0))
    except PermissionError:
        if not select.select([pidfd], [], [], _ENDING_SECONDS)[0]:
            raise


def _let_in(pid: int, pidfd: int, listener: socket.socket, door: socket.socket) -> NoReturn:
    """Hand the relay the calls of process `pid` alone, and tell it of the first other call."""
    _first_look(pidfd)
    told = False
    while True:
        call = listener.accept()[0]
        with suppress(BrokenPipeError), _unless_gone():
            if _is_among(_copies(pid, pidfd), call):
                send(door, "call", files=[call.fileno()])
            elif not told:
                told = True
                send(door, "refused")
        call.close()


def _keep_door(started: SimpleQueue[tuple[int, int]], *calls: socket.socket) -> NoReturn:
    """_let_in, for the number and the pidfd that `started` gives. A fault goes into _fault and ends
    this process, and so the sandbox."""
    why = "process 1 of the sandbox can take no calls"
    try:
        _let_in(*started.get(), *calls)
    except Exception as error:
        why += f": {_said(error)}"
        raise
    finally:
        _fault.write(why.encode()[: len(_fault)])
        os._exit(BROKEN)


def _init(
    channel: socket.socket,
    calls: tuple[socket.socket, socket.socket],
    plan: Plan,
    ids: int | None,
    shown: Mapping[str, root.Shown],
    id_map: int,
    group: Path | None,
) -> int:
    if group:
        (group / "cgroup.procs").write_text("0", encoding="ascii")
    kernel.unshare(Namespace.MOUNT | Namespace.CGROUP)
    os.setsid()
    os.umask(0o022)
    _limit()
    allowed = root.build(plan, ids, shown, id_map)
    kernel.drop_capabilities(ids)
    kernel.prctl(Prctl.DUMPABLE, 0)
    started: SimpleQueue[tuple[int, int]] = SimpleQueue()
    threading.Thread(target=_keep_door, args=(started, *calls), daemon=True).start()
    landlock.restrict(allowed)
    seccomp.install()
    _verify()
    for number in _IGNORED:
        signal.signal(number, signal.SIG_DFL)
    streams = [socket.socketpair() for _ in range(3)]
    streams[0][0].shutdown(socket.SHUT_RD)
    stdin, stdout, stderr = (theirs.fileno() for _, theirs in streams)
    # No new module loads from here on: the command may be able to write where imports look.
    sys.meta_path.clear()
    command = subprocess.Popen(
        plan["command"],
        cwd=plan["cwd"],
        env=plan["environment"],
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
    )
    pidfd = kernel.syscall(Call.PIDFD_OPEN, command.pid, 0)
    send(channel, "streams", files=[ours.fileno() for ours, _ in streams])
    first = 0
    for kept in (*sorted((pidfd, *(end.fileno() for end in calls))), 1 << 32):
        if first < kept:
            kernel.syscall(Call.CLOSE_RANGE, first, kept - 1, 0)
        first = kept + 1
    started.put((command.pid, pidfd))
    while True:
        pid, status = os.wait()
        if pid == command.pid:
            return _exit_code(status)


def _is_removal(entry: os.DirEntry[str]) -> bool:
    """Whether `entry`, in an upper layer, is overlayfs's mark of what was removed below."""
    status = entry.stat(follow_symlinks=False)
    return stat.S_ISCHR(status.st_mode) and status.st_rdev == 0


def _reports(folder: int, name: str, *, inside: bool) -> Iterator[tuple[str, int | None]]:
    """The name and an open descriptor of each regular file in a report folder, at most DEEPEST
    folders below `folder`, and the name with None of what was removed there. `inside` says that
    `folder` is or lies in one. No link is followed, and a report's hidden folders, which hold a
    run's working files, are passed over."""
    with os.scandir(folder) as entries:
        for entry in entries:
            if inside and entry.is_file(follow_symlinks=False):
                flags = os.O_RDONLY | os.O_NOFOLLOW
                yield name + entry.name, os.open(entry.name, flags, dir_fd=folder)
            elif inside and _is_removal(entry):
                yield name + entry.name, None
            elif (
                entry.is_dir(follow_symlinks=False)
                and name.count("/") < DEEPEST
                and not (inside and entry.name.startswith("."))
            ):
                below = os.open(entry.name, FOLDER, dir_fd=folder)
                report = inside or bool(REPORT_DIR_RE.match(entry.name))
                yield from _reports(below, f"{name}{entry.name}/", inside=report)
                os.close(below)


def _hand_out(channel: socket.socket) -> None:
    try:
        upper = os.open(root.upper(0), FOLDER)
    except FileNotFoundError:
        return
    kernel.raise_file_limit()
    for name, file in _reports(upper, "", inside=False):
        if file is None:
            send(channel, "removed", name)
        else:
            send(channel, "file", name, [file])
            os.close(file)


def _keep(channel: socket.socket) -> None:
    plan = receive_plan(channel)
    ids = plan["user"] or _claim_id() if os.geteuid() == 0 else None
    group = _CGROUPS / f"claude-security-sandbox-{os.getpid()}" if ids and plan["cgroup"] else None
    try:
        if group:
            _make_cgroup(group, plan)
        _enter_namespaces()
        socket.sethostname(HOST_NAME)
        kernel.bring_up("lo")
        listener = socket.create_server(RELAY, backlog=128)
        door, relay = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        with relay:
            send(channel, "relay", files=[relay.fileno()])
        calls = (listener, door)
        root.stage(plan)
        shown = root.open_shown(plan)
        owner = shown[plan["writable"][0]].status
        id_map = _id_map(channel, owner, ids) if ids and not plan["user"] else 0
        kernel.unshare(Namespace.PID)

        def guard() -> int:
            kernel.unshare(Namespace.PID)
            init = _fork(channel, lambda: _init(channel, calls, plan, ids, shown, id_map, group))
            channel.close()
            return _exit_code(os.waitpid(init, 0)[1])

        pid = _fork(channel, guard)
        guard_end = kernel.syscall(Call.PIDFD_OPEN, pid, 0)
        # The supervisor orders the end by closing its side, or by being gone.
        ended = select.select([guard_end, channel], [], [], plan["seconds"])[0]
        os.kill(pid, signal.SIGKILL)
        code = _exit_code(os.waitpid(pid, 0)[1])
    finally:
        with suppress(OSError):
            if group:
                group.rmdir()
    # Before the files: the supervisor stops reading if they are too many.
    if guard_end not in ended:
        send(channel, "note", "the run was stopped" if ended else "the time limit ended the run")
    send(channel, "exit", str(code if ended else TIMED_OUT))
    _hand_out(channel)
    if why := _fault[:].rstrip(b"\0"):
        send(channel, "error", why.decode())


def main() -> NoReturn:
    for number in _IGNORED:
        signal.signal(number, signal.SIG_IGN)
    nothing = os.open(os.devnull, os.O_RDWR)
    for stream in range(3):
        os.dup2(nothing, stream)
    channel = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    channel.connect(f"\0{sys.argv[1]}")
    # Any user can read the name, so only the peer's user id says whose plan comes.
    if kernel.peer_uid(channel) != int(os.environ.get("SUDO_UID", os.geteuid())):
        with suppress(OSError):
            send(channel, "error", "the keeper was not called by the user behind sudo")
        sys.exit(BROKEN)
    try:
        _keep(channel)
    except Exception as error:
        with suppress(OSError):
            send(channel, "error", _said(error))
        sys.exit(BROKEN)
    sys.exit(0)


if __name__ == "__main__":
    main()
