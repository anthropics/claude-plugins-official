# Show task status

## Instructions

1. Find the active task in `.claude/CLAUDE.md` or scan `.claude/task/`

2. If no active task, tell the user and suggest `/task-start`

3. If active task found, display:
   - Task ID
   - Goal (from plan.md)
   - Checklist progress (X/Y complete)
   - Last 5 entries from decisions.log
   - Current blockers (from handoff.md)