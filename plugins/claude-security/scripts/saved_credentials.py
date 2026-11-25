#!/usr/bin/env python3
"""Name each file of a checkout that may hold a saved credential, for the GitHub Action.

Usage:
  saved_credentials.py CHECKOUT

Reads the job's token from standard input. Every byte there counts as the token's, so the caller
sends no line end. Searches each regular file under CHECKOUT. The caller runs it as root. It follows
no link under CHECKOUT. It passes over what permissions still close to it, and what is gone since it
was listed. On standard error it names:

  - each file that contains the token, as plain text or inside one line of base64 text;
  - each file called config or config.worktree that contains, in any letter case, the word
    extraheader or a file name of the form git-credentials-ID.config, where ID is hex digits and
    dashes.

In a name, ? stands for each character that is not an ASCII letter or digit or one of . _ / -.
Exits 0 if it names no file; 1 if it names one or more; 2 on a usage error. A search that fails
never exits with 0. Python 3.9, stdlib only.
"""

from __future__ import annotations

import base64
import mmap
import os
import re
import stat
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

USAGE = "usage: saved_credentials.py CHECKOUT, with the job's token on standard input\n"
# A bare repository's folder can have any name, so only the file's own name counts.
GIT_SETTINGS = frozenset({"config", "config.worktree"})
SAVED_FORM = re.compile(rb"extraheader|git-credentials-[0-9a-f-]+\.config", re.IGNORECASE)
SKIPPED = (PermissionError, FileNotFoundError)
FOUND = (
    "saved_credentials.py: each file named above may hold a saved credential (? stands for an "
    "unusual character). The file contains the job's GITHUB_TOKEN, as plain text or in base64. Or "
    "the file is called config or config.worktree and contains what actions/checkout writes when "
    "it saves a credential: the word extraheader, or the name of a file, like "
    "git-credentials-1a2b.config, in which it saves one. Change the step that writes the token "
    "there, set persist-credentials: false on every actions/checkout step, or, where no "
    "actions/checkout step wrote that word or name, remove it.\n"
)
FAILED = "saved_credentials.py: the search failed at {}: {}."


class SearchError(Exception):
    """The search failed at a file; the message is FAILED, with the file's name and the reason."""


def log_safe(path: str) -> str:
    """`path`, with ? for each character that is not an ASCII letter or digit or one of . _ / -."""
    return re.sub(r"[^\w./-]", "?", path, flags=re.ASCII)


def spellings(token: bytes) -> list[bytes]:
    """`token`, and three parts of its base64 text. One line of base64 text that encodes `token`
    contains one of the three."""
    # The first 3 characters and the last one can also encode a neighbour, so they are cut off.
    shifted = (base64.b64encode(b"." * shift + token).rstrip(b"=")[3:-1] for shift in range(3))
    return [token, *shifted]


def unless_skipped(error: OSError) -> None:
    """Raises `error`, which kept os.fwalk out of a folder, unless it is one of SKIPPED."""
    if not isinstance(error, SKIPPED):
        raise error


def mapped(name: str, folder: int) -> mmap.mmap | None:
    """The bytes of the regular file `name` in the open folder `folder`; None if the file is empty
    when it is mapped. Raises OSError for anything else, a link among them."""
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=folder)
    try:
        return mmap.mmap(descriptor, 0, prot=mmap.PROT_READ)
    except ValueError:
        return None
    finally:
        os.close(descriptor)


def may_hold_credential(path: str, name: str, folder: int, spelt: Sequence[bytes]) -> bool:
    """Whether the regular file `name` in the open folder `folder` contains one of `spelt`, or is a
    git settings file that matches SAVED_FORM. False for a file that one of SKIPPED keeps from the
    search; SearchError, which names the file under the folder's `path`, for any other OSError."""
    try:
        found = os.stat(name, dir_fd=folder, follow_symlinks=False)
        if not (stat.S_ISREG(found.st_mode) and found.st_size):
            return False
        text = mapped(name, folder)
        if text is None:
            return False
        with text:
            return any(text.find(one) >= 0 for one in spelt) or (
                name in GIT_SETTINGS and SAVED_FORM.search(text) is not None
            )
    except SKIPPED:
        return False
    except OSError as error:
        raise SearchError(FAILED.format(log_safe(f"{path}/{name}"), error.strerror)) from error


def main(argv: list[str]) -> int:
    token = sys.stdin.buffer.read()
    if len(argv) != 1 or not os.path.isdir(argv[0]) or not token:
        sys.stderr.write(USAGE)
        return 2
    spelt = spellings(token)
    try:
        found = [
            log_safe(f"{path}/{name}")
            for path, _, names, folder in os.fwalk(
                os.path.realpath(argv[0]), onerror=unless_skipped
            )
            for name in names
            if may_hold_credential(path, name, folder, spelt)
        ]
    except SearchError as error:
        sys.exit(str(error))
    except OSError as error:
        sys.exit(FAILED.format("a folder", error.strerror))
    except RecursionError:
        sys.exit(FAILED.format("a folder", "nested too deeply"))
    if found:
        sys.stderr.write("\n".join((*found, FOUND)))
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
