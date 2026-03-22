#!/usr/bin/env python3
# tested with: claude code v2.1.77
# SYNC: canonical copy is scripts/mine.py — keep these in sync
"""
mine.py -- Parse Claude Code JSONL conversation files into SQLite.

Reads all JSONL session logs from ~/.claude/projects/ and populates a
normalized SQLite database at ~/.claude/mine.db with sessions, messages,
tool calls, subagent tracking, and full-text search.

Usage:
    python3 scripts/mine.py                         # full backfill
    python3 scripts/mine.py --incremental           # only new/modified files
    python3 scripts/mine.py --file PATH             # parse single file
    python3 scripts/mine.py --project NAME          # one project (partial match)
    python3 scripts/mine.py --since 2025-01-01      # sessions after date
    python3 scripts/mine.py --workers 8             # parallel workers
    python3 scripts/mine.py --dry-run               # report without writing
    python3 scripts/mine.py --stats                 # print DB summary
    python3 scripts/mine.py --verify                # spot-check 10 sessions
    python3 scripts/mine.py --sanitize              # redact secrets
    python3 scripts/mine.py --export-csv            # export to CSV
    python3 scripts/mine.py --vacuum                # compact DB
"""

from __future__ import annotations

import argparse
import csv
import json
import multiprocessing
import os
import pathlib
import random
import re
import sqlite3
import sys
import time
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLAUDE_DIR = pathlib.Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_DIR / "projects"
DEFAULT_DB_PATH = CLAUDE_DIR / "mine.db"
SCHEMA_PATH = pathlib.Path(__file__).resolve().parent / "schema.sql"
MINEIGNORE_PATH = CLAUDE_DIR / ".mineignore"

# Content preview limits
USER_PREVIEW_LIMIT = 2000
ASSISTANT_PREVIEW_LIMIT = 500

# Gap threshold for active duration: 5 minutes
ACTIVE_GAP_THRESHOLD = 300

# Types to skip entirely
SKIP_TYPES = frozenset({"progress", "file-history-snapshot"})

# Types we extract messages from
MESSAGE_TYPES = frozenset({"user", "assistant"})

# Secret patterns to sanitize
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{36,}"),
    re.compile(r"AKIA[A-Z0-9]{16}"),
    re.compile(r"password=[^\s&\"']+", re.IGNORECASE),
    re.compile(r"secret=[^\s&\"']+", re.IGNORECASE),
    re.compile(r"token=[^\s&\"']+", re.IGNORECASE),
]


# ---------------------------------------------------------------------------
# Tool input summary extraction
# ---------------------------------------------------------------------------

def extract_tool_summary(tool_name: str, tool_input: dict[str, Any]) -> str:
    """Return a human-readable one-line summary for a tool invocation."""
    if not isinstance(tool_input, dict):
        return str(tool_input)[:300]

    if tool_name in ("Read", "Write", "Edit"):
        return tool_input.get("file_path", json.dumps(tool_input)[:300])

    if tool_name == "Bash":
        # Prefer command, fall back to description
        cmd = tool_input.get("command", "")
        desc = tool_input.get("description", "")
        return cmd if cmd else desc if desc else json.dumps(tool_input)[:300]

    if tool_name == "Glob":
        return tool_input.get("pattern", json.dumps(tool_input)[:300])

    if tool_name == "Grep":
        pattern = tool_input.get("pattern", "")
        path = tool_input.get("path", "")
        if path:
            return f"{pattern} in {path}"
        return pattern if pattern else json.dumps(tool_input)[:300]

    if tool_name == "Task":
        return tool_input.get("description", json.dumps(tool_input)[:300])

    # Fallback: first 300 chars of JSON
    return json.dumps(tool_input, ensure_ascii=False)[:300]


# ---------------------------------------------------------------------------
# Content preview extraction
# ---------------------------------------------------------------------------

def extract_content_preview(content: Any, limit: int) -> str | None:
    """Extract a text preview from message content (string or array)."""
    if content is None:
        return None

    if isinstance(content, str):
        return content[:limit]

    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                btype = block.get("type", "")
                if btype == "text":
                    parts.append(block.get("text", ""))
                elif btype == "thinking":
                    parts.append("[thinking]")
                elif btype == "tool_use":
                    name = block.get("name", "tool")
                    parts.append(f"[tool_use: {name}]")
                elif btype == "tool_result":
                    # User messages can contain tool_result blocks
                    inner = block.get("content", "")
                    if isinstance(inner, list):
                        for sub in inner:
                            if isinstance(sub, dict) and sub.get("type") == "text":
                                parts.append(sub.get("text", "")[:200])
                    elif isinstance(inner, str):
                        parts.append(inner[:200])
            remaining = limit - sum(len(p) for p in parts)
            if remaining <= 0:
                break
        return " ".join(parts)[:limit]

    return str(content)[:limit]


# ---------------------------------------------------------------------------
# Sanitization
# ---------------------------------------------------------------------------

def sanitize_string(s: str | None) -> str | None:
    """Redact secrets from a string."""
    if s is None:
        return None
    for pattern in SECRET_PATTERNS:
        s = pattern.sub("[REDACTED]", s)
    return s


def sanitize_result(result: dict[str, Any]) -> dict[str, Any]:
    """Redact secrets from an entire parse result."""
    # Sanitize session-level fields
    for key in ("first_user_prompt", "cwd", "project_dir"):
        if key in result and isinstance(result[key], str):
            result[key] = sanitize_string(result[key])

    # Sanitize messages
    for msg in result.get("messages", []):
        if msg.get("content_preview"):
            msg["content_preview"] = sanitize_string(msg["content_preview"])

    # Sanitize tool calls
    for tc in result.get("tool_calls", []):
        if tc.get("input_summary"):
            tc["input_summary"] = sanitize_string(tc["input_summary"])

    # Sanitize errors
    for err in result.get("errors", []):
        if err.get("error_message"):
            err["error_message"] = sanitize_string(err["error_message"])
        if err.get("input_summary"):
            err["input_summary"] = sanitize_string(err["input_summary"])

    return result


# ---------------------------------------------------------------------------
# ISO timestamp parsing
# ---------------------------------------------------------------------------

def parse_iso(ts: str | None) -> float | None:
    """Parse ISO 8601 timestamp to epoch seconds. Returns None on failure."""
    if not ts:
        return None
    try:
        # Handle Z suffix and +00:00 offset
        clean = ts.replace("Z", "+00:00")
        # Python 3.11+ handles this natively
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(clean)
        return dt.timestamp()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Single-file parser (runs in worker process)
# ---------------------------------------------------------------------------

