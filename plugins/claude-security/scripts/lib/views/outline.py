"""The shape of a file's lines, and none of their text."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

MAX_ROWS = 320
_TAB_COLUMNS = 4


def outline(lines: Sequence[bytes]) -> bytes:
    """Two bytes for each of at most MAX_ROWS evenly spaced lines: its indent and its length."""
    rows = min(len(lines), MAX_ROWS)
    spaced = (lines[row * len(lines) // rows] for row in range(rows))
    picked = (line.expandtabs(_TAB_COLUMNS).rstrip() for line in spaced)
    shape = ((len(line) - len(line.lstrip()), len(line)) for line in picked)
    return bytes(min(n, 255) for pair in shape for n in pair)
