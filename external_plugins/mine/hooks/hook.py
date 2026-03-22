#!/usr/bin/env python3
# tested with: claude code v2.1.81
"""hook.py -- unified hook dispatcher for the mine plugin.

Handles all hook events. No bash scripts, no jq dependency.
All JSON parsing via stdlib json, all SQL via parameterized queries.
"""

from __future__ import annotations

import json
import os
import pathlib
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

CLAUDE_DIR = pathlib.Path.home() / ".claude"
DB_PATH = CLAUDE_DIR / "mine.db"
CONFIG_PATH = CLAUDE_DIR / "mine.json"
HOOK_DIR = pathlib.Path(__file__).resolve().parent
SCRIPTS_DIR = HOOK_DIR.parent / "scripts"


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------

def load_config() -> dict:
    """Load mine.json config. Returns empty dict if missing or invalid."""
    try:
        return json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
    except (json.JSONDecodeError, OSError):
        return {}


def is_enabled(config: dict, feature: str) -> bool:
    """Check if a feature toggle is enabled (default: True)."""
    return config.get(feature, True) is not False


def db_connect() -> sqlite3.Connection | None:
    """Connect to mine.db with WAL mode and 5s timeout. None if DB missing."""
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH), timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def find_mine_py() -> pathlib.Path | None:
    """Locate mine.py relative to this hook script."""
    candidates = [
        SCRIPTS_DIR / "mine.py",
        HOOK_DIR.parent.parent / "scripts" / "mine.py",
    ]
    # also search installed plugin paths
    plugins_dir = CLAUDE_DIR / "plugins"
    if plugins_dir.exists():
        for p in plugins_dir.rglob("mine/scripts/mine.py"):
            candidates.append(p)
    for c in candidates:
        if c.exists():
            return c
    return None


def extract_tool_summary(tool_name: str, tool_input: dict) -> str:
    """Extract a human-readable summary from tool input. Mirrors mine.py logic."""
    if not isinstance(tool_input, dict):
        return str(tool_input)[:300]
    if tool_name in ("Read", "Write", "Edit"):
        return tool_input.get("file_path", "")
    if tool_name == "Bash":
        return (tool_input.get("command") or tool_input.get("description") or "")[:200]
    if tool_name in ("Grep", "Glob"):
        return tool_input.get("pattern", "")
    if tool_name == "Task":
        return (tool_input.get("description") or tool_input.get("prompt") or "")[:200]
    # fallback: first value
    vals = list(tool_input.values())
    return str(vals[0])[:200] if vals else ""


def log(msg: str, stderr: bool = True) -> None:
    """Print a log message. stderr for debug, stdout for Claude-visible context."""
    print(msg, file=sys.stderr if stderr else sys.stdout)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def handle_ingest(payload: dict, config: dict) -> None:
    """SessionEnd (async): parse main transcript + subagent transcripts."""
    if not is_enabled(config, "ingest"):
        return

    transcript = payload.get("transcript_path", "")
    if not transcript or not os.path.isfile(transcript):
        log(f"[mine] ingest: no valid transcript_path, skipping")
        return

    mine_py = find_mine_py()
    if not mine_py:
        log("[mine] ingest: mine.py not found")
        return

    # parse main session
    log(f"[mine] ingest: parsing {transcript}")
    subprocess.run(
        [sys.executable, str(mine_py), "--file", transcript],
        capture_output=False,
    )

    # parse subagent transcripts
    subagents_dir = pathlib.Path(transcript).parent / "subagents"
    if subagents_dir.is_dir():
        for sub in sorted(subagents_dir.glob("*.jsonl")):
            log(f"[mine] ingest: parsing subagent {sub}")
            subprocess.run(
                [sys.executable, str(mine_py), "--file", str(sub)],
                capture_output=False,
            )

    log("[mine] ingest: done")


def handle_subagent(payload: dict, config: dict) -> None:
    """SubagentStop: parse a single subagent transcript."""
    if not is_enabled(config, "ingest"):  # shares ingest toggle
        return

    transcript = payload.get("agent_transcript_path", "")
    if not transcript or not os.path.isfile(transcript):
        log("[mine] subagent: no valid transcript, skipping")
        return

    mine_py = find_mine_py()
    if not mine_py:
        log("[mine] subagent: mine.py not found")
        return

    log(f"[mine] subagent: parsing {transcript}")
    subprocess.run(
        [sys.executable, str(mine_py), "--file", transcript],
        capture_output=False,
    )


