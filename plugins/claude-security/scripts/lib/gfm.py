"""Model-written text made safe for GitHub Flavored Markdown (GFM) that GitHub draws for other
people, such as a review (and its copy in REVIEW.md) or a job summary: nothing in it loads by
itself. Also code spans, fences and sections that nothing inside can close. For any other report
on the user's disk, use lib/markdown.py."""

from __future__ import annotations

import re
from collections import Counter

from .markdown import FENCE_RUN_RE, fenceable, printable
from .markdown import code_span as markdown_code_span
from .strictjson import clean, has_lone_surrogate, well_formed

ZERO_WIDTH = "\u200b"
_LOADS_RE = re.compile(
    r"!(?=\[)"
    r"|<(?=[?!]|/?[A-Za-z][\w-]*(?:[\s/>]|$))"
    r"|(?:(?<!`)`{3,}(?!`)|(?<!~)~{3,}(?!~))[ \t]*"
    r"(?!(?!(?:mermaid|geojson|topojson|stl|math|suggestion)\b)[A-Za-z0-9_+#.-]*(?:[ \t\n]|$))",
    re.IGNORECASE,
)
_REFERS_RE = re.compile(
    r"@(?=[A-Za-z0-9&])|#(?=[0-9])|(?<![A-Za-z0-9])(?i:gh)(?=\\?-[0-9])|&(?=#|commat;|num;)"
)
_INERT = str.maketrans({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    **{sign: f"\\{sign}" for sign in "\\[]*_~|$"},
})
_LEADING_RE = re.compile(r"^(?:[-+]|\d+[.)])")
_LINKING_RE = re.compile(r"[@#]|:(?=//)|(?i:www)(?=\.)|(?i:gh)(?=-\d)")


_MAY_HIDE_A_BACKTICK_RE = re.compile(r"[<\[$]|\S$")
# What shows as nothing or as a blank: Unicode's Default_Ignorable_Code_Point, U+2028 and U+2029.
INVISIBLE_RE = re.compile(
    r"[\u00ad\u034f\u061c\u115f\u1160\u17b4\u17b5\u180b-\u180f\u200b-\u200f\u2028-\u202e"
    r"\u2060-\u206f\u3164\ufe00-\ufe0f\ufeff\uffa0\ufff0-\ufff8"
    r"\U0001bca0-\U0001bca3\U0001d173-\U0001d17a\U000e0000-\U000e0fff]"
)


def postable(text: str) -> str:
    """printable(text) with U+FFFD in place of each lone surrogate, for a text that goes to
    GitHub. A high surrogate with a low one right after it, as given or once printable() has
    removed what stood between them, becomes the one character that the two encode."""
    return well_formed(printable(text))


def section(markdown: str) -> str:
    """`markdown` as printable() leaves it, with a zero-width space, inside code too, after each
    start of an image, of HTML, of a fence that GitHub draws or offers to commit, and of a mention
    or a short reference such as #12. The space is meant to keep the text from loading anything by
    itself, and from notifying anybody."""
    return _REFERS_RE.sub(rf"\g<0>{ZERO_WIDTH}", _loads_nothing(markdown))


def _loads_nothing(markdown: str) -> str:
    """section()'s first half: `markdown` as printable() leaves it, with a zero-width space after
    each start of what GitHub could fetch, draw or read as HTML."""
    return _LOADS_RE.sub(rf"\g<0>{ZERO_WIDTH}", printable(markdown))


def prose(value: object) -> str:
    """A model-written text field as section() leaves it, stripped, with fence-length runs of
    backticks or tildes also broken by zero-width spaces. So the text cannot forge a suggestion
    block, carry a finding marker of its own, or leave the section it sits in."""
    stripped = section(clean(value)).strip()
    return FENCE_RUN_RE.sub(lambda run: ZERO_WIDTH.join(run.group(0)), stripped)


def one_line(value: object) -> str:
    """`value` folded onto one line, then made safe as prose() makes it, for a field shown in a
    heading or a table cell. Where it ends in an odd number of backslashes, one more is added, so
    that the last one shows and escapes nothing that the caller writes next. Its backticks are
    _paired() first. All of them also become apostrophes unless each span opens at the start or
    behind a space, with no "<", "[" or "$" before it outside a span."""
    line = _paired(plain_line(clean(value)))
    if any(_MAY_HIDE_A_BACKTICK_RE.search(part) for part in line.split("`")[:-1:2]):
        line = line.replace("`", "'")
    text = prose(line)
    return text + "\\" * ((len(text) - len(text.rstrip("\\"))) % 2)


def _paired(line: str) -> str:
    """`line`, with an apostrophe for every backtick if one has no partner, or a span opens with
    more than one."""
    parts = line.split("`")
    return line.replace("`", "'") if len(parts) % 2 == 0 or "" in parts[1::2] else line


def plain_line(text: str) -> str:
    """printable(text) folded onto one line, for a plain-text log or a code span."""
    return " ".join(printable(text).split())


def inert(value: object) -> str:
    """A model-written text that may hold words and code spans only, on one line. Outside its code
    spans, each character that opens Markdown, HTML or math is escaped, and a zero-width space
    follows what starts a mention, a reference or a bare link. An emoji code and a bare commit id
    still render. Its backticks are _paired() first."""
    parts = _paired(plain_line(clean(value))).split("`")
    shown = "".join(
        code_span(part)
        if at % 2
        else _LINKING_RE.sub(rf"\g<0>{ZERO_WIDTH}", part.translate(_INERT))
        for at, part in enumerate(parts)
    )
    return _LEADING_RE.sub(lambda mark: f"{mark[0][:-1]}\\{mark[0][-1]}", shown)


def code_span(text: str) -> str:
    """`text`, treated as _loads_nothing() and then fenceable() treat it, as an inline code span
    fenced with more backticks than any run inside it, so a backtick in the text cannot close it."""
    return markdown_code_span(_loads_nothing(text))


def fenced(text: str | None, info: str) -> str:
    """fenceable(text) in a code fence with more backticks than any run inside it, so that none
    can close it. None gives an empty fence (as a `suggestion`: delete the commented lines); an
    empty string gives one blank line (replace them with a blank line)."""
    text = None if text is None else fenceable(text)
    runs: list[str] = re.findall(r"`+", text or "")
    ticks = "`" * max([3, *(len(run) + 1 for run in runs)])
    body = "" if text is None else f"\n{text}"
    return f"{ticks}{info}{body}\n{ticks}"


def carriable(diff: str) -> bool:
    """Whether a suggestion can carry the diff's lines as they are: UTF-8, nothing that fenceable()
    removes but the CR of a CRLF line ending, and no file's end without a final newline."""
    lf = diff.replace("\r\n", "\n")
    intact = fenceable(lf) == lf and not any(line.startswith("\\") for line in lf.split("\n"))
    return intact and not has_lone_surrogate(lf)


def adds_invisible(diff: str) -> bool:
    """Whether the diff's added lines hold a character of INVISIBLE_RE more often than its removed
    lines do."""
    lines = diff.split("\n")
    added, removed = (
        Counter(INVISIBLE_RE.findall("".join(line for line in lines if line.startswith(sign))))
        for sign in "+-"
    )
    return bool(added - removed)


def details(body: str, title: str) -> str:
    """`body` in a collapsed section titled `title`. GitHub renders the body as Markdown."""
    return f"<details>\n<summary>{title}</summary>\n\n{body.strip()}\n\n</details>"
