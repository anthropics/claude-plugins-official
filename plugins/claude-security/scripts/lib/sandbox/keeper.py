"""The supervisor's side of a sandbox on this machine: the keeper process and its messages."""

from __future__ import annotations

import os
import pwd
import secrets
import socket
import subprocess
import sys
from contextlib import suppress
from typing import TYPE_CHECKING, final

from .. import plugin
from . import kernel, landlock, seccomp, streams
from .kernel import Prctl
from .landlock import Access
from .plan import SYSTEM_PATH, Message, SandboxError, receive, send_plan

if TYPE_CHECKING:
    from collections.abc import Generator

    from .plan import Plan


def _connect(*, sudo: bool) -> tuple[subprocess.Popen[bytes], socket.socket]:
    """Start the keeper, with none of this process's environment, and take its call. Its socket has
    no path that another user can change. Any user can read its name, so a caller with another
    user id is turned away."""
    name = f"claude-sandbox-{secrets.token_hex(16)}"
    program = str(plugin.ROOT / "scripts/sandbox_keeper.py")
    keeper = (sys.executable, "-ISB", "-X", "utf8", program, name)
    keeper_user = 0 if sudo else os.geteuid()
    with socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET) as listener:
        listener.bind(f"\0{name}")
        listener.listen(1)
        listener.settimeout(0.2)
        job = subprocess.Popen(
            ("sudo", "--", *keeper) if sudo else keeper,
            cwd="/",
            env={"PATH": os.pathsep.join(SYSTEM_PATH)},
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
        while job.poll() is None:
            with suppress(socket.timeout):
                call = listener.accept()[0]
                if kernel.peer_uid(call) == keeper_user:
                    return job, call
                call.close()
    msg = f"the sandbox's keeper did not start (exit {job.returncode})"
    raise SandboxError(msg)


def user(name: str) -> pwd.struct_passwd:
    """The entry of the user `name`. ValueError if there is none."""
    try:
        return pwd.getpwnam(name)
    except KeyError as error:
        raise ValueError(name) from error


def harden() -> None:
    """Go on behind the sandbox's system call filter, with no new privileges and not dumpable. No
    thread may be running."""
    kernel.prctl(Prctl.NO_NEW_PRIVILEGES, 1)
    # This process holds the credential: no core file and no tracer may read it.
    kernel.prctl(Prctl.DUMPABLE, 0)
    seccomp.install()


def become(entry: pwd.struct_passwd, out: str) -> None:
    """Go on as the user of `entry` for good, hardened, with Landlock's rights to write only below
    `out` and at /dev/null. Needs root and Landlock version 3, and no thread may be running."""
    if landlock.version() < landlock.TRUNCATE_SINCE:
        msg = f"--user needs Landlock version {landlock.TRUNCATE_SINCE} (Linux 6.2) or newer"
        raise SandboxError(msg)
    kernel.prctl(Prctl.NO_NEW_PRIVILEGES, 1)
    landlock.restrict({
        "/": Access.READ,
        "/dev/null": Access.DEVICE,
        out: Access.WRITE,
    })
    os.setgroups([])
    os.setresgid(entry.pw_gid, entry.pw_gid, entry.pw_gid)
    os.setresuid(entry.pw_uid, entry.pw_uid, entry.pw_uid)
    harden()


class Door(socket.socket):
    """The outer end of the socket on which process 1 hands over the calls that it lets in."""

    def accept(self) -> tuple[socket.socket, None]:  # pyright: ignore[reportImplicitOverride]
        """The next call. EOFError once an end is shut and no call waits, OSError if a call lost
        its socket."""
        try:
            while message := receive(self):
                if message.files:
                    return socket.socket(fileno=message.files[0]), None
                streams.say("refused a call that was not shown to be of the command's own process")
        except SandboxError as error:
            raise OSError(str(error)) from error
        raise EOFError


@final
class Keeper:
    """Builds the sandbox of `plan`."""

    def __init__(self, plan: Plan, *, sudo: bool) -> None:
        self._plan: Plan = plan
        self._job, self._channel = _connect(sudo=sudo)
        kernel.raise_file_limit()

    def messages(self) -> Generator[Message, None, None]:
        with suppress(BrokenPipeError):
            send_plan(self._channel, self._plan)
        try:
            while message := self._received():
                yield message
        except SandboxError as error:
            yield Message("error", str(error), [])

    def _received(self) -> Message | None:
        try:
            return receive(self._channel)
        except ConnectionResetError:
            return receive(self._channel)

    def stop(self) -> None:
        """End the command. Its reports still come."""
        with suppress(OSError):
            self._channel.shutdown(socket.SHUT_WR)

    def wait(self) -> int:
        self._channel.close()
        return self._job.wait()
