"""Read a unified diff as git writes it: its files, their hunks, and what each hunk replaces."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

DIFF_HEADER = "diff --git "
HUNK = re.compile(r"^@@ -([0-9]+)(?:,([0-9]+))? \+([0-9]+)(?:,([0-9]+))? @@")
_NOT_IN_PLACE = (
    "old mode ",
    "new mode ",
    "deleted file mode ",
    "new file mode ",
    "rename ",
    "copy ",
    "similarity index ",
    "Binary files ",
    "GIT binary patch",
)
# A regular file's modes; an `index` line naming another (a link's, a submodule's) is not text.
_FILE_MODES = ("100644", "100755")
_ESCAPES = {"a": "\a", "b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v"}
_QUOTED_RE = re.compile(r'"(?:[^"\\]|\\.)*"')


@dataclass(frozen=True)
class Hunk:
    """One `@@` hunk: where it sits on each side, and its body lines with their prefixes."""

    old_start: int
    new_start: int
    new_count: int
    lines: tuple[str, ...]


@dataclass(frozen=True)
class Replacement:
    """A hunk restated as "replace old-side lines start..end (inclusive) with this text";
    `text` is None when the hunk only deletes those lines, and an empty string replaces
    them with one blank line."""

    start: int
    end: int
    text: str | None

    def covers(self, line: int) -> bool:
        """Whether old-side `line` is one of the lines replaced."""
        return self.start <= line <= self.end


@dataclass
class FileDiff:
    """One `diff --git` section."""

    old_path: str | None = None
    new_path: str | None = None
    in_place: bool = True
    hunks: list[Hunk] = field(default_factory=list)

    def new_side_spans(self) -> list[tuple[int, int]]:
        """The new-side line ranges (inclusive) this section's hunks cover."""
        return [(h.new_start, h.new_start + h.new_count - 1) for h in self.hunks if h.new_count > 0]

    def replacements(self) -> list[Replacement] | None:
        """Each hunk as a replacement of old-side lines; None when no line replacement can
        express the section: it is not an in-place text edit of one existing regular file (a
        rename, a mode change, a created, deleted or binary file, a link or a submodule), or a
        hunk has no line to anchor on.
        """
        if not (self.in_place and self.old_path and self.old_path == self.new_path):
            return None
        kept = [r for hunk in self.hunks if (r := _replacement(hunk)) is not None]
        return kept if kept and len(kept) == len(self.hunks) else None


def _replacement(hunk: Hunk) -> Replacement | None:
    body = [line for line in hunk.lines if not line.startswith("\\")]
    changed = [i for i, line in enumerate(body) if not line.startswith(" ")]
    if not changed:
        return None
    lead, last = changed[0], changed[-1]
    core = body[lead : last + 1]
    old = [line[1:] for line in core if line[0] in " -"]
    new = [line[1:] for line in core if line[0] in " +"]
    start = hunk.old_start + lead
    if not old:
        if lead:
            start -= 1
            old, new = [body[lead - 1][1:]], [body[lead - 1][1:], *new]
        elif last + 1 < len(body):
            old, new = [body[last + 1][1:]], [*new, body[last + 1][1:]]
        else:
            return None
    return Replacement(start, start + len(old) - 1, "\n".join(new) if new else None)


def name_field(text: str) -> str:
    """The file name that follows `--- ` or `+++ `, as git spelt it, without what can trail it."""
    name = text.split("\r", 1)[0]
    quoted = _QUOTED_RE.match(name)
    return quoted[0] if quoted else name.split("\t", 1)[0]


def _name(marked: str) -> str | None:
    """The path on a `--- `/`+++ ` line: a/ or b/ dropped, C-quoting undone, None for /dev/null."""
    name = name_field(marked[4:])
    if len(name) > 1 and name.startswith('"') and name.endswith('"'):
        name = _unquote(name[1:-1])
    if name == "/dev/null":
        return None
    return name[2:] if name[:2] in {"a/", "b/"} else name


def _unquote(text: str) -> str:
    out = bytearray()
    chars = iter(text)
    for char in chars:
        if char != "\\":
            out += char.encode("utf-8", "surrogateescape")
            continue
        nxt = next(chars, "")
        if nxt in _ESCAPES:
            out += _ESCAPES[nxt].encode("ascii")
        elif nxt.isdigit():
            digits = nxt + "".join(next(chars, "") for _ in range(2))
            out.append(int(digits, 8) & 0xFF)
        else:
            out += nxt.encode("utf-8", "surrogateescape")
    return out.decode("utf-8", "surrogateescape")


def parse(text: str) -> list[FileDiff]:
    """Every `diff --git` section in `text`, in order."""
    files: list[FileDiff] = []
    current: FileDiff | None = None
    lines = text.replace("\r\n", "\n").split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if line.startswith(DIFF_HEADER):
            current = FileDiff()
            files.append(current)
            continue
        if current is None:
            continue
        if matched := HUNK.match(line):
            old_count, new_count = int(matched[2] or "1"), int(matched[4] or "1")
            body: list[str] = []
            need_old, need_new = old_count, new_count
            while i < len(lines):
                entry = lines[i]
                tag = entry[:1]
                if tag == " " and (need_old > 0 or need_new > 0):
                    need_old, need_new = need_old - 1, need_new - 1
                elif tag == "-" and need_old > 0:
                    need_old -= 1
                elif tag == "+" and need_new > 0:
                    need_new -= 1
                elif tag != "\\":
                    break
                body.append(entry)
                i += 1
            current.hunks.append(Hunk(int(matched[1]), int(matched[3]), new_count, tuple(body)))
        elif current.hunks:
            continue
        elif line.startswith("--- "):
            current.old_path = _name(line)
        elif line.startswith("+++ "):
            current.new_path = _name(line)
        elif line.startswith(_NOT_IN_PLACE) or (
            line.startswith("index ") and line.count(" ") == 2 and not line.endswith(_FILE_MODES)
        ):
            current.in_place = False
    return files
