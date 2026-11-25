"""What a scan records and says of the directories that it could not read."""

from __future__ import annotations

import os
from pathlib import PurePath
from typing import Final

from .strictjson import JsonMap, is_list, is_map, is_str

_CAUSE: Final = "the scan could not read one or more directories (permission denied)"
UNREADABLE_NEXT: Final = (
    "; take all coverage fields from coverage.json, not from the completion notice: "
    f'completenessCheckOutcome is "not-checkable", because {_CAUSE}'
)
_NOT_READ: Final = "the scan could not read it (permission denied)"


def _at_or_below(path: object, roots: list[PurePath]) -> bool:
    """Whether `path` is a string that lies at or below one of `roots`."""
    return is_str(path) and any(map(PurePath(os.path.normpath(path)).is_relative_to, roots))


def _lies_in(entry: object, roots: list[PurePath]) -> bool:
    """Whether a skipped component has paths, and each lies at or below one of `roots`."""
    paths = entry.get("paths") if is_map(entry) else None
    return is_list(paths) and bool(paths) and all(_at_or_below(path, roots) for path in paths)


def _lowered(coverage: JsonMap) -> JsonMap:
    """The outcome "not-checkable", with the permission cause after any that the workflow gave."""
    earlier = coverage.get("topLevelRejected")
    cause = f"{earlier}; {_CAUSE}" if earlier else _CAUSE
    return {"completenessCheckOutcome": "not-checkable", "topLevelRejected": cause}


def corrected(coverage: JsonMap, meta: JsonMap) -> JsonMap:
    """`coverage`, corrected for the directories that write_scan_meta.py named as unreadable, and
    unchanged where it named none. Each one is a skipped component with a fixed reason, in place of
    the skipped components that lie in it, and no longer counts as unaccounted for. "checked", and a
    "partial" that then lists no directory, become "not-checkable"."""
    revision, scan_root = meta.get("revision"), meta.get("scan_root")
    recorded = revision.get("unreadable_dirs") if is_map(revision) else None
    named = [name for name in recorded if is_str(name)] if is_list(recorded) else []
    if not named:
        return coverage
    roots = [PurePath(start, name) for name in named for start in ("", scan_root) if is_str(start)]
    skipped = coverage.get("skippedComponents")
    kept = [entry for entry in skipped if not _lies_in(entry, roots)] if is_list(skipped) else []
    not_read = [{"name": name, "paths": [name], "reason": _NOT_READ} for name in named]
    listed = coverage.get("unaccountedTopLevelDirs")
    left = [path for path in listed if not _at_or_below(path, roots)] if is_list(listed) else []
    outcome = coverage.get("completenessCheckOutcome")
    lower = outcome == "checked" or (outcome == "partial" and not left)
    return {
        **coverage,
        "skippedComponents": [*not_read, *kept],
        "unaccountedTopLevelDirs": left,
        **(_lowered(coverage) if lower else {}),
    }


def is_lowered(coverage: JsonMap) -> bool:
    """Whether `coverage` has the cause that corrected() gives."""
    cause = coverage.get("topLevelRejected")
    return is_str(cause) and cause.endswith(_CAUSE)
