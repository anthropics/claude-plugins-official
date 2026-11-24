"""Read and write regular files, and test whether a directory holds only regular files and
folders."""

from __future__ import annotations

import errno
import os
import secrets
import stat
import sys
from contextlib import suppress
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

_OPEN_FLAGS = os.O_BINARY if sys.platform == "win32" else os.O_NOFOLLOW | os.O_NONBLOCK
READ_LIMIT = 64 * 1024 * 1024


def _refusal(path: Path) -> OSError:
    return OSError(errno.EINVAL, "not a regular file", str(path))


def _opened(path: Path, flags: int) -> int:
    """A descriptor on `path`, which is a regular file; OSError if anything else is there."""
    if os.path.lexists(path) and not stat.S_ISREG(path.lstat().st_mode):
        raise _refusal(path)
    try:
        descriptor = os.open(path, flags | _OPEN_FLAGS, 0o666)
    except OSError as error:
        if error.errno != errno.ELOOP:
            raise
        raise _refusal(path) from None
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise _refusal(path)
    return descriptor


def read_bytes(path: Path, most: int = READ_LIMIT) -> bytes:
    """The bytes of `path`; OSError where it is not a regular file, a link to one included, and,
    with errno EFBIG, where it holds more than `most` bytes."""
    with os.fdopen(_opened(path, os.O_RDONLY), "rb") as handle:
        data = handle.read(most + 1)
    if len(data) > most:
        raise OSError(errno.EFBIG, f"more than {most} bytes", str(path))
    return data


def read_text(path: Path, most: int = READ_LIMIT) -> str:
    """`path` as UTF-8 text; OSError as for read_bytes, ValueError where it is not UTF-8."""
    return read_bytes(path, most).decode("utf-8")


def all_plain(directory: Path) -> bool:
    """Whether everything under `directory`, at any depth, is a regular file or a folder, with no
    link among them, and every folder can be listed."""
    folders = [os.fspath(directory)]
    try:
        while folders:
            with os.scandir(folders.pop()) as entries:
                for entry in entries:
                    if entry.is_dir(follow_symlinks=False):
                        folders.append(entry.path)
                    elif not entry.is_file(follow_symlinks=False):
                        return False
    except OSError:
        return False
    return True


def write_bytes(path: Path, data: bytes) -> None:
    """Write `data` to a new file and move it to `path`, in place of a regular file if one is there.
    If the write or the move fails, the file at `path` stays as it was. OSError if anything else is
    there when it starts, including a link."""
    if os.path.lexists(path) and not stat.S_ISREG(path.lstat().st_mode):
        raise _refusal(path)
    new = path.with_name(f"{path.name}.{secrets.token_hex(8)}")
    handle = os.fdopen(_opened(new, os.O_WRONLY | os.O_CREAT | os.O_EXCL), "wb")
    try:
        with handle:
            handle.write(data)
        new.replace(path)
    except BaseException:
        with suppress(OSError):
            new.unlink()
        raise
