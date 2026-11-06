#!/usr/bin/env python3
"""Write scan-meta.json for a run: the record of what was scanned.

Mints the scan's id, records when the scan started, and captures, from git
itself: the revision, the scan root's path within the repository, the
credential-free https form of its remote and, for a whole-repository scan,
the tree's top-level directories, printed as a JSON array on a
`top_level_dirs:` line and recorded in the meta file with any root-level
symbolic links left out of them. For a codebase scan it also lists the scan
target's tracked files into target-files.json beside the meta file and prints
their count on a `file_count:` line and, for a whole-repository scan, the
count under each top-level directory on a `dir_file_counts:` line. For a
changes or commit scan it writes the files the change touches into numbered
changed-files.<n>.json chunks beside the meta file and prints the change as its
two commit ids on a `range:` line, the count of those files on a
`changed_file_count:` line, their added-plus-deleted line count on a
`diff_line_count:` line and, last, the list itself on a `changed_files:`
line when it is short enough to hand over (null when it is not).

`--effort max` is recorded as `high`, and a `relay:` line carries the note
that tells the user so.

Usage:
  write_scan_meta.py <run_dir> <scan_root> --mode scan|changes|commit
                     --effort low|medium|high|max [--scope a,b] [--base <ref>]
                     [--merge-base <sha>] [--commit <sha>]

A changes scan names its `--merge-base`; a commit scan names its `--commit`,
which must be the checked-out commit.

Exits 0 on success, 1 on a refusal naming what is wrong (a run directory that
already holds a scan-meta.json is one), 2 on a usage error; the file is
written only on success.
Python 3.9-compatible, stdlib only.
"""

from __future__ import annotations

import argparse
import os
import re
import stat
import sys
import uuid
from collections import Counter
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import NamedTuple, TypedDict
from urllib.parse import quote, unquote, urlsplit

# The lib/ package lives next to this script. Python normally adds a script's own
# directory to the import path, but not under -P or PYTHONSAFEPATH, so we add it here.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import absolute, console, plugin, strictjson
from lib.git import run as git
from lib.revision import Revision, change_range


class Effort(Enum):
    """An effort tier, as `--effort` spells it."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAX = "max"


class Args(argparse.Namespace):
    """The parsed command line."""

    run_dir: str = ""
    scan_root: str = ""
    mode: str = ""
    effort: Effort = Effort.MEDIUM
    scope: str = ""
    base: str | None = None
    merge_base: str | None = None
    commit: str | None = None


class MetaError(Exception):
    """A refusal: the command line was well-formed but the run cannot be recorded."""


# Paths per changed-files.<n>.json; workflows/scan.js derives the chunk count from the same size.
CHANGED_FILES_CHUNK = 100
CHANGED_FILES_INLINE_CHARS = 25_000


class ChangedFiles(TypedDict):
    """One changed-files.<n>.json chunk: its number, the whole change's file count, its files."""

    chunk: int
    total_files: int
    files: list[str]


class Change(NamedTuple):
    """A change: its two commits as the `<base>..<commit>` range the scan diffs,
    the files it touches and its added-plus-deleted line count, None when a
    binary file leaves the count unknown."""

    range: str
    files: list[str]
    lines: int | None


class Extent(NamedTuple):
    """The scan target's top-level directories, its root-level symbolic links, the
    tracked top-level directories its working tree does not hold, and whether
    git tracks anything here at all."""

    dirs: list[str]
    symlinks: list[str]
    absent: list[str]
    tracked: bool


