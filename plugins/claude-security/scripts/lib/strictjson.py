"""JSON in and out of the scripts, stricter than the json module in both directions.

Input is model-written and output is read by other tools, so load() refuses
what json.load admits but a conforming reader does not (NaN, Infinity, a
number that overflows to infinity, nesting past the interpreter's limit) and,
apart from those, a whole number of more than 4,300 characters, and
text() keeps non-ASCII readable while escaping what UTF-8 or a JSONL line
reader cannot take (an unpaired surrogate, the Unicode line separators).
"""

from __future__ import annotations

import errno
import json
import math
import re
from collections.abc import Mapping
from typing import TYPE_CHECKING, NoReturn, cast

# pyright: reportMissingModuleSource=false
if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from typing_extensions import TypeGuard

JsonMap = Mapping[str, object]

# The separators a naive line reader would split a JSONL record on.
_SEPARATOR_ESCAPES = {0x85: "\\u0085", 0x2028: "\\u2028", 0x2029: "\\u2029"}
# The code units UTF-8 cannot encode; surrogateescape mints them from bytes.
_SURROGATES = re.compile(r"[\ud800-\udfff]")
_MOST_DIGITS = 4300


def is_map(value: object) -> TypeGuard[JsonMap]:
    """Whether `value` is a JSON object."""
    return isinstance(value, dict)


def is_list(value: object) -> TypeGuard[list[object]]:
    """Whether `value` is a JSON array."""
    return isinstance(value, list)


def is_str(value: object) -> TypeGuard[str]:
    """Whether `value` is a JSON string."""
    return isinstance(value, str)


def clean(value: object) -> str:
    """A record's text field, stripped; empty when absent or not text."""
    return value.strip() if is_str(value) else ""


def is_int(value: object) -> TypeGuard[int]:
    """Whether `value` is a JSON integer; JSON's booleans are not numbers."""
    return isinstance(value, int) and not isinstance(value, bool)


def as_int(value: object) -> int:
    """A record's integer field; 0 when absent or not an integer."""
    return value if is_int(value) else 0


def as_map(value: object) -> JsonMap:
    """A record's object field; empty when absent or not an object."""
    return value if is_map(value) else {}


def maps(value: object) -> list[JsonMap]:
    """The objects in a record's array field; empty when absent or not an array."""
    return [item for item in value if is_map(item)] if is_list(value) else []


def strings(value: object) -> list[str]:
    """The strings in a record's array field; empty when absent or not an array."""
    return [item for item in value if is_str(item)] if is_list(value) else []


def has_lone_surrogate(value: str) -> bool:
    """Whether `value` holds a surrogate, the one code unit UTF-8 cannot encode, even one that
    stands beside its other half."""
    return _SURROGATES.search(value) is not None


def well_formed(value: str) -> str:
    """`value` with each unpaired surrogate as U+FFFD, and each high surrogate with a low one right
    after it as the one character that the two encode."""
    return value.encode("utf-16", "surrogatepass").decode("utf-16", "replace")


def surrogates_are_bytes(value: str) -> bool:
    """Whether `value` is text that decoding bytes with errors="surrogateescape" gives: each
    surrogate in DC80-DCFF, and no consecutive ones whose bytes read as UTF-8."""
    try:
        return value == value.encode("utf-8", "surrogateescape").decode("utf-8", "surrogateescape")
    except UnicodeEncodeError:
        return False


def _refuse(token: str) -> NoReturn:
    msg = f"{token} is not JSON"
    raise ValueError(msg)


def _finite(digits: str) -> float:
    value = float(digits)
    if not math.isfinite(value):
        msg = "a number is out of range"
        raise ValueError(msg)
    return value


def _whole(digits: str) -> int:
    if len(digits) > _MOST_DIGITS:
        msg = "a number is too long"
        raise ValueError(msg)
    return int(digits)


def loads(
    document: str, object_pairs_hook: Callable[[list[tuple[str, object]]], object] | None = None
) -> object:
    """The JSON value in `document`; ValueError if not strict JSON, or if a whole number has more
    than 4,300 characters. `object_pairs_hook` is json.loads()'s."""
    try:
        return cast(
            "object",
            json.loads(
                document,
                parse_constant=_refuse,
                parse_float=_finite,
                parse_int=_whole,
                object_pairs_hook=object_pairs_hook,
            ),
        )
    except RecursionError as error:
        msg = "nested too deeply"
        raise ValueError(msg) from error


def load(path: Path, encoding: str = "utf-8") -> object:
    """The JSON value in `path`, read as `encoding`; OSError if unreadable or not a regular file,
    ValueError if the bytes are not in that encoding, or as in loads()."""
    if path.exists() and not path.is_file():
        raise OSError(errno.EINVAL, "not a regular file", str(path))
    return loads(path.read_text(encoding=encoding))


def text(value: object, indent: int | None = None) -> str:
    """`value` as UTF-8-encodable JSON text: non-ASCII kept, finite only, separators escaped."""
    dumped = json.dumps(value, ensure_ascii=False, allow_nan=False, indent=indent)
    return _SURROGATES.sub(
        lambda match: f"\\u{ord(match.group()):04x}", dumped.translate(_SEPARATOR_ESCAPES)
    )
