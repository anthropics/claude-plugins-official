"""A scanned file a finding names: reading it, and finding the line that places the finding."""

from __future__ import annotations

import re
from bisect import bisect_right
from itertools import accumulate
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


def read(scan_root: str, file: str) -> str | None:
    """The text of `file`, relative to `scan_root`; None when it cannot be read."""
    try:
        return Path(scan_root, file).read_bytes().decode("utf-8", "surrogateescape")
    except (OSError, ValueError):
        return None


def placed_line(text: str | None, line: int, snippet: str) -> int:
    """The 1-based line of `text` that places a finding declaring `line` and quoting `snippet`.

    `text` is the text of the finding's file, None when it was not read; the
    declared `line` comes back unchanged then, and when no line of the file
    places the finding (placing_row).
    """
    if text is None:
        return line
    row = placing_row(normalized_lines(text), line, snippet)
    return line if row is None else row + 1


def normalized_lines(source: str) -> list[str]:
    """A file's lines, split on the newline alone, each with its whitespace normalized."""
    return [" ".join(each.split()) for each in source.split("\n")]


def quoted_lines(text: str, snippet: str, *, whole: bool) -> set[int]:
    """Every 1-based line of `text` on which the quoted `snippet` occurs, whitespace aside.

    With `whole`, only occurrences that are entire lines of `text` count, so a
    quote of part of a line matches nothing.
    """
    lines = normalized_lines(text)
    quoted = " ".join(snippet.split())
    spans = [
        (first, last)
        for first, last in occurrences(lines, quoted)
        if not whole or " ".join(filter(None, lines[first : last + 1])) == quoted
    ]
    return {row + 1 for first, last in spans for row in range(first, last + 1)}


def placing_span(lines: Sequence[str], line: int, snippet: str) -> tuple[int, int] | None:
    """The (first, last) rows of the occurrence of `snippet` nearest the declared line, or None."""
    declared = line - 1
    return min(
        occurrences(lines, " ".join(snippet.split())),
        key=lambda span: abs(min(max(declared, span[0]), span[1]) - declared),
        default=None,
    )


def placing_row(lines: Sequence[str], line: int, snippet: str) -> int | None:
    """The index into the normalized `lines` of the one placing a finding; None when none does.

    The finding is placed on the line nearest its declared `line` where
    `snippet`, the code it quotes, appears, whitespace aside, and on the
    declared line itself when it appears nowhere.
    """
    declared = line - 1
    span = placing_span(lines, line, snippet)
    at = declared if span is None else min(max(declared, span[0]), span[1])
    return at if 0 <= at < len(lines) else None


def occurrences(lines: Sequence[str], quoted: str) -> list[tuple[int, int]]:
    """The (first, last) index into the normalized `lines` of each occurrence of `quoted`."""
    if not quoted:
        return []
    filled = [row for row, line in enumerate(lines) if line]
    starts = list(accumulate((len(lines[row]) + 1 for row in filled), initial=0))
    flat = " ".join(lines[row] for row in filled)

    def row_at(offset: int) -> int:
        return filled[bisect_right(starts, offset) - 1]

    return [
        (row_at(found.start()), row_at(found.end() - 1))
        for found in re.finditer(re.escape(quoted), flat)
    ]
