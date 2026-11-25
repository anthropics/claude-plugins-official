"""What a scan of a branch's changes is diffed from: a base, or the older end of a typed range.

A refusal's message is for the Security Lead, and says what to tell the user."""

from __future__ import annotations

from . import git

BASES = ("origin/HEAD", "origin/main", "origin/master", "main", "master")
NAMED_COMMITS = 20
COMMIT_LINE_CHARS = 200
NAME_A_BASE = "tell them to name a base to diff against with --base, and stop"


class ChangeError(Exception):
    """A change that cannot be scanned as asked for."""


def default_base(root: str) -> str:
    """The ref to diff the checked-out branch against where none is named."""
    upstream = git.run(root, "rev-parse", "--abbrev-ref", "@{upstream}")
    pushed = git.run(root, "rev-parse", "--abbrev-ref", "@{push}")
    own_copy = upstream == pushed
    names = BASES if upstream is None or own_copy else (upstream, *BASES)
    found = next((name for name in names if git.commit_id(root, name)), None)
    if found is None:
        msg = f"no base to diff against was found; tell the user so, {NAME_A_BASE}"
        raise ChangeError(msg)
    return found


def merge_base(root: str, base: str, head: str) -> str:
    """The commit at which `head` parted from `base`."""
    commit = git.commit_id(root, base)
    if commit is None:
        msg = f"--base {base!r} does not resolve to a commit; tell the user so, {NAME_A_BASE}"
        raise ChangeError(msg)
    parted = git.run(root, "merge-base", commit, head, ok=(0, 1))
    if parted:
        return parted
    shallow = git.run(root, "rev-parse", "--is-shallow-repository")
    if parted is None or shallow is None:
        msg = f"git gave no merge base of HEAD and {base!r}; tell the user so, and stop"
    elif shallow == "true":
        msg = (
            f"the checkout does not hold the history that HEAD and {base!r} share, as in a depth-1 "
            "clone; tell the user so, with `git fetch --unshallow` or a deeper fetch as the "
            "remedy, and stop"
        )
    else:
        msg = f"HEAD and {base!r} share no history; tell the user so, {NAME_A_BASE}"
    raise ChangeError(msg)


def count(root: str, span: str) -> int:
    """How many commits the range `span` holds."""
    printed = git.run(root, "rev-list", "--count", span)
    if printed is None:
        msg = f"git could not count the commits of {span}; tell the user so, and stop"
        raise ChangeError(msg)
    return int(printed)


def _names_of(typed: str) -> tuple[str, str]:
    """The two ends of a range, as typed with two dots or three."""
    first, dots, second = typed.partition("..")
    if not dots:
        msg = (
            f"{typed!r} is no range: a range is typed as two ends with .. between them; tell the "
            "user so, and stop"
        )
        raise ChangeError(msg)
    return first or "HEAD", second.removeprefix(".") or "HEAD"


def older_end(root: str, typed: str, head: str) -> str:
    """The name of a range's older end. Refused where a scan from there up to `head` would leave
    out a commit of the range, or would start somewhere else."""
    first, second = _names_of(typed)
    older, newer = (git.commit_id(root, name) for name in (first, second))
    if older is None or newer is None:
        named = first if older is None else second
        msg = f"{named!r} in the range {typed!r} names no commit; tell the user so, and stop"
        raise ChangeError(msg)
    if older == newer:
        msg = f"both ends of the range {typed!r} are one commit; tell the user so, and stop"
        raise ChangeError(msg)
    if not count(root, f"{older}..{newer}"):
        msg = (
            f"the range {typed!r} is empty as typed, because {second} is already in the history of "
            f"{first}; tell the user that, and that {second}..{first} names the commits between "
            "them, and stop"
        )
        raise ChangeError(msg)
    if count(root, f"{head}..{newer}"):
        msg = (
            f"{second} is not in HEAD's history; tell the user that the scan reads only the code "
            f"that is checked out, so they would check {second} out and ask again, and stop"
        )
        raise ChangeError(msg)
    if count(root, f"{head}..{older}"):
        msg = (
            f"{first} is not in HEAD's history, so the scan would start somewhere the user did not "
            "name; tell the user that, and that they would name an older end in HEAD's history or "
            "scan the branch's changes instead, and stop"
        )
        raise ChangeError(msg)
    return first


def commits_after(root: str, typed: str, head: str) -> list[str]:
    """The newest commits of `head` after the newer end of a range that older_end() took, one
    line each."""
    newer = git.commit_id(root, _names_of(typed)[1])
    if newer is None:
        msg = f"git could not read the newer end of {typed!r}; tell the user so, and stop"
        raise ChangeError(msg)
    span = f"{newer}..{head}"
    listed = git.run(root, "rev-list", "--oneline", f"--max-count={NAMED_COMMITS}", span)
    if listed is None:
        msg = f"git could not list the commits of {span}; tell the user so, and stop"
        raise ChangeError(msg)
    return [line[:COMMIT_LINE_CHARS] for line in listed.split("\n")] if listed else []