def handle_mistakes(payload: dict, config: dict) -> None:
    """PostToolUseFailure: record error and surface past similar failures."""
    if not is_enabled(config, "mistakes"):
        return

    conn = db_connect()
    if not conn:
        return

    tool_name = payload.get("tool_name", "")
    session_id = payload.get("session_id", "")
    error_msg = payload.get("error", "")
    tool_input = payload.get("tool_input", {})

    if not tool_name or not session_id:
        conn.close()
        return

    input_summary = extract_tool_summary(tool_name, tool_input)
    error_short = error_msg[:500]
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # look up project name for this session
    row = conn.execute(
        "SELECT project_name FROM sessions WHERE id = ? LIMIT 1",
        (session_id,),
    ).fetchone()
    project_name = row[0] if row else ""

    # check for past similar failures in this project
    if project_name:
        past = conn.execute(
            """SELECT e.error_message, e.input_summary, e.timestamp
            FROM errors e JOIN sessions s ON s.id = e.session_id
            WHERE e.tool_name = ? AND s.project_name = ?
            ORDER BY e.timestamp DESC LIMIT 5""",
            (tool_name, project_name),
        ).fetchall()

        if past:
            # stdout goes to Claude as context
            print(f"[mine:mistakes] {tool_name} has failed {len(past)} time(s) before in '{project_name}'.")
            last = past[0]
            if last[0]:
                print(f"[mine:mistakes] Previous failure ({last[2]}): input='{(last[1] or '')[:100]}' error='{last[0][:200]}'")

    # always record the current failure
    conn.execute(
        """INSERT INTO errors (session_id, tool_name, input_summary, error_message, is_interrupt, timestamp)
        VALUES (?, ?, ?, ?, 0, ?)""",
        (session_id, tool_name, input_summary, error_short, timestamp),
    )
    conn.commit()
    conn.close()
    log(f"[mine] mistakes: recorded {tool_name} failure")


def handle_burn(payload: dict, config: dict) -> None:
    """PreCompact: compare session tokens to project average, warn if >2x."""
    if not is_enabled(config, "burn"):
        return

    conn = db_connect()
    if not conn:
        return

    session_id = payload.get("session_id", "")
    if not session_id:
        conn.close()
        return

    # get current session tokens + project name
    row = conn.execute(
        """SELECT COALESCE(total_input_tokens,0) + COALESCE(total_output_tokens,0)
                + COALESCE(total_cache_creation_tokens,0) + COALESCE(total_cache_read_tokens,0),
                project_name
        FROM sessions WHERE id = ? LIMIT 1""",
        (session_id,),
    ).fetchone()

    if not row or not row[1] or row[0] == 0:
        conn.close()
        return

    current_tokens, project_name = row

    # project average for sessions that had compaction
    avg_row = conn.execute(
        """SELECT CAST(AVG(
            COALESCE(total_input_tokens,0) + COALESCE(total_output_tokens,0)
            + COALESCE(total_cache_creation_tokens,0) + COALESCE(total_cache_read_tokens,0)
        ) AS INTEGER)
        FROM sessions
        WHERE project_name = ? AND is_subagent = 0 AND compaction_count > 0 AND id != ?""",
        (project_name, session_id),
    ).fetchone()

    avg_tokens = avg_row[0] if avg_row and avg_row[0] else 0

    # fallback to global average
    if avg_tokens == 0:
        avg_row = conn.execute(
            """SELECT CAST(AVG(
                COALESCE(total_input_tokens,0) + COALESCE(total_output_tokens,0)
                + COALESCE(total_cache_creation_tokens,0) + COALESCE(total_cache_read_tokens,0)
            ) AS INTEGER)
            FROM sessions WHERE is_subagent = 0 AND compaction_count > 0 AND id != ?""",
            (session_id,),
        ).fetchone()
        avg_tokens = avg_row[0] if avg_row and avg_row[0] else 0

    conn.close()

    if avg_tokens == 0:
        return

    ratio = current_tokens / avg_tokens

    # warn if >2x average
    if ratio > 2.0:
        if current_tokens >= 1_000_000_000:
            token_fmt = f"{current_tokens / 1_000_000_000:.1f}B"
        elif current_tokens >= 1_000_000:
            token_fmt = f"{current_tokens / 1_000_000:.1f}M"
        else:
            token_fmt = f"{current_tokens // 1000}K"

        # rough cost estimate (dominant cost is cache reads at $0.50/1M)
        cost_est = current_tokens * 50 / 1_000_000_000
        print(f"[mine:burn] this session is at {token_fmt} tokens — {ratio:.1f}x your avg for '{project_name}' (~${cost_est:.2f} estimated)")


def handle_compact(payload: dict, config: dict) -> None:
    """PreCompact: increment compaction_count for session."""
    if not is_enabled(config, "compact"):
        return

    conn = db_connect()
    if not conn:
        return

    session_id = payload.get("session_id", "")
    if not session_id:
        conn.close()
        return

    conn.execute(
        "UPDATE sessions SET compaction_count = compaction_count + 1 WHERE id = ?",
        (session_id,),
    )
    conn.commit()
    conn.close()
    log(f"[mine] compact: incremented compaction_count for {session_id}")


def handle_precompact(payload: dict, config: dict) -> None:
    """PreCompact: run both compact + burn in a single invocation."""
    handle_compact(payload, config)
    handle_burn(payload, config)


