#!/usr/bin/env python3
"""Write scan-meta.json for a run: the record of what was scanned.

Captures the revision from git itself and, for a whole-repository scan, the
tree's top-level directories, printed as a JSON array on a `top_level_dirs:`
line and recorded in the meta file.

Usage:
  write_scan_meta.py <run_dir> <scan_root> --mode scan|changes|commit
                     --effort low|medium|high|max [--scope a,b] [--base <ref>]
                     [--merge-base <sha>] [--commit <sha>]

Exits 0 on success. A caller error prints a one-line diagnostic to stderr and
exits non-zero without writing the file.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import TypedDict, cast

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_report import RenderError, atomic_write

PLUGIN_NAME = "claude-security"
REPORT_DIR_PREFIX = "CLAUDE-SECURITY-"
GIT_ENV = dict(os.environ, GIT_TERMINAL_PROMPT="0")


class Revision(TypedDict, total=False):
    """What was scanned. `versioned` is always present; the rest when in git."""

    versioned: bool
    commit: str | None
    parent: str | None
    branch: str | None
    dirty: bool | None
    base: str | None
    merge_base: str | None


class Options(TypedDict):
    """The parsed, typed command line -- argparse hands back untyped attributes."""

    run_dir: str
    scan_root: str
    mode: str
    effort: str
    scope: str
    base: str | None
    merge_base: str | None
    commit: str | None


class MetaError(Exception):
    """An input error the caller must correct."""


def _opt_str(value: object) -> str | None:
    """An argparse optional as str-or-None, typed."""
    return None if value is None else str(value)


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
    return out.stdout.decode("utf-8", "replace").rstrip("\r\n")


def top_level_dirs(scan_root: str) -> list[str] | None:
    """The scan target's top-level directories, computed from the tree itself.

    Inside a git work tree the tracked files decide; where nothing is tracked
    the immediate subdirectories do. `.git` and `CLAUDE-SECURITY-*` report
    directories are excluded. None when the tree could not be listed.
    """
    names: set[str] = set()
    listing = git(scan_root, "ls-files", "-z")
    if listing:
        for path in listing.split("\0"):
            top, sep, _rest = path.partition("/")
            if sep and top:
                names.add(top)
            elif path and os.path.isdir(os.path.join(scan_root, path)):
                names.add(path)
    else:
        try:
            with os.scandir(scan_root) as entries:
                names.update(entry.name for entry in entries if entry.is_dir(follow_symlinks=False))
        except OSError:
            return None
        names.discard(".git")
    return sorted(n for n in names if not n.startswith(REPORT_DIR_PREFIX))


def worktree_dirty(scan_root: str) -> bool | None:
    """True/False/None (unknown) for the working tree, ignoring report dirs."""
    status = git(scan_root, "status", "--porcelain", "--untracked-files=all")
    if status is None:
        return None
    for line in status.splitlines():
        if len(line) < len("XY P"):
            continue
        path = line[3:].split(" -> ")[-1]
        top = path.split("/", 1)[0]
        if top.startswith(REPORT_DIR_PREFIX):
            continue
        return True
    return False


def capture_revision(scan_root: str, opts: Options) -> Revision:
    versioned = git(scan_root, "rev-parse", "--is-inside-work-tree") == "true"
    if opts["mode"] == "commit":
        if not versioned:
            msg = f"--mode commit needs a git repository; {scan_root!r} is not one"
            raise MetaError(msg)
        commit_arg = opts["commit"] or ""
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
    if opts["mode"] == "changes":
        revision["base"] = opts["base"]
        revision["merge_base"] = opts["merge_base"]
    return revision


def parse_options(argv: list[str]) -> Options:
    ap = argparse.ArgumentParser(prog="write_scan_meta")
    ap.add_argument("run_dir")
    ap.add_argument("scan_root")
    ap.add_argument("--mode", required=True, choices=["scan", "changes", "commit"])
    ap.add_argument("--effort", required=True, choices=["low", "medium", "high", "max"])
    ap.add_argument("--scope", default="")
    ap.add_argument("--base", default=None)
    ap.add_argument("--merge-base", dest="merge_base", default=None)
    ap.add_argument("--commit", default=None)
    ns = ap.parse_args(argv)
    return {
        "run_dir": str(cast("object", ns.run_dir)),
        "scan_root": str(cast("object", ns.scan_root)),
        "mode": str(cast("object", ns.mode)),
        "effort": str(cast("object", ns.effort)),
        "scope": str(cast("object", ns.scope)),
        "base": _opt_str(cast("object", ns.base)),
        "merge_base": _opt_str(cast("object", ns.merge_base)),
        "commit": _opt_str(cast("object", ns.commit)),
    }


def main(argv: list[str]) -> int:
    opts = parse_options(argv)
    if opts["mode"] == "commit" and not opts["commit"]:
        msg = "--mode commit requires --commit <sha>"
        raise MetaError(msg)

    run_dir = os.path.realpath(os.path.abspath(opts["run_dir"]))
    if not os.path.isdir(run_dir):
        msg = f"run directory does not exist: {run_dir}"
        raise MetaError(msg)
    scan_root = os.path.realpath(os.path.abspath(opts["scan_root"]))
    revision = capture_revision(scan_root, opts)
    scope = [s.strip() for s in opts["scope"].split(",") if s.strip()]
    if scope and all(s in {".", "./"} for s in scope):
        scope = []
    whole_repo = opts["mode"] == "scan" and not scope
    top_level = top_level_dirs(scan_root) if whole_repo else None
    if whole_repo and top_level is None:
        sys.stderr.write(f"write_scan_meta: could not list {scan_root}; top_level_dirs unknown\n")
    meta: dict[str, object] = {
        "scan_root": scan_root,
        "run_dir": run_dir,
        "flow": "scan" if opts["mode"] == "scan" else "changes",
        "agent": f"{PLUGIN_NAME}:{PLUGIN_NAME}",
        "mode": opts["mode"],
        "scope": scope,
        "effort": opts["effort"],
        "model": None,
        "revision": revision,
        "revision_source": "self-reported",
        "top_level_dirs": top_level,
    }
    path = os.path.join(run_dir, "scan-meta.json")
    atomic_write(path, json.dumps(meta, indent=2) + "\n")
    sys.stdout.write(f"scan-meta.json written: {path}\n")
    sys.stdout.write(f"revision: {revision.get('commit') or 'UNVERSIONED'}\n")
    sys.stdout.write(f"top_level_dirs: {json.dumps(top_level)}\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (MetaError, RenderError) as error:
        sys.stderr.write(f"write_scan_meta: {error}\n")
        sys.exit(2)
    except OSError as error:
        sys.stderr.write(f"write_scan_meta: could not write the run's output: {error}\n")
        sys.exit(2)
