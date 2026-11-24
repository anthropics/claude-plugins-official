"""The full screen and the raw keys of a terminal, for the length of a view."""

from __future__ import annotations

import contextlib
import os
import re
import signal
import sys
import time
from typing import TYPE_CHECKING, Callable

from lib.live.terminal import size as terminal_size

if TYPE_CHECKING:
    from collections.abc import Generator
    from types import FrameType

_ENTER = b"\x1b[?1049h\x1b[?25l\x1b[?7l\x1b[0m\x1b[2J"
_LEAVE = b"\x1b[?2026l\x1b[0m\x1b[2J\x1b[H\x1b[?7h\x1b[?25h\x1b[?1049l"
_QUESTION, _ANSWER = re.compile(rb"\x1b\[[56]n"), re.compile(r"\x1b\[(0n|1;\d+R)")
_PIECE = 4096


class Terminal:
    def __init__(self) -> None:
        self._held: contextlib.ExitStack[bool | None] = contextlib.ExitStack()
        self._pause: bool = False
        self._asked: int = 0
        self._answered: int = 0

    @classmethod
    @contextlib.contextmanager
    def taken(cls) -> Generator[Terminal, None, None]:
        """Hold the terminal for a block, and give it back as it was however the block ends."""
        terminal = cls()
        with _handling(terminal._ask_to_pause), terminal._held:
            terminal._take()
            yield terminal

    def size(self) -> tuple[int, int]:
        with contextlib.suppress(OSError, ValueError):
            told = os.get_terminal_size(sys.stdout.fileno())
            if min(told) > 0:
                return told
        return terminal_size()

    @property
    def unanswered(self) -> int:
        """The questions that the terminal has still to answer."""
        return self._asked - self._answered

    def write(self, output: bytes) -> None:
        self._asked += len(_QUESTION.findall(output))
        _write(output)

    def read(self, timeout: float) -> str | None:
        """What the terminal sent within `timeout` seconds. None: it was paused and taken anew."""
        typed = self._read(timeout)
        if (self._pause or "\x1a" in typed) and sys.platform != "win32":
            self._held.close()
            handler = signal.signal(signal.SIGTSTP, signal.SIG_DFL)
            os.killpg(os.getpgrp(), signal.SIGTSTP)
            signal.signal(signal.SIGTSTP, handler)
            self._take()
            return None
        return typed

    def _read(self, timeout: float) -> str:
        typed = _typed(timeout)
        self._answered += len(_ANSWER.findall(typed))
        return typed

    def _take(self) -> None:
        sys.stdout.flush()
        self._held.enter_context(_raw())
        self._held.callback(self._leave)
        self._pause = False
        self._asked = self._answered
        _write(_ENTER)

    def _leave(self) -> None:
        _write(_LEAVE)
        # An answer that is still on its way would reach the shell as typed text.
        deadline = time.monotonic() + (3.0 if self._answered else 1.5)
        with contextlib.suppress(EOFError, OSError):
            while self._answered < self._asked and time.monotonic() < deadline:
                self._read(0.05)

    def _ask_to_pause(self, *_: object) -> None:
        self._pause = True


@contextlib.contextmanager
def _handling(pause: Callable[[int, FrameType | None], object]) -> Generator[None, None, None]:
    """Turn the signals that would end the process at once into KeyboardInterrupt, and SIGTSTP into
    a call of `pause`. A signal that has a handler already keeps it."""
    stop = signal.default_int_handler
    handlers = {
        "SIGTERM": stop,
        "SIGHUP": stop,
        "SIGQUIT": stop,
        "SIGBREAK": stop,
        "SIGTSTP": pause,
    }
    with contextlib.ExitStack() as before:
        for number in signal.Signals:
            if number.name in handlers and signal.getsignal(number) == signal.SIG_DFL:
                before.callback(signal.signal, number, signal.SIG_DFL)
                signal.signal(number, handlers[number.name])
        yield


def _write(output: bytes) -> None:
    text = output.decode(errors="replace")
    with contextlib.suppress(OSError), open(1, "wb", buffering=0, closefd=False) as out:
        for start in range(0, len(text), _PIECE):
            left = text[start : start + _PIECE].encode()
            while left:
                left = left[out.write(left) or 0 :]


if sys.platform == "win32":
    import msvcrt

    from lib.live.terminal import console_mode

    _CTRL_C_LINES_ECHO = 0x0007

    @contextlib.contextmanager
    def _raw() -> Generator[None, None, None]:
        keys = console_mode(sys.stdin.fileno(), 0, _CTRL_C_LINES_ECHO)
        with console_mode(sys.stdout.fileno()), keys:
            yield

    def _typed(timeout: float) -> str:
        deadline, typed = time.monotonic() + timeout, ""
        while not msvcrt.kbhit() and time.monotonic() < deadline:
            time.sleep(0.01)
        while msvcrt.kbhit():
            typed += msvcrt.getwch()
        # A special key is \0 or à, then a code. The view reads à and the next character as one key.
        return typed.replace("\0", "\xe0")

else:
    import select
    import termios

    _UNFINISHED = re.compile(rb"\x1b(\[[0-?]*|O)?\Z")

    @contextlib.contextmanager
    def _raw() -> Generator[None, None, None]:
        fd = sys.stdin.fileno()
        before = termios.tcgetattr(fd)
        raw = termios.tcgetattr(fd)
        raw[0] &= ~(termios.IXON | termios.ICRNL)
        raw[3] &= ~(termios.ECHO | termios.ICANON | termios.ISIG | termios.IEXTEN)
        raw[6][termios.VMIN], raw[6][termios.VTIME] = 1, 0
        try:
            termios.tcsetattr(fd, termios.TCSANOW, raw)
            yield
        finally:
            with contextlib.suppress(termios.error):
                termios.tcsetattr(fd, termios.TCSAFLUSH, before)

    def _typed(timeout: float) -> str:
        fd = sys.stdin.fileno()
        if not select.select([fd], [], [], timeout)[0]:
            return ""
        typed = os.read(fd, 1024)
        if not typed:
            raise EOFError
        # The rest of an escape sequence can come a moment after its first bytes.
        while _UNFINISHED.search(typed) and select.select([fd], [], [], 0.05)[0]:
            more = os.read(fd, 1024)
            if not more:
                raise EOFError
            typed += more
        return typed.decode("utf-8", "ignore")