def parse_jsonl_file(args: tuple[str, bool]) -> dict[str, Any]:
    """
    Parse a single JSONL file and return a dict with all extracted data.

    Args:
        args: Tuple of (file_path, is_subagent)

    Returns:
        Dict containing session info, messages, tool_calls, errors, and metadata.
    """
    file_path_str, is_subagent = args
    file_path = pathlib.Path(file_path_str)

    result: dict[str, Any] = {
        "file_path": file_path_str,
        "is_subagent": is_subagent,
        "session_id": None,
        "parent_session_id": None,
        "agent_id": None,
        "slug": None,
        "project_dir": None,
        "cwd": None,
        "project_name": None,
        "git_branch": None,
        "model": None,
        "version": None,
        "permission_mode": None,
        "start_time": None,
        "end_time": None,
        "first_user_prompt": None,
        "messages": [],
        "tool_calls": [],
        "errors": [],
        "compaction_count": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_cache_creation_tokens": 0,
        "total_cache_read_tokens": 0,
        "file_size_bytes": 0,
        "file_mtime": None,
        "line_count": 0,
        "error_count": 0,
        "status": "ok",
        "parse_error": None,
    }

    try:
        stat = file_path.stat()
        result["file_size_bytes"] = stat.st_size
        result["file_mtime"] = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime(stat.st_mtime)
        )
    except OSError as e:
        result["status"] = "error"
        result["parse_error"] = f"Cannot stat file: {e}"
        return result

    # For subagent files, derive parent session ID and agent ID from path
    # Pattern: {session-id}/subagents/agent-{agent-id}.jsonl
    if is_subagent:
        parts = file_path.parts
        try:
            subagents_idx = parts.index("subagents")
            parent_session_id = parts[subagents_idx - 1]
            result["parent_session_id"] = parent_session_id
        except (ValueError, IndexError):
            pass

        # Extract agent_id from filename: agent-{id}.jsonl
        stem = file_path.stem  # e.g., "agent-aa3f813" or "agent-acompact-38cc9f"
        if stem.startswith("agent-"):
            result["agent_id"] = stem[6:]  # everything after "agent-"

    timestamps: list[float] = []
    line_number = 0

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for raw_line in f:
                line_number += 1
                raw_line = raw_line.strip()
                if not raw_line:
                    continue

                try:
                    record = json.loads(raw_line)
                except json.JSONDecodeError:
                    result["error_count"] += 1
                    continue

                if not isinstance(record, dict):
                    result["error_count"] += 1
                    continue

                rtype = record.get("type")

                # Skip types we don't care about
                if rtype in SKIP_TYPES:
                    continue

                # Extract session-level metadata from first user/assistant line
                if rtype in MESSAGE_TYPES or rtype == "system":
                    sid = record.get("sessionId")
                    if sid and result["session_id"] is None:
                        result["session_id"] = sid

                    if result["slug"] is None:
                        result["slug"] = record.get("slug")
                    if result["cwd"] is None:
                        result["cwd"] = record.get("cwd")
                    if result["git_branch"] is None:
                        result["git_branch"] = record.get("gitBranch")
                    if result["version"] is None:
                        result["version"] = record.get("version")
                    if result["permission_mode"] is None:
                        result["permission_mode"] = record.get("permissionMode")

                    # Track agent ID from any record that has it
                    if record.get("agentId") and result["agent_id"] is None:
                        result["agent_id"] = record.get("agentId")

                # Track timestamps for duration computation
                ts_str = record.get("timestamp")
                ts_epoch = parse_iso(ts_str)
                if ts_epoch is not None:
                    timestamps.append(ts_epoch)
                if ts_str:
                    if result["start_time"] is None:
                        result["start_time"] = ts_str
                    result["end_time"] = ts_str

                # ---- Handle system messages (compactions, etc.) ----
                if rtype == "system":
                    subtype = record.get("subtype", "")
                    if subtype == "compact_boundary":
                        result["compaction_count"] += 1
                    continue

                # ---- Skip non-message types (queue-operation, pr-link, etc.) ----
                if rtype not in MESSAGE_TYPES:
                    continue

                # ---- Extract message data ----
                message = record.get("message", {})
                if not isinstance(message, dict):
                    continue

                content = message.get("content")
                role = message.get("role", rtype)
                model = message.get("model")

                # Track the first model we see
                if model and result["model"] is None:
                    result["model"] = model

                # Content analysis for assistant messages
                has_tool_use = False
                has_thinking = False
                tool_calls_in_msg: list[dict[str, Any]] = []

                if isinstance(content, list):
                    for block in content:
                        if not isinstance(block, dict):
                            continue
                        btype = block.get("type")

                        if btype == "thinking":
                            has_thinking = True

                        elif btype == "tool_use":
                            has_tool_use = True
                            tool_name = block.get("name", "unknown")
                            tool_input = block.get("input", {})
                            tool_calls_in_msg.append({
                                "tool_use_id": block.get("id"),
                                "tool_name": tool_name,
                                "input_summary": extract_tool_summary(
                                    tool_name, tool_input
                                ),
                                "timestamp": ts_str,
                            })

                # Content preview
                if rtype == "user":
                    preview = extract_content_preview(content, USER_PREVIEW_LIMIT)
                else:
                    preview = extract_content_preview(content, ASSISTANT_PREVIEW_LIMIT)

                # First user prompt (text content from the first user message)
                if rtype == "user" and result["first_user_prompt"] is None:
                    # Only capture human-authored prompts, not tool_result blocks
                    if isinstance(content, str):
                        result["first_user_prompt"] = content[:2000]
                    elif isinstance(content, list):
                        # Check if it's a genuine user prompt (not tool results)
                        text_parts = []
                        is_tool_result = all(
                            isinstance(b, dict) and b.get("type") == "tool_result"
                            for b in content
                            if isinstance(b, dict)
                        )
                        if not is_tool_result:
                            for block in content:
                                if isinstance(block, str):
                                    text_parts.append(block)
                                elif isinstance(block, dict) and block.get("type") == "text":
                                    text_parts.append(block.get("text", ""))
                            if text_parts:
                                result["first_user_prompt"] = " ".join(text_parts)[:2000]

                # Usage/token tracking for assistant messages
                usage = message.get("usage", {}) if rtype == "assistant" else {}
                if isinstance(usage, dict):
                    input_tokens = usage.get("input_tokens", 0) or 0
                    output_tokens = usage.get("output_tokens", 0) or 0

                    # Cache tokens: use top-level fields (the nested
                    # cache_creation.ephemeral_* is a breakdown of the same
                    # value, NOT additional tokens — don't double-count)
                    cache_creation_tokens = usage.get("cache_creation_input_tokens", 0) or 0
                    cache_read_tokens = usage.get("cache_read_input_tokens", 0) or 0

                    # Fall back to nested object only if top-level is missing
                    if cache_creation_tokens == 0:
                        cache_creation_obj = usage.get("cache_creation", {})
                        if isinstance(cache_creation_obj, dict):
                            cache_creation_tokens = (
                                (cache_creation_obj.get("ephemeral_5m_input_tokens", 0) or 0)
                                + (cache_creation_obj.get("ephemeral_1h_input_tokens", 0) or 0)
                            )

                    result["total_input_tokens"] += input_tokens
                    result["total_output_tokens"] += output_tokens
                    result["total_cache_creation_tokens"] += cache_creation_tokens
                    result["total_cache_read_tokens"] += cache_read_tokens
                else:
                    input_tokens = 0
                    output_tokens = 0
                    cache_creation_tokens = 0
                    cache_read_tokens = 0

                # Build message record
                msg_record = {
                    "uuid": record.get("uuid"),
                    "parent_uuid": record.get("parentUuid"),
                    "type": rtype,
                    "role": role,
                    "model": model,
                    "content_preview": preview,
                    "has_tool_use": has_tool_use,
                    "has_thinking": has_thinking,
                    "stop_reason": message.get("stop_reason"),
                    "input_tokens": input_tokens if rtype == "assistant" else None,
                    "output_tokens": output_tokens if rtype == "assistant" else None,
                    "cache_creation_tokens": cache_creation_tokens if rtype == "assistant" else None,
                    "cache_read_tokens": cache_read_tokens if rtype == "assistant" else None,
                    "service_tier": usage.get("service_tier") if isinstance(usage, dict) else None,
                    "inference_geo": usage.get("inference_geo") if isinstance(usage, dict) else None,
                    "request_id": record.get("requestId"),
                    "is_sidechain": record.get("isSidechain", False),
                    "agent_id": record.get("agentId"),
                    "user_type": record.get("userType"),
                    "line_number": line_number,
                    "timestamp": ts_str,
                }

                result["messages"].append(msg_record)
                result["tool_calls"].extend(tool_calls_in_msg)

    except Exception as e:
        result["status"] = "error"
        result["parse_error"] = str(e)

    result["line_count"] = line_number

    # ---- Derive project_name from cwd or directory structure ----
    # Prefer cwd basename (e.g., /home/user/projects/myapp -> "myapp")
    # Fall back to the encoded project dir name from ~/.claude/projects/
    if result["cwd"]:
        result["project_name"] = pathlib.Path(result["cwd"]).name
        # Also set project_dir from the encoded directory name
        try:
            rel = pathlib.Path(file_path_str).relative_to(PROJECTS_DIR)
            result["project_dir"] = str(PROJECTS_DIR / rel.parts[0])
        except (ValueError, IndexError):
            result["project_dir"] = result["cwd"]
    else:
        try:
            rel = pathlib.Path(file_path_str).relative_to(PROJECTS_DIR)
            project_dir_name = rel.parts[0]
            result["project_name"] = project_dir_name
            result["project_dir"] = str(PROJECTS_DIR / project_dir_name)
        except (ValueError, IndexError):
            pass

    # ---- Compute durations ----
    if timestamps:
        timestamps.sort()
        # Wall duration: first to last timestamp
        wall_seconds = timestamps[-1] - timestamps[0]
        result["duration_wall_seconds"] = int(wall_seconds)

        # Active duration: sum of gaps < 5 minutes
        active = 0.0
        for i in range(1, len(timestamps)):
            gap = timestamps[i] - timestamps[i - 1]
            if gap < ACTIVE_GAP_THRESHOLD:
                active += gap
        result["duration_active_seconds"] = int(active)
    else:
        result["duration_wall_seconds"] = 0
        result["duration_active_seconds"] = 0

    # ---- Generate a unique session ID ----
    if result["session_id"] is None:
        # Use the filename stem as a fallback session ID
        result["session_id"] = file_path.stem

    # For subagent files, make the session ID unique by appending the agent ID
    # since all subagent files from the same parent share the parent's sessionId
    if is_subagent and result["agent_id"]:
        result["session_id"] = f"{result['session_id']}::{result['agent_id']}"
    elif is_subagent:
        # No agent_id found — use filename to guarantee uniqueness
        result["session_id"] = f"{result['session_id']}::{file_path.stem}"

    return result


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def load_mineignore() -> list[str]:
    """Load patterns from ~/.claude/.mineignore (one per line)."""
    if not MINEIGNORE_PATH.exists():
        return []
    patterns: list[str] = []
    with open(MINEIGNORE_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    return patterns


def should_ignore(project_dir_name: str, ignore_patterns: list[str]) -> bool:
    """Check if a project directory matches any ignore pattern."""
    for pattern in ignore_patterns:
        if pattern in project_dir_name:
            return True
    return False


def discover_jsonl_files(
    project_filter: str | None = None,
    single_file: str | None = None,
) -> list[tuple[str, bool]]:
    """
    Discover all JSONL files to parse.

    Returns:
        List of (file_path, is_subagent) tuples.
    """
    if single_file:
        p = pathlib.Path(single_file).resolve()
        if not p.exists():
            print(f"Error: file not found: {single_file}", file=sys.stderr)
            sys.exit(1)
        is_sub = "subagents" in p.parts
        return [(str(p), is_sub)]

    if not PROJECTS_DIR.exists():
        print(f"Error: projects directory not found: {PROJECTS_DIR}", file=sys.stderr)
        sys.exit(1)

    ignore_patterns = load_mineignore()
    files: list[tuple[str, bool]] = []

    for project_dir in sorted(PROJECTS_DIR.iterdir()):
        if not project_dir.is_dir():
            continue

        dir_name = project_dir.name

        # Apply project filter (partial match)
        if project_filter and project_filter.lower() not in dir_name.lower():
            continue

        # Apply mineignore
        if should_ignore(dir_name, ignore_patterns):
            continue

        # Main session files: direct children of the project dir
        for jsonl_file in sorted(project_dir.glob("*.jsonl")):
            if jsonl_file.is_file():
                files.append((str(jsonl_file), False))

        # Subagent files: {session-id}/subagents/agent-*.jsonl
        for jsonl_file in sorted(project_dir.glob("*/subagents/*.jsonl")):
            if jsonl_file.is_file():
                files.append((str(jsonl_file), True))

    return files


# ---------------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------------

def init_db(db_path: pathlib.Path) -> sqlite3.Connection:
    """Initialize the SQLite database with schema."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA mmap_size=268435456")  # 256MB mmap
    conn.execute("PRAGMA cache_size=-64000")     # 64MB page cache
    conn.execute("PRAGMA temp_store=MEMORY")

    # Read and execute schema
    if SCHEMA_PATH.exists():
        schema_sql = SCHEMA_PATH.read_text()
        conn.executescript(schema_sql)
    else:
        print(
            f"Warning: schema file not found at {SCHEMA_PATH}. "
            "Database may not have correct structure.",
            file=sys.stderr,
        )

    # Check and run migrations
    version = conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
    current_version = int(version[0]) if version else 1

    if current_version < 2:
        # v2: model_pricing table (already created by schema.sql above)
        conn.execute("UPDATE meta SET value='2' WHERE key='schema_version'")
        conn.commit()

    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# Database writing
# ---------------------------------------------------------------------------

def write_result_to_db(
    conn: sqlite3.Connection, result: dict[str, Any]
) -> None:
    """Write a parsed JSONL result to the database."""
    cursor = conn.cursor()
    session_id = result["session_id"]

    # Count messages by type
    user_count = sum(1 for m in result["messages"] if m["type"] == "user")
    assistant_count = sum(1 for m in result["messages"] if m["type"] == "assistant")
    tool_use_count = len(result["tool_calls"])
    thinking_count = sum(1 for m in result["messages"] if m.get("has_thinking"))

    # Count user prompts (user messages that are not tool results)
    user_prompt_count = 0
    for m in result["messages"]:
        if m["type"] == "user" and m.get("user_type") == "external":
            user_prompt_count += 1

    # Count API calls (assistant messages with a request_id)
    api_call_count = sum(
        1 for m in result["messages"]
        if m["type"] == "assistant" and m.get("request_id")
    )

    # Delete existing data for this session (for re-parsing)
    cursor.execute("DELETE FROM tool_calls WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM errors WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    # Insert session
    cursor.execute(
        """
        INSERT INTO sessions (
            id, slug, project_dir, cwd, project_name, git_branch, model,
            version, permission_mode, start_time, end_time,
            duration_wall_seconds, duration_active_seconds,
            message_count, user_message_count, assistant_message_count,
            tool_use_count, thinking_block_count, user_prompt_count,
            api_call_count, compaction_count,
            total_input_tokens, total_output_tokens,
            total_cache_creation_tokens, total_cache_read_tokens,
            is_subagent, parent_session_id, agent_id,
            first_user_prompt, file_path, file_size_bytes, file_mtime
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?,
            ?, ?,
            ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?
        )
        """,
        (
            session_id,
            result["slug"],
            result["project_dir"],
            result["cwd"],
            result["project_name"],
            result["git_branch"],
            result["model"],
            result["version"],
            result["permission_mode"],
            result["start_time"],
            result["end_time"],
            result["duration_wall_seconds"],
            result["duration_active_seconds"],
            len(result["messages"]),
            user_count,
            assistant_count,
            tool_use_count,
            thinking_count,
            user_prompt_count,
            api_call_count,
            result["compaction_count"],
            result["total_input_tokens"],
            result["total_output_tokens"],
            result["total_cache_creation_tokens"],
            result["total_cache_read_tokens"],
            result["is_subagent"],
            result.get("parent_session_id"),
            result.get("agent_id"),
            result["first_user_prompt"],
            result["file_path"],
            result["file_size_bytes"],
            result["file_mtime"],
        ),
    )

    # Insert messages
    for msg in result["messages"]:
        cursor.execute(
            """
            INSERT INTO messages (
                session_id, uuid, parent_uuid, type, role, model,
                content_preview, has_tool_use, has_thinking, stop_reason,
                input_tokens, output_tokens, cache_creation_tokens,
                cache_read_tokens, service_tier, inference_geo,
                request_id, is_sidechain, agent_id, user_type,
                line_number, timestamp
            ) VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?
            )
            """,
            (
                session_id,
                msg["uuid"],
                msg["parent_uuid"],
                msg["type"],
                msg["role"],
                msg["model"],
                msg["content_preview"],
                msg["has_tool_use"],
                msg["has_thinking"],
                msg["stop_reason"],
                msg["input_tokens"],
                msg["output_tokens"],
                msg["cache_creation_tokens"],
                msg["cache_read_tokens"],
                msg["service_tier"],
                msg["inference_geo"],
                msg["request_id"],
                msg["is_sidechain"],
                msg["agent_id"],
                msg["user_type"],
                msg["line_number"],
                msg["timestamp"],
            ),
        )

    # Insert tool calls
    for tc in result["tool_calls"]:
        cursor.execute(
            """
            INSERT INTO tool_calls (
                session_id, message_uuid, tool_use_id, tool_name,
                input_summary, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                None,  # message_uuid linked at message level
                tc["tool_use_id"],
                tc["tool_name"],
                tc["input_summary"],
                tc["timestamp"],
            ),
        )

    # Insert subagent record if this is a subagent file
    if result["is_subagent"] and result.get("parent_session_id"):
        # Check if parent session exists (it might not be parsed yet)
        cursor.execute(
            "SELECT id FROM sessions WHERE id = ?",
            (result["parent_session_id"],),
        )
        if cursor.fetchone():
            cursor.execute(
                """
                INSERT OR REPLACE INTO subagents (
                    parent_session_id, agent_id, agent_type,
                    transcript_path, start_time, end_time,
                    duration_seconds, message_count, tool_use_count,
                    total_input_tokens, total_output_tokens
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result["parent_session_id"],
                    result.get("agent_id"),
                    None,  # agent_type could be derived from name
                    result["file_path"],
                    result["start_time"],
                    result["end_time"],
                    result["duration_wall_seconds"],
                    len(result["messages"]),
                    tool_use_count,
                    result["total_input_tokens"],
                    result["total_output_tokens"],
                ),
            )

    # Update project_paths
    if result["project_name"] and result["project_dir"]:
        cursor.execute(
            """
            INSERT INTO project_paths (
                project_name, project_dir, cwd, first_seen, last_seen, session_count
            ) VALUES (?, ?, ?, ?, ?, 1)
            ON CONFLICT(project_name, project_dir) DO UPDATE SET
                cwd = COALESCE(excluded.cwd, project_paths.cwd),
                first_seen = MIN(COALESCE(project_paths.first_seen, excluded.first_seen), excluded.first_seen),
                last_seen = MAX(COALESCE(project_paths.last_seen, excluded.last_seen), excluded.last_seen),
                session_count = project_paths.session_count + 1
            """,
            (
                result["project_name"],
                result["project_dir"],
                result["cwd"],
                result["start_time"],
                result["start_time"],
            ),
        )

    # Update parse_log
    parse_duration_ms = int(
        (time.time() - result.get("_parse_start", time.time())) * 1000
    )
    cursor.execute(
        """
        INSERT OR REPLACE INTO parse_log (
            file_path, file_size, file_mtime, session_id,
            line_count, error_count, status, parse_duration_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result["file_path"],
            result["file_size_bytes"],
            result["file_mtime"],
            session_id,
            result["line_count"],
            result["error_count"],
            result["status"],
            parse_duration_ms,
        ),
    )


