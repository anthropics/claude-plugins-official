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
count under each top-level directory on a `dir_file_counts:` line.

Usage:
  write_scan_meta.py <run_dir> <scan_root> --mode scan|changes|commit
                     --effort low|medium|high|max [--scope a,b] [--base <ref>]
                     [--merge-base <sha>] [--commit <sha>]

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
import subprocess
import sys
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, NamedTuple, TypedDict
from urllib.parse import quote, unquote, urlsplit

# The lib/ package lives next to this script. Python normally adds a script's own
# directory to the import path, but not under -P or PYTHONSAFEPATH, so we add it here.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import absolute, console, plugin, strictjson

GIT_ENV = dict(os.environ, GIT_TERMINAL_PROMPT="0")


class Revision(TypedDict, total=False):
    """What was scanned. `versioned` is always present; the rest when in git."""

    versioned: bool
    commit: str | None
    parent: str | None
    branch: str | None
    dirty: bool | None
    sparse: Literal[True]
    not_checked_out_dirs: list[str]
    base: str | None
    merge_base: str | None


class Args(argparse.Namespace):
    """The parsed command line."""

    run_dir: str = ""
    scan_root: str = ""
    mode: str = ""
    effort: str = ""
    scope: str = ""
    base: str | None = None
    merge_base: str | None = None
    commit: str | None = None


class MetaError(Exception):
    """A refusal: the command line was well-formed but the run cannot be recorded."""


def git(cwd: str, *args: str) -> str | None:
    """One read-only git call, prompts suppressed. None on any failure."""
    try:
        out = subprocess.run(
            ["git", "-C", cwd, *args],
            env=GIT_ENV,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.decode("utf-8", "surrogateescape").rstrip("\r\n")


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
    if opts.mode == "commit":
        if not versioned:
            msg = f"--mode commit needs a git repository; {scan_root!r} is not one"
            raise MetaError(msg)
        commit_arg = opts.commit or ""
        sha = git(scan_root, "rev-parse", "--verify", "--quiet", commit_arg + "^{commit}")
        if not sha:
            msg = f"--commit {commit_arg!r} does not resolve to a commit"
            raise MetaError(msg)
        return {
            "versioned": True,
            "commit": sha,
            "parent": git(scan_root, "rev-parse", "--verify", "--quiet", sha + "^") or None,
            "branch": git(scan_root, "rev-parse", "--abbrev-ref", "HEAD"),
            "dirty": False,
        }
    if not versioned:
        return {"versioned": False}
    revision: Revision = {
        "versioned": True,
        "commit": git(scan_root, "rev-parse", "HEAD"),
        "branch": git(scan_root, "rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": worktree_dirty(scan_root),
    }
    if opts.mode == "changes":
        revision["base"] = opts.base
        revision["merge_base"] = opts.merge_base
    return revision


def scoped(entry: str, scan_root: str) -> str:
    """A scope entry relative to the scan root; an absolute spelling of anything else is refused."""
    if not absolute.spelled(entry):
        return entry
    msg = f"--scope entry {entry!r} is not inside the scan root {scan_root!r}"
    if not os.path.isabs(entry):
        raise MetaError(f"{msg}; write ./{entry} to name a directory in the tree")
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
    raise MetaError(msg)


def parse_options(argv: list[str]) -> Args:
    """The parsed command line; anything wrong with it is argparse's exit 2."""
    ap = argparse.ArgumentParser(prog="write_scan_meta", allow_abbrev=False)
    ap.add_argument("run_dir")
    ap.add_argument("scan_root")
    ap.add_argument("--mode", required=True, choices=plugin.MODES)
    ap.add_argument("--effort", required=True, choices=["low", "medium", "high", "max"])
    ap.add_argument("--scope")
    ap.add_argument("--base")
    ap.add_argument("--merge-base", dest="merge_base")
    ap.add_argument("--commit")
    opts = ap.parse_args(argv, namespace=Args())
    if opts.mode == "commit" and not opts.commit:
        ap.error("--mode commit requires --commit <sha>")
    if not os.path.isdir(opts.run_dir):
        ap.error(f"run directory does not exist: {opts.run_dir}")
    return opts


def main(argv: list[str]) -> int:
    opts = parse_options(argv)
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
        sys.stderr.write(f"write_scan_meta: could not list {scan_root}; file_count unknown\n")
    if whole_repo and extent is None:
        sys.stderr.write(f"write_scan_meta: could not list {scan_root}; top_level_dirs unknown\n")
    top_level, symlinks = (extent.dirs, extent.symlinks) if whole_repo and extent else (None, None)
    dir_file_counts = None
    if top_level is not None and files is not None:
        per_dir = Counter(path.partition("/")[0] for path in files if "/" in path)
        dir_file_counts = {name: per_dir[name] for name in top_level}
    if symlinks:
        sys.stderr.write(
            "write_scan_meta: root-level symbolic links not followed, "
            f"left out of top_level_dirs: {', '.join(symlinks)}\n"
        )
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
        "effort": opts.effort,
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
    except FileExistsError as error:
        msg = (
            f"{run_dir} already holds a scan's scan-meta.json, so another scan is using this "
            "report directory; make a new report directory named for the current time and "
            "run this again there"
        )
        raise MetaError(msg) from error
    if files is not None:
        (run_dir / plugin.TARGET_FILES_NAME).write_bytes((strictjson.text(files) + "\n").encode())
    sys.stdout.write(f"scan-meta.json written: {path}\n")
    sys.stdout.write(f"revision: {revision.get('commit') or 'UNVERSIONED'}\n")
    if absent is not None:
        listed = strictjson.text(absent)
        sys.stdout.write(f"sparse checkout: top-level directories not checked out: {listed}\n")
    sys.stdout.write(f"top_level_dirs: {strictjson.text(top_level)}\n")
    sys.stdout.write(f"file_count: {strictjson.text(None if files is None else len(files))}\n")
    sys.stdout.write(f"dir_file_counts: {strictjson.text(dir_file_counts)}\n")
    return 0


if __name__ == "__main__":
    console.tolerate_undecodable_names()
    try:
        sys.exit(main(sys.argv[1:]))
    except MetaError as error:
        sys.stderr.write(f"write_scan_meta: {error}\n")
        sys.exit(1)
    except OSError as error:
        sys.stderr.write(f"write_scan_meta: could not write the run's output: {error}\n")
        sys.exit(1)
