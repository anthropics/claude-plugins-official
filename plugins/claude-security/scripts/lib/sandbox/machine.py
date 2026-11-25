"""A sandbox in a virtual machine of Apple's container tool. The machine has no network and no
share of the host: the folders go in as a tar stream, and all else crosses its standard streams."""

from __future__ import annotations

import errno
import io
import os
import secrets
import select
import shutil
import socket
import stat
import subprocess
import tarfile
import tempfile
import threading
import time
from contextlib import suppress
from pathlib import Path
from typing import IO, TYPE_CHECKING, cast, final

from .. import plugin
from . import streams
from .plan import MOST_CALLS, Message, SandboxError, plan_text, refuse_a_swap
from .results import MOST_BYTES, folder_of
from .tunnel import FIRST_CALL, STDERR, STDIN, STDOUT, Tunnel

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterator

    from _typeshed import ReadableBuffer

    from .plan import Plan

USER = 61184
PYTHON = "python3"
_START_SECONDS, _GRACE_SECONDS = 1800, 120
_EXIT_CODES = {str(code).encode() for code in range(256)}
_NOT_ENDED = "the virtual machine did not end in time"
_CLOCK_TICK_SECONDS = 0.2
_TOO_DEEP = "the folders lie too deep to copy into a virtual machine"
_KEPT = ("HOME", "PATH", "TMPDIR", "USER")
# O_NONBLOCK: a pipe in a file's place must not hang the copy.
NO_LINK = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
# tarfile's filter would refuse the folder's own links. No entry's path runs through a link.
_BOOT = """\
import runpy, sys, tarfile
with tarfile.open(fileobj=sys.stdin.buffer, mode="r|") as tar:
    tar.extraction_filter = lambda member, path: member
    tar.extractall("/", numeric_owner=True)
runpy.run_path(sys.argv[1], run_name="__main__")
"""


class _Output(io.FileIO):
    """A pipe that drops what it is given once `ending` says so, so that a reader that does not read
    cannot hold up the machine's frames past a stop or the clock. `dropped` says if it has."""

    def __init__(self, pipe: int, ending: Callable[[], bool]) -> None:
        super().__init__(pipe, "wb")
        self._ending: Callable[[], bool] = ending
        self.dropped: bool = False

    def write(self, data: ReadableBuffer) -> int:  # pyright: ignore[reportImplicitOverride]
        view = memoryview(data)
        for start in range(0, len(view), select.PIPE_BUF):
            while not (self._ending() or select.select([], [self], [], 1)[1]):
                pass
            if self._ending():
                self.dropped = True
                break
            super().write(view[start : start + select.PIPE_BUF])
        return len(view)


