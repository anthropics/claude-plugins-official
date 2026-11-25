"""The scripts' console output: paths in the encoding in which they name their files, warnings and
failed removals, printed readably."""

from __future__ import annotations

import io
import os
import sys

_ERRORS = "backslashreplace"


def paths_encoding() -> str:
    """The encoding in which a printed path names its file: UTF-8 on Windows, and elsewhere the
    file-system encoding."""
    return "utf-8" if os.name == "nt" else sys.getfilesystemencoding()


def print_in_the_paths_encoding() -> None:
    """Make stdout and stderr write in paths_encoding(). A name that it could not decode is written
    as escapes."""
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding=paths_encoding(), errors=_ERRORS)


def read_as_utf8(text: str, encoding: str | None = None) -> str:
    """The bytes of `text` in `encoding`, read as UTF-8. What `encoding` cannot encode becomes an
    escape, as on the streams that print_in_the_paths_encoding() sets. A byte that is not valid
    UTF-8 becomes an escape too, where a reader of the streams sees U+FFFD. By default, `encoding`
    is theirs: paths_encoding()."""
    return text.encode(encoding or paths_encoding(), _ERRORS).decode("utf-8", _ERRORS)


def warn(text: str) -> None:
    """A WARNING line on stderr: the run carries on, and stdout stays what the caller reads."""
    sys.stderr.write(f"WARNING: {text}\n")


def removal_failure_detail(error: OSError) -> object:
    """The operator-readable reason a tree removal failed."""
    return str(error) if error.strerror or not error.args else error.args[0]