def tree_extent(scan_root: str) -> Extent | None:
    """The scan target's top-level directories, computed from the tree itself.

    Inside a git work tree the tracked files decide; where nothing is tracked
    the immediate subdirectories do. Entries are classified without following
    symbolic links, so nothing outside the checkout is read: a root-level
    symbolic link is never one of the directories, and is named in `symlinks`
    so the report can say it was not followed. `.git` and `CLAUDE-SECURITY-*`
    report directories are excluded. None when the tree could not be listed.
    """
    names: set[str] = set()
    symlinks: set[str] = set()
    listing = git(scan_root, "ls-files", "-z")
    if listing:
        for path in listing.split("\0"):
            top, sep, _rest = path.partition("/")
            if sep and top:
                names.add(top)
            elif path:
                try:
                    mode = os.lstat(os.path.join(scan_root, path)).st_mode
                except OSError:
                    continue
                if stat.S_ISLNK(mode):
                    symlinks.add(path)
                elif stat.S_ISDIR(mode):
                    names.add(path)
    else:
        try:
            with os.scandir(scan_root) as entries:
                for entry in entries:
                    if entry.is_symlink():
                        symlinks.add(entry.name)
                    elif entry.is_dir(follow_symlinks=False):
                        names.add(entry.name)
        except OSError:
            return None
        names.discard(".git")
    kept = sorted(n for n in names if not n.startswith(plugin.REPORT_DIR_PREFIX))
    on_disk = {n for n in kept if os.path.lexists(os.path.join(scan_root, n))}
    dirs = [n for n in kept if n in on_disk]
    return Extent(dirs, sorted(symlinks), [n for n in kept if n not in on_disk], bool(listing))


def sparse_checkout(scan_root: str, extent: Extent | None) -> list[str] | None:
    """The tracked top-level directories a sparse checkout left out; None when it is not one."""
    if git(scan_root, "config", "--bool", "core.sparseCheckout") != "true":
        return None
    return extent.absent if extent else []


def target_files(scan_root: str, scope: list[str]) -> list[str] | None:
    """The scan target's tracked regular files in the working tree, sorted; None if unlisted."""
    listing = git(scan_root, "ls-files", "-z", "--", *scope)
    if listing is None:
        return None
    return sorted({
        path
        for path in listing.split("\0")
        if path
        and not path.startswith(plugin.REPORT_DIR_PREFIX)
        and regular_file(os.path.join(scan_root, path))
    })


def changed_files(scan_root: str, scope: list[str], *, commits: str) -> Change:
    """The change `commits` names (`<base>..<commit>`) within `scope`, from `git diff-tree`."""
    numstat = ("diff-tree", "-r", "--no-commit-id", "--numstat", "-z", "-M", "--relative")
    listing = git(scan_root, *numstat, commits, "--", *scope)
    if listing is None:
        msg = f"git could not diff {commits} in {scan_root!r}"
        raise MetaError(msg)
    lines: dict[str, int | None] = {}
    records = iter(listing.split("\0"))
    for record in records:
        if not record:
            continue
        added, deleted, path = record.split("\t", 2)
        if not path:
            next(records, "")
            path = next(records, "")
        if path and not path.startswith(plugin.REPORT_DIR_PREFIX):
            lines[path] = None if "-" in {added, deleted} else int(added) + int(deleted)
    known = [count for count in lines.values() if count is not None]
    total = sum(known) if len(known) == len(lines) else None
    return Change(commits, sorted(lines), total)


def change_lines(change: Change | None) -> list[str]:
    """The range, changed_file_count, diff_line_count and changed_files lines record() prints."""
    if change is None:
        return [
            "range: null",
            "changed_file_count: null",
            "diff_line_count: null",
            "changed_files: null",
        ]
    listed = strictjson.text(change.files)
    handed = listed if len(listed) <= CHANGED_FILES_INLINE_CHARS else "null"
    return [
        f"range: {strictjson.text(change.range)}",
        f"changed_file_count: {len(change.files)}",
        f"diff_line_count: {strictjson.text(change.lines)}",
        f"changed_files: {handed}",
    ]


def regular_file(path: str) -> bool:
    """Whether `path` is a regular file, judged without following a symbolic link."""
    try:
        return stat.S_ISREG(os.lstat(path).st_mode)
    except OSError:
        return False


REMOTE_SCHEMES = frozenset({"http", "https", "ssh", "git", "git+ssh"})


