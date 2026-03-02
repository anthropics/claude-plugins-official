#!/usr/bin/env python3
"""Audit capture for hookify — MAESTRO NO-LIES enforcement loop.

Captures actual filesystem state (not tool claims) before and after
tool executions. Writes organized, queryable audit artifacts.

Output structure:
    ~/MAESTRO/audits/
    ├── INDEX.md                     # Master index with query examples
    ├── raw/                         # JSONL for jq/duckdb (machine)
    │   └── {YYYY-MM-DD}.jsonl
    ├── diffs/                       # Individual unified diff files
    │   └── {YYYY-MM-DD}/
    │       └── {HHMMSS}-{tool}-{basename}.diff
    ├── sessions/                    # Per-session markdown reports
    │   └── {session_id}.md
    ├── daily/                       # Daily rollup summaries
    │   └── {YYYY-MM-DD}.md
    └── forensics/                   # No-ops, integrity failures
        └── {YYYY-MM-DD}/
            └── {HHMMSS}-noop-{basename}.txt

Verification patterns covered:
1. FILE PROOF:  sha256 before/after + unified diff (Edit/Write/MultiEdit/NotebookEdit)
2. BASH PROOF:  command + exit code + stdout + file-target diffs
3. SESSION:     correlated records via session_id, summary on Stop
4. NO-OP FLAG:  detects when tool claims a write but sha256 didn't change

Design principles:
- Source of truth = filesystem (hashlib sha256), never tool output
- Never blocks operations — all failures are silent (stderr only)
- JSONL for machines, markdown for humans, .diff for forensics
- Pre-snapshots in /tmp, organized artifacts in ~/MAESTRO/audits/
"""

import difflib
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------

AUDIT_ROOT = Path.home() / "MAESTRO" / "audits"
RAW_DIR = AUDIT_ROOT / "raw"
DIFFS_DIR = AUDIT_ROOT / "diffs"
SESSIONS_DIR = AUDIT_ROOT / "sessions"
DAILY_DIR = AUDIT_ROOT / "daily"
FORENSICS_DIR = AUDIT_ROOT / "forensics"
SNAPSHOT_DIR = Path(tempfile.gettempdir()) / "hookify-audit-snapshots"

MAX_CONTENT_BYTES = 100_000
MAX_DIFF_LINES = 500
MAX_STDOUT_BYTES = 5_000

FILE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")

# Session ID: stable per parent process (Claude Code session) + date
SESSION_ID = f"{os.getppid()}-{datetime.now().strftime('%Y%m%d')}"

_ABS_PATH_RE = re.compile(r'(?:^|\s|[>|;(&])(/[^\s;|>&)]+)')
_WRITE_CMD_RE = re.compile(
    r'\b(?:tee|sed\s+-i|cp|mv|rm|touch|mkdir|chmod|chown|install|ln|rsync)\b|[>]'
)


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------


def _ensure_dirs() -> None:
    """Create all output directories."""
    for d in (RAW_DIR, DIFFS_DIR, SESSIONS_DIR, DAILY_DIR, FORENSICS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _now_hms() -> str:
    return datetime.now().strftime("%H%M%S")


def _file_sha256(path: str) -> Optional[str]:
    """SHA-256 from actual filesystem. None if unreadable."""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def _is_binary(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            return b"\x00" in f.read(8192)
    except Exception:
        return True


def _read_file_text(path: str) -> Optional[str]:
    if _is_binary(path):
        return None
    try:
        with open(path, "r", errors="replace") as f:
            return f.read(MAX_CONTENT_BYTES)
    except Exception:
        return None


def _extract_file_path(tool_name: str, tool_input: Dict[str, Any]) -> Optional[str]:
    if tool_name in FILE_TOOLS:
        return tool_input.get("file_path") or tool_input.get("notebook_path")
    return None


def _extract_bash_file_targets(command: str) -> List[str]:
    if not _WRITE_CMD_RE.search(command):
        return []
    paths = _ABS_PATH_RE.findall(command)
    targets = []
    for p in paths:
        p = p.rstrip("'\"`)],;")
        if os.path.isfile(p):
            targets.append(p)
    return list(set(targets))


def _snapshot_key(file_path: str) -> str:
    return hashlib.md5(file_path.encode()).hexdigest()


def _bash_snapshot_key(command: str) -> str:
    return "bash-" + hashlib.md5(command.encode()).hexdigest()


def _compute_diff(before: str, after: str, file_path: str) -> str:
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)
    diff = difflib.unified_diff(
        before_lines, after_lines,
        fromfile=f"a/{file_path}", tofile=f"b/{file_path}",
    )
    lines = list(diff)
    if len(lines) > MAX_DIFF_LINES:
        lines = lines[:MAX_DIFF_LINES]
        lines.append(f"\n... truncated ({MAX_DIFF_LINES} line cap)\n")
    return "".join(lines)


def _safe_basename(file_path: str) -> str:
    """File-system-safe basename for use in artifact filenames."""
    name = os.path.basename(file_path)
    return re.sub(r'[^\w.\-]', '_', name)


# ---------------------------------------------------------------------------
# Artifact writers
# ---------------------------------------------------------------------------


def _base_record(event: str, tool: str) -> Dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": SESSION_ID,
        "event": event,
        "tool": tool,
    }