# ---------------------------------------------------------------------------
# Incremental filtering
# ---------------------------------------------------------------------------

def filter_incremental(
    conn: sqlite3.Connection, files: list[tuple[str, bool]]
) -> list[tuple[str, bool]]:
    """Filter out files that have not changed since last parse."""
    cursor = conn.cursor()
    filtered: list[tuple[str, bool]] = []

    for file_path, is_subagent in files:
        cursor.execute(
            "SELECT file_size, file_mtime FROM parse_log WHERE file_path = ?",
            (file_path,),
        )
        row = cursor.fetchone()
        if row is None:
            # Never parsed before
            filtered.append((file_path, is_subagent))
            continue

        prev_size, prev_mtime = row
        try:
            stat = pathlib.Path(file_path).stat()
            current_size = stat.st_size
            current_mtime = time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(stat.st_mtime)
            )
        except OSError:
            continue

        if current_size != prev_size or current_mtime != prev_mtime:
            filtered.append((file_path, is_subagent))

    return filtered


# ---------------------------------------------------------------------------
# --since filtering
# ---------------------------------------------------------------------------

def filter_by_date(
    files: list[tuple[str, bool]], since: str
) -> list[tuple[str, bool]]:
    """Filter files by modification date (keep files modified on or after `since`)."""
    since_epoch = parse_iso(since + "T00:00:00Z")
    if since_epoch is None:
        print(f"Error: invalid date format: {since}", file=sys.stderr)
        sys.exit(1)

    filtered: list[tuple[str, bool]] = []
    for file_path, is_subagent in files:
        try:
            mtime = pathlib.Path(file_path).stat().st_mtime
            if mtime >= since_epoch:
                filtered.append((file_path, is_subagent))
        except OSError:
            continue
    return filtered


