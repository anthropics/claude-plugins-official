"""What a terminal can show."""

from __future__ import annotations

import codecs
import contextlib
import enum
import os
import shutil
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Generator, Mapping

_TRUE_COLOUR_TERMS = ("kitty", "ghostty", "alacritty", "wezterm", "foot", "direct", "rio")
_TRUE_COLOUR_PROGRAMS = {
    "iTerm.app",
    "vscode",
    "WezTerm",
    "ghostty",
    "Hyper",
    "Tabby",
    "WarpTerminal",
}


class Colour(enum.IntEnum):
    NONE = 0
    BASIC = 1
    INDEXED = 2
    TRUE = 3


class Glyphs(enum.IntEnum):
    ASCII = 0
    BLOCKS = 1
    FULL = 2


@dataclass(frozen=True)
class Caps:
    colour: Colour
    glyphs: Glyphs
    motion: bool

    @classmethod
    def of(cls, env: Mapping[str, str], encoding: str, *, windows: bool) -> Caps:
        motion = env.get("CLAUDE_SECURITY_REDUCED_MOTION", "") in {"", "0"}
        return cls(_colour(env, windows), _glyphs(env, encoding, windows), motion)

    @classmethod
    def here(cls) -> Caps:
        return cls.of(os.environ, sys.stdout.encoding or "", windows=os.name == "nt")


def size() -> tuple[int, int]:
    """The terminal's columns and lines, or the usual ones if it does not say."""
    columns, lines = shutil.get_terminal_size()
    # Python 3.9 passes on a terminal's size of 0.
    return columns or 80, lines or 24


def dumb() -> bool:
    """True if TERM says that the terminal acts on no escape sequence. Windows does not set it."""
    return (os.environ.get("TERM") or ("" if os.name == "nt" else "dumb")) == "dumb"


def _colour(env: Mapping[str, str], windows: bool) -> Colour:
    term = env.get("TERM", "")
    if env.get("NO_COLOR"):
        return Colour.NONE
    if env.get("FORCE_COLOR") in {"0", "1", "2", "3"}:
        return Colour(int(env["FORCE_COLOR"]))
    if term == "linux":
        return Colour.BASIC
    indexed = Colour.INDEXED if "256" in term else Colour.BASIC
    if term.startswith("screen") and "TMUX" not in env:
        return indexed
    true = (
        env.get("COLORTERM") in {"truecolor", "24bit"}
        or env.get("TERM_PROGRAM") in _TRUE_COLOUR_PROGRAMS
        or any(name in term for name in _TRUE_COLOUR_TERMS)
        or windows
    )
    return Colour.TRUE if true else indexed


def _glyphs(env: Mapping[str, str], encoding: str, windows: bool) -> Glyphs:
    # Python writes UTF-8 in the C locale too, and can set LC_CTYPE itself, so only LC_ALL is read.
    if not _is_utf8(encoding) or env.get("LC_ALL") in {"C", "POSIX"}:
        return Glyphs.ASCII
    legacy = windows and not {"WT_SESSION", "TERM_PROGRAM", "TERM", "ConEmuANSI"} & env.keys()
    return Glyphs.BLOCKS if legacy or env.get("TERM") == "linux" else Glyphs.FULL


def _is_utf8(encoding: str) -> bool:
    try:
        return codecs.lookup(encoding).name == "utf-8"
    except LookupError:
        return False


if sys.platform == "win32":
    import ctypes
    import msvcrt

    _ESCAPES_OUT = 0x0005

    @contextlib.contextmanager
    def console_mode(fd: int, on: int = _ESCAPES_OUT, off: int = 0) -> Generator[None, None, None]:
        """Set and clear console mode bits. By default, make the console act on escape sequences."""
        kernel, mode = ctypes.windll.kernel32, ctypes.c_ulong()
        handle = ctypes.c_void_p(msvcrt.get_osfhandle(fd))
        known = cast("int", kernel.GetConsoleMode(handle, ctypes.byref(mode)))
        try:
            if known:
                kernel.SetConsoleMode(handle, mode.value & ~off | on)
            yield
        finally:
            if known:
                kernel.SetConsoleMode(handle, mode.value)

else:

    @contextlib.contextmanager
    def console_mode(fd: int, on: int = 0, off: int = 0) -> Generator[None, None, None]:
        """Nothing to set: only a Windows console has these modes."""
        del fd, on, off
        yield
