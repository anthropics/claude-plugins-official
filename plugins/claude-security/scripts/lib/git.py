"""Read-only git calls for the scripts: one runner, prompts suppressed, output byte-faithful."""

from __future__ import annotations

import os
import subprocess

REDIRECTS = frozenset({"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"})
ENV = {k: v for k, v in os.environ.items() if k not in REDIRECTS} | {"GIT_TERMINAL_PROMPT": "0"}


def run(cwd: str, *args: str) -> str | None:
    """The stdout of `git -C <cwd> <args>` without trailing newlines; None on any failure."""
    try:
        out = subprocess.run(
            ["git", "-C", cwd, *args],
            env=ENV,
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
