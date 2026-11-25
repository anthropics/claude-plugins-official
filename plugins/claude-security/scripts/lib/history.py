"""The commits of a repository whose message reads like a security fix."""

from __future__ import annotations

import re
from enum import Enum
from itertools import islice
from typing import TYPE_CHECKING, TypedDict

from . import console, strictjson
from .git import NO_ORDER_FILE
from .git import run as git

if TYPE_CHECKING:
    from collections.abc import Collection, Iterator
    from pathlib import Path

FILE_NAME = "past-fixes.jsonl"
CLEAR_WORDS = (
    "security|vulnerab|CVE-[0-9]|GHSA-|from fork|exploit|attack|malicious|injection"
    "|XSS|CSRF|SSRF|XXE"
)
HINT_WORDS = (
    "untrusted|arbitrary|unsafe|insecure|tra(ns)?versal|IDOR|saniti[sz]|escap|deseriali[sz]"
    "|pollution|open.redirect|remote.code|bypass|privilege|permission|authori[sz]|authenticat"
    "|hijack|spoof|tamper|credential|hard.?coded|leak|disclos|harden|validat|verif|prevent"
    "|restrict|reject|forbid|disallow|malform|overflow|out.of.bounds|use.after.free|double.free"
    "|fuzz|crash|panic|infinite|unbounded|exhaust|denial.of.service|DoS|race.condition|TOCTOU"
)
# A regex that git and Python read alike.
_PARTIAL_CLONE_KEYS = (
    r"core\.partialclonefilter|extensions\.partialclone|remote\..*\.(promisor|partialclonefilter)"
)
MAX_COMMITS = 400
FILES_PER_COMMIT = 5
LINE_CHARS = 120
TIMEOUT_S = 10


class NoList(Enum):
    """A cause for which the list cannot be made, in the warning's words."""

    NO_FILES = "the scan listed no file in the scan target"
    NO_COMMIT = "the scan found no checked-out git commit at the scan root"


class PastFix(TypedDict):
    """A commit as `<date> <id> <subject>`, cut at LINE_CHARS, and the first FILES_PER_COMMIT
    files, in path order, that it touched and the target still holds."""

    commit: str
    files: list[str]


def _log(words: str, scan_root: str, scope: list[str]) -> str | None:
    """What git prints of the newest commits whose message matches `words`; None if it fails."""
    return git(
        scan_root,
        "log",
        f"--max-count={MAX_COMMITS}",
        "--full-history",
        # A commit with no parent in this clone would name every file in the tree.
        "--min-parents=1",
        "--regexp-ignore-case",
        "--extended-regexp",
        f"--grep={words}",
        "--no-show-signature",
        "--encoding=UTF-8",
        "--format=%x00%as %h %s",
        "--name-only",
        "--no-renames",
        "--no-follow",
        "--diff-merges=first-parent",
        "--relative",
        NO_ORDER_FILE,
        "-z",
        "--",
        *(scope or ["."]),
        timeout=TIMEOUT_S,
        env={"GIT_NO_LAZY_FETCH": "1", "LC_ALL": "C"},
    )


def _commits(log: str) -> Iterator[tuple[str, list[str]]]:
    """Each commit git printed with a file name: its line, then the files it touched."""
    # Under -z a commit prints as NUL, its formatted line, NUL, newline, then each name and a NUL.
    for commit in log.split("\0\0"):
        line, _, names = commit.strip("\0").partition("\0\n")
        if names:
            yield line, names.split("\0")


def past_fixes(scan_root: str, scope: list[str], files: Collection[str]) -> list[PastFix] | None:
    """Up to MAX_COMMITS commits whose message reads like a security fix, each with up to
    FILES_PER_COMMIT of the `files` it touched: first those that say so outright, then those that
    hint at it, the newest first in each. Empty when git gives no such history. None, with a
    warning, when a git call fails."""
    clear = _log(CLEAR_WORDS, scan_root, scope)
    hints = None if clear is None else _log(HINT_WORDS, scan_root, scope)
    if clear is None or hints is None:
        _warn_no_list(
            f"git log failed or took over {TIMEOUT_S} seconds (it always fails on a git older than "
            "2.31)"
        )
        return None
    tracked = frozenset(files)
    commits = {line: paths for log in (clear, hints) for line, paths in _commits(log)}
    return [
        PastFix(
            commit=line[:LINE_CHARS],
            files=sorted(tracked.intersection(paths))[:FILES_PER_COMMIT],
        )
        for line, paths in islice(commits.items(), MAX_COMMITS)
    ]


def partial_clone(scan_root: str) -> bool | None:
    """Whether the repository's own configuration sets a partial clone key. None where it cannot be
    read, or sets no key under [core] and no partial clone key."""
    keys = rf"^(core\..*|{_PARTIAL_CLONE_KEYS})$"
    read = ("config", "--local", "--includes", "--name-only", "-z", "--get-regexp", keys)
    names = git(scan_root, *read, env={"LC_ALL": "C"})
    if names is None:
        return None
    return any(re.fullmatch(_PARTIAL_CLONE_KEYS, name) for name in names.split("\0"))


def _may_list(scan_root: str) -> bool:
    """True where partial_clone() returns False. Otherwise it warns and returns False."""
    partial = partial_clone(scan_root)
    if partial is None:
        why = "could not be read, or sets nothing under [core]"
    elif partial:
        why = "sets a partial clone key (as git clone --filter does)"
    else:
        return True
    _warn_no_list(f"the repository's own git configuration {why}")
    return False


def _warn_no_list(why: str) -> None:
    console.warn(f"{why}, so this scan does not look at past security fixes")


def write_past_fixes(
    run_dir: Path, scan_root: str, scope: list[str], files: Collection[str] | NoList
) -> int | None:
    """Write the list into the run directory, one JSON line per commit, and return how many it
    wrote. With `files` empty, as the caller gives it at low effort, git does not run and the list
    is empty. With a NoList in place of `files` the list cannot be made: git does not run, and
    the warning gives that cause. None, after a warning, where the list could not be made or
    written. Wherever it cannot be made, the file is written empty."""
    fixes: list[PastFix] | None = []
    if isinstance(files, NoList):
        _warn_no_list(files.value)
        fixes = None
    elif files:
        fixes = past_fixes(scan_root, scope, files) if _may_list(scan_root) else None
    try:
        (run_dir / FILE_NAME).write_bytes(
            "".join(strictjson.text(fix) + "\n" for fix in fixes or []).encode()
        )
    except OSError as error:
        _warn_no_list(f"the list of commits could not be written ({error})")
        return None
    return None if fixes is None else len(fixes)
