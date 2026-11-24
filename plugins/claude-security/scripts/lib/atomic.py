"""Writing a file whole: a write that fails or is killed leaves no cut-off file in its place."""

from __future__ import annotations

import os
import stat
from contextlib import suppress
from pathlib import Path
from typing import Final

SUFFIX: Final = ".partial"


def write(path: Path, data: bytes, *, like: Path | None = None) -> None:
    """Write `data` to a temporary file, then move that file onto `path`.

    A write that fails or is killed before the move leaves `path` as it was. Two writes of one file
    must not overlap. The new file's mode is no wider than that of the file that it replaces, but
    for the owner's write bit. A symbolic link at `path` to a file, or to a name where no file is
    yet, is followed. The temporary file is beside the file that gets the data, which with a link is
    the file behind it. Its name is that file's name and `SUFFIX`, and the call first removes any
    file at that name. On any error, Ctrl-C too, the call removes the temporary file: it stays only
    after a kill, or where that removal fails.

    With `like`, the rule on the mode goes by the file there, and not by the one at `path`: with no
    file there, the mode is a new file's. A symbolic link there is followed. A folder there gives
    its own mode bits.
    """
    target = Path(os.path.realpath(path))
    partial = target.with_name(target.name + SUFFIX)
    mode = 0o666
    with suppress(FileNotFoundError):
        mode = (like or target).stat().st_mode & 0o777 | stat.S_IWUSR
    partial.unlink(missing_ok=True)
    try:
        with open(partial, "xb", opener=lambda name, flags: os.open(name, flags, mode)) as file:
            file.write(data)
        partial.replace(target)
    except BaseException:
        with suppress(OSError):
            partial.unlink()
        raise
