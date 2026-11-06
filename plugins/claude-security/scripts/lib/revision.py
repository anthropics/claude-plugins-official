"""The revision a scan records, and the `<base>..<commit>` range a change scan's revision names."""

from __future__ import annotations

from typing import Literal, TypedDict

from .strictjson import JsonMap, is_str


class Revision(TypedDict, total=False):
    """What was scanned. `versioned` is always present; the rest when in git."""

    versioned: bool
    commit: str | None
    parent: str | None
    branch: str | None
    dirty: bool | None
    sparse: Literal[True]
    not_checked_out_dirs: list[str]
    base: str | None
    merge_base: str | None


def change_range(revision: JsonMap) -> str | None:
    """The `<base>..<commit>` range a change scan's revision names; None when it names no change."""
    base = revision.get("merge_base") or revision.get("parent")
    commit = revision.get("commit")
    return f"{base}..{commit}" if is_str(base) and is_str(commit) else None
