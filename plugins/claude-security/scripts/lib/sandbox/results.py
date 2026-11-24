"""Report files on their way out of the sandbox, which wrote them and may have meant harm."""

from __future__ import annotations

import io
import os
import re
import secrets
import shutil
import stat
from contextlib import ExitStack, contextmanager, suppress
from itertools import takewhile
from typing import TYPE_CHECKING, BinaryIO, NamedTuple

from ..plugin import COMPLETE_NAME, MESSAGE_TOLD, REPORT_DIR_RE

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence
    from pathlib import Path

_MOST_FILES = 10_000
MOST_BYTES = 256 << 20
DEEPEST = 32
_LONGEST_NAME = 4096
# No hidden name, nothing that a tool of the host runs, and no instructions for a later session.
_PART = re.compile(r"\w[\w.-]{0,200}", re.ASCII)
_FILE = re.compile(
    r"(?!(claude|claude\.local|agents?|gemini|skill)\.md\Z).*\.(md|jsonl|sarif|patch)"
    rf"|(CLAUDE-SECURITY-.*|analysis|[A-Z]\d+)\.json|checkout-changes\.txt|{COMPLETE_NAME}",
    re.IGNORECASE,
)
_KEPT_INSIDE = re.compile(rf"\.gitignore|{re.escape(MESSAGE_TOLD)}[\w.-]+")
# Claude Code loads a plugin's instructions from folders of these names.
_LOADED = frozenset({"agents", "commands", "output-styles", "skills"})
FOLDER = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
ON_THE_WAY = os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_PATH", os.O_RDONLY)
NEW = os.O_WRONLY | os.O_CREAT | os.O_EXCL
# Of this process alone: two runs can write to one report folder at once.
_UNFINISHED = f".copying-{os.getpid()}-{secrets.token_hex(8)}"


class _Place(NamedTuple):
    """Where a report folder comes out: `way` leads there from `out`, `inside` is where it lay,
    `there` is where it comes out, from `out`, and `moved` says that it lay neither directly in the
    command's folder nor, in place, directly in `out`."""

    way: list[str]
    inside: str
    there: str
    moved: bool


@contextmanager
def folder_of(path: str) -> Generator[int, None, None]:
    """Open the folder that holds `path`, part by part, so that no link on the way is followed."""
    folder = os.open("/", ON_THE_WAY)
    try:
        for part in path.split("/")[1:-1]:
            inner = os.open(part, ON_THE_WAY, dir_fd=folder)
            os.close(folder)
            folder = inner
        yield folder
    finally:
        os.close(folder)


def _parts(name: str) -> tuple[list[str], list[str], str]:
    """The folders of `name` above its report folder, those from that folder down, and its leaf."""
    *folders, leaf = name.split("/")
    above = [*takewhile(lambda part: not REPORT_DIR_RE.match(part), folders)]
    return above, folders[len(above) :], leaf


def _stands_for_the_mark(folders: Sequence[str], leaf: str) -> bool:
    """Whether a report's path, from its report folder down, holds the mark's name, on a disk that
    may ignore case, anywhere but as the mark of its outermost report folder."""
    is_mark = leaf == COMPLETE_NAME and len(folders) == 1
    others = folders if is_mark else (*folders, leaf)
    return any(part.casefold() == COMPLETE_NAME.casefold() for part in others)


def _fence(folder: int) -> None:
    """Give a report folder a .gitignore if it has none, and end the word of an earlier run that it
    was finished."""
    try:
        os.stat(".gitignore", dir_fd=folder, follow_symlinks=False)
    except FileNotFoundError:
        _write(io.BytesIO(b"*\n"), folder, ".gitignore")
    with suppress(FileNotFoundError):
        os.unlink(COMPLETE_NAME, dir_fd=folder)


def _write(source: BinaryIO, folder: int, name: str) -> None:
    """Put the file in place whole, or leave what was there. Its mode bits for group and others are
    no wider than those of what it replaces. No group or ACL carries over."""
    mode = 0o644
    with suppress(FileNotFoundError):
        mode &= os.stat(name, dir_fd=folder, follow_symlinks=False).st_mode | stat.S_IRWXU
    try:
        with os.fdopen(os.open(_UNFINISHED, NEW, mode, dir_fd=folder), "wb") as target:
            shutil.copyfileobj(source, target)
        os.replace(_UNFINISHED, name, src_dir_fd=folder, dst_dir_fd=folder)
    finally:
        with suppress(FileNotFoundError):
            os.unlink(_UNFINISHED, dir_fd=folder)


