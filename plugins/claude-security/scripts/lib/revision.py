"""The revision a scan, a triage or an attack surface analysis records, read from git and named in
the stamp, and the `<base>..<commit>` range a change scan's revision names."""

from __future__ import annotations

from typing import Literal, TypedDict

from . import git, plugin
from .strictjson import JsonMap, is_map, is_str


class Revision(TypedDict, total=False):
    """What was scanned or analyzed. `versioned` is always present; the rest when in git, but
    for the `commit` and `dirty` that a triage writes as null outside it."""

    versioned: bool
    commit: str | None
    parent: str | None
    branch: str | None
    dirty: bool | None
    sparse: Literal[True]
    not_checked_out_dirs: list[str]
    unreadable_dirs: list[str]
    base: str | None
    merge_base: str | None


SELF_REPORTED = "self-reported"


def change_range(revision: JsonMap) -> str | None:
    """The `<base>..<commit>` range a change scan's revision names; None when it names no change."""
    base = revision.get("merge_base") or revision.get("parent")
    commit = revision.get("commit")
    return f"{base}..{commit}" if is_str(base) and is_str(commit) else None


class RevisionError(Exception):
    """A revision that cannot name a stamp file; the message says why."""


def revision_tag(revision: object) -> str:
    """The stamp's filename tag: <sha12>[-dirty], or UNVERSIONED."""
    if not is_map(revision):
        msg = f"the run's revision {revision!r} is not an object, so it cannot name the stamp file"
        raise RevisionError(msg)
    sha = revision.get("commit")
    if not sha:
        return "UNVERSIONED"
    if not is_str(sha) or not plugin.SHA_RE.match(sha):
        msg = f"the run's revision {sha!r} is not a hex commit id, so it cannot name the stamp file"
        raise RevisionError(msg)
    return sha[: plugin.SHORT_ID_CHARS] + ("" if revision.get("dirty") is False else "-dirty")


def dirty(status: str) -> bool:
    """Whether `git status --porcelain` shows a change in the working tree. A report directory
    does not count."""
    for line in status.splitlines():
        if len(line) < len("XY P"):
            continue
        path = line[3:].split(" -> ")[-1]
        if any(part.startswith(plugin.REPORT_DIR_PREFIX) for part in path.split("/")[:-1]):
            continue
        return True
    return False


def head_of(root: str) -> Revision:
    """The commit and the branch of the git checkout that holds `root`, read without a look at its
    working tree."""
    head = git.run(root, "rev-parse", "--verify", "--quiet", "HEAD")
    branch = git.run(root, "rev-parse", "--abbrev-ref", "HEAD")
    return {"versioned": True, "commit": head, "branch": branch}


def checked_out(root: str, timeout: int = git.TIMEOUT) -> tuple[Revision, str | None]:
    """The revision of the git checkout that holds `root`, and the text of `git status` that the
    revision's `dirty` comes from. The text and `dirty` are both None where git status failed or
    ran past `timeout` seconds."""
    revision = head_of(root)
    status = git.run(root, "status", "--porcelain", "--untracked-files=all", timeout=timeout)
    revision["dirty"] = None if status is None else dirty(status)
    return revision, status
