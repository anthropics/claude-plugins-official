"""Model-written text made safe to place in Markdown, as prose or in a code span, and a list of
such spans for a sentence."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .display import single_line
from .strictjson import clean

if TYPE_CHECKING:
    from collections.abc import Sequence

# ASCII and C1 controls but \t and \n, and the bidirectional characters that reorder text.
CONTROL_RE = re.compile(
    r"[\x00-\x08\x0b-\x1f\x7f-\x9f\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]"
)
# More than 79 backticks, which a code span may fail to hold: the 79 to keep, and the rest.
LONG_RUN_RE = re.compile(r"(`{79})`+")
# Runs that could open or close a Markdown fence.
FENCE_RUN_RE = re.compile(r"`{3,}|~{3,}")
# HTML that would open or close a collapsed section, or open a comment.
SECTION_HTML_RE = re.compile(r"<(?=/?(?:details|summary)\b|!--)", re.IGNORECASE)
HEADING_RE = re.compile(r"^ {0,3}(?=#)", re.MULTILINE)
# GitHub's Markdown library closes no code span that is fenced with more than 80 backticks.
_LONGEST_RUN = "`" * 79
_OVERLONG_RUN = re.compile(_LONGEST_RUN + "`+")
_CODE = rf"(?<!`)(?P<ticks>`{{1,{len(_LONGEST_RUN)}}})(?!`)[^\n]+?(?<!`)(?P=ticks)(?!`)"
_ADDRESS = (
    r"(?i:(?:https?|ftp)://|mailto:|xmpp:|www\.|(?<![\w.+-])[\w.+-]+@[\w.-])"
    r"[^ \t\n]*(?<![,.;:!?'\")\]}])"
)
_ACTS = r"[\\*\[~|`$<&]|(?<![A-Za-z0-9])_|_(?![A-Za-z0-9])"
_PIECE = re.compile(f"(?:{_CODE}|(?P<address>{_ADDRESS}))+|(?P<acts>{_ACTS})")
_NO_CODE = re.compile(f"(?P<address>{_ADDRESS})|(?P<acts>{_ACTS})")
_ENTITY = {"<": "&lt;", "&": "&amp;", "\\": "&bsol;"}
_LINE_START = re.compile(r"^(\d*)([#>+=.):-])", re.MULTILINE)
_LINE_END = re.compile(r"\r\n?|[\x0b\x0c\x1c-\x1f\x85]")
_INDENT = re.compile(r"(?<=\n)[ \t]+|(?<![ \t])[ \t]+(?=\n)")


def printable(text: str) -> str:
    """`text` with control and bidirectional-formatting characters removed."""
    return CONTROL_RE.sub("", text)


def fenceable(text: str) -> str:
    """printable(text), each run of more than 79 backticks cut to 79, for a code span or a fence."""
    return LONG_RUN_RE.sub(r"\1", printable(text))


def apart(text: str) -> str:
    """`text` with a space in place of each character that printable() removes."""
    return CONTROL_RE.sub(" ", text)


def section(markdown: str) -> str:
    """`markdown` with control characters removed and the HTML that would open or close a
    collapsed section, or open a comment, escaped."""
    return SECTION_HTML_RE.sub("&lt;", printable(markdown))


def prose(value: object) -> str:
    """A model-written text field made safe to place in Markdown: treated as section() treats
    its text, with fence-length runs of backticks or tildes also broken by zero-width spaces, so
    the text cannot open a fence, carry an HTML comment, or leave the section it sits in."""
    return _defused(clean(value))


def _defused(text: str) -> str:
    """`text` treated as section() treats it, with fence-length runs of backticks or tildes also
    broken by zero-width spaces."""
    return FENCE_RUN_RE.sub(lambda run: "\u200b".join(run.group(0)), section(text))


def under_a_heading(markdown: str) -> str:
    """prose(markdown) with a backslash before each "#" that opens a line, so that no such line is a
    heading."""
    return HEADING_RE.sub(r"\g<0>\\", prose(markdown))


def one_line(value: object) -> str:
    """prose(value) folded onto one line, for a field shown in a heading or a table cell."""
    return single_line(prose(value))


def unbroken(text: str) -> str:
    """`text`, a name or a piece of code, treated as _defused() treats it, on one line. Its spaces
    stay as they are."""
    return " ".join(filter(None, _defused(text).splitlines()))


def span(text: str) -> str:
    """A name or a piece of code as a code span on one line, with a space in place of each character
    that printable() removes. Its own spaces stay as they are."""
    return code_span(unbroken(apart(text)))


def code_span(text: str) -> str:
    """fenceable(text) as an inline code span fenced with more backticks than any run inside it, so
    a backtick in the text cannot close it."""
    text = fenceable(text)
    runs: list[str] = re.findall(r"`+", text)
    ticks = "`" * max((len(run) + 1 for run in runs), default=1)
    # Markdown strips one space from each end of a span that has one at both, and is not all spaces.
    spaced = text.startswith(" ") and text.endswith(" ") and bool(text.strip(" "))
    pad = " " if text.startswith("`") or text.endswith("`") or spaced else ""
    return f"{ticks}{pad}{text}{pad}{ticks}"


def at_most(limit: int, items: Sequence[str]) -> str:
    """The first `limit` items, with commas between them, and how many more there are."""
    more = len(items) - limit
    return ", ".join(items[:limit]) + (f", and {more} more" if more > 0 else "")


def literal(text: str) -> str:
    """A record's plain `text` as Markdown that shows it as written. A web or mail address becomes
    code, and what would act as Markdown is escaped. The text's own code spans stay, unless one of
    its backticks is in none. A control character that is white space, but a tab, ends its line. A
    tab inside a line stays. Any other control character, each line's indent and the white space at
    its end are dropped."""
    text = _INDENT.sub("", printable(_LINE_END.sub("\n", text)).strip())
    lone = any(piece["acts"] == "`" for piece in _PIECE.finditer(text))
    shown = (_NO_CODE if lone else _PIECE).sub(_escaped, text)
    return _LINE_START.sub(r"\1\\\2", shown)


def _escaped(piece: re.Match[str]) -> str:
    if piece["acts"]:
        return _ENTITY.get(piece[0]) or f"\\{piece[0]}"
    return code(piece[0]) if piece["address"] else piece[0]


def inline(text: str) -> str:
    """literal(text) on one line, with one space between words."""
    return single_line(literal(text))


def code(text: str) -> str:
    """`text` on one line as a code span, with each run of 80 or more backticks cut to 79. Empty if
    none of it can be shown."""
    shown = _OVERLONG_RUN.sub(_LONGEST_RUN, printable(text.replace("\n", " ")))
    return code_span(shown) if shown.strip() else ""


def location(file: str, line: int) -> str:
    """A file and its line as code, or the file alone if the line is unknown."""
    return code(f"{file}:{line}" if line > 0 else file)
