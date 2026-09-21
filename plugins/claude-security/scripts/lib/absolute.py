"""Whether a path is absolute on any platform, and where an absolute path sits under a root."""

from __future__ import annotations

import ntpath
import os
from pathlib import PurePath


def spelled(path: str) -> bool:
    """True for a rooted, drive-qualified or UNC path, whichever platform reads it."""
    return (
        os.path.isabs(path)
        or path.replace("\\", "/").startswith("/")
        or bool(ntpath.splitdrive(path)[0])
    )


def relative(path: str, root: str) -> str | None:
    """Where a normalised absolute `path` sits below `root`, as "a/b" ("." for root); else None."""
    try:
        inside = PurePath(path).relative_to(root)
    except ValueError:
        return None
    # A ".." could name somewhere above root; a normalised path never carries one.
    return None if ".." in inside.parts else inside.as_posix()