class Results:
    """Copies report folders directly into `out`, an absolute path with no link in it, within limits
    and following no link. With `in_place`, `out` is the scanned folder, and what does not lie
    directly in it comes out directly in the command's own folder, to which `start` leads from
    there. `moved` names each that came out and lay neither directly in the command's folder nor,
    with `in_place`, directly in `out`. Of report folders of one name that would come out in one
    place, only the first one's files come out, and none comes out elsewhere than it lay, or without
    `in_place`, where one stands already, nor, with `in_place`, elsewhere than it lay if one of its
    name stands where it lay. A save needs `out` and `start` free of report folders. None comes out
    of a folder that is hidden or that a plugin loads from, but for one on the way to the command's
    folder, to a report below that."""

    def __init__(self, out: Path, start: Sequence[str] = (), *, in_place: bool) -> None:
        with folder_of(str(out / "any")) as place:
            self.folder: int = os.open(".", FOLDER, dir_fd=place)
        self._start: list[str] = [*start]
        self._in_place: bool = in_place
        self._files: int = 0
        self._bytes: int = 0
        self.refused: int = 0
        self.clashed: int = 0
        self.moved: dict[str, None] = {}
        self._sources: dict[str, str] = {}

    @property
    def flooded(self) -> bool:
        """Whether so much was refused that the rest is not worth a look."""
        return self.refused >= _MOST_FILES

    def _place(self, above: list[str], folder: str) -> _Place:
        """Where a report folder called `folder` below `above` inside comes out."""
        home = self._start if above or not self._in_place else []
        way = home if self._in_place else []
        return _Place(way, "/".join((*above, folder)), "/".join((*way, folder)), above != home)

    def claim(self, name: str) -> bool:
        """Whether the report folder of `name`, a name that may come out, may come out where it
        would: no other report folder of that name took that place first, and, for one that
        comes out elsewhere than it lay or without `in_place`, none stood there before, and,
        with `in_place`, for one that comes out elsewhere than it lay, none of its name stands
        where it lay. If so, it takes the place; else the file counts as refused and as clashed.
        OSError if the place where it would come out cannot be looked at."""
        above, folders, _ = _parts(name)
        where = self._place(above, folders[0])
        if (
            where.there not in self._sources
            and not ((where.moved or not self._in_place) and self._stands(where.way, folders[0]))
            and not (where.moved and self._in_place and self._lay(above, folders[0]))
        ):
            self._sources[where.there] = where.inside
        taken = self._sources.get(where.there) != where.inside
        self.clashed += taken
        self.refused += taken
        return not taken

    def _stands(self, way: Sequence[str], folder: str) -> bool:
        """Whether anything called `folder` stands outside at the end of `way`, following no link.
        OSError but for a missing name."""
        place = self.folder
        with ExitStack() as opened:
            try:
                for part in way:
                    place = os.open(part, ON_THE_WAY, dir_fd=place)
                    opened.callback(os.close, place)
                os.stat(folder, dir_fd=place, follow_symlinks=False)
            except FileNotFoundError:
                return False
        return True

    def _lay(self, above: Sequence[str], folder: str) -> bool:
        """Whether anything called `folder` stands on the host at `above`, a way that the command
        chose: a name that cannot be looked up there, or a file or link on the way, is none."""
        try:
            return self._stands(above, folder)
        except (OSError, ValueError):
            return False

    def may_come_out(self, name: str) -> bool:
        """Whether a file called `name` inside may come out by its name, if the limits leave room
        for it. Its place is for `claim` to decide."""
        above, folders, leaf = _parts(name)
        named = all(map(_PART.fullmatch, (*folders, leaf))) and _FILE.fullmatch(leaf)
        below = above[: len(self._start)] == self._start
        rest = above[len(self._start) :] if below else above
        odd = any(part.startswith(".") or part.casefold() in _LOADED for part in rest)
        odd = odd or _stands_for_the_mark(folders, leaf) or name.count("/") > DEEPEST
        odd = odd or len(name) > _LONGEST_NAME
        return bool(not odd and folders and named)

    def save(self, name: str, file: int) -> None:
        """Copy the open `file`, called `name` inside, if it may come out; else count it in
        `refused`. A report folder's own .gitignore and .message-told-<stage> files stay in and are
        not counted. OSError if the copy fails."""
        with os.fdopen(file, "rb") as source, ExitStack() as opened:
            above, folders, leaf = _parts(name)
            if folders and REPORT_DIR_RE.match(folders[-1]) and _KEPT_INSIDE.fullmatch(leaf):
                return
            size = os.fstat(file).st_size
            fits = self._files < _MOST_FILES and self._bytes + size <= MOST_BYTES
            if not (fits and self.may_come_out(name)):
                self.refused += 1
                return
            if not self.claim(name):
                return
            where = self._place(above, folders[0])
            self._files, self._bytes = self._files + 1, self._bytes + size
            place = self.folder
            for part in (*where.way, *folders):
                with suppress(FileExistsError):
                    os.mkdir(part, dir_fd=place)
                place = os.open(part, FOLDER, dir_fd=place)
                opened.callback(os.close, place)
                if REPORT_DIR_RE.match(part):
                    _fence(place)
            _write(source, place, leaf)
            if where.moved:
                self.moved[where.inside] = None
