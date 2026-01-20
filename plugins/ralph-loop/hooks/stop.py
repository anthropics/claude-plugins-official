#!/usr/bin/env python3

"""
Ralph Loop Stop Hook (Python)

Cross-platform replacement for stop-hook.sh.
Avoids bash/WSL path issues on Windows and avoids external jq dependency.

Behavior:
- If no active loop state file: allow stop (exit 0, no output)
- If completion reached (promise matched or max iterations reached): clean state and allow stop
- Otherwise: block stop and feed the same prompt back via JSON decision
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional


def _read_stdin_json() -> Dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        v = json.loads(raw)
        return v if isinstance(v, dict) else {}
    except Exception:
        return {}


def _project_dir() -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env)
    return Path.cwd()


def _state_file(project_dir: Path) -> Path:
    return project_dir / ".claude" / "ralph-loop.local.md"


def _remove_file(p: Path) -> None:
    try:
        p.unlink(missing_ok=True)  # type: ignore[arg-type]
    except TypeError:
        # Python < 3.8 fallback
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass
    except Exception:
        pass


def _extract_frontmatter(md: str) -> Optional[str]:
    m = re.match(r"(?s)^---\s*\r?\n(.*?)\r?\n---\s*\r?\n", md)
    return m.group(1) if m else None


def _front_value(front: str, key: str) -> Optional[str]:
    m = re.search(rf"(?m)^\s*{re.escape(key)}\s*:\s*(.*)\s*$", front)
    return m.group(1).strip() if m else None


def _strip_yaml_quotes(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    s = v.strip()
    if s.lower() == "null" or s == "":
        return None
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        s = s[1:-1]
    return s if s else None


def _prompt_text(md: str) -> Optional[str]:
    # Everything after the closing --- line
    return re.sub(r"(?s)^---\s*\r?\n.*?\r?\n---\s*\r?\n", "", md, count=1) or None


def _read_last_assistant_text(transcript_path: Path) -> Optional[str]:
    last_line = None
    try:
        with transcript_path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if '"role":"assistant"' in line:
                    last_line = line
    except Exception:
        return None

    if not last_line:
        return None

    try:
        obj = json.loads(last_line)
    except Exception:
        return None

    content = (((obj or {}).get("message") or {}).get("content"))  # type: ignore[assignment]
    if not isinstance(content, list):
        return None

    parts = []
    for c in content:
        if isinstance(c, dict) and c.get("type") == "text" and isinstance(c.get("text"), str):
            parts.append(c["text"])
    out = "\n".join(parts).strip()
    return out if out else None


def main() -> int:
    hook_input = _read_stdin_json()
    project_dir = _project_dir()
    state_path = _state_file(project_dir)

    if not state_path.exists():
        return 0

    try:
        state_md = state_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        _remove_file(state_path)
        return 0

    front = _extract_frontmatter(state_md)
    if front is None:
        _remove_file(state_path)
        return 0

    iteration_raw = _front_value(front, "iteration")
    max_iter_raw = _front_value(front, "max_iterations")
    completion_raw = _front_value(front, "completion_promise")

    try:
        iteration = int((iteration_raw or "").strip())
        max_iterations = int((max_iter_raw or "").strip())
    except Exception:
        _remove_file(state_path)
        return 0

    completion_promise = _strip_yaml_quotes(completion_raw)

    if max_iterations > 0 and iteration >= max_iterations:
        _remove_file(state_path)
        return 0

    transcript_path_val = hook_input.get("transcript_path")
    transcript_path = Path(transcript_path_val) if isinstance(transcript_path_val, str) else None
    if transcript_path is None or not transcript_path.exists():
        _remove_file(state_path)
        return 0

    last_output = _read_last_assistant_text(transcript_path)
    if not last_output:
        _remove_file(state_path)
        return 0

    if completion_promise:
        m = re.search(r"(?s)<promise>(.*?)</promise>", last_output)
        if m:
            promise_text = re.sub(r"\s+", " ", m.group(1).strip())
            if promise_text == completion_promise:
                _remove_file(state_path)
                return 0

    prompt = _prompt_text(state_md)
    if prompt is None or not prompt.strip():
        _remove_file(state_path)
        return 0

    next_iteration = iteration + 1

    # Update iteration line (first match)
    updated, n = re.subn(r"(?m)^iteration:\s*.*$", f"iteration: {next_iteration}", state_md, count=1)
    if n != 1:
        _remove_file(state_path)
        return 0
    try:
        state_path.write_text(updated, encoding="utf-8")
    except Exception:
        _remove_file(state_path)
        return 0

    if completion_promise:
        system_msg = (
            f"Ralph iteration {next_iteration} | To stop: output <promise>{completion_promise}</promise> "
            f"(ONLY when statement is TRUE - do not lie to exit!)"
        )
    else:
        system_msg = f"Ralph iteration {next_iteration} | No completion promise set - loop runs infinitely"

    out = {
        "decision": "block",
        "reason": prompt,
        "systemMessage": system_msg,
    }
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