# ---------------------------------------------------------------------------
# --stats command
# ---------------------------------------------------------------------------

def print_stats(db_path: pathlib.Path) -> None:
    """Print a summary of the database contents."""
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print(f"\n{'='*60}")
    print(f"  Claude Code Miner -- Database Summary")
    print(f"  {db_path}")
    print(f"{'='*60}\n")

    # DB file size
    db_size = db_path.stat().st_size
    if db_size > 1_000_000_000:
        size_str = f"{db_size / 1_000_000_000:.2f} GB"
    elif db_size > 1_000_000:
        size_str = f"{db_size / 1_000_000:.1f} MB"
    else:
        size_str = f"{db_size / 1_000:.1f} KB"
    print(f"  Database size: {size_str}")

    # Session counts
    cursor.execute("SELECT COUNT(*) FROM sessions WHERE is_subagent = 0")
    main_sessions = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM sessions WHERE is_subagent = 1")
    sub_sessions = cursor.fetchone()[0]
    print(f"  Sessions: {main_sessions} main + {sub_sessions} subagent = {main_sessions + sub_sessions} total")

    # Message counts
    cursor.execute("SELECT COUNT(*) FROM messages")
    msg_count = cursor.fetchone()[0]
    print(f"  Messages: {msg_count:,}")

    # Tool call counts
    cursor.execute("SELECT COUNT(*) FROM tool_calls")
    tc_count = cursor.fetchone()[0]
    print(f"  Tool calls: {tc_count:,}")

    # Top tools
    cursor.execute(
        "SELECT tool_name, COUNT(*) as cnt FROM tool_calls "
        "GROUP BY tool_name ORDER BY cnt DESC LIMIT 10"
    )
    rows = cursor.fetchall()
    if rows:
        print(f"\n  Top tools:")
        for row in rows:
            print(f"    {row[0]:20s} {row[1]:>8,}")

    # Token totals (user sessions only)
    cursor.execute(
        "SELECT SUM(total_input_tokens), SUM(total_output_tokens), "
        "SUM(total_cache_creation_tokens), SUM(total_cache_read_tokens) "
        "FROM sessions WHERE is_subagent = 0"
    )
    row = cursor.fetchone()
    if row and row[0]:
        print(f"\n  Tokens:")
        print(f"    Input:          {row[0]:>14,}")
        print(f"    Output:         {row[1]:>14,}")
        print(f"    Cache creation: {row[2]:>14,}")
        print(f"    Cache read:     {row[3]:>14,}")

    # Project counts
    cursor.execute("SELECT COUNT(DISTINCT project_name) FROM sessions WHERE is_subagent = 0")
    proj_count = cursor.fetchone()[0]
    print(f"\n  Projects: {proj_count}")

    # Top projects by session count
    cursor.execute(
        "SELECT project_name, COUNT(*) as cnt FROM sessions "
        "WHERE is_subagent = 0 "
        "GROUP BY project_name ORDER BY cnt DESC LIMIT 10"
    )
    rows = cursor.fetchall()
    if rows:
        print(f"\n  Top projects (by session count):")
        for row in rows:
            name = row[0] or "(unknown)"
            # Shorten long names
            if len(name) > 50:
                name = "..." + name[-47:]
            print(f"    {name:50s} {row[1]:>6}")

    # Date range
    cursor.execute(
        "SELECT MIN(start_time), MAX(end_time) FROM sessions WHERE is_subagent = 0"
    )
    row = cursor.fetchone()
    if row and row[0]:
        print(f"\n  Date range: {row[0][:10]} to {row[1][:10]}")

    # Model distribution (user sessions only)
    cursor.execute(
        "SELECT model, COUNT(*) as cnt FROM sessions "
        "WHERE model IS NOT NULL AND is_subagent = 0 "
        "GROUP BY model ORDER BY cnt DESC"
    )
    rows = cursor.fetchall()
    if rows:
        print(f"\n  Models:")
        for row in rows:
            print(f"    {row[0]:30s} {row[1]:>6}")

    # Parse log summary
    cursor.execute("SELECT COUNT(*) FROM parse_log WHERE status = 'ok'")
    ok = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM parse_log WHERE status != 'ok'")
    err = cursor.fetchone()[0]
    print(f"\n  Parse log: {ok} ok, {err} errors")

    # API value estimate (using the view)
    try:
        cursor.execute(
            "SELECT SUM(estimated_cost_usd) FROM session_costs WHERE is_subagent = 0"
        )
        row = cursor.fetchone()
        total_cost = row[0] if row and row[0] else 0

        if total_cost:
            print(f"\n  API inference value: ${total_cost:,.2f}")
            print(f"    (what this usage would cost at published API rates)")

            # Value by model tier
            cursor.execute(
                "SELECT "
                "  CASE "
                "    WHEN model LIKE '%opus%' THEN 'opus' "
                "    WHEN model LIKE '%sonnet%' THEN 'sonnet' "
                "    WHEN model LIKE '%haiku%' THEN 'haiku' "
                "    ELSE 'other' "
                "  END AS tier, "
                "  COUNT(*) AS sessions, "
                "  ROUND(SUM(estimated_cost_usd), 2) AS cost "
                "FROM session_costs "
                "WHERE model IS NOT NULL AND model <> '<synthetic>' AND is_subagent = 0 "
                "GROUP BY tier ORDER BY cost DESC"
            )
            rows = cursor.fetchall()
            if rows:
                print(f"\n  API value by model:")
                for row in rows:
                    pct = row[2] / total_cost * 100 if total_cost else 0
                    print(f"    {row[0]:10s} {row[1]:>5} sessions  ${row[2]:>10,.2f}  ({pct:.0f}%)")

            # Top projects by API value
            cursor.execute(
                "SELECT project_name, COUNT(*) as sessions, "
                "  ROUND(SUM(estimated_cost_usd), 2) AS cost "
                "FROM session_costs "
                "WHERE project_name IS NOT NULL AND is_subagent = 0 "
                "GROUP BY project_name ORDER BY cost DESC LIMIT 10"
            )
            rows = cursor.fetchall()
            if rows:
                print(f"\n  Top projects (by API value):")
                for row in rows:
                    name = row[0] or "(unknown)"
                    if len(name) > 30:
                        name = "..." + name[-27:]
                    pct = row[2] / total_cost * 100 if total_cost else 0
                    print(f"    {name:30s} {row[1]:>5} sessions  ${row[2]:>10,.2f}  ({pct:.0f}%)")

            # Cache efficiency
            cursor.execute(
                "SELECT SUM(total_cache_read_tokens), "
                "  SUM(total_cache_creation_tokens), "
                "  SUM(total_input_tokens) "
                "FROM sessions "
                "WHERE model IS NOT NULL AND model <> '<synthetic>' AND is_subagent = 0"
            )
            row = cursor.fetchone()
            if row and row[0]:
                cache_read, cache_create, uncached = row[0], row[1], row[2]
                total_input = cache_read + cache_create + uncached
                if total_input > 0:
                    hit_rate = cache_read / total_input * 100
                    print(f"\n  Cache efficiency: {hit_rate:.1f}% hit rate")
                if cache_create > 0:
                    ratio = cache_read / cache_create
                    print(f"  Cache read:write ratio: {ratio:.1f}x")

    except sqlite3.OperationalError:
        pass  # View may not exist

    print()
    conn.close()