@final
class Machine:
    """Gives the messages that a keeper gives, but a fault ends the run at once. It checks the order
    of the frames that it turns into messages. The output, the exit code and its note are the
    machine's word."""

    def __init__(self, plan: Plan, image: str) -> None:
        self._plan: Plan = plan
        self._stopped: bool = False
        self._why: str = ""
        self._ending: bool = False
        self._outputs: list[_Output] = []
        self._folder: tempfile.TemporaryDirectory[str] = tempfile.TemporaryDirectory(
            prefix="claude-sandbox-"
        )
        self._relay: str = f"{self._folder.name}/relay"
        self._name: str = f"claude-security-{secrets.token_hex(6)}"
        self._kept: dict[str, str] = {k: os.environ[k] for k in _KEPT if k in os.environ}
        self._nothing: int = os.open(os.devnull, os.O_WRONLY)
        size = ("--memory", f"{plan['memory'] * 4 // 3 >> 20}M", "--cpus", str(os.cpu_count() or 1))
        walls = ("--network", "none", "--cap-add", "ALL", "--uid", "0", "--entrypoint", "env")
        guest = (PYTHON, "-ISB", "-c", _BOOT, str(plugin.ROOT / "scripts/sandbox_guest.py"))
        run = ("container", "run", "--rm", "-i", "--name", self._name, *size, *walls, image, *guest)
        try:
            self._job: subprocess.Popen[bytes] = subprocess.Popen(
                run,
                cwd="/",
                env=self._kept,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
        except FileNotFoundError as error:
            msg = (
                "Apple's container tool is not on PATH. "
                "To install it, run 'brew install container', then 'container system start'."
            )
            raise SandboxError(msg) from error
        self._in, out, err = (
            cast("IO[bytes]", end) for end in (self._job.stdin, self._job.stdout, self._job.stderr)
        )
        self._said: threading.Thread = streams.copy_out(os.dup(err.fileno()), 2, streams.say)
        self._tunnel: Tunnel = Tunnel(out, self._in)
        self._deadline: tuple[float, str] | None = None
        self._kill_in(_START_SECONDS, "the copy or the start of the virtual machine took too long")
        threading.Thread(target=self._watch_the_clock, daemon=True).start()

    def _kill_in(self, seconds: float, why: str) -> None:
        """Kill the machine after `seconds`, with `why` as the fault. This replaces any clock."""
        self._deadline = time.monotonic() + seconds, why

    def _watch_the_clock(self) -> None:
        while deadline := self._deadline:
            if time.monotonic() >= deadline[0]:
                self._kill(deadline[1])
                return
            time.sleep(_CLOCK_TICK_SECONDS)

    def _kill(self, why: str = "") -> None:
        self._why = why or self._why
        self._ending = True
        with suppress(OSError, subprocess.SubprocessError):
            command = ("container", "kill", self._name)
            subprocess.run(command, env=self._kept, capture_output=True, timeout=30, check=False)
        self._job.kill()

    def _started(self) -> Iterator[Message]:
        if not self._stopped:
            self._kill_in(self._plan["seconds"] + _GRACE_SECONDS, _NOT_ENDED)
        with socket.socket(socket.AF_UNIX) as listener:
            listener.bind(self._relay)
            listener.listen(128)
            yield Message("relay", "", [listener.detach()])
        (source, stdin), (stdout, out), (stderr, err) = os.pipe(), os.pipe(), os.pipe()
        self._tunnel.carry(STDIN, os.fdopen(source, "rb", buffering=0))
        self._outputs = [_Output(pipe, lambda: self._ending) for pipe in (out, err)]
        self._tunnel.deliver_to(STDOUT, self._outputs[0])
        self._tunnel.deliver_to(STDERR, self._outputs[1])
        yield Message("streams", "", [stdin, stdout, stderr])

    def _is_free(self, lane: int) -> bool:
        taken = self._tunnel.open_calls()
        return lane >= FIRST_CALL and lane not in taken and len(taken) < 2 * MOST_CALLS

    def _call(self, lane: int) -> None:
        if self._stopped:
            return
        call = socket.socket(socket.AF_UNIX)
        try:
            call.connect(self._relay)
        except OSError:
            call.close()
            self._tunnel.send(b"k", lane)
        else:
            self._tunnel.join(lane, call)

    def _pack(self, room: int) -> None:
        """Write what the plan shows: folders, links and regular files, with the plan's text in
        place of the files that it replaces, each once, and no mount below that it does not name.
        SandboxError if that is more than `room` bytes, if a file cannot be read whole, if a file
        or folder changes places or is not reached during the copy, if a path that the plan pins is
        not the folder of its pin, or after a stop."""
        # By the files, since macOS ignores case, and by name, since git can replace a file.
        named = self._plan["replaced"]
        replaced: dict[tuple[int, int], str] = {}
        for name, text in named.items():
            with suppress(FileNotFoundError):
                status = os.lstat(name)
                replaced[status.st_dev, status.st_ino] = text
        blanked: dict[str, bytes] = {}
        shown = sorted({*self._plan["writable"], *self._plan["readable"]})
        left = set(shown)
        last = ""

        # By descriptors: another user can put a link in the place of a path that was checked.
        def add(tar: tarfile.TarFile, folder: int, name: str, path: str, device: int) -> None:
            nonlocal room, last
            last = path
            if self._stopped:
                msg = "the copy into the virtual machine was stopped"
                raise SandboxError(msg)
            status = os.stat(name, dir_fd=folder, follow_symlinks=False)
            if f"/{path}" in left:
                left.remove(f"/{path}")
                refuse_a_swap(self._plan, f"/{path}", status)
                device = status.st_dev
            if status.st_dev != device:
                streams.say(f"what is mounted at /{path} does not show")
                return
            identity = status.st_dev, status.st_ino
            if (text := replaced.get(identity, named.get(f"/{path}"))) is not None:
                blanked[path] = text.encode()
                return
            entry = tarfile.TarInfo(path)
            entry.mode, entry.mtime = status.st_mode & 0o777, status.st_mtime
            entry.uid = entry.gid = USER
            if stat.S_ISLNK(status.st_mode):
                entry.type, entry.linkname = tarfile.SYMTYPE, os.readlink(name, dir_fd=folder)
                tar.addfile(entry)
            if not stat.S_ISDIR(status.st_mode) and not stat.S_ISREG(status.st_mode):
                return
            opened = os.open(name, NO_LINK, dir_fd=folder)
            try:
                if not os.path.samestat(status, os.fstat(opened)):
                    msg = f"/{path} changed places during the copy"
                    raise SandboxError(msg)
                if stat.S_ISDIR(status.st_mode):
                    entry.type = tarfile.DIRTYPE
                    tar.addfile(entry)
                    for inner in sorted(os.listdir(opened)):  # noqa: PTH208
                        add(tar, opened, inner, f"{path}/{inner}", device)
                    return
                entry.size = status.st_size
                if (room := room - entry.size) < 0:
                    msg = "the folders are too large to copy into a virtual machine"
                    raise SandboxError(msg)
                with os.fdopen(opened, "rb", closefd=False) as file:
                    tar.addfile(entry, file)
            finally:
                os.close(opened)

        def add_top(tar: tarfile.TarFile, path: str) -> None:
            nonlocal last
            last = path[1:]
            # A second walk could write through a link that the first one copied.
            if any(Path(path).is_relative_to(top) for top in shown if top != path):
                msg = f"{path} was not reached by the copy of the folder above it"
                raise SandboxError(msg)
            with folder_of(path) as above:
                add(tar, above, Path(path).name, last, -1)

        try:
            with tarfile.open(fileobj=self._in, mode="w|") as tar:
                for path in filter(left.__contains__, shown):
                    add_top(tar, path)
                for name, text in blanked.items():
                    entry = tarfile.TarInfo(name)
                    entry.size, entry.uid, entry.gid = len(text), USER, USER
                    tar.addfile(entry, io.BytesIO(text))
        except BrokenPipeError:
            raise
        except RecursionError as error:
            raise SandboxError(_TOO_DEEP) from error
        except OSError as error:
            msg = _TOO_DEEP if error.errno == errno.EMFILE else f"/{last} was not copied: {error}"
            raise SandboxError(msg) from error

    def _load(self) -> None:
        plan: Plan = {**self._plan, "pinned": {}, "replaced": {}, "user": USER, "cgroup": False}
        text = plan_text(plan)
        self._pack(shutil.disk_usage(Path.home()).free // 2)
        self._tunnel.send(b"p", data=text.encode())

    def messages(self) -> Generator[Message, None, None]:
        try:
            self._load()
            yield from self._read()
            if self._why:
                yield Message("error", self._why, [])
        except (OSError, SandboxError) as error:
            self._kill()
            gone = isinstance(error, BrokenPipeError)
            said = "the virtual machine ended early" if gone else str(error)
            yield Message("error", self._why or said, [])
        except GeneratorExit:
            self._kill()
            raise
        finally:
            self._tunnel.end_files()
            with suppress(OSError):
                self._folder.cleanup()

    def _read(self) -> Iterator[Message]:
        started = ended = noted = False
        name = ""
        file: IO[bytes] | None = None
        for kind, lane, data in self._tunnel.frames():
            if kind == b"s" and not started and not ended:
                started = True
                yield from self._started()
            elif kind == b"c" and started and self._is_free(lane):
                self._call(lane)
            elif kind == b"f" and started and not file:
                name, file = os.fsdecode(data), tempfile.TemporaryFile()  # noqa: SIM115
            elif kind == b"r" and started and not file:
                yield Message("removed", os.fsdecode(data), [])
            elif kind == b"d" and file and data:
                file.write(data if file.tell() <= MOST_BYTES else b"")
            elif kind == b"d" and file:
                with file:
                    file.seek(0)
                    yield Message("file", name, [os.dup(file.fileno())])
                file = None
            elif kind == b"x" and not ended and data in _EXIT_CODES and (started or data != b"0"):
                ended = True
                yield Message("exit", data.decode(), [])
            elif kind == b"n" and not ended:
                noted = True
                yield Message("note", data.decode(errors="replace"), [])
            else:
                said = data.decode(errors="replace") if kind == b"e" else ""
                raise SandboxError(said or "the virtual machine broke the protocol")
        if file:
            msg = "the virtual machine ended inside a report"
            raise SandboxError(msg)
        if not noted and any(output.dropped for output in self._outputs):
            msg = "the stop dropped some of the command's output"
            raise SandboxError(msg)

    def stop(self) -> None:
        """End the command, and drop its output that has not come out. Its reports still come."""
        if self._stopped:
            return
        self._stopped = True
        self._ending = True
        self._kill_in(_GRACE_SECONDS, _NOT_ENDED)
        os.dup2(self._nothing, self._in.fileno(), inheritable=False)

    def wait(self) -> int:
        """After stop(), whose clock ends the wait."""
        code = self._job.wait()
        self._deadline = None
        self._said.join(_GRACE_SECONDS)
        os.close(self._nothing)
        return code
