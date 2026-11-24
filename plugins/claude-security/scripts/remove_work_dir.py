#!/usr/bin/env python3
"""Remove the working folder that a stage of an attack surface analysis leaves behind.

Usage:
  remove_work_dir.py <work_dir>

Removes `<work_dir>`, touches nothing else, and prints one line that says what it did.
`<work_dir>` must be the folder `.work` in a stage's directory of an analysis's output directory,
CLAUDE-SECURITY-<timestamp>/stage<n>-<name>/.work. The output directory must be there, in the
current directory, with the analysis.json that marks it as an analysis's. Each of the three must be
a folder, and not a link. Otherwise nothing is removed. Exits 0 when the folder is gone or was never
there, 1 when it is refused or cannot be removed, 2 on a usage error. Python 3.9, stdlib only.
"""

from __future__ import annotations

import argparse
import os
import stat
import sys
from pathlib import Path

# -P and PYTHONSAFEPATH leave this script's folder, which holds lib/, off sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import console, plugin
from lib.link import is_link
from lib.removal import remove_tree
from lib.surface_dir import OUTPUT_RE, WORK_DIR_NAME, Stage, in_current_directory


class Args(argparse.Namespace):
    """The parsed command line."""

    work_dir: str = ""


def file_type(path: Path) -> int:
    """The file type of `path` itself, as `stat.S_IFMT` gives it; 0 where nothing is there."""
    try:
        return stat.S_IFMT(path.lstat().st_mode)
    except (FileNotFoundError, NotADirectoryError):
        return 0


def why_kept(work: Path) -> str | None:
    """Why the folder `work` is left alone, or None where it may be removed or is not there."""
    stage, output = work.parent, work.parent.parent
    fits = (
        work.name == WORK_DIR_NAME
        and stage.name in {each.folder for each in Stage}
        and OUTPUT_RE.match(output.name)
    )
    if not fits:
        return "not the working folder of a stage of an attack surface analysis"
    link = next((path for path in (work, stage, output) if is_link(path)), None)
    if link:
        return f"'{link}' is a symbolic link"
    if not file_type(output):
        return f"there is no folder '{output}'"
    if not in_current_directory(output):
        return f"'{output}' is not in the current directory. Run this command from {output.parent}"
    other = next((p for p in (output, stage, work) if file_type(p) not in {0, stat.S_IFDIR}), None)
    if other:
        return f"'{other}' is not a folder"
    if not plugin.holds_analysis(output):
        return (
            f"'{output}' holds no {plugin.ANALYSIS_META_NAME} that can be read, so it does not "
            "count as an attack surface analysis's folder"
        )
    return None


def remove(work: Path) -> tuple[int, str]:
    """Remove `work` where it may go; the exit code, and the line that says what was done."""
    reason = why_kept(work)
    if reason:
        return 1, f"did not remove {work}: {reason}"
    if not file_type(work):
        return 0, f"no {work} to remove"
    remove_tree(work)
    return 0, f"removed {work}"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="remove_work_dir.py",
        description="Remove a stage's working folder.",
        allow_abbrev=False,
    )
    parser.add_argument("work_dir", help=f"the folder {WORK_DIR_NAME} in a stage's directory")
    given = parser.parse_args(argv, namespace=Args()).work_dir
    try:
        # abspath folds ".." without following symlinks, so the checks judge the path as written.
        code, line = remove(Path(os.path.abspath(given)))
    except OSError as error:
        code = 1
        line = f"WARNING: could not remove {given}: {console.removal_failure_detail(error)}"
    print(line)
    return code


if __name__ == "__main__":
    console.print_in_the_paths_encoding()
    sys.exit(main(sys.argv[1:]))
