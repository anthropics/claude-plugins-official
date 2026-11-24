"""The Linux calls that the sandbox makes, most of which Python's library does not offer."""

from __future__ import annotations

import ctypes
import fcntl
import os
import re
import resource
import socket
import struct
from enum import IntEnum, IntFlag
from pathlib import Path
from typing import cast

_libc = ctypes.CDLL(None, use_errno=True)

_AT_FDCWD = -100
_AT_EMPTY_PATH = 0x1000
_AT_RECURSIVE = 0x8000
_ID_MAPPED = 0x100000
_DEVICE, _UP = "16sH22x", 0x1


class Call(IntEnum):
    """System calls that have the same number on x86-64 and arm64."""

    OPEN_TREE = 428
    MOVE_MOUNT = 429
    PIDFD_OPEN = 434
    CLOSE_RANGE = 436
    OPENAT2 = 437
    PIDFD_GETFD = 438
    MOUNT_SETATTR = 442
    LANDLOCK_CREATE_RULESET = 444
    LANDLOCK_ADD_RULE = 445
    LANDLOCK_RESTRICT_SELF = 446


class Namespace(IntFlag):
    MOUNT = 0x00020000
    CGROUP = 0x02000000
    UTS = 0x04000000
    IPC = 0x08000000
    USER = 0x10000000
    PID = 0x20000000
    NET = 0x40000000


class Mount(IntFlag):
    """Flags of mount(2). The first four are also attributes of mount_setattr(2)."""

    READ_ONLY = 0x1
    NO_SETUID = 0x2
    NO_DEVICES = 0x4
    NO_EXEC = 0x8
    RECURSIVE = 0x4000
    PRIVATE = 0x40000
    SLAVE = 0x80000


class Prctl(IntEnum):
    PARENT_DEATH_SIGNAL = 1
    DUMPABLE = 4
    SECCOMP = 22
    DROP_BOUNDING_CAPABILITY = 24
    SECURE_BITS = 28
    NO_NEW_PRIVILEGES = 38
    AMBIENT_CAPABILITIES = 47


def _call(name: str, *args: int | bytes | None) -> int:
    words = (ctypes.c_long(arg) if isinstance(arg, int) else arg for arg in args)
    if (result := cast("int", _libc[name](*words))) < 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), name)
    return result


def syscall(call: Call, *args: int | bytes | None) -> int:
    try:
        return _call("syscall", call, *args)
    except OSError as error:
        raise OSError(error.errno, error.strerror, call.name.lower()) from None


def prctl(option: Prctl, *args: int) -> None:
    _call("prctl", option, *(*args, 0, 0, 0, 0)[:4])


def unshare(namespaces: Namespace) -> None:
    _call("unshare", namespaces)


def mount(kind: str, target: str, flags: Mount, options: str = "") -> None:
    """Mount a new file system of type `kind`, or, with no type, change how `target` propagates."""
    name = kind.encode() or None
    try:
        _call("mount", name, os.fsencode(target), name, flags, options.encode())
    except OSError as error:
        raise OSError(error.errno, f"mount {kind}: {error.strerror}", target) from None


def set_attributes(tree: int, flags: Mount, id_map: int = 0, *, recursive: bool = True) -> None:
    """Add `flags` to the mount of `tree` and, if `recursive`, to each mount below it, and make them
    private; `id_map` is a user namespace that maps its owners."""
    attributes = struct.pack("4Q", flags | (_ID_MAPPED if id_map else 0), 0, Mount.PRIVATE, id_map)
    where = _AT_EMPTY_PATH | (_AT_RECURSIVE if recursive else 0)
    syscall(Call.MOUNT_SETATTR, tree, b"", where, attributes, len(attributes))


def no_link(path: str) -> int:
    """A descriptor of `path`, for finding it and not for reading it. OSError if its path holds a
    link."""
    no_links = 0x4
    opening = struct.pack("3Q", os.O_PATH | os.O_CLOEXEC, 0, no_links)
    try:
        return syscall(Call.OPENAT2, _AT_FDCWD, os.fsencode(path), opening, len(opening))
    except OSError as error:
        raise OSError(error.errno, error.strerror, path) from error


