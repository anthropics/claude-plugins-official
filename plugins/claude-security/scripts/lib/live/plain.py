"""A scan as lines of text: a log while it runs, and a summary when it ends."""

from __future__ import annotations

import sys
import textwrap
import time
from collections import Counter
from contextlib import ExitStack
from itertools import starmap
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from lib import display

from .scan import SEVERITIES, Stage, State
from .terminal import Caps, Colour, Glyphs, console_mode, dumb, size

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .scan import Scan

    Line = list[tuple[str, str]]

# Each shade in 16 colours, in 256 and in full colour.
_SHADES = {
    "text": ("0",) * 3,
    "strong": ("1",) * 3,
    "dim": ("90", "38;5;102", "38;2;135;134;127"),
    "CRITICAL": ("31", "38;5;167", "38;2;214;69;93"),
    "HIGH": ("91", "38;5;173", "38;2;217;119;87"),
    "MEDIUM": ("33", "38;5;179", "38;2;217;179;108"),
    "LOW": ("34", "38;5;68", "38;2;106;155;204"),
}
_LIVE, _FAILED = "HIGH", "CRITICAL"
_ENDED = {State.DONE: ("✻ Scan complete", _LIVE), State.SKIPPED: ("✻ Nothing to scan", _LIVE)}
_PLAIN = {
    Glyphs.ASCII: str.maketrans("✻✽✶✳✢✕⎿…·", "****+xL.."),
    Glyphs.BLOCKS: str.maketrans("✻✽✶✳✢✕⎿…", "****+x└."),
}
_SPINNER = "·✢✳✶✻✽✽✻✶✳✢·"
_STILL = "✻"
_CLEAR_LINE = "\r\x1b[K"
_FRAME_SECONDS = 0.12
_LOG_SECONDS = 0.5
_COUNTS_EVERY = 60.0
_PIPE_COLUMNS = 200


class _News(NamedTuple):
    at: float
    text: str
    shade: str
    ended: bool = False


class _Pen:
    """Turns lines into text in the colours and glyphs that the output can show."""

    def __init__(self) -> None:
        self.caps: Caps = Caps.here()
        self.live: bool = sys.stdout.isatty() and not dumb()

    @property
    def room(self) -> int:
        if not self.live:
            return _PIPE_COLUMNS
        return size()[0] - 1

    def _shaded(self, said: str, shade: str) -> str:
        safe = display.written_out(said)
        if not self.live or self.caps.colour is Colour.NONE:
            return safe
        code = _SHADES.get(shade, _SHADES["text"])[self.caps.colour - 1]
        return f"\x1b[{code}m{safe}\x1b[0m"

    def text(self, line: Line) -> str:
        """The line, with nothing in it from the scan that a terminal acts on."""
        shaded = "".join(starmap(self._shaded, line))
        out = shaded.translate(_PLAIN.get(self.caps.glyphs, {}))
        return out.encode("ascii", "replace").decode() if self.caps.glyphs is Glyphs.ASCII else out


def _cut(text: str, room: int) -> str:
    line = display.written_out(display.single_line(text))
    return line if len(line) <= room else f"{line[: max(room - 1, 0)]}…"


def _clock(seconds: float) -> str:
    minutes, rest = divmod(int(seconds), 60)
    return f"{minutes}:{rest:02}"


def _counts(scan: Scan) -> str:
    n, counted = scan.totals(), display.counted
    if scan.candidates:
        tried = counted(n["candidates"], "candidate")
        return f"{tried} · {n['confirmed']} confirmed · {n['refuted']} refuted"
    return (
        f"{counted(n['running'], 'agent')} at work · {n['files_read']:,}/{n['files']:,} files read"
        f" · {n['tools']:,} tool call{'s' * (n['tools'] != 1)} · {counted(n['leads'], 'lead')}"
    )


