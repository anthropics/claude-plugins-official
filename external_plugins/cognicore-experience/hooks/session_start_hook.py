#!/usr/bin/env python
"""
CogniCore SessionStart Hook for Claude Code.

Initializes the environment context and provides a brief summary of available
verified memories and known failure patterns in the persistent CogniCore database.
"""

import sys
import os
import json
import platform
import subprocess
from pathlib import Path


def get_git_info():
    repo_id = "unknown"
    commit = ""
    branch = ""
    try:
        remote_res = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if remote_res.returncode == 0 and remote_res.stdout.strip():
            repo_id = remote_res.stdout.strip().replace(".git", "").split("/")[-1]

        commit_res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if commit_res.returncode == 0:
            commit = commit_res.stdout.strip()

        branch_res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if branch_res.returncode == 0:
            branch = branch_res.stdout.strip()
    except Exception:
        pass
    return repo_id, commit, branch


def main():
    repo_id, commit, branch = get_git_info()
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    os_name = platform.system()

    # Inform the agent about the CogniCore experience skill & tools
    msg = (
        f"[CogniCore Experience] Active (Env: Python {py_ver} on {os_name}, Repo: {repo_id}@{branch}). "
        f"Use `cognicore_recall_experience` before non-trivial tasks to retrieve verified solutions and failure warnings."
    )
    print(msg)


if __name__ == "__main__":
    main()