def clone(place: int, *, recursive: bool = True) -> int:
    """A copy of the mount at the descriptor `place` that lies nowhere yet. This process's mount
    namespace must hold `place`; a later namespace can take the copy."""
    copy = 0x1
    cloning = copy | os.O_CLOEXEC | _AT_EMPTY_PATH | (_AT_RECURSIVE if recursive else 0)
    return syscall(Call.OPEN_TREE, place, b"", cloning)


def attach(tree: int, point: int) -> None:
    """Mount the copy `tree` on the descriptor `point`, and close both."""
    from_descriptor, to_descriptor = 0x4, 0x40
    syscall(Call.MOVE_MOUNT, tree, b"", point, b"", from_descriptor | to_descriptor)
    os.close(tree)
    os.close(point)


def bind(source: str, point: int, flags: Mount) -> None:
    """Show `source`, whose path must hold no link, at the descriptor `point`, which this closes.
    The flags hold before it shows."""
    place = no_link(source)
    tree = clone(place)
    os.close(place)
    set_attributes(tree, flags)
    attach(tree, point)


def enter_root(folder: str) -> None:
    """Make `folder` the root of this mount namespace, and detach the old root."""
    detach = 0x2
    os.chdir(folder)
    _call("pivot_root", b".", b".")
    _call("umount2", b".", detach)
    os.chdir("/")


def mount_points() -> list[str]:
    """Where this process has mounts, by /proc/self/mountinfo."""
    lines = os.fsdecode(Path("/proc/self/mountinfo").read_bytes()).split("\n")[:-1]
    return [re.sub(r"\\(\d{3})", lambda code: chr(int(code[1], 8)), x.split(" ")[4]) for x in lines]


def peer_uid(channel: socket.socket) -> int:
    """The user of the process at the other end of the unix socket `channel`: the one that it had
    when it called `connect` or `listen`."""
    fields = "iII"
    seen = channel.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize(fields))
    return cast("int", struct.unpack(fields, seen)[1])


def raise_file_limit() -> None:
    """Let this process hold as many descriptors as its hard limit allows."""
    hard = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    resource.setrlimit(resource.RLIMIT_NOFILE, (hard, hard))


def bring_up(device: str) -> None:
    set_flags = 0x8914
    with socket.socket() as any_socket:
        fcntl.ioctl(any_socket, set_flags, struct.pack(_DEVICE, device.encode(), _UP))


def devices_up() -> list[str]:
    """The network devices of this namespace that are up."""
    get_flags = 0x8913
    with socket.socket() as any_socket:

        def flags(name: str) -> int:
            told = fcntl.ioctl(any_socket, get_flags, struct.pack(_DEVICE, name.encode(), 0))
            return cast("int", struct.unpack(_DEVICE, told)[1])

        return [name for _, name in socket.if_nameindex() if flags(name) & _UP]


def drop_capabilities(ids: int | None) -> None:
    """Give up every capability for good. With `ids`, also become that user and group alone.
    This sets no_new_privs, which landlock.restrict and seccomp.install need."""
    secure_bits, clear_all, version_3 = 0xE3, 4, 0x20080522
    prctl(Prctl.SECURE_BITS, secure_bits)
    prctl(Prctl.AMBIENT_CAPABILITIES, clear_all)
    for capability in range(int(Path("/proc/sys/kernel/cap_last_cap").read_bytes()) + 1):
        prctl(Prctl.DROP_BOUNDING_CAPABILITY, capability)
    if ids is not None:
        os.setgroups([])
        os.setresgid(ids, ids, ids)
        os.setresuid(ids, ids, ids)
    _call("capset", struct.pack("Ii", version_3, 0), bytes(24))
    prctl(Prctl.NO_NEW_PRIVILEGES, 1)
