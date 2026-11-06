"""Whether a path is a link that a removal must not be sent through."""

from __future__ import annotations

import os
import stat


def is_link(path: str | os.PathLike[str]) -> bool:
    """Whether `path` is a symbolic link or, on Windows, a directory junction.

    False for a path that is absent or cannot be examined.
    """
    try:
        status = os.lstat(path)
    except OSError:
        return False
    if stat.S_ISLNK(status.st_mode):
        return True
    if os.name == "nt":
        reparse_point = status.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
        return bool(reparse_point) and status.st_reparse_tag == stat.IO_REPARSE_TAG_MOUNT_POINT
    return False
