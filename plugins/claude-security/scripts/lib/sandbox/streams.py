"""The command's stdin, stdout and stderr. What comes out cannot steer a UTF-8 terminal or a CI
runner."""

from __future__ import annotations

import errno
import os
import re
import select
import threading
import time
from contextlib import suppress
from typing import TYPE_CHECKING

from ..markdown import CONTROL_RE

if TYPE_CHECKING:
    from collections.abc import Callable

_LONGEST_LINE = 32 << 20
_MOST_BYTES = 2 << 30
_CONTROL = re.compile(rf"{CONTROL_RE.pattern}|[\u2028\u2029]")
_COMMAND = re.compile(r"^(\W*?:)(?=:)|##(?=\w*\[)")
# A write must not cut into another's line, on one stream or on two that are one file.
_STDOUT, _STDERR = threading.Lock(), threading.Lock()
_SAY_SECONDS = 1
_last_write = [0.0]


def harmless(line: bytes) -> bytes:
    """`line` with no control character but tab and newline, and with no workflow command."""
    text = _CONTROL.sub("", line.decode(errors="replace"))
    return _COMMAND.sub(r"\g<0> ", text).encode()


def _shown(line: bytes) -> bytes:
    return harmless(line).rstrip(b"\n") + b"\n"


def last_write() -> float:
    """When, by time.monotonic, a write of copy_out last went through."""
    return _last_write[0]


def _write(target: int, line: bytes) -> None:
    with _STDERR if target == 2 or os.path.sameopenfile(1, 2) else _STDOUT:
        view = memoryview(_shown(line))
        while view:
            try:
                view = view[os.write(target, view[: select.PIPE_BUF]) :]
            except BlockingIOError:
                select.select([], [target], [])
            _last_write[0] = time.monotonic()


def say(text: str) -> None:
    """A line of the sandbox's own on stderr. It can quote the command. Where stderr does not drain,
    it waits for a second or two and may lose the line."""
    line = _shown(f"sandbox: {text}".replace("\n", " ").encode(errors="replace"))
    if not _STDERR.acquire(timeout=_SAY_SECONDS):
        return
    try:
        with suppress(OSError):
            for start in range(0, len(line), select.PIPE_BUF):
                if not select.select([], [2], [], _SAY_SECONDS)[1]:
                    break
                os.write(2, line[start : start + select.PIPE_BUF])
    finally:
        _STDERR.release()


def copy_in(source: int, target: int, fail: Callable[[str], None]) -> None:
    """Copy `source` to the command's stdin in the background, and close it at the end. A failed
    read calls `fail`, but for a terminal's EIO and a `source` that is not open for reading."""
    is_terminal = os.isatty(source)

    def read() -> bytes:
        while True:
            try:
                return os.read(source, 1 << 16)
            except BlockingIOError:  # noqa: PERF203
                select.select([source], [], [])
            except OSError as error:
                is_shut_out = error.errno == errno.EIO and is_terminal
                if not (is_shut_out or error.errno == errno.EBADF):
                    fail(f"stdin cannot be read: {error.strerror}")
                return b""

    def run() -> None:
        with suppress(OSError), os.fdopen(target, "wb") as stdin:
            while chunk := read():
                stdin.write(chunk)
                stdin.flush()

    threading.Thread(target=run, daemon=True).start()


def copy_out(source: int, target: int, fail: Callable[[str], None]) -> threading.Thread:
    """Copy output line by line. Calls `fail` if it cannot, or may not, go on."""

    def run() -> None:
        left = _MOST_BYTES
        with os.fdopen(source, "rb") as output:
            try:
                while (line := output.readline(_LONGEST_LINE)) and (left := left - len(line)) > 0:
                    _write(target, line)
            except OSError as error:
                return fail(f"the command's output cannot be written: {error.strerror}")
            except MemoryError:
                return fail("the command's output does not fit in memory")
            return fail("the command printed too much") if line else None

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread
