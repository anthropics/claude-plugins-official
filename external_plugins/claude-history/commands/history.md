---
description: View and manage transcript history
argument-hint: [status|open|list]
allowed-tools: Bash, Read
---

# /history - Transcript History Management

View and manage your backed-up Claude conversations.

## Usage

Based on the argument:

### `/history` or `/history status`
Show export statistics:
1. Read `exports/index.json` if it exists
2. Report:
   - Total sessions backed up
   - Date range (oldest to newest)
   - Total size on disk
   - Last backup time

### `/history list`
List recent sessions:
1. Read `exports/index.json`
2. Show last 10 sessions with:
   - Date and time
   - Summary (truncated)
   - Message count
   - Size

### `/history open`
Open the exports folder:
```bash
# Windows
explorer exports

# Mac
open exports

# Linux
xdg-open exports
```

## How It Works

The claude-history plugin automatically backs up every conversation:

1. **On every message** - Transcript saved to `exports/YYYY-MM-DD/`
2. **On session end** - Final backup with complete conversation
3. **Index maintained** - `exports/index.json` tracks all sessions

Each backup includes:
- `.jsonl` - Full transcript (Claude's native format)
- `.meta.json` - Metadata (session ID, git branch, message count)
