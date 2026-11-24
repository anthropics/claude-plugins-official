"""The scanned tree: its files, and their lines, counted up to a limit or estimated from size."""

from __future__ import annotations

import os
import stat
from collections import defaultdict
from dataclasses import dataclass
from itertools import accumulate
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from lib import console, display, git, plugin

from lib.views.outline import outline

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping, Sequence

MAX_PLOTS = 12_000
PATH_CHARS = 1024
_FILE_BYTES = 512 * 1024
_TREE_BYTES = 96 * 1024 * 1024
BYTES_PER_LINE = 40


@dataclass(frozen=True)
class Plot:
    """A file, or a folder that counts as one piece."""

    path: str
    lines: int
    outline: bytes = b""

    @classmethod
    def of(cls, path: str, data: bytes) -> Plot:
        lines = data.splitlines()
        return cls(
            path,
            len(lines),
            outline(lines),
        )


class Atlas:
    """The plots of a tree, in path order."""

    def __init__(self, plots: Sequence[Plot], held: Mapping[str, range] | None = None) -> None:
        self.plots: Sequence[Plot] = plots
        self.lines: int = sum(plot.lines for plot in plots)
        # The lines of its plot that each file takes up, counted from 0.
        self.files: Mapping[str, range] = held or {plot.path: range(plot.lines) for plot in plots}
        self._index: dict[str, int] = {plot.path: i for i, plot in enumerate(plots)}

    @classmethod
    def of(cls, root: Path) -> Atlas:
        """The atlas of the files under `root`: those git lists, or all of them if it lists none."""
        paths = sorted(path for path in _listing(root) if not _is_report(path))
        if len(paths) > MAX_PLOTS:
            return cls(*_folders(root, paths))
        return cls(list(_files(root, paths)))

    def find(self, path: str) -> int | None:
        """The index of the plot that holds `path`, a path relative to the root."""
        above = PurePosixPath(path[:PATH_CHARS]).parents
        found = (self._index.get(str(p)) for p in (PurePosixPath(path), *above))
        return next((i for i in found if i is not None), None)

    def plot_line(self, path: str, line: int) -> int:
        """The line of its plot that a line of the file at `path` falls on. It is 0 for a file that
        takes up no line: one that is not listed, or too small to count."""
        lines = self.files.get(path)
        return lines.start + min(max(line, 1), len(lines)) if lines else 0

    def under(self, path: str) -> Sequence[int]:
        """The indexes of the plots at or below `path`, or else of the plot that holds it."""
        stem = path.partition("*")[0].rstrip("/").removeprefix("./")
        if stem in {"", "."}:
            return range(len(self.plots))
        if (exact := self._index.get(stem)) is not None:
            return [exact]
        prefix = f"{stem}/"
        below = [i for i, plot in enumerate(self.plots) if plot.path.startswith(prefix)]
        holder = self.find(stem)
        return below or ([] if holder is None else [holder])

    def matching(self, path: str) -> Sequence[int]:
        """The indexes of the plots that a component's path names. Where its first star stands
        inside a name, the text before it is a prefix. If no plot has it, under() answers."""
        start, star, _ = path.partition("*")
        if not star or start.endswith("/"):
            return self.under(path)
        found = [i for i, plot in enumerate(self.plots) if plot.path.startswith(start)]
        return found or self.under(path)


def _can_fetch(root: Path) -> bool:
    """Whether a config key can let git fetch a missing object in `root`. A fault counts as yes."""
    asked = ("config", "--get-regexp", "promisor|partialclone")
    return git.run(str(root), *asked, env={"LC_ALL": "C"}, ok=(1,)) is None


def _listing(root: Path) -> Iterable[str]:
    # This runs outside the sandbox, so git must start no program that the repository names.
    no_fsmonitor = ("-c", "core.fsmonitor=")
    env = {"GIT_NO_LAZY_FETCH": "1"}
    # A git before 2.45 can ignore that variable, but it refuses the option: the walk below lists.
    no_fetch = ("--no-lazy-fetch",) if _can_fetch(root) else ()
    tracked = git.run(str(root), *no_fetch, *no_fsmonitor, "ls-files", "-z", env=env, exact=True)
    if tracked:
        return set(tracked.split("\0")) - {""}
    if tracked is None and git.holder_of(str(root)):
        name = display.written_out(str(root))
        console.warn(f"git could not list {name}, so the progress counts ignored files too")
    return (
        git.from_disk(Path(folder, name).relative_to(root).as_posix())
        for folder, _, names in os.walk(root)
        if ".git" not in Path(folder).relative_to(root).parts
        for name in names
        if name != ".git"
    )


def _is_report(path: str) -> bool:
    return plugin.REPORT_DIR_RE.match(path.partition("/")[0]) is not None


def _size(path: Path) -> int:
    try:
        return path.lstat().st_size
    except OSError:
        return 0


def _read(path: Path) -> bytes | None:
    """The start of a regular text file, or None for anything else."""
    try:
        if not stat.S_ISREG(path.lstat().st_mode):
            return None
        with path.open("rb") as stream:
            data = stream.read(_FILE_BYTES)
    except OSError:
        return None
    return None if b"\0" in data else data


def _files(root: Path, paths: Sequence[str]) -> Iterator[Plot]:
    budget = _TREE_BYTES
    for path in paths:
        place = root / git.for_disk(path)
        data = _read(place) if budget > 0 else None
        if data is None:
            yield Plot(path, 0 if budget > 0 else _size(place) // BYTES_PER_LINE)
        else:
            budget -= len(data)
            yield Plot.of(path, data)


def _folders(root: Path, paths: Sequence[str]) -> tuple[list[Plot], dict[str, range]]:
    """The tree cut at the greatest depth that leaves at most MAX_PLOTS pieces, and the lines of
    its piece that each file takes up. Where the top level alone has more pieces, those past
    MAX_PLOTS are left out. Lines are estimated from sizes."""

    def cut(depth: int) -> dict[str, list[str]]:
        pieces: dict[str, list[str]] = defaultdict(list)
        for path in paths:
            pieces["/".join(path.split("/")[:depth])].append(path)
        return pieces

    pieces = cut(1)
    for depth in range(2, max(path.count("/") for path in paths) + 2):
        deeper = cut(depth)
        if len(deeper) > MAX_PLOTS:
            break
        pieces = deeper
    plots: list[Plot] = []
    files: dict[str, range] = {}
    for name, held in list(pieces.items())[:MAX_PLOTS]:
        ends = list(accumulate(_size(root / git.for_disk(p)) // BYTES_PER_LINE for p in held))
        files.update(zip(held, map(range, [0, *ends], ends)))
        plots.append(Plot(name, ends[-1]))
    return plots, files