# ---------------------------------------------------------------------------
# --verify command
# ---------------------------------------------------------------------------

def verify_sessions(db_path: pathlib.Path) -> None:
    """Spot-check 10 random sessions against raw JSONL files."""
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, file_path, message_count, tool_use_count, "
        "total_input_tokens, total_output_tokens "
        "FROM sessions WHERE file_path IS NOT NULL"
    )
    all_sessions = cursor.fetchall()

    if not all_sessions:
        print("No sessions found in database.")
        conn.close()
        return

    sample_size = min(10, len(all_sessions))
    sample = random.sample(all_sessions, sample_size)

    print(f"\nVerifying {sample_size} random sessions against raw JSONL...\n")

    pass_count = 0
    fail_count = 0

    for session in sample:
        sid = session["id"]
        fpath = session["file_path"]
        db_msg_count = session["message_count"]
        db_tool_count = session["tool_use_count"]

        if not pathlib.Path(fpath).exists():
            print(f"  SKIP {sid[:12]}... file missing: {fpath}")
            continue

        # Re-parse the file
        result = parse_jsonl_file((fpath, "subagents" in fpath))
        actual_msg_count = len(result["messages"])
        actual_tool_count = len(result["tool_calls"])

        match = (
            db_msg_count == actual_msg_count
            and db_tool_count == actual_tool_count
        )

        if match:
            print(f"  PASS {sid[:12]}... msgs={db_msg_count} tools={db_tool_count}")
            pass_count += 1
        else:
            print(
                f"  FAIL {sid[:12]}... "
                f"msgs: db={db_msg_count} actual={actual_msg_count} | "
                f"tools: db={db_tool_count} actual={actual_tool_count}"
            )
            fail_count += 1

    print(f"\nResults: {pass_count} passed, {fail_count} failed out of {sample_size}")
    conn.close()