def sanitize_remote(url: str | None) -> str | None:
    """`url` as a credential-free https URL naming the same repository, or None.

    Userinfo, query and fragment are stripped; the scheme becomes https and the
    host lowercase; a port survives only from an http or https URL; scp-like
    `user@host:path` is read as ssh; a trailing `/` or `.git` is dropped, so
    the ssh and https spellings of one repository come out equal. A URL that
    does not name a hosted repository is None.
    """
    text = (url or "").strip()
    if not text or "[" in text or "]" in text or strictjson.has_lone_surrogate(text):
        return None
    if "://" in text:
        try:
            parts = urlsplit(text)
            port = parts.port if parts.scheme.lower() in {"http", "https"} else None
        except ValueError:
            return None
        if parts.scheme.lower() not in REMOTE_SCHEMES:
            return None
        host = (parts.hostname or "").lower()
        location = host if port is None else f"{host}:{port}"
        path = parts.path
    else:
        # Userinfo splits off first: an optional user@ group backtracks and leaks the secret.
        rest = text.rpartition("@")[2]
        matched = re.match(r"([^@:/\\]{2,}):(.*)", rest)
        if not matched:
            return None
        location = matched[1].lower()
        path = matched[2]
    if not re.fullmatch(r"[a-z0-9.-]+(?::\d+)?", location):
        return None
    path = quote(unquote(path.strip("/"))).removesuffix(".git").rstrip("/")
    if not path:
        return None
    return f"https://{location}/{path}"


def worktree_dirty(scan_root: str) -> bool | None:
    """True/False/None (unknown) for the working tree, ignoring report dirs."""
    status = git(scan_root, "status", "--porcelain", "--untracked-files=all")
    if status is None:
        return None
    for line in status.splitlines():
        if len(line) < len("XY P"):
            continue
        path = line[3:].split(" -> ")[-1]
        if any(part.startswith(plugin.REPORT_DIR_PREFIX) for part in path.split("/")[:-1]):
            continue
        return True
    return False