def _news(scan: Scan, told: dict[Stage, State], since: int) -> Iterator[_News]:
    """The time, text and shade of each stage that began or ended, and of each new note."""
    for stage, phase in scan.phases.items():
        before, told[stage] = told[stage], phase.state
        if phase.started is not None and before is not phase.state:
            if before in {State.WAITING, State.SKIPPED}:
                yield _News(phase.started, stage.value, "strong")
            if phase.ended is not None:
                took = _clock(phase.ended - phase.started)
                yield _News(
                    phase.ended, f"{stage.value} {phase.state.value} in {took}", "dim", ended=True
                )
    yield from (_News(n.at, f"⎿ {n.text}", "text") for n in scan.notes if n.rev > since)


def _order(news: _News) -> float:
    # A stage ends a moment after the next one starts.
    return news.at - news.ended


def run(scan: Scan) -> None:
    """Print the scan's progress until it ends."""
    pen, told = _Pen(), dict.fromkeys(Stage, State.WAITING)
    target, since, counted = scan.target, 0, 0.0
    facts = (target.mode, target.effort, "sandboxed" if target.sandboxed else "NOT SANDBOXED")
    head = [("✻ ", _LIVE), ("Claude Security plugin", "strong"), (f"  {target.name}", "text")]
    with console_mode(1), ExitStack() as ending:
        if pen.live:
            ending.callback(print, _CLEAR_LINE, end="", flush=True)
        print(pen.text([*head, (f" · {' · '.join(filter(None, facts))}", "dim")]), flush=True)
        while True:
            with scan.changed:
                news = sorted(_news(scan, told, since), key=_order)
                since, now, running, counts = scan.rev, scan.now(), scan.running, _counts(scan)
            if not running or (not pen.live and now - counted >= _COUNTS_EVERY):
                news.append(_News(now, f"⎿ {counts}", "dim"))
                counted = now
            lines = (
                [(f"{_clock(item.at):>7}  ", "dim"), (_cut(item.text, pen.room - 9), item.shade)]
                for item in news
            )
            out = "".join(f"{pen.text(line)}\n" for line in lines)
            if pen.live:
                turn = int(time.monotonic() / _FRAME_SECONDS) % len(_SPINNER)
                sign = _SPINNER[turn] if pen.caps.motion else _STILL
                said = _cut(f"{_clock(now)} · {counts}", pen.room - 2)
                shown = pen.text([(f"{sign} ", _LIVE), (said, "dim")])
                status = shown if running else ""
                out = f"{_CLEAR_LINE}{out}{status}"
            print(out, end="", flush=True)
            if not running:
                return
            time.sleep(_FRAME_SECONDS if pen.live and pen.caps.motion else _LOG_SECONDS)


def summary(scan: Scan) -> str:
    """The closing block: how the scan ended, its findings, and the files that it wrote."""
    pen, result = _Pen(), scan.result
    done = result.state is State.DONE
    found = Counter(finding.severity for finding in scan.findings)
    tally = [(_cut(result.verification, 24), "text")] if result.verification else []
    tally += [(f"{found[level]} {level.lower()}", level) for level in SEVERITIES if found[level]]
    tally += [("no findings", "text")] if done and not found else []
    said = _ENDED.get(result.state, ("✕ Scan not complete", _FAILED))
    took = (f" in {_clock(scan.now())}", "dim")
    head = [said, took, *(part for told in tally for part in ((" · ", "dim"), told))]
    rows: list[Line] = []
    for finding in scan.findings:
        place = _cut(f"{finding.file}:{finding.line}", pen.room // 2)
        rows.append([
            (f"  {_cut(finding.id, 4):<5}", "strong"),
            (f"{_cut(finding.severity, 8):<10}", finding.severity),
            (f"{_cut(finding.title, pen.room - 19 - len(place))}  ", "text"),
            (place, "dim"),
        ])
    wrapped = (
        textwrap.wrap(
            line,
            max(pen.room - 2, 20),
            subsequent_indent="  " * line.startswith("- "),
            break_long_words=False,
            break_on_hyphens=False,
        )
        for line in result.message.splitlines()
    )
    message = [[(f"  {line}", "text")] for held in wrapped for line in held or [""]]
    files = [[(f"  {Path(result.report_dir, name)}", "dim")] for name in result.files]
    sections = [[head], rows, message, files]
    return "\n\n".join("\n".join(map(pen.text, part)) for part in sections if part)
