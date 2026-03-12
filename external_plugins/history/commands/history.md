---
description: Search past Claude Code sessions by keyword across all projects
argument-hint: <query> [--days N] [--project name] [--limit N]
---

# History

Search everything you've ever typed to Claude Code, across all projects and sessions. Reads `~/.claude/history.jsonl` and returns matching prompts with timestamps, project paths, and a resume command to jump straight back into that session.

## Parameters

- `<query>` — search query (required). Case-insensitive substring match.
- `--days <N>` — only search the last N days (default: **90**)
- `--project <name>` — filter to sessions whose project path contains this string
- `--limit <N>` — max results (default: **10**)

## Procedure

### Step 1: Parse arguments

Extract the query and any flags from the arguments. Defaults: `--days 90`, `--limit 10`, no project filter. Anything that isn't a recognized flag or flag value is part of the query.

### Step 2: Search history

Write this script to `/tmp/cc_history.py` and run it with `python3 /tmp/cc_history.py <query> [--days N] [--project name] [--limit N]`:

```python
import json, sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

args = sys.argv[1:]
query_parts, days, limit, project_filter = [], 90, 10, None
i = 0
while i < len(args):
    if args[i] == "--days" and i + 1 < len(args):
        days = int(args[i + 1]); i += 2
    elif args[i] == "--project" and i + 1 < len(args):
        project_filter = args[i + 1]; i += 2
    elif args[i] == "--limit" and i + 1 < len(args):
        limit = int(args[i + 1]); i += 2
    else:
        query_parts.append(args[i]); i += 1

query = " ".join(query_parts)
if not query:
    print("Usage: /history <query> [--days N] [--project name] [--limit N]")
    sys.exit(1)

history_file = Path.home() / ".claude" / "history.jsonl"
if not history_file.exists():
    print("~/.claude/history.jsonl not found.")
    sys.exit(1)

cutoff_ms = (datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000
results = []

for line in history_file.read_text(errors="replace").splitlines():
    try:
        entry = json.loads(line)
    except json.JSONDecodeError:
        continue

    if entry.get("timestamp", 0) < cutoff_ms:
        continue

    text = entry.get("display", "")
    project = entry.get("project", "")

    if project_filter and project_filter.lower() not in project.lower():
        continue

    if query.lower() not in text.lower():
        continue

    results.append(entry)

results.sort(key=lambda e: e.get("timestamp", 0), reverse=True)
total = len(results)
results = results[:limit]

if not results:
    suggestion = f"/history {query} --days {days * 2}"
    if project_filter:
        suggestion += f" --project {project_filter}"
    if limit != 10:
        suggestion += f" --limit {limit}"
    print(f'No matches for "{query}" in the last {days} days.')
    print(f"Try: {suggestion}")
    sys.exit(0)

count_msg = f"Found {total} match(es)" if total <= limit else f"Found {total} match(es) (showing {limit})"
print(f'{count_msg} for "{query}":\n')
for e in results:
    ts = datetime.fromtimestamp(e["timestamp"] / 1000).strftime("%Y-%m-%d %H:%M")
    project = e.get("project", "unknown")
    snippet = e.get("display", "").strip().replace("\n", " ")[:200]
    session_id = e.get("sessionId", "")
    print(f"[{ts}]  {project}")
    print(f"  {snippet}")
    if session_id:
        encoded = project.lstrip("/").replace("/", "-")
        session_file = Path.home() / ".claude" / "projects" / f"-{encoded}" / f"{session_id}.jsonl"
        if session_file.exists():
            print(f"  resume: claude --resume {session_id}")
        else:
            print(f"  ⚠ session transcript deleted (default retention: 30 days)")
            print(f"  To keep sessions longer: add \"cleanupPeriodDays\": 90 to ~/.claude/settings.json")
    print()
```

### Step 3: Show results

Print the script output as-is. Each result shows:
- Timestamp and project path
- The matching prompt (truncated to 200 chars)
- A `claude --resume <id>` command to jump back into that session

$ARGUMENTS
