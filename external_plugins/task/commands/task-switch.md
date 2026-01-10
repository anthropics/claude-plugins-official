# Switch to a different task

## Instructions

1. **List available tasks**
   - Scan `.claude/task/` for task directories (format: `task_YYYYMMDD_HHMMSS`)
   - Also check `.claude/task/archive/` for archived tasks
   - Show each task with:
     - Task ID
     - Goal (first line of plan.md after "## Goal")
     - Status (from checklist.md: IN_PROGRESS, COMPLETED, etc.)
     - Whether it's archived

2. **If no task ID provided as argument**:
   - Display the list of tasks
   - Ask user which task to switch to

3. **If task ID provided or selected**:
   - Validate the task ID format (`task_YYYYMMDD_HHMMSS`)
   - Check if task exists in `.claude/task/` or `.claude/task/archive/`
   - If archived, ask user if they want to unarchive it (move back to active)

4. **Switch to the task**:
   - Update `.claude/CLAUDE.md` to reference the new task:
   ```markdown
   # Active Task

   @.claude/task/<task_id>/plan.md
   @.claude/task/<task_id>/checklist.md
   @.claude/task/<task_id>/handoff.md
   ```
   - Append to the new task's decisions.log: "[TIMESTAMP] Switched to this task"

5. **Tell the user**:
   - Switched to task: <task_id>
   - Show goal and current progress
   - Remind them to check `/task-status` for details

## Example usage
```
/task-switch                    # List tasks and choose
/task-switch task_20260110_143000  # Switch directly
```
