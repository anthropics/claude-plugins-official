"""Removing a directory tree the plugin made, whose files or directories may be read-only."""

from __future__ import annotations

import functools
import os
import shutil
import stat
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING

from .link import is_link

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import TracebackType


def writable_then(
    root: str,
    function: Callable[..., object],
    name: str,
    exc_info: tuple[type[BaseException], BaseException, TracebackType],
) -> None:
    """rmtree's error handler for the tree at `root`: retry a refused unlink or rmdir once, after
    making the entry writable on Windows (a link never touched) or, on POSIX, its parent when that
    is a real directory inside `root`; an entry already gone counts as removed; raise anything else,
    or a retry that fails. `root` is absolute and normalised, as os.path.abspath writes it."""
    if isinstance(exc_info[1], FileNotFoundError):
        return
    if function not in {os.unlink, os.rmdir}:
        raise exc_info[1]
    with suppress(FileNotFoundError):
        if os.name == "nt":
            if not is_link(name):
                Path(name).chmod(stat.S_IWRITE)
        else:
            parent = Path(os.path.abspath(name)).parent
            if os.path.commonpath([root, parent]) == root and not is_link(parent):
                mode = parent.stat().st_mode
                if not mode & stat.S_IWUSR:
                    parent.chmod(mode | stat.S_IWUSR)
        function(name)


def remove_tree(path: Path) -> None:
    """Remove the tree at `path`, first making writable a read-only entry (Windows) or a
    read-only directory in it (POSIX) that blocks the removal; an OSError names what could still
    not be removed."""
    root = os.path.abspath(path)
    shutil.rmtree(root, onerror=functools.partial(writable_then, root))
