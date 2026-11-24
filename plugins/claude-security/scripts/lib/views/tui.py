"""The full-screen terminal view of a scan."""

from __future__ import annotations

import contextlib
import json
import os
import re
import struct
import time
from dataclasses import asdict
from typing import TYPE_CHECKING, cast

from lib.live import plain
from lib.live.terminal import Caps, Glyphs, dumb

from . import renderer
from .screen import Terminal

if TYPE_CHECKING:
    from collections.abc import Mapping

    from lib.live.scan import Scan

# The view's table of glyphs has one entry more than Glyphs.
_NERD_GLYPHS = len(Glyphs)
# An answer of the view starts with whether to leave and the seconds to wait.
_ANSWER = struct.Struct("<?d")
# The sequences that the view writes: moves, colors, a clear, two questions and synchronized output.
_SEQUENCE = re.compile(
    r"\x1b\[(?:\d{1,4};\d{1,4}H|H|\d{1,4}G|[\d;]{1,64}m|2J|[56]n|\?2026[hl])", re.ASCII
)
# The terminal types an answer to each, and a frame has one at its start and one at its end.
_MOST_QUESTIONS = 2
# A view stops asking a silent terminal after a few. Late answers reach the shell as typed text.
_MOST_UNANSWERED = 64
# The controls, and what stands for a byte that the terminal's encoding does not take.
_CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f\udc80-\udcff]")


def link(env: Mapping[str, str]) -> dict[str, bool]:
    """What the environment says of the link to the terminal."""
    remote = bool({"SSH_CONNECTION", "SSH_CLIENT", "SSH_TTY"} & env.keys())
    # tmux and screen answer status requests themselves, so the answers say nothing of the link.
    return {"remote": remote, "relayed": remote and bool({"TMUX", "STY"} & env.keys())}


def light_background(env: Mapping[str, str]) -> bool:
    """True if the terminal names a light background in COLORFGBG."""
    # The last field is the background: 7 is white, and 9 to 15 are bright.
    return env.get("COLORFGBG", "").rpartition(";")[2] in {"7", *map(str, range(9, 16))}


def checked(output: bytes, *, utf8: bool = True) -> bytes:
    """The view's output. Raises RendererError on a control or a byte that a view does not write."""
    text = output.decode("utf-8" if utf8 else "ascii", "surrogateescape")
    asked = text.count("\x1b[5n") + text.count("\x1b[6n")
    if asked > _MOST_QUESTIONS or _CONTROL.search(_SEQUENCE.sub("", text)):
        msg = "the view wrote an unknown control sequence, or asked too much"
        raise renderer.RendererError(msg)
    return output


def _show(scan: Scan, facts: dict[str, object]) -> None:
    view = renderer.Renderer(scan, "term/main.mjs")
    with contextlib.closing(view), Terminal.taken() as terminal, contextlib.suppress(EOFError):
        view.ask(b"C" + json.dumps(facts).encode())
        typed, began, ended = None, 0.0, 0.0
        while True:
            times = struct.pack("<ddd", time.monotonic(), began, ended)
            if typed:
                answer = view.ask(b"K" + times + typed.encode(errors="replace"))
            elif typed is None:
                answer = view.ask(b"R" + times)
            else:
                answer = view.show(b"T" + times + struct.pack("<HH", *terminal.size()))
            if len(answer) < _ANSWER.size:
                msg = "the view gave no answer"
                raise renderer.RendererError(msg)
            leave, wait = cast("tuple[bool, float]", _ANSWER.unpack_from(answer))
            if leave:
                return
            if terminal.unanswered > _MOST_UNANSWERED:
                msg = "the view asked the terminal too many questions"
                raise renderer.RendererError(msg)
            began = time.monotonic()
            terminal.write(checked(answer[_ANSWER.size :], utf8=facts["glyphs"] != Glyphs.ASCII))
            ended = time.monotonic()
            typed = terminal.read(max(wait - (ended - began), 0) if wait < 1 else 0)


def run(scan: Scan, url: str = "", *, nerd_fonts: bool = False, light: bool | None = None) -> None:
    """Show the scan until the person quits. While the scan runs, quitting asks first. Where the
    view cannot be drawn, print the scan's progress as lines."""
    caps = Caps.here()
    facts: dict[str, object] = {**asdict(caps), **link(os.environ)}
    facts |= {"url": url, "asks": os.name != "nt"}
    facts["light"] = light_background(os.environ) if light is None else light
    if nerd_fonts and caps.glyphs is not Glyphs.ASCII:
        facts["glyphs"] = _NERD_GLYPHS
    try:
        if not dumb():
            _show(scan, facts)
            return
    except renderer.RendererError as error:
        print(f"The full-screen view is off: {error}.", flush=True)
    plain.run(scan)