# ---------------------------------------------------------------------------
# --export-csv command
# ---------------------------------------------------------------------------

def export_csv(db_path: pathlib.Path) -> None:
    """Export sessions and tool_calls tables as CSV files."""
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    export_dir = db_path.parent
    tables = ["sessions", "tool_calls"]

    for table in tables:
        csv_path = export_dir / f"{table}.csv"
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table}")  # noqa: S608 -- table name is hardcoded
        rows = cursor.fetchall()

        if not rows:
            print(f"  {table}: empty, skipping")
            continue

        columns = [desc[0] for desc in cursor.description]

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for row in rows:
                writer.writerow(list(row))

        print(f"  Exported {len(rows):,} rows to {csv_path}")

    conn.close()


# ---------------------------------------------------------------------------
# --debug-discovery command
# ---------------------------------------------------------------------------

def debug_discovery() -> None:
    """Print file discovery diagnostics: counts, dates, skipped files."""
    ignore_patterns = load_mineignore()

    print(f"\n{'='*60}")
    print(f"  File Discovery Diagnostics")
    print(f"{'='*60}\n")
    print(f"  Projects dir: {PROJECTS_DIR}")
    print(f"  Mineignore:   {MINEIGNORE_PATH} ({'exists' if MINEIGNORE_PATH.exists() else 'not found'})")

    if ignore_patterns:
        print(f"  Ignore patterns ({len(ignore_patterns)}):")
        for pat in ignore_patterns:
            print(f"    - {pat}")
    print()

    all_files = discover_jsonl_files()
    main_files = [(f, s) for f, s in all_files if not s]
    sub_files = [(f, s) for f, s in all_files if s]

    print(f"  Total files discovered: {len(all_files)}")
    print(f"    Main sessions: {len(main_files)}")
    print(f"    Subagent files: {len(sub_files)}")
    print()

    # Per-project breakdown
    project_stats: dict[str, dict[str, Any]] = {}
    for fpath, is_sub in all_files:
        try:
            rel = pathlib.Path(fpath).relative_to(PROJECTS_DIR)
            proj_dir = rel.parts[0]
        except (ValueError, IndexError):
            proj_dir = "(unknown)"

        if proj_dir not in project_stats:
            project_stats[proj_dir] = {"count": 0, "oldest": None, "newest": None}

        project_stats[proj_dir]["count"] += 1

        try:
            mtime = pathlib.Path(fpath).stat().st_mtime
            mtime_str = time.strftime("%Y-%m-%d", time.gmtime(mtime))
            if project_stats[proj_dir]["oldest"] is None or mtime_str < project_stats[proj_dir]["oldest"]:
                project_stats[proj_dir]["oldest"] = mtime_str
            if project_stats[proj_dir]["newest"] is None or mtime_str > project_stats[proj_dir]["newest"]:
                project_stats[proj_dir]["newest"] = mtime_str
        except OSError:
            pass

    print(f"  Per-project breakdown ({len(project_stats)} projects):\n")
    print(f"    {'Project':<55s} {'Files':>6s}  {'Oldest':>10s}  {'Newest':>10s}")
    print(f"    {'-'*55} {'-'*6}  {'-'*10}  {'-'*10}")

    for proj_dir in sorted(project_stats, key=lambda k: project_stats[k]["count"], reverse=True):
        stats = project_stats[proj_dir]
        name = proj_dir if len(proj_dir) <= 55 else "..." + proj_dir[-52:]
        oldest = stats["oldest"] or "?"
        newest = stats["newest"] or "?"
        print(f"    {name:<55s} {stats['count']:>6d}  {oldest:>10s}  {newest:>10s}")

    # Check for skipped directories
    if PROJECTS_DIR.exists() and ignore_patterns:
        print(f"\n  Skipped directories (matched .mineignore):")
        skipped = 0
        for d in sorted(PROJECTS_DIR.iterdir()):
            if d.is_dir() and should_ignore(d.name, ignore_patterns):
                jsonl_count = sum(1 for _ in d.glob("**/*.jsonl"))
                print(f"    {d.name} ({jsonl_count} files)")
                skipped += 1
        if skipped == 0:
            print(f"    (none)")

    print()


