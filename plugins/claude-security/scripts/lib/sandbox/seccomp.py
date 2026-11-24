"""The seccomp filter: the parts of the kernel that the sandbox cannot call."""

from __future__ import annotations

import ctypes
import errno
import platform
import socket
import struct
from itertools import chain
from typing import TYPE_CHECKING

from .kernel import Namespace, Prctl, prctl

if TYPE_CHECKING:
    from collections.abc import Iterable

Program = list[bytes]

_REFUSED = {
    "acct": (163, 89),
    "add_key": (248, 217),
    "adjtimex": (159, 171),
    "bpf": (321, 280),
    "chroot": (161, 51),
    "clock_adjtime": (305, 266),
    "clock_settime": (227, 112),
    "delete_module": (176, 106),
    "fanotify_init": (300, 262),
    "finit_module": (313, 273),
    "init_module": (175, 105),
    "ioperm": (173, None),
    "iopl": (172, None),
    "kcmp": (312, 272),
    "kexec_file_load": (320, 294),
    "kexec_load": (246, 104),
    "keyctl": (250, 219),
    "lookup_dcookie": (212, 18),
    "mbind": (237, 235),
    "migrate_pages": (256, 238),
    "modify_ldt": (154, None),
    "mount": (165, 40),
    "move_pages": (279, 239),
    "mq_open": (240, 180),
    "msgget": (68, 186),
    "open_by_handle_at": (304, 265),
    "perf_event_open": (298, 241),
    "pivot_root": (155, 41),
    "process_vm_readv": (310, 270),
    "process_vm_writev": (311, 271),
    "ptrace": (101, 117),
    "quotactl": (179, 60),
    "reboot": (169, 142),
    "request_key": (249, 218),
    "sched_setattr": (314, 274),
    "set_mempolicy": (238, 237),
    "setdomainname": (171, 162),
    "sethostname": (170, 161),
    "setns": (308, 268),
    "settimeofday": (164, 170),
    "swapoff": (168, 225),
    "swapon": (167, 224),
    "sysfs": (139, None),
    "syslog": (103, 116),
    "umount2": (166, 39),
    "unshare": (272, 97),
    "uselib": (134, None),
    "userfaultfd": (323, 282),
    "ustat": (136, None),
    "vhangup": (153, 58),
    "vmsplice": (278, 75),
}
_INSPECTED = {
    "clone": (56, 220),
    "ioctl": (16, 29),
    "pipe2": (293, 59),
    "prlimit64": (302, 261),
    "seccomp": (317, 277),
    "setrlimit": (160, 164),
    "setsockopt": (54, 208),
    "socket": (41, 198),
    "socketpair": (53, 199),
}
_SHARED_FROM = 424
_NEWER = {
    "pidfd_send_signal": 424,
    "pidfd_open": 434,
    "close_range": 436,
    "openat2": 437,
    "faccessat2": 439,
    "epoll_pwait2": 441,
    "landlock_create_ruleset": 444,
    "landlock_add_rule": 445,
    "landlock_restrict_self": 446,
    "futex_waitv": 449,
    "fchmodat2": 452,
    "map_shadow_stack": 453,
    "futex_wake": 454,
    "futex_wait": 455,
    "futex_requeue": 456,
    "mseal": 462,
}
_MACHINES = {"x86_64": (0, 0xC000003E), "aarch64": (1, 0xC00000B7)}

_LOAD, _AND, _EQUAL, _AT_LEAST, _HAS_BIT, _RETURN = 0x20, 0x54, 0x15, 0x35, 0x45, 0x06
_TIOCSTI, _TIOCLINUX, _TIOCSETD = 0x5412, 0x541C, 0x5423
_SOCKET_TYPE, _TCP_ULP, _NEW_LISTENER, _NOTIFICATION_PIPE = 0xF, 31, 0x8, 0o200
_CORE_LIMIT = 4


def _step(code: int, value: int, if_true: int = 0, if_false: int = 0) -> Program:
    return [struct.pack("HBBI", code, if_true, if_false, value)]


def _fail(code: int) -> Program:
    return _step(_RETURN, 0x00050000 | code)


_ALLOW = _step(_RETURN, 0x7FFF0000)
_KILL = _step(_RETURN, 0x80000000)
_DENY = _fail(errno.EPERM)
_IGNORE = _fail(0)


