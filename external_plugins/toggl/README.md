# Toggl

Connect [Toggl Track](https://toggl.com) to Claude Code so you can log and review time entries using natural language.

## Prerequisites

- [Node.js](https://nodejs.org) 18 or later
- A [Toggl Track](https://toggl.com) account

## Setup

**1. Install the plugin:**

```bash
claude plugin marketplace add https://github.com/run-as-root/toggl-claude-plugin
claude plugin install toggl
```

**2. Get your Toggl API token:**

Go to [track.toggl.com/profile](https://track.toggl.com/profile) and scroll to the bottom — your API token is listed under **API Token**. Click to reveal it.

**3. Save your token:**

```bash
mkdir -p ~/.claude/toggl
echo "YOUR_API_TOKEN" > ~/.claude/toggl/credentials
chmod 600 ~/.claude/toggl/credentials
```

**4. Restart Claude Code.**

## Usage

The skill activates automatically when you mention time tracking. Just speak naturally:

```
"Log 2h on the AVA project / Login Bug task yesterday"
"What did I track this week?"
"How much time did I spend on Cover AIT in May?"
"Log 8h public holiday today"
"Is anything currently running?"
```

Claude resolves project and task names automatically before logging.

> **Note:** If your Toggl workspace requires both a project and task on every entry, Claude will always resolve both before logging.

## Tools

| Tool | Purpose |
|------|---------|
| `toggl_get_me` | Get user info and workspace ID |
| `toggl_list_projects` | List all active projects |
| `toggl_list_tasks` | List tasks inside a project |
| `toggl_list_time_entries` | Query entries by date range, project, or task |
| `toggl_get_summary` | Aggregated time totals by project and task |
| `toggl_create_time_entry` | Log a completed time entry |
| `toggl_get_current_timer` | Check what's currently running |

## Source

[github.com/run-as-root/toggl-claude-plugin](https://github.com/run-as-root/toggl-claude-plugin)