# ---------------------------------------------------------------------------
# --rollup command
# ---------------------------------------------------------------------------

def compute_rollups(db_path: pathlib.Path) -> None:
    """Rebuild daily_rollups table from sessions + session_costs."""
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return

    conn = init_db(db_path)

    print("Rebuilding daily_rollups...")
    conn.execute("DELETE FROM daily_rollups")

    conn.execute("""
        INSERT INTO daily_rollups (date, project_name, model, sessions, main_sessions, subagent_sessions,
            input_tokens, output_tokens, cache_read_tokens, cache_creation_tokens,
            tool_calls, errors, active_seconds, estimated_cost_usd)
        SELECT
            SUBSTR(s.start_time, 1, 10) AS date,
            COALESCE(s.project_name, '') AS project_name,
            COALESCE(s.model, '') AS model,
            COUNT(*) AS sessions,
            SUM(CASE WHEN s.is_subagent = 0 THEN 1 ELSE 0 END),
            SUM(CASE WHEN s.is_subagent = 1 THEN 1 ELSE 0 END),
            SUM(s.total_input_tokens),
            SUM(s.total_output_tokens),
            SUM(s.total_cache_read_tokens),
            SUM(s.total_cache_creation_tokens),
            SUM(s.tool_use_count),
            (SELECT COUNT(*) FROM errors e WHERE e.session_id = s.id),
            SUM(s.duration_active_seconds),
            SUM(sc.estimated_cost_usd)
        FROM sessions s
        JOIN session_costs sc ON s.id = sc.id
        WHERE s.start_time IS NOT NULL
        GROUP BY SUBSTR(s.start_time, 1, 10), COALESCE(s.project_name, ''), COALESCE(s.model, '')
    """)

    row_count = conn.execute("SELECT COUNT(*) FROM daily_rollups").fetchone()[0]
    conn.commit()
    conn.close()

    print(f"Done. {row_count} rollup rows created.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point: parse args, discover files, parse in parallel, write to DB."""
    parser = argparse.ArgumentParser(
        description="Parse Claude Code JSONL conversation files into SQLite.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 scripts/mine.py                       # full backfill\n"
            "  python3 scripts/mine.py --incremental          # only new/modified\n"
            "  python3 scripts/mine.py --file path/to.jsonl   # single file\n"
            "  python3 scripts/mine.py --project rudy          # one project\n"
            "  python3 scripts/mine.py --stats                 # print summary\n"
        ),
    )

    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Only parse new or modified files (checks parse_log table).",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Parse a single JSONL file.",
    )
    parser.add_argument(
        "--project",
        type=str,
        default=None,
        help="Parse one project directory (partial match on directory name).",
    )
    parser.add_argument(
        "--since",
        type=str,
        default=None,
        help="Only parse sessions modified after this date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of parallel workers (default: cpu_count()).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be parsed without writing to the database.",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print database summary and exit.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Spot-check 10 random sessions against raw JSONL files.",
    )
    parser.add_argument(
        "--sanitize",
        action="store_true",
        help="Redact strings matching secret patterns (sk-..., ghp_..., etc.).",
    )
    parser.add_argument(
        "--export-csv",
        action="store_true",
        help="Export sessions and tool_calls tables as CSV.",
    )
    parser.add_argument(
        "--vacuum",
        action="store_true",
        help="Run VACUUM on the database to reclaim space.",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        help=f"Path to SQLite database (default: {DEFAULT_DB_PATH}).",
    )
    parser.add_argument(
        "--debug-discovery",
        action="store_true",
        help="Print file discovery diagnostics (counts, dates, skipped files) and exit.",
    )
    parser.add_argument(
        "--rollup",
        action="store_true",
        help="Rebuild daily_rollups table from sessions + session_costs and exit.",
    )

    args = parser.parse_args()

    db_path = pathlib.Path(args.db) if args.db else DEFAULT_DB_PATH
    worker_count = args.workers or multiprocessing.cpu_count()

    # ---- Handle action-only flags ----

    if args.stats:
        print_stats(db_path)
        return

    if args.verify:
        verify_sessions(db_path)
        return

    if args.export_csv:
        print("Exporting CSV...")
        export_csv(db_path)
        return

    if args.vacuum:
        if not db_path.exists():
            print(f"Database not found: {db_path}")
            return
        print(f"Running VACUUM on {db_path}...")
        before_size = db_path.stat().st_size
        conn = sqlite3.connect(str(db_path))
        conn.execute("VACUUM")
        conn.close()
        after_size = db_path.stat().st_size
        saved = before_size - after_size
        print(
            f"Done. {before_size / 1_000_000:.1f} MB -> {after_size / 1_000_000:.1f} MB "
            f"(saved {saved / 1_000_000:.1f} MB)"
        )
        return

    if args.debug_discovery:
        debug_discovery()
        return

    if args.rollup:
        compute_rollups(db_path)
        return

    # ---- Discovery phase ----

    print("Discovering JSONL files...")
    files = discover_jsonl_files(
        project_filter=args.project,
        single_file=args.file,
    )

    if not files:
        print("No JSONL files found.")
        return

    print(f"Found {len(files)} JSONL files.")

    # ---- Initialize DB (needed for incremental check) ----

    if not args.dry_run:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = init_db(db_path)
    else:
        conn = None

    # ---- Apply filters ----

    if args.incremental and conn is not None:
        before = len(files)
        files = filter_incremental(conn, files)
        skipped = before - len(files)
        print(f"Incremental mode: {skipped} unchanged files skipped, {len(files)} to parse.")

    if args.since:
        before = len(files)
        files = filter_by_date(files, args.since)
        skipped = before - len(files)
        print(f"Date filter (>= {args.since}): {skipped} files skipped, {len(files)} to parse.")

    if not files:
        print("Nothing to parse after filtering.")
        if conn:
            conn.close()
        return

    # ---- Dry run ----

    if args.dry_run:
        main_count = sum(1 for _, is_sub in files if not is_sub)
        sub_count = sum(1 for _, is_sub in files if is_sub)
        total_size = 0
        for fpath, _ in files:
            try:
                total_size += pathlib.Path(fpath).stat().st_size
            except OSError:
                pass

        if total_size > 1_000_000_000:
            size_str = f"{total_size / 1_000_000_000:.2f} GB"
        elif total_size > 1_000_000:
            size_str = f"{total_size / 1_000_000:.1f} MB"
        else:
            size_str = f"{total_size / 1_000:.1f} KB"

        print(f"\nDry run summary:")
        print(f"  Main sessions:  {main_count}")
        print(f"  Subagent files: {sub_count}")
        print(f"  Total files:    {len(files)}")
        print(f"  Total size:     {size_str}")
        print(f"  Workers:        {worker_count}")
        print(f"  DB path:        {db_path}")

        if args.project:
            print(f"  Project filter: {args.project}")
        if args.since:
            print(f"  Since:          {args.since}")

        return

    # ---- Parallel parse phase ----

    total = len(files)
    print(f"\nParsing {total} files with {worker_count} workers...")

    t_start = time.time()
    results: list[dict[str, Any]] = []
    completed = 0
    error_files = 0
    total_messages = 0
    total_tools = 0

    # Use multiprocessing.Pool for parallelism
    # Each worker parses one file and returns a dict
    with multiprocessing.Pool(processes=worker_count) as pool:
        for result in pool.imap_unordered(parse_jsonl_file, files):
            completed += 1
            results.append(result)

            if result["status"] != "ok":
                error_files += 1

            total_messages += len(result.get("messages", []))
            total_tools += len(result.get("tool_calls", []))

            # Progress every 100 files
            if completed % 100 == 0 or completed == total:
                elapsed = time.time() - t_start
                rate = completed / elapsed if elapsed > 0 else 0
                print(
                    f"  [{completed}/{total}] parsing... "
                    f"({rate:.0f} files/sec, "
                    f"{total_messages:,} msgs, "
                    f"{total_tools:,} tools)"
                )

    parse_elapsed = time.time() - t_start

    # ---- Write phase (single-threaded, main process only) ----

    print(f"\nWriting {len(results)} results to {db_path}...")
    t_write = time.time()

    write_count = 0
    write_errors = 0

    for result in results:
        if result["status"] == "error" and not result["messages"]:
            # Log the parse failure but skip DB write if no data extracted
            if conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO parse_log (
                        file_path, file_size, file_mtime, session_id,
                        line_count, error_count, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        result["file_path"],
                        result["file_size_bytes"],
                        result["file_mtime"],
                        result["session_id"],
                        result["line_count"],
                        result["error_count"],
                        result["status"],
                    ),
                )
            write_errors += 1
            continue

        # Apply sanitization if requested
        if args.sanitize:
            result = sanitize_result(result)

        # Stamp parse start for duration tracking
        result["_parse_start"] = t_write

        try:
            if conn:
                write_result_to_db(conn, result)
                write_count += 1
        except sqlite3.Error as e:
            write_errors += 1
            if conn:
                # Log the error in parse_log
                try:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO parse_log (
                            file_path, file_size, file_mtime, session_id,
                            line_count, error_count, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            result["file_path"],
                            result["file_size_bytes"],
                            result["file_mtime"],
                            result["session_id"],
                            result["line_count"],
                            result["error_count"],
                            f"write_error: {e}",
                        ),
                    )
                except sqlite3.Error:
                    pass

        # Commit in batches of 100 for better write performance
        if write_count % 100 == 0 and conn:
            conn.commit()

    # Final commit
    if conn:
        conn.commit()

    write_elapsed = time.time() - t_write

    # ---- Summary ----

    total_elapsed = time.time() - t_start
    json_errors = sum(r["error_count"] for r in results)

    print(f"\n{'='*60}")
    print(f"  Parse complete")
    print(f"{'='*60}")
    print(f"  Files parsed:      {write_count:,}")
    print(f"  Files with errors: {error_files}")
    print(f"  Write errors:      {write_errors}")
    print(f"  Malformed lines:   {json_errors:,}")
    print(f"  Messages:          {total_messages:,}")
    print(f"  Tool calls:        {total_tools:,}")
    print(f"  Parse time:        {parse_elapsed:.1f}s")
    print(f"  Write time:        {write_elapsed:.1f}s")
    print(f"  Total time:        {total_elapsed:.1f}s")
    print(f"  Database:          {db_path}")

    if args.sanitize:
        print(f"  Sanitization:      enabled")

    print()

    if conn:
        conn.close()


if __name__ == "__main__":
    main()
