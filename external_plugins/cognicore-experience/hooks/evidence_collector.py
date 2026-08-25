#!/usr/bin/env python
"""
CogniCore Evidence Collector Hook for Claude Code.

Executed during PostToolUse when Bash commands run (e.g. test suites, builds, linters).
Records verifiable execution evidence (command, exit_code, stdout_hash, timestamp, git commit)
into the session evidence buffer so it is available for VerificationGate evaluation.
"""

import sys
import os
import json
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def get_git_commit() -> str:
    """Gets the current git commit hash if in a git repository."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return ""


def get_evidence_file_path() -> Path:
    """Returns the path to the session evidence buffer file."""
    evidence_dir = Path.cwd() / ".cognicore"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    return evidence_dir / "session_evidence.json"


def record_tool_evidence(tool_input: str, tool_output: str, exit_code: int = 0):
    """Saves execution evidence into the session buffer."""
    evidence_path = get_evidence_file_path()

    records = []
    if evidence_path.exists():
        try:
            with open(evidence_path, "r", encoding="utf-8") as f:
                records = json.load(f)
            if not isinstance(records, list):
                records = []
        except Exception:
            records = []

    stdout_hash = hashlib.sha256(tool_output.encode("utf-8")).hexdigest()[:16]
    commit = get_git_commit()
    timestamp = datetime.now(timezone.utc).isoformat()

    record = {
        "command": tool_input.strip(),
        "exit_code": int(exit_code),
        "stdout_hash": stdout_hash,
        "timestamp": timestamp,
        "commit": commit,
    }

    records.append(record)

    # Keep last 50 execution records in session buffer
    records = records[-50:]

    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


def main():
    # Read hook payload from stdin if available
    try:
        input_data = sys.stdin.read()
        if input_data:
            payload = json.loads(input_data)
            tool_name = payload.get("tool", "")
            tool_input = payload.get("input", {}).get("command", "") or payload.get("command", "")
            tool_output = payload.get("output", "") or payload.get("result", "")
            exit_code = payload.get("exit_code", 0)

            if tool_input:
                record_tool_evidence(tool_input, tool_output, exit_code)
    except Exception:
        # Hooks should be fail-safe and never break the user session
        pass


if __name__ == "__main__":
    main()
