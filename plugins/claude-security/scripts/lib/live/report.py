"""A finished report: delivered, and read back."""

from __future__ import annotations

import os
import re
import secrets
import shutil
import stat
from contextlib import ExitStack, suppress
from typing import TYPE_CHECKING

from lib import display, last_report, plugin, products, strictjson
from lib.finding import unpercent
from lib.link import is_link
from lib.strictjson import JsonMap, as_int, clean, strings

from .scan import Finding

if TYPE_CHECKING:
    from collections.abc import Collection, Sequence
    from pathlib import Path

    from .atlas import Atlas

_PRODUCTS = (plugin.RESULTS_MD_NAME, plugin.JSONL_NAME, plugin.SARIF_NAME)
# The names that render_report.py gives a stamp. Any other could hold text that the scan chose.
_STAMP = re.compile(
    rf"{plugin.REVISION_PREFIX}([0-9a-fA-F]{{1,{plugin.SHORT_ID_CHARS}}}(-dirty)?|UNVERSIONED)\.json"
)
_FACTS = ("id", "severity", "confidence", "file", "line", "category", "cwe_id")
_WITHHELD = "Not shown: the report can still hold credential values"
_MOST_BYTES = 256 * 1024 * 1024


def recall(places: Sequence[Path], reports: Path) -> list[Path]:
    """Copy the last report of each target from `places` into `reports`, where a codebase scan
    looks for it, and return the copies. After one that cannot be read, the next older is copied.
    Of two with one name, the earlier place's is taken."""
    named: list[Path] = []
    for place in places:
        with suppress(OSError):
            named += _named(place)
    copies: list[Path] = []
    taken: set[tuple[str, frozenset[str]] | None] = {None}
    for folder in sorted(named, key=lambda path: path.name, reverse=True):
        if (target := last_report.target_of(folder)) in taken:
            continue
        with suppress(OSError, products.ProductError):
            # A copy that fails the reads below stays, so the caller must know of it too.
            copies.append(deliver(folder, reports))
            products.Stamp.read(copies[-1])
            products.records(copies[-1] / plugin.JSONL_NAME, required=True)
            taken.add(target)
    return copies


def _named(folder: Path, but: Collection[Path] = ()) -> list[Path]:
    """What has a report directory's name in `folder`, oldest first."""
    named = (p for p in folder.iterdir() if plugin.REPORT_DIR_RE.match(p.name))
    return sorted(p for p in named if p not in but)


def finished(reports: Path, earlier: Collection[Path]) -> Path | None:
    """The newest report directory under `reports` that holds a revision stamp, but for those in
    `earlier`."""
    real = (p for p in _named(reports, earlier) if p.is_dir() and not is_link(p))
    stamped = [p for p in real if any(map(plugin.is_revision_stamp, p.iterdir()))]
    return stamped[-1] if stamped else None


def deliver(source: Path, into: Path) -> Path:
    """Copy the report's files to a new directory of the same name in `into`, and return it.
    Raises OSError if a step fails, after it tries to remove what it made."""
    target = into / source.name
    target.mkdir()
    try:
        (target / ".gitignore").write_text("*\n", encoding="utf-8")
        for path in sorted(source.iterdir()):
            if path.name in _PRODUCTS or _STAMP.fullmatch(path.name):
                (target / path.name).write_bytes(read_below(source.parent, source.name, path.name))
    except OSError:
        shutil.rmtree(target, ignore_errors=True)
        raise
    return target


def set_aside(source: Path, run: Path) -> Path:
    """Move the folder that holds the report directory, unread, to a new name beside `run`, and
    return the report directory's new path."""
    source.parent.chmod(0o700)
    name = f"{plugin.NAME}-report-{secrets.token_hex(8)}"
    return source.parent.rename(run.with_name(name)) / source.name


def read_below(folder: Path, *names: str) -> bytes:
    """The regular file that `names` lead to from `folder`, with no link on the way."""
    # The scan writes below this folder, and a link there would lead out of the sandbox's limits.
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    with ExitStack() as held:
        if os.open in os.supports_dir_fd:
            fd = os.open(folder, flags)
            for name in names:
                held.callback(os.close, fd)
                fd = os.open(name, flags, dir_fd=fd)
        else:
            steps = [folder.joinpath(*names[:end]) for end in range(1, len(names) + 1)]
            if any(map(is_link, steps)):
                msg = f"{names[-1]} lies behind a link"
                raise OSError(msg)
            fd = os.open(steps[-1], flags | getattr(os, "O_BINARY", 0))
        held.callback(os.close, fd)
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            msg = f"{names[-1]} is not a regular file"
            raise OSError(msg)
        data = held.enter_context(os.fdopen(fd, "rb", closefd=False)).read(_MOST_BYTES + 1)
    if len(data) > _MOST_BYTES:
        msg = f"{names[-1]} is too large"
        raise OSError(msg)
    return data


def missing(stamp: products.Stamp, listed: int) -> str:
    """What the stamp shows to be missing from a scan whose JSONL holds `listed` findings. It is
    empty for a complete scan."""
    gaps = {
        f"The report is not verified: {stamp.reason or 'it gives no reason'}.": not stamp.verified,
        f"The reading of {display.counted(stamp.lost, 'researcher')} is missing.": stamp.lost,
        "A refused finding is not in the list.": stamp.refused,
        "A finding may be missing: the report's counts do not agree.": listed != stamp.total,
    }
    return " ".join(gap for gap, holds in gaps.items() if holds)


def findings(report: Path, atlas: Atlas, *, texts: bool) -> list[Finding]:
    """The findings in the report's JSONL. Without `texts`, each has only _FACTS and the title
    _WITHHELD."""
    whole = products.records(report / plugin.JSONL_NAME, required=True)
    bare = ({key: record.get(key) for key in _FACTS} | {"title": _WITHHELD} for record in whole)
    return [_finding(record, atlas) for record in (whole if texts else bare)]


def _finding(record: JsonMap, atlas: Atlas) -> Finding:
    def text(key: str) -> str:
        return strictjson.well_formed(clean(record.get(key)))

    name, line = unpercent(text("file")), as_int(record.get("line"))
    return Finding(
        id=text("id"),
        title=text("title"),
        severity=text("severity"),
        confidence=text("confidence"),
        file=strictjson.well_formed(name),
        line=line,
        plot=atlas.find(name),
        plot_line=atlas.plot_line(name, line),
        category=text("category"),
        cwe=text("cwe_id"),
        symbol=text("symbol"),
        snippet=text("snippet"),
        description=text("description"),
        impact=text("impact"),
        exploit_scenario=text("exploit_scenario"),
        preconditions=strings(record.get("preconditions")),
        recommendation=text("recommendation"),
    )
