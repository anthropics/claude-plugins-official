"""What the supervisor tells the keeper to build, the messages between the two, and the values that
the sandbox's programs share."""

from __future__ import annotations

import errno
import json
import os
import socket
import sys
from typing import TYPE_CHECKING, NamedTuple, TypedDict, cast

from .. import strictjson

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

RELAY = ("127.0.0.1", 8417)
HOME = "/home/sandbox"
HOST_NAME = "claude-security-sandbox"
SYSTEM_PATH = ("/usr/local/bin", "/usr/bin", "/bin", "/usr/local/sbin", "/usr/sbin", "/sbin")
# No option can show a path in these.
HIDDEN_FOLDERS = ("/boot", "/dev", "/etc", "/proc", "/run", "/sys", "/var/run")
# The user ids that a keeper with root picks from: numbers that systemd's table leaves unused.
FREE_IDS = range(60706, 61184)
MOST_CALLS = 32
TIMED_OUT, BROKEN = 124, 125
LARGEST_MESSAGE = 1 << 20
SHORTEST_PRIVATE = 6
SWAPPED = (
    "is not the folder that was checked: another user may have swapped a folder on the way to it, "
    "so look who can write there"
)
# What a program says on a Python older than the sandbox needs, else empty.
UNGUARDED: str = (
    ""
    if sys.version_info >= (3, 10)
    else "the sandbox sends no request to an https host on Python 3.9: put Python 3.10 or later "
    "first on PATH as python3"
)
_TOO_LONG = (
    "the command, its variables and the files that the sandbox blanks or copies, such as git's "
    "config files, are too long together"
)
_MOST_FDS = 3


class SandboxError(Exception):
    """The sandbox cannot start or go on; the message says why."""


class Plan(TypedDict):
    """One sandbox. Each folder and file to show has an absolute path with no link in it."""

    command: Sequence[str]
    environment: Mapping[str, str]
    cwd: str
    # Folders that show copy-on-write: the first is the scanned one.
    writable: Sequence[str]
    readable: Sequence[str]
    pinned: Mapping[str, str]
    replaced: Mapping[str, str]
    etc: Mapping[str, str]
    seconds: float
    memory: int
    cgroup: bool
    user: int


def identity(status: os.stat_result) -> str:
    """What tells one folder or file from another, whatever its name."""
    return f"{status.st_dev}:{status.st_ino}"


def refuse_a_swap(plan: Plan, path: str, status: os.stat_result) -> None:
    """SandboxError where the plan pins `path` to another folder than the one of `status`."""
    seen = identity(status)
    if plan["pinned"].get(path, seen) != seen:
        msg = f"{path} {SWAPPED}"
        raise SandboxError(msg)


class Message(NamedTuple):
    kind: str
    text: str
    files: Sequence[int]


def send(channel: socket.socket, kind: str, text: str = "", files: Sequence[int] = ()) -> None:
    socket.send_fds(channel, [os.fsencode(f"{kind} {text}")], files)


def receive(channel: socket.socket) -> Message | None:
    """The next message; None when the other side has closed."""
    flags = socket.MSG_CMSG_CLOEXEC
    data, files, received = socket.recv_fds(channel, LARGEST_MESSAGE, _MOST_FDS, flags)[:3]
    if received & socket.MSG_CTRUNC:
        msg = "a message lost its files: too many are open"
        raise SandboxError(msg)
    kind, _, text = os.fsdecode(data).partition(" ")
    return Message(kind, text, files) if data else None


def _as_keeper_reads(name: str) -> str:
    """`name`, a path or a variable of this process, as a process with no locale reads it."""
    return os.fsencode(name).decode("utf-8", "surrogateescape")


def plan_text(plan: Plan) -> str:
    """`plan` as one message. SandboxError if it is too long for one."""
    sent = {
        **plan,
        "command": [*map(_as_keeper_reads, plan["command"])],
        "environment": {
            _as_keeper_reads(name): _as_keeper_reads(value)
            for name, value in plan["environment"].items()
        },
        "cwd": _as_keeper_reads(plan["cwd"]),
        "writable": [*map(_as_keeper_reads, plan["writable"])],
        "readable": [*map(_as_keeper_reads, plan["readable"])],
        "pinned": {_as_keeper_reads(name): pin for name, pin in plan["pinned"].items()},
        "replaced": {_as_keeper_reads(name): text for name, text in plan["replaced"].items()},
        "etc": {_as_keeper_reads(name): text for name, text in plan["etc"].items()},
    }
    if len(text := json.dumps(sent, allow_nan=False)) > LARGEST_MESSAGE:
        raise SandboxError(_TOO_LONG)
    return text


def parsed_plan(text: str) -> Plan:
    return cast("Plan", strictjson.loads(text))


def send_plan(channel: socket.socket, plan: Plan) -> None:
    try:
        send(channel, "plan", plan_text(plan))
    except OSError as error:
        if error.errno != errno.EMSGSIZE:
            raise
        raise SandboxError(_TOO_LONG) from error


def receive_plan(channel: socket.socket) -> Plan:
    if not (message := receive(channel)):
        msg = "the supervisor sent no plan"
        raise SandboxError(msg)
    plan = parsed_plan(message.text)
    names = (*plan["writable"], *plan["readable"], *plan["replaced"], *plan["etc"])
    if any(".." in name.split("/") for name in names):
        msg = "a path of the plan holds '..'"
        raise SandboxError(msg)
    return plan
