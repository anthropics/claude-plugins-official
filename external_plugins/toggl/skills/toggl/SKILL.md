---
name: toggl
description: >
  Use this skill when the user mentions Toggl, time tracking, logging hours, logging time,
  tracking work, "how much did I work", "what did I track", "log X hours on Y",
  "how much time on project/task", "summary for this week", or anything related to
  tracking or reviewing time spent on tasks or projects.
version: 1.1.0
---

# Toggl Time Tracking

You have access to seven Toggl MCP tools. Use them to log and review time.

## Tools Available

| Tool | Purpose |
|------|---------|
| `toggl_get_me` | Get user info and workspace ID |
| `toggl_list_projects` | List projects (id + name) |
| `toggl_list_tasks` | List tasks inside a project (id + name) |
| `toggl_list_time_entries` | Query entries by date range, optionally filtered by project/task |
| `toggl_get_summary` | Aggregated totals grouped by project → task for a period |
| `toggl_create_time_entry` | Log a completed time entry (with optional project + task) |
| `toggl_get_current_timer` | Check what's currently running |

## Logging Time

### Basic flow
"Log 2h on Design today" →
1. `toggl_list_projects` → find project ID matching "Design"
2. `toggl_create_time_entry` with description, duration_minutes=120, start=today, project_id

### With a task
"Log 1h on the Login Bug task in the AVA project" →
1. `toggl_list_projects` → find project_id for "AVA"
2. `toggl_list_tasks(project_id)` → find task_id for "Login Bug"
3. `toggl_create_time_entry` with project_id + task_id

### Duration parsing
- "2h" → 120 min · "1.5h" / "90 minutes" → 90 min · "30m" → 30 min

### Date parsing (always compute from actual current date)
- "today" → YYYY-MM-DD of today
- "yesterday" → today minus 1 day
- "last Monday" → the most recent past Monday
- Always pass YYYY-MM-DD to the tool

### Project/task matching
- Match case-insensitively, partial match is fine
- If no project match: log without project_id and say so
- If project found but no task match: log with project only and say so

## Querying Time Entries

"What did I track today?" → `toggl_list_time_entries` start_date=today
"Show entries for the AVA project this week" → `toggl_list_time_entries` start_date=Monday, end_date=today, project_id=<avaid>

**Display format:**
- Duration as "1h 30m" not raw minutes
- Group by project when multiple projects appear
- Sum total at the end
- Resolve project_id → name via `toggl_list_projects` if names are unknown

## Summarising Time (totals per project/task)

"How much time on the AVA project this month?" →
1. `toggl_list_projects` → find project_id for "AVA"
2. `toggl_get_summary` start_date=first of month, end_date=today, project_id=<avaid>
3. Show grand_total and per-task breakdown

"How much did I track last week in total?" →
`toggl_get_summary` start_date=last Monday, end_date=last Sunday

"How much time on the Login task this week?" →
1. Resolve project → get project_id
2. `toggl_list_tasks(project_id)` → get task_id
3. `toggl_get_summary` with task_id

## Checking Running Timer

"Is anything running?" / "What am I tracking?" → `toggl_get_current_timer`

## Error Handling

- Token error → tell user to check `~/.claude/toggl/credentials`
- Project not found → log without project, mention it
- Task not found → log with project only, mention it
- Date ambiguous → pick the most reasonable interpretation, confirm after
