# mine

Mines every Claude Code session into a local SQLite database. Query your usage history — costs, tokens, tools, projects, errors, and full-text search across all conversations.

## what it does

`/mine` gives you 18+ query intents over your Claude Code session history:

```
/mine                    → 7-day dashboard with projects, tools, models, insights
/mine cost               → API value breakdown by project, model, daily trend
/mine search "websocket" → full-text search across all conversations
/mine top projects       → projects ranked by API value, cache rate
/mine hotspots           → files you keep editing
/mine mistakes           → expensive failures + error patterns
/mine story <project>    → narrative history of a project
/mine compare this week vs last → side-by-side delta comparison
```

5 hooks run automatically during sessions:

| Event | What it does |
|---|---|
| SessionEnd | Parses session transcripts into mine.db |
| SubagentStop | Parses subagent transcripts |
| PreCompact | Cost anomaly warning + compaction tracking |
| SessionStart | Project move detection, solution recall, auto-backfill |
| PostToolUseFailure | Records errors, surfaces past similar failures |

## architecture

- **1 Python file** (`hook.py`) handles all hooks — no bash scripts, no jq
- **1 Python parser** (`mine.py`) converts JSONL session logs to SQLite
- **1 skill** (`SKILL.md`) with 18+ intent handlers using SQL queries
- **0 pip dependencies** — stdlib only (json, sqlite3, pathlib, subprocess)

## requirements

- `python3` (3.9+)
- `sqlite3` CLI (ships with macOS and most Linux)

## data

All data stays local at `~/.claude/mine.db`. Dollar amounts show **API inference value** (published per-token rates), not subscription cost. All queries exclude subagent sessions by default.

## source

[github.com/anipotts/claude-code-tips](https://github.com/anipotts/claude-code-tips/tree/main/plugins/mine)