def capture_revision(scan_root: str, opts: Args) -> Revision:
    versioned = git(scan_root, "rev-parse", "--is-inside-work-tree") == "true"
    if opts.mode != "scan" and not versioned:
        msg = f"--mode {opts.mode} needs a git repository; {scan_root!r} is not one"
        raise MetaError(msg)
    if opts.mode == "commit":
        commit_arg = opts.commit or ""
        sha = git(scan_root, "rev-parse", "--verify", "--quiet", commit_arg + "^{commit}")
        if not sha:
            msg = f"--commit {commit_arg!r} does not resolve to a commit"
            raise MetaError(msg)
        short = sha[: plugin.SHORT_ID_CHARS]
        parent = git(scan_root, "rev-parse", "--verify", "--quiet", sha + "^") or None
        if parent is None:
            msg = (
                f"the parent of commit {short} is not in this clone (a shallow checkout); "
                "fetch more history before scanning the commit"
                if names_a_parent(scan_root, sha)
                else f"commit {short} is the repository's first and has no parent to "
                "diff against; scan the codebase at that commit instead"
            )
            raise MetaError(msg)
        if sha != git(scan_root, "rev-parse", "--verify", "--quiet", "HEAD"):
            msg = (
                f"commit {short} is not checked out, and a commit scan runs only on the "
                f"checked-out commit (HEAD); tell the user to check {short} out and ask again, "
                "and stop: never check it out or add a worktree yourself"
            )
            raise MetaError(msg)
        return {
            "versioned": True,
            "commit": sha,
            "parent": parent,
            "branch": git(scan_root, "rev-parse", "--abbrev-ref", "HEAD"),
            "dirty": False,
        }
    if not versioned:
        return {"versioned": False}
    head = git(scan_root, "rev-parse", "--verify", "--quiet", "HEAD")
    revision: Revision = {
        "versioned": True,
        "commit": head,
        "branch": git(scan_root, "rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": worktree_dirty(scan_root),
    }
    if opts.mode == "changes":
        if not head:
            msg = "HEAD names no commit yet, so there is no change to scan"
            raise MetaError(msg)
        base_arg = opts.merge_base or ""
        merge_base = git(scan_root, "rev-parse", "--verify", "--quiet", base_arg + "^{commit}")
        if not merge_base:
            msg = (
                f"--merge-base {opts.merge_base!r} does not resolve to a commit "
                "(a shallow clone may not hold it: fetch more history)"
            )
            raise MetaError(msg)
        if git(scan_root, "merge-base", "--is-ancestor", merge_base, head) is None:
            msg = (
                f"--merge-base {opts.merge_base!r} is not an ancestor of HEAD, so it is not "
                "this branch's merge base (a shallow clone cannot compute one: fetch more history)"
            )
            raise MetaError(msg)
        revision["base"] = opts.base
        revision["merge_base"] = merge_base
    return revision


def names_a_parent(scan_root: str, sha: str) -> bool:
    """Whether the commit object itself records a parent, whatever the clone holds of it."""
    body = git(scan_root, "cat-file", "commit", sha)
    if body is None:
        msg = f"git could not read commit {sha[: plugin.SHORT_ID_CHARS]}, so its parent is unknown"
        raise MetaError(msg)
    return any(line.startswith("parent ") for line in body.split("\n\n", 1)[0].splitlines())


def scoped(entry: str, scan_root: str) -> str:
    """A scope entry relative to the scan root; an absolute spelling of anything else is refused."""
    if not absolute.spelled(entry):
        return entry
    outside = f"--scope entry {entry!r} is not inside the scan root {scan_root!r}"
    if not os.path.isabs(entry):
        msg = f"{outside}; write ./{entry} to name a directory in the tree"
        raise MetaError(msg)
    literal = os.path.abspath(entry)
    parent, name = os.path.split(literal)
    try:
        resolutions = [
            literal,
            os.path.join(os.path.realpath(parent), name),
            os.path.realpath(entry),
        ]
    except OSError:
        resolutions = [literal]
    for resolved in resolutions:
        if (relative := absolute.relative(resolved, scan_root)) is not None:
            return relative
    raise MetaError(outside)


def tier(word: str) -> Effort:
    """The tier a word names, whatever its case or the spaces around it; any other is refused."""
    try:
        return Effort(word.strip().lower())
    except ValueError:
        offered = ", ".join(effort.value for effort in Effort if effort is not Effort.MAX)
        msg = (
            f"{word!r} is not an effort tier; the tiers are {offered}. "
            "Tell the user so and start no scan; do not choose a tier for them"
        )
        raise argparse.ArgumentTypeError(msg) from None


def parse_options(argv: list[str]) -> Args:
    """The parsed command line; anything wrong with it is argparse's exit 2."""
    parser = argparse.ArgumentParser(prog="write_scan_meta.py", allow_abbrev=False)
    parser.add_argument("run_dir")
    parser.add_argument("scan_root")
    parser.add_argument("--mode", required=True, choices=plugin.MODES)
    parser.add_argument("--effort", required=True, type=tier)
    parser.add_argument("--scope")
    parser.add_argument("--base")
    parser.add_argument("--merge-base", dest="merge_base")
    parser.add_argument("--commit")
    opts = parser.parse_args(argv, namespace=Args())
    if opts.mode == "commit" and not opts.commit:
        parser.error("--mode commit requires --commit <sha>")
    if opts.mode == "changes" and not opts.merge_base:
        parser.error("--mode changes requires --merge-base <sha>")
    if not os.path.isdir(opts.run_dir):
        parser.error(f"run directory does not exist: {opts.run_dir}")
    return opts


def record(opts: Args) -> None:
    """Record what is scanned into the run directory's scan-meta.json and print its summary."""
    # abspath first: "x/.." is x's parent as typed, where realpath alone would follow a symlink x.
    run_dir = Path(os.path.realpath(os.path.abspath(opts.run_dir)))
    scan_root = os.path.realpath(os.path.abspath(opts.scan_root))
    revision = capture_revision(scan_root, opts)
    extent = tree_extent(scan_root)
    absent = sparse_checkout(scan_root, extent) if revision.get("versioned") else None
    if absent is not None:
        revision["sparse"] = True
        revision["not_checked_out_dirs"] = absent
    scan_prefix = (
        git(scan_root, "rev-parse", "--show-prefix") if revision.get("versioned") else None
    )
    remote = (
        sanitize_remote(git(scan_root, "remote", "get-url", "origin"))
        if revision.get("versioned")
        else None
    )
    scope = [scoped(entry.strip(), scan_root) for entry in opts.scope.split(",") if entry.strip()]
    if scope and all(s in {".", "./"} for s in scope):
        scope = []
    whole_repo = opts.mode == "scan" and not scope
    tracked = opts.mode == "scan" and extent is not None and extent.tracked
    files = target_files(scan_root, scope) if tracked else None
    if tracked and files is None:
        sys.stderr.write(f"write_scan_meta.py: could not list {scan_root}; file_count unknown\n")
    change = None
    if opts.mode != "scan":
        commits = change_range(revision)
        if commits is None:
            msg = "the change's endpoints are unknown"
            raise MetaError(msg)
        change = changed_files(scan_root, scope, commits=commits)
    if whole_repo and extent is None:
        sys.stderr.write(
            f"write_scan_meta.py: could not list {scan_root}; top_level_dirs unknown\n"
        )
    top_level, symlinks = (extent.dirs, extent.symlinks) if whole_repo and extent else (None, None)
    dir_file_counts = None
    if top_level is not None and files is not None:
        per_dir = Counter(path.partition("/")[0] for path in files if "/" in path)
        dir_file_counts = {name: per_dir[name] for name in top_level}
    if symlinks:
        sys.stderr.write(
            "write_scan_meta.py: root-level symbolic links not followed, "
            f"left out of top_level_dirs: {', '.join(symlinks)}\n"
        )
    retired = opts.effort is Effort.MAX
    effort = Effort.HIGH if retired else opts.effort
    meta: dict[str, object] = {
        "scan_id": str(uuid.uuid4()),
        "started_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "scan_root": scan_root,
        "scan_prefix": scan_prefix,
        "remote": remote,
        "run_dir": str(run_dir),
        "flow": "scan" if opts.mode == "scan" else "changes",
        "agent": f"{plugin.NAME}:{plugin.NAME}",
        "mode": opts.mode,
        "scope": scope,
        "effort": effort.value,
        "asked_for_max": retired,
        "model": None,
        "revision": revision,
        "revision_source": "self-reported",
        "top_level_dirs": top_level,
        "unfollowed_symlinks": symlinks,
    }
    path = run_dir / "scan-meta.json"
    # Created exclusively: a run directory that already holds one belongs to another scan.
    try:
        with path.open("x", encoding="utf-8", newline="\n") as out:
            out.write(strictjson.text(meta, indent=2) + "\n")
    except (FileExistsError, PermissionError) as error:
        if isinstance(error, PermissionError) and not path.is_dir():
            raise
        msg = (
            f"{run_dir} already holds a scan's scan-meta.json, so another scan is using this "
            "report directory; make a new report directory named for the current time and "
            "run this again there"
        )
        raise MetaError(msg) from error
    if files is not None:
        (run_dir / plugin.TARGET_FILES_NAME).write_bytes((strictjson.text(files) + "\n").encode())
    if change is not None:
        for number, start in enumerate(range(0, len(change.files), CHANGED_FILES_CHUNK), start=1):
            chunk: ChangedFiles = {
                "chunk": number,
                "total_files": len(change.files),
                "files": change.files[start : start + CHANGED_FILES_CHUNK],
            }
            (run_dir / f"changed-files.{number}.json").write_bytes(
                (strictjson.text(chunk, indent=1) + "\n").encode()
            )
    print(f"scan-meta.json written: {path}")
    print(f"revision: {revision.get('commit') or 'UNVERSIONED'}")
    if absent is not None:
        print(f"sparse checkout: top-level directories not checked out: {strictjson.text(absent)}")
    if retired:
        print(plugin.RETIRED_MAX_RELAY)
    print(f"top_level_dirs: {strictjson.text(top_level)}")
    print(f"file_count: {strictjson.text(None if files is None else len(files))}")
    print(f"dir_file_counts: {strictjson.text(dir_file_counts)}")
    for line in change_lines(change):
        print(line)


def main(argv: list[str]) -> int:
    opts = parse_options(argv)
    try:
        record(opts)
    except MetaError as error:
        sys.stderr.write(f"write_scan_meta.py: {error}\n")
        return 1
    except OSError as error:
        sys.stderr.write(f"write_scan_meta.py: could not write the run's output: {error}\n")
        return 1
    return 0


if __name__ == "__main__":
    console.tolerate_undecodable_names()
    sys.exit(main(sys.argv[1:]))
