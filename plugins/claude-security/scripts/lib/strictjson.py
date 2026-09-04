"""JSON in and out of the scripts, stricter than the json module in both directions.

Input is model-written and output is read by other tools, so load() refuses
what json.load admits but a conforming reader does not (NaN, Infinity, a
number that overflows to infinity, nesting past the interpreter's limit), and
text() keeps non-ASCII readable while escaping what UTF-8 or a JSONL line
reader cannot take (an unpaired surrogate, the Unicode line separators).
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from typing import TYPE_CHECKING, NoReturn, cast

if TYPE_CHECKING:
    from pathlib import Path
    from typing import TypeGuard

JsonMap = Mapping[str, object]

# The separators a naive line reader would split a JSONL record on.
_SEPARATOR_ESCAPES = {0x85: "\\u0085", 0x2028: "\\u2028", 0x2029: "\\u2029"}
# The code units UTF-8 cannot encode; surrogateescape mints them from bytes.
_SURROGATES = re.compile(r"[\ud800-\udfff]")


def is_map(value: object) -> TypeGuard[JsonMap]:
    """Whether `value` is a JSON object."""
    return isinstance(value, dict)


def is_list(value: object) -> TypeGuard[list[object]]:
    """Whether `value` is a JSON array."""
    return isinstance(value, list)


def is_str(value: object) -> TypeGuard[str]:
    """Whether `value` is a JSON string."""
    return isinstance(value, str)


def is_int(value: object) -> TypeGuard[int]:
    """Whether `value` is a JSON integer; JSON's booleans are not numbers."""
    return isinstance(value, int) and not isinstance(value, bool)


def has_lone_surrogate(value: str) -> bool:
    """Whether `value` holds an unpaired surrogate, the one code unit UTF-8 cannot encode."""
    return _SURROGATES.search(value) is not None


def _refuse(token: str) -> NoReturn:
    msg = f"{token} is not JSON"
    raise ValueError(msg)


def _finite(digits: str) -> float:
    value = float(digits)
    if not math.isfinite(value):
        msg = f"{digits} is out of range"
        raise ValueError(msg)
    return value


def load(path: Path) -> object:
    """The JSON value in `path`; OSError if unreadable, ValueError if not strict JSON."""
    with path.open(encoding="utf-8") as handle:
        try:
            return cast("object", json.load(handle, parse_constant=_refuse, parse_float=_finite))
        except RecursionError as error:
            msg = "nested too deeply"
            raise ValueError(msg) from error


def text(value: object, indent: int | None = None) -> str:
    """`value` as UTF-8-encodable JSON text: non-ASCII kept, finite only, separators escaped."""
    dumped = json.dumps(value, ensure_ascii=False, allow_nan=False, indent=indent)
    return _SURROGATES.sub(
        lambda match: f"\\u{ord(match.group()):04x}", dumped.translate(_SEPARATOR_ESCAPES)
    )
