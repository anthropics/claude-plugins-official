"""A scan as the views read it, with nothing in it that does not print."""

from __future__ import annotations

import json
import struct
import unicodedata
from typing import TYPE_CHECKING, cast

from lib import display, strictjson

if TYPE_CHECKING:
    from collections.abc import Sequence

    from lib.live.atlas import Atlas
    from lib.live.scan import Scan

_MOST_CHARS = 64 * 1024


def _printable(value: object) -> object:
    if isinstance(value, str):
        return "\n".join(map(display.written_out, display.capped(value, _MOST_CHARS).splitlines()))
    if strictjson.is_map(value):
        return {key: _printable(held) for key, held in value.items()}
    if isinstance(value, (list, tuple)):
        return [_printable(held) for held in cast("Sequence[object]", value)]
    return value


def _line(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def _joins_the_last(ch: str) -> bool:
    # Hangul's conjoining vowels and finals are letters, but take no cell of their own.
    mark = unicodedata.category(ch) in {"Mn", "Me"}
    return mark or "\u1160" <= ch <= "\u11ff" or "\ud7b0" <= ch <= "\ud7ff"


def atlas(tree: Atlas) -> bytes:
    """Each plot's path, line count and outline."""
    names = (display.written_out(plot.path).encode()[:0xFFFF] for plot in tree.plots)
    return struct.pack("<I", len(tree.plots)) + b"".join(
        struct.pack("<H", len(name))
        + name
        + struct.pack("<IH", min(plot.lines, 0xFFFFFFFF), len(plot.outline) // 2)
        + plot.outline
        for name, plot in zip(names, tree.plots)
    )


def delta(scan: Scan, since: int) -> str:
    """Scan.delta(since) on one line, with the characters that do not take one terminal cell."""
    change = {key: _printable(held) for key, held in scan.delta(since).items()}
    text = _line(change)
    paths = "" if since else "".join(plot.path for plot in scan.atlas.plots)
    if text.isascii() and paths.isascii():
        return text
    seen = sorted(ch for ch in {*text, *paths} if ch.isprintable())
    wide = "".join(ch for ch in seen if unicodedata.east_asian_width(ch) in {"W", "F"})
    marks = "".join(filter(_joins_the_last, seen))
    return _line({**change, "wide": wide, "marks": marks})
