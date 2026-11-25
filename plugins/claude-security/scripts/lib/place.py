"""Where a script that a rule can pre-approve may run git: refusal() gives the reason for which it
may not run git in a folder, in words for the session."""

from __future__ import annotations

import os
import re
from pathlib import Path

from .git import holder_of

# Set to 1, it lets a script run git outside the session's own folder and repository.
ELSEWHERE = "CLAUDE_SECURITY_ROOT_ELSEWHERE"
_HEAD_BYTES = 255
_HEAD = re.compile(rb"ref:[ \t\n\r]*refs/|[0-9a-fA-F]{40}")


def _in_session(folder: str, *, same_git: bool) -> bool:
    """Whether `folder` is the working directory, lies below it or, if `same_git`, has the same
    holder_of() as it. An OSError while two folders are compared counts as False. It makes no call
    of git."""
    try:
        there = Path(os.path.realpath(folder))
        if any(os.path.lexists(p) and p.samefile(os.curdir) for p in (there, *there.parents)):
            return True
        if not same_git:
            return False
        ours, theirs = holder_of(os.curdir), holder_of(folder)
        return ours is not None and theirs is not None and ours.samefile(theirs)
    except OSError:
        return False


def _names_a_ref(head: Path) -> bool:
    """Whether `head` is a link into refs/, whatever it leads to, or a file that names a ref or a
    commit id."""
    if head.is_symlink():
        # The link's own text: a Path would drop the last slash of "refs/".
        return os.readlink(head).startswith("refs/")  # noqa: PTH115
    if not os.path.isfile(head):
        return False
    with head.open("rb") as file:
        return _HEAD.match(file.read(_HEAD_BYTES)) is not None


def _git_directory(folder: Path) -> bool:
    """Whether git would take `folder` for a git directory."""
    shared = folder / "commondir"
    try:
        name = (
            shared.read_bytes().rstrip(b"\r\n").partition(b"\0")[0]
            if os.path.isfile(shared)
            else b""
        )
        return _names_a_ref(folder / "HEAD") and all(
            os.access(folder / os.fsdecode(name) / part, os.X_OK) for part in ("objects", "refs")
        )
    except (OSError, ValueError):
        return False


def in_git_directory(folder: str) -> bool:
    """Whether git's search from `folder` upward meets a git directory before it meets a checkout's
    top: `folder` is, or lies in, a bare repository or a checkout's .git. It makes no call of
    git."""
    here = Path(os.path.realpath(folder))
    for p in (here, *here.parents):
        if os.path.isfile(p / ".git") or _git_directory(p / ".git"):
            return False
        if _git_directory(p):
            return True
    return False


def outside(folder: str, *, same_git: bool) -> str | None:
    """Why a script runs no git for `folder`, in words for the session: it is not in the session's
    own folder or, if `same_git`, repository. None where it is, or where ELSEWHERE is set to 1."""
    if os.environ.get(ELSEWHERE) == "1" or _in_session(folder, same_git=same_git):
        return None
    nor_shares, whose = (
        (", and does not share its .git", "it") if same_git else ("", "a repository in it")
    )
    return (
        f"{folder} is outside the folder that this session works in{nor_shares}. git's settings "
        f"for {whose} can name programs that git runs, and the user has not been asked about them. "
        f"To continue, run this command again with `env {ELSEWHERE}=1` before python3. Claude Code "
        "may then ask the user to approve it."
    )


def refusal(folder: str) -> str | None:
    """Why a script runs no git in `folder`, in words for the session; None where it may. It may
    not where in_git_directory() holds. Else outside() decides."""
    if in_git_directory(folder):
        return (
            f"{folder} lies in a git directory: a bare repository, or a checkout's .git. The "
            "plugin's scripts run no git there. Tell the user that they can name a checkout or a "
            "linked worktree of that repository, or the project's folder above it."
        )
    return outside(folder, same_git=True)
