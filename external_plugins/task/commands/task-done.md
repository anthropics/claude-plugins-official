# Complete task

## Instructions

1. Find the active task in `.claude/CLAUDE.md` or `.claude/task/`

2. If no active task, tell the user there is nothing to complete

3. If active task found:
   - Update checklist.md: mark all items done, set Status to COMPLETED
   - Update handoff.md: set Current State to "Task completed"
   - Append to decisions.log: "[TIMESTAMP] Task marked as complete"
   - Remove the task imports from `.claude/CLAUDE.md`

4. **Archive the task**:
   - Create `.claude/task/archive/` directory if it doesn't exist
   - Move the entire task folder to `.claude/task/archive/<task_id>/`
   - This keeps the task directory clean while preserving history

5. Tell the user:
   - Task completed
   - Summary of what was accomplished
   - Task archived to `.claude/task/archive/<task_id>/` for reference

## Important
- Always archive completed tasks to prevent accumulation
- Never delete task files - archive them instead