def _write_jsonl(record: Dict[str, Any]) -> None:
    """Append to daily JSONL in raw/."""
    try:
        _ensure_dirs()
        path = RAW_DIR / f"{_today()}.jsonl"
        with open(path, "a") as f:
            f.write(json.dumps(record, default=str) + "\n")
    except Exception as e:
        print(f"Hookify audit JSONL error: {e}", file=sys.stderr)


def _write_diff_file(tool_name: str, file_path: str, diff_text: str) -> Optional[str]:
    """Write individual .diff file. Returns relative path from AUDIT_ROOT."""
    try:
        day_dir = DIFFS_DIR / _today()
        day_dir.mkdir(parents=True, exist_ok=True)
        basename = _safe_basename(file_path)
        filename = f"{_now_hms()}-{tool_name}-{basename}.diff"
        out = day_dir / filename
        with open(out, "w") as f:
            f.write(diff_text)
        return f"diffs/{_today()}/{filename}"
    except Exception as e:
        print(f"Hookify diff file error: {e}", file=sys.stderr)
        return None


def _write_forensic_flag(
    tool_name: str, file_path: str, pre_sha: str, post_sha: str,
    detail: str = "no-op",
) -> Optional[str]:
    """Write forensic flag for no-ops / integrity failures. Returns relative path."""
    try:
        day_dir = FORENSICS_DIR / _today()
        day_dir.mkdir(parents=True, exist_ok=True)
        basename = _safe_basename(file_path)
        filename = f"{_now_hms()}-{detail}-{basename}.txt"
        out = day_dir / filename
        lines = [
            f"FORENSIC FLAG: {detail.upper()}",
            f"Timestamp : {datetime.now(timezone.utc).isoformat()}",
            f"Session   : {SESSION_ID}",
            f"Tool      : {tool_name}",
            f"File      : {file_path}",
            f"Pre SHA256: {pre_sha}",
            f"Post SHA256: {post_sha}",
            "",
            "Agent claimed a write but the file hash did not change.",
            "This means the tool either:",
            "  A) Made no actual modification (no-op)",
            "  B) Wrote identical content back",
            "  C) Failed silently",
        ]
        with open(out, "w") as f:
            f.write("\n".join(lines) + "\n")
        return f"forensics/{_today()}/{filename}"
    except Exception as e:
        print(f"Hookify forensic flag error: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Public API — called from hooks
# ---------------------------------------------------------------------------


def capture_pre_snapshot(tool_name: str, tool_input: Dict[str, Any]) -> None:
    """Capture pre-execution filesystem state. Called from PreToolUse hook."""
    try:
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        if tool_name in FILE_TOOLS:
            _snapshot_file_tool(tool_name, tool_input)
        elif tool_name == "Bash":
            _snapshot_bash_targets(tool_input)
    except Exception as e:
        print(f"Hookify pre-snapshot error: {e}", file=sys.stderr)


def capture_post_diff(
    tool_name: str,
    tool_input: Dict[str, Any],
    tool_output: Optional[Any] = None,
) -> None:
    """Capture post-execution state, compute diff, write all artifacts.
    Called from PostToolUse hook."""
    try:
        if tool_name == "Bash":
            _audit_bash(tool_input, tool_output)
            return
        if tool_name in FILE_TOOLS:
            _audit_file_tool(tool_name, tool_input)
    except Exception as e:
        print(f"Hookify post-diff error: {e}", file=sys.stderr)


def capture_session_summary() -> None:
    """Write session markdown report + update daily rollup + update INDEX.
    Called from Stop hook."""
    try:
        _ensure_dirs()
        records = _load_session_records()
        if not records:
            return

        stats = _compute_session_stats(records)
        _write_session_report(stats, records)
        _update_daily_rollup(stats)
        _write_index()
        _cleanup_stale_snapshots()

    except Exception as e:
        print(f"Hookify session summary error: {e}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Internal — file tool snapshots
# ---------------------------------------------------------------------------


def _snapshot_file_tool(tool_name: str, tool_input: Dict[str, Any]) -> None:
    file_path = _extract_file_path(tool_name, tool_input)
    if not file_path:
        return
    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": SESSION_ID,
        "tool_name": tool_name,
        "file_path": file_path,
        "file_existed": os.path.exists(file_path),
        "sha256": _file_sha256(file_path),
        "content": _read_file_text(file_path),
    }
    key = _snapshot_key(file_path)
    with open(SNAPSHOT_DIR / f"{key}.json", "w") as f:
        json.dump(snapshot, f)


def _audit_file_tool(tool_name: str, tool_input: Dict[str, Any]) -> None:
    file_path = _extract_file_path(tool_name, tool_input)
    if not file_path:
        return

    # Load pre-snapshot
    key = _snapshot_key(file_path)
    snap_path = SNAPSHOT_DIR / f"{key}.json"
    pre = None
    if snap_path.exists():
        try:
            with open(snap_path) as f:
                pre = json.load(f)
            snap_path.unlink()
        except Exception:
            pass

    # Post state from filesystem
    post_sha = _file_sha256(file_path)
    post_content = _read_file_text(file_path)
    post_exists = os.path.exists(file_path)

    # Diff
    pre_content = pre.get("content") if pre else None
    diff_text = None
    if pre_content is not None and post_content is not None:
        diff_text = _compute_diff(pre_content, post_content, file_path)
    elif pre_content is None and post_content is not None:
        diff_text = _compute_diff("", post_content, file_path)
    elif pre_content is not None and post_content is None:
        diff_text = _compute_diff(pre_content, "", file_path)

    pre_sha = pre.get("sha256") if pre else None
    is_noop = pre_sha is not None and pre_sha == post_sha
    is_verified = pre_sha is not None and pre_sha != post_sha

    # Write .diff file
    diff_rel_path = None
    if diff_text and diff_text.strip():
        diff_rel_path = _write_diff_file(tool_name, file_path, diff_text)

    # Flag no-ops as forensic incidents
    forensic_rel_path = None
    if is_noop:
        forensic_rel_path = _write_forensic_flag(
            tool_name, file_path, pre_sha or "", post_sha or "",
        )

    # JSONL record
    record = _base_record("file_mutation", tool_name)
    record.update({
        "file_path": file_path,
        "pre_sha256": pre_sha,
        "post_sha256": post_sha,
        "pre_existed": pre.get("file_existed") if pre else None,
        "post_exists": post_exists,
        "mutation_verified": is_verified,
        "no_op": is_noop,
        "diff_lines": len(diff_text.splitlines()) if diff_text else 0,
        "diff_file": diff_rel_path,
        "forensic_file": forensic_rel_path,
    })
    if diff_text:
        record["diff"] = diff_text

    _write_jsonl(record)


# ---------------------------------------------------------------------------
# Internal — bash auditing
# ---------------------------------------------------------------------------


def _snapshot_bash_targets(tool_input: Dict[str, Any]) -> None:
    command = tool_input.get("command", "")
    targets = _extract_bash_file_targets(command)
    if not targets:
        return
    snapshots = {}
    for path in targets:
        snapshots[path] = {"sha256": _file_sha256(path), "existed": True}
    key = _bash_snapshot_key(command)
    with open(SNAPSHOT_DIR / f"{key}.json", "w") as f:
        json.dump({"command": command, "session_id": SESSION_ID, "targets": snapshots}, f)


def _audit_bash(tool_input: Dict[str, Any], tool_output: Optional[Any] = None) -> None:
    command = tool_input.get("command", "")
    record = _base_record("bash_command", "Bash")
    record["command"] = command[:2000]

    if tool_output:
        if isinstance(tool_output, dict):
            record["exit_code"] = tool_output.get(
                "exit_code", tool_output.get("exitCode")
            )
            stdout = tool_output.get("stdout", tool_output.get("output", ""))
            if isinstance(stdout, str):
                record["stdout_tail"] = stdout[-MAX_STDOUT_BYTES:]
            stderr = tool_output.get("stderr", "")
            if isinstance(stderr, str) and stderr:
                record["stderr_tail"] = stderr[-1000:]
        elif isinstance(tool_output, str):
            record["stdout_tail"] = tool_output[-MAX_STDOUT_BYTES:]

    # File-target diffs
    key = _bash_snapshot_key(command)
    snap_path = SNAPSHOT_DIR / f"{key}.json"
    file_diffs = []
    if snap_path.exists():
        try:
            with open(snap_path) as f:
                snap = json.load(f)
            snap_path.unlink()
            for path, pre_state in snap.get("targets", {}).items():
                post_sha = _file_sha256(path)
                pre_sha = pre_state.get("sha256")
                changed = pre_sha != post_sha
                entry = {
                    "file_path": path,
                    "pre_sha256": pre_sha,
                    "post_sha256": post_sha,
                    "post_exists": os.path.exists(path),
                    "changed": changed,
                }
                # Write .diff for changed bash targets too
                if changed:
                    pre_content = _read_file_text(path)
                    if pre_content is not None:
                        # Can't diff — we didn't store pre-content for bash targets
                        # Just note the hash change
                        pass
                file_diffs.append(entry)
        except Exception:
            pass

    if file_diffs:
        record["file_diffs"] = file_diffs

    _write_jsonl(record)


# ---------------------------------------------------------------------------
# Session report generation
# ---------------------------------------------------------------------------


def _load_session_records() -> List[Dict[str, Any]]:
    """Load all JSONL records for the current session from today's file."""
    path = RAW_DIR / f"{_today()}.jsonl"
    if not path.exists():
        return []
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if rec.get("session_id") == SESSION_ID:
                    records.append(rec)
            except json.JSONDecodeError:
                continue
    return records


def _compute_session_stats(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate stats from session records."""
    file_mutations = 0
    verified = 0
    no_ops = 0
    bash_cmds = 0
    bash_file_changes = 0
    files_touched: Dict[str, Dict[str, Any]] = {}  # path -> {tool, verified, noop}
    noops_detail: List[Dict[str, Any]] = []
    bash_log: List[Dict[str, Any]] = []
    first_ts = None
    last_ts = None

    for rec in records:
        ts = rec.get("timestamp", "")
        if first_ts is None or ts < first_ts:
            first_ts = ts
        if last_ts is None or ts > last_ts:
            last_ts = ts

        event = rec.get("event", "")
        if event == "file_mutation":
            file_mutations += 1
            fp = rec.get("file_path", "")
            tool = rec.get("tool", "")
            is_v = rec.get("mutation_verified", False)
            is_n = rec.get("no_op", False)
            if is_v:
                verified += 1
            if is_n:
                no_ops += 1
                noops_detail.append(rec)
            status = "verified" if is_v else ("NO-OP" if is_n else "unverified")
            files_touched[fp] = {"tool": tool, "status": status}
        elif event == "bash_command":
            bash_cmds += 1
            bash_file_changes += len(rec.get("file_diffs", []))
            bash_log.append({
                "command": rec.get("command", "")[:120],
                "exit_code": rec.get("exit_code"),
            })

    return {
        "session_id": SESSION_ID,
        "date": _today(),
        "first_ts": first_ts,
        "last_ts": last_ts,
        "file_mutations": file_mutations,
        "verified": verified,
        "no_ops": no_ops,
        "bash_cmds": bash_cmds,
        "bash_file_changes": bash_file_changes,
        "files_touched": files_touched,
        "noops_detail": noops_detail,
        "bash_log": bash_log,
        "integrity": "CLEAN" if no_ops == 0 else f"{no_ops} NO-OP(S) FLAGGED",
    }


def _write_session_report(stats: Dict[str, Any], records: List[Dict[str, Any]]) -> None:
    """Write per-session markdown report + JSONL summary record."""
    sid = stats["session_id"]

    lines = [
        f"# Session Report: {sid}",
        "",
        f"**Date**: {stats['date']}",
        f"**Started**: {stats['first_ts'] or 'N/A'}",
        f"**Ended**: {stats['last_ts'] or 'N/A'}",
        f"**Integrity**: {stats['integrity']}",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| File mutations | {stats['file_mutations']} |",
        f"| Verified (sha256 changed) | {stats['verified']} |",
        f"| No-ops (sha256 identical) | {stats['no_ops']} |",
        f"| Bash commands | {stats['bash_cmds']} |",
        f"| Bash file-target changes | {stats['bash_file_changes']} |",
        "",
    ]

    # Files touched
    if stats["files_touched"]:
        lines.append("## Files Touched")
        lines.append("")
        for fp, info in sorted(stats["files_touched"].items()):
            flag = " **<-- NO-OP**" if info["status"] == "NO-OP" else ""
            lines.append(f"- `{fp}` ({info['tool']}, {info['status']}){flag}")
        lines.append("")

    # Forensic flags
    if stats["noops_detail"]:
        lines.append("## Forensic Flags")
        lines.append("")
        for noop in stats["noops_detail"]:
            fp = noop.get("file_path", "?")
            lines.append(f"### NO-OP: `{fp}`")
            lines.append(f"- **Tool**: {noop.get('tool', '?')}")
            lines.append(f"- **Pre SHA256**: `{noop.get('pre_sha256', '?')}`")
            lines.append(f"- **Post SHA256**: `{noop.get('post_sha256', '?')}`")
            ff = noop.get("forensic_file")
            if ff:
                lines.append(f"- **Forensic file**: `{ff}`")
            lines.append("")

    # Bash command log
    if stats["bash_log"]:
        lines.append("## Bash Commands")
        lines.append("")
        for i, entry in enumerate(stats["bash_log"], 1):
            ec = entry.get("exit_code")
            ec_str = f"exit {ec}" if ec is not None else "exit ?"
            lines.append(f"{i}. `{entry['command']}` ({ec_str})")
        lines.append("")

    # Diff files index
    diff_files = [r.get("diff_file") for r in records if r.get("diff_file")]
    if diff_files:
        lines.append("## Diff Files")
        lines.append("")
        for df in diff_files:
            lines.append(f"- [`{df}`](../{df})")
        lines.append("")

    # Query examples
    lines.extend([
        "## Query This Session",
        "",
        "```bash",
        f"# All mutations in this session",
        f"jq -c 'select(.session_id==\"{sid}\" and .event==\"file_mutation\")' raw/{stats['date']}.jsonl",
        "",
        f"# No-ops only (agent lies)",
        f"jq -c 'select(.session_id==\"{sid}\" and .no_op==true)' raw/{stats['date']}.jsonl",
        "",
        f"# Bash commands",
        f"jq -r 'select(.session_id==\"{sid}\" and .event==\"bash_command\") | .command' raw/{stats['date']}.jsonl",
        "```",
        "",
    ])

    # Write session report
    report_path = SESSIONS_DIR / f"{sid}.md"
    with open(report_path, "w") as f:
        f.write("\n".join(lines))

    # Also write summary to JSONL
    summary = _base_record("session_summary", "Stop")
    summary.update({
        "file_mutations": stats["file_mutations"],
        "verified_mutations": stats["verified"],
        "no_ops_detected": stats["no_ops"],
        "bash_commands": stats["bash_cmds"],
        "bash_file_changes": stats["bash_file_changes"],
        "files_touched": sorted(stats["files_touched"].keys()),
        "integrity": stats["integrity"],
        "report_file": f"sessions/{sid}.md",
    })
    _write_jsonl(summary)


def _update_daily_rollup(stats: Dict[str, Any]) -> None:
    """Append this session to the daily rollup markdown."""
    day = stats["date"]
    path = DAILY_DIR / f"{day}.md"

    # Read existing or create header
    existing = ""
    if path.exists():
        with open(path) as f:
            existing = f.read()

    if not existing:
        existing = "\n".join([
            f"# Daily Audit: {day}",
            "",
            "## Sessions",
            "",
            "| Session | Mutations | Verified | No-Ops | Bash | Integrity |",
            "|---------|-----------|----------|--------|------|-----------|",
            "",
        ])

    # Build the row
    sid = stats["session_id"]
    row = (
        f"| [{sid}](../sessions/{sid}.md) "
        f"| {stats['file_mutations']} "
        f"| {stats['verified']} "
        f"| {stats['no_ops']} "
        f"| {stats['bash_cmds']} "
        f"| {stats['integrity']} |"
    )

    # Insert row before the blank line after the table header
    # Find the table and append
    table_end = existing.rfind("|")
    if table_end >= 0:
        # Find end of last table row
        next_newline = existing.find("\n", table_end)
        if next_newline >= 0:
            existing = existing[: next_newline + 1] + row + "\n" + existing[next_newline + 1:]
        else:
            existing += "\n" + row + "\n"
    else:
        existing += row + "\n"

    # Append files touched section for this session
    existing += f"\n### Session {sid} — Files\n\n"
    for fp, info in sorted(stats["files_touched"].items()):
        flag = " **NO-OP**" if info["status"] == "NO-OP" else ""
        existing += f"- `{fp}` ({info['tool']}){flag}\n"

    # Append forensic flags if any
    if stats["no_ops"] > 0:
        existing += f"\n### Session {sid} — Forensic Flags\n\n"
        for noop in stats["noops_detail"]:
            fp = noop.get("file_path", "?")
            existing += f"- **NO-OP**: `{fp}` (tool: {noop.get('tool')}, sha unchanged)\n"

    existing += "\n"

    with open(path, "w") as f:
        f.write(existing)


def _write_index() -> None:
    """Write/update INDEX.md at the audit root."""
    # Collect recent daily reports
    daily_files = sorted(DAILY_DIR.glob("*.md"), reverse=True)[:30]
    session_files = sorted(SESSIONS_DIR.glob("*.md"), reverse=True)[:30]
    forensic_dirs = sorted(FORENSICS_DIR.glob("*"), reverse=True)[:30]

    lines = [
        "# MAESTRO Audit Index",
        "",
        "Automated enforcement-loop audit trail produced by hookify.",
        "Every tool write is verified against the filesystem (sha256),",
        "not the tool's claim.",
        "",
        "## Directory Structure",
        "",
        "| Directory | Contents | Format |",
        "|-----------|----------|--------|",
        "| `raw/` | Machine-readable audit records | JSONL (jq/duckdb) |",
        "| `diffs/` | Per-mutation unified diff files | .diff |",
        "| `sessions/` | Per-session human-readable reports | Markdown |",
        "| `daily/` | Daily rollup summaries | Markdown |",
        "| `forensics/` | No-op flags, integrity failures | Plain text |",
        "",
        "## Recent Daily Reports",
        "",
    ]
    for f in daily_files:
        lines.append(f"- [{f.stem}](daily/{f.name})")
    if not daily_files:
        lines.append("- (none yet)")
    lines.append("")

    lines.append("## Recent Sessions")
    lines.append("")
    for f in session_files:
        lines.append(f"- [{f.stem}](sessions/{f.name})")
    if not session_files:
        lines.append("- (none yet)")
    lines.append("")

    if any(d.is_dir() and any(d.iterdir()) for d in forensic_dirs if d.is_dir()):
        lines.append("## Forensic Flags")
        lines.append("")
        for d in forensic_dirs:
            if d.is_dir():
                flags = list(d.iterdir())
                if flags:
                    lines.append(f"- **{d.name}**: {len(flags)} flag(s)")
        lines.append("")

    lines.extend([
        "## Query Examples",
        "",
        "```bash",
        "# Count all mutations today",
        f"jq -c 'select(.event==\"file_mutation\")' raw/{_today()}.jsonl | wc -l",
        "",
        "# Find all no-ops (agent claimed write, nothing changed)",
        f"jq -c 'select(.no_op==true)' raw/{_today()}.jsonl",
        "",
        "# List files touched by a session",
        "jq -r 'select(.session_id==\"SESSION_ID\") | .file_path // empty' raw/DATE.jsonl | sort -u",
        "",
        "# DuckDB aggregate by tool",
        "duckdb -c \"SELECT tool, count(*), sum(CASE WHEN no_op THEN 1 ELSE 0 END) as no_ops FROM read_json_auto('raw/*.jsonl') WHERE event='file_mutation' GROUP BY tool\"",
        "",
        "# Tail today's audit live",
        f"tail -f raw/{_today()}.jsonl | jq .",
        "```",
        "",
    ])

    with open(AUDIT_ROOT / "INDEX.md", "w") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------


def _cleanup_stale_snapshots() -> None:
    """Remove snapshot files older than 1 hour (orphaned pre-snapshots)."""
    try:
        if not SNAPSHOT_DIR.exists():
            return
        now = datetime.now().timestamp()
        for snap in SNAPSHOT_DIR.iterdir():
            if snap.suffix == ".json":
                age = now - snap.stat().st_mtime
                if age > 3600:
                    snap.unlink()
    except Exception:
        pass