def handle_startup(payload: dict, config: dict) -> None:
    """SessionStart: migration, freshness check, backfill, move detect, search."""
    # one-time migration: miner -> mine
    old_db = CLAUDE_DIR / "miner.db"
    if old_db.exists() and not DB_PATH.exists():
        old_db.rename(DB_PATH)
        old_config = CLAUDE_DIR / "miner.json"
        if old_config.exists():
            old_config.rename(CONFIG_PATH)
        old_ignore = CLAUDE_DIR / ".minerignore"
        if old_ignore.exists():
            old_ignore.rename(CLAUDE_DIR / ".mineignore")
        print("[mine] migrated miner.db -> mine.db")

    conn = db_connect()
    if not conn:
        return

    # first-run feedback
    count = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    if count == 0:
        log("[mine] first session — tracking starts now")

    cwd = payload.get("cwd") or os.getcwd()
    project_name = os.path.basename(cwd)

    # --- freshness check + auto-backfill ---
    if is_enabled(config, "auto_backfill"):
        row = conn.execute(
            "SELECT MAX(start_time) FROM sessions WHERE is_subagent = 0"
        ).fetchone()
        latest = row[0] if row else None

        if latest:
            try:
                # parse ISO timestamp
                latest_clean = latest.split(".")[0].replace("Z", "")
                latest_dt = datetime.fromisoformat(latest_clean).replace(tzinfo=timezone.utc)
                gap = (datetime.now(timezone.utc) - latest_dt).total_seconds()

                if gap > 86400:  # >1 day stale
                    mine_py = find_mine_py()
                    if mine_py:
                        gap_days = int(gap / 86400)
                        log(f"[mine:heal] data is {gap_days}d stale. backfilling in background...")
                        subprocess.Popen(
                            [sys.executable, str(mine_py), "--incremental"],
                            stdout=open(str(CLAUDE_DIR / "mine-backfill.log"), "a"),
                            stderr=subprocess.STDOUT,
                        )
            except (ValueError, OSError):
                pass

    # --- project move detection ---
    if is_enabled(config, "move_detect"):
        rows = conn.execute(
            """SELECT cwd, session_count FROM project_paths
            WHERE project_name = ? AND cwd != ?
            ORDER BY last_seen DESC LIMIT 1""",
            (project_name, cwd),
        ).fetchall()

        if rows:
            old_cwd, old_count = rows[0]
            print(f"[mine] Project '{project_name}' was previously at {old_cwd} ({old_count} sessions). All history preserved in mine.")

    # --- search / solution recall ---
    if is_enabled(config, "search"):
        prompts = conn.execute(
            """SELECT m.content_preview FROM messages m
            JOIN sessions s ON s.id = m.session_id
            WHERE s.project_name = ? AND m.role = 'user'
                AND m.content_preview IS NOT NULL AND m.content_preview != ''
            ORDER BY m.timestamp DESC LIMIT 5""",
            (project_name,),
        ).fetchall()

        if prompts:
            session_count = conn.execute(
                "SELECT COUNT(*) FROM sessions WHERE project_name = ? AND is_subagent = 0",
                (project_name,),
            ).fetchone()[0]

            last_session = conn.execute(
                """SELECT start_time FROM sessions
                WHERE project_name = ? AND is_subagent = 0
                ORDER BY start_time DESC LIMIT 1""",
                (project_name,),
            ).fetchone()

            if session_count > 0:
                last_time = last_session[0] if last_session else "unknown"
                print(f"[mine:search] {session_count} previous sessions on '{project_name}'. Last: {last_time}.")
                print("[mine:search] Recent work:")
                for row in prompts[:3]:
                    print(f"  - {(row[0] or '')[:120]}")

    conn.close()


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

HANDLERS: dict[str, tuple[str | None, callable]] = {
    "ingest":     ("ingest",   handle_ingest),
    "subagent":   ("ingest",   handle_subagent),    # shares ingest toggle
    "mistakes":   ("mistakes", handle_mistakes),
    "burn":       ("burn",     handle_burn),
    "compact":    ("compact",  handle_compact),
    "precompact": (None,       handle_precompact),  # runs compact + burn together
    "startup":    (None,       handle_startup),      # manages its own toggles
}


def main() -> None:
    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <event>", file=sys.stderr)
        print(f"events: {', '.join(HANDLERS)}", file=sys.stderr)
        sys.exit(1)

    event = sys.argv[1]
    if event not in HANDLERS:
        print(f"[mine] unknown event: {event}", file=sys.stderr)
        sys.exit(1)

    # read payload from stdin
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        payload = {}

    config = load_config()

    # check feature toggle (if handler has one)
    toggle_key, handler = HANDLERS[event]
    if toggle_key and not is_enabled(config, toggle_key):
        sys.exit(0)

    try:
        handler(payload, config)
    except Exception as e:
        print(f"[mine] {event} error: {e}", file=sys.stderr)
        sys.exit(0)  # don't block Claude Code on hook errors


if __name__ == "__main__":
    main()