def _argument(index: int, *, high: bool = False) -> Program:
    # The low 32 bits are all that the kernel reads of a number inspected here. Not so of a pointer.
    return _step(_LOAD, 16 + 8 * index + 4 * high)


def _when(test: int, value: int, then: Program) -> Program:
    """Run `then`, which must return on every path, if the loaded value passes; else go past it."""
    return _step(test, value, 0, len(then)) + then


def _one_of(values: Iterable[int], then: Program) -> Program:
    return [step for value in values for step in _when(_EQUAL, value, then)]


def _inspections() -> dict[str, Program]:
    unsupported = _fail(errno.EAFNOSUPPORT)
    protocols = (0, socket.IPPROTO_TCP, socket.IPPROTO_UDP)
    plain = _argument(2) + _one_of(protocols, _ALLOW) + unsupported
    types = (socket.SOCK_STREAM, socket.SOCK_DGRAM)
    internet = _argument(1) + _step(_AND, _SOCKET_TYPE) + _one_of(types, plain) + unsupported
    route = _argument(2) + _when(_EQUAL, socket.NETLINK_ROUTE, _ALLOW) + unsupported
    unix = _argument(0) + _when(_EQUAL, socket.AF_UNIX, _ALLOW)
    upper_layer = _argument(2) + _when(_EQUAL, _TCP_ULP, _DENY) + _ALLOW
    # The limit on core dumps stays. Scripts often lower it, so the call seems to succeed.
    no_high = _argument(2, high=True) + _when(_EQUAL, 0, _ALLOW) + _IGNORE
    only_read = _argument(2) + _when(_EQUAL, 0, no_high) + _IGNORE
    return {
        "clone": _argument(0) + _when(_HAS_BIT, sum(Namespace), _DENY) + _ALLOW,
        "ioctl": _argument(1) + _one_of((_TIOCSTI, _TIOCLINUX, _TIOCSETD), _DENY) + _ALLOW,
        "pipe2": _argument(1) + _when(_HAS_BIT, _NOTIFICATION_PIPE, _DENY) + _ALLOW,
        "prlimit64": _argument(1) + _when(_EQUAL, _CORE_LIMIT, only_read) + _ALLOW,
        "seccomp": _argument(1) + _when(_HAS_BIT, _NEW_LISTENER, _DENY) + _ALLOW,
        "setrlimit": _argument(0) + _when(_EQUAL, _CORE_LIMIT, _IGNORE) + _ALLOW,
        "setsockopt": _argument(1) + _when(_EQUAL, socket.IPPROTO_TCP, upper_layer) + _ALLOW,
        "socket": unix
        + _one_of((socket.AF_INET, socket.AF_INET6), internet)
        + _when(_EQUAL, socket.AF_NETLINK, route)
        + unsupported,
        "socketpair": unix + unsupported,
    }


def program(machine: str) -> Program:
    """The filter for `machine`, as platform.machine() names it."""
    if machine not in _MACHINES:
        msg = f"the sandbox has no system call filter for {machine}"
        raise OSError(msg)
    column, architecture = _MACHINES[machine]
    refused = (number for numbers in _REFUSED.values() if (number := numbers[column]) is not None)
    inspected = (
        _when(_EQUAL, _INSPECTED[name][column], steps) for name, steps in _inspections().items()
    )
    newer = _one_of(_NEWER.values(), _ALLOW) + _fail(errno.ENOSYS)
    return [
        *_step(_LOAD, 4),
        *_step(_EQUAL, architecture, len(_KILL), 0),
        *_KILL,
        *_step(_LOAD, 0),
        *_when(_AT_LEAST, _SHARED_FROM, newer),
        *_one_of(refused, _DENY),
        *chain.from_iterable(inspected),
        *_ALLOW,
    ]


def install() -> None:
    """Put this thread and what it starts behind the filter. The caller has set no_new_privs, as
    kernel.drop_capabilities does."""
    mode_filter = 2
    steps = program(platform.machine())
    code = ctypes.create_string_buffer(b"".join(steps))
    header = ctypes.create_string_buffer(struct.pack("HP", len(steps), ctypes.addressof(code)))
    prctl(Prctl.SECCOMP, mode_filter, ctypes.addressof(header))
