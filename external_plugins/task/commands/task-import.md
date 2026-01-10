# Import a shared task

## Instructions

When the user runs `/task-import <file_path>`, import a shared task:

1. **Get the file path** to the `.task.json` file

2. **Run the collaboration script**:
   ```bash
   node .claude/plugins/task/scripts/collaboration.js import <file_path>
   ```

3. **What happens**:
   - New task directory created with new ID
   - All task files restored
   - Import note added to decisions.log
   - Comments preserved

4. **Tell the user**:
   - New task ID
   - Original task ID
   - Imported files
   - How to switch to the task

## Usage Examples

```
/task-import ./task_20260110_100000.task.json
/task-import /path/to/shared-task.task.json
```

## Import Process

1. **Validation**
   - Checks file format version
   - Validates required fields

2. **New ID Generation**
   - Creates new `task_YYYYMMDD_HHMMSS` ID
   - Ensures no collision with existing tasks

3. **File Creation**
   - plan.md
   - checklist.md
   - handoff.md
   - decisions.log (with import note appended)
   - comments.json (if present)

4. **Import Note**
   ```
   [2026-01-10T15:30:00] Imported from: task_20260110_100000
   [2026-01-10T15:30:00] Original export date: 2026-01-10T15:00:00
   ```

## After Import

1. Run `/task-switch` to see all tasks including the imported one
2. Switch to the imported task
3. Review the plan and checklist
4. Continue work or modify as needed

## Notes

- The original task ID is preserved in the decisions log
- Comments are imported but you can add new ones
- Dependencies are noted but not automatically linked
- You can import the same task multiple times (each gets a new ID)
