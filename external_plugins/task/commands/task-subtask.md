# Create a subtask

## Instructions

When the user runs `/task-subtask "<goal>"`, create a subtask linked to the current task:

1. **Get the active task** as parent
   - If no active task, ask user to specify parent ID

2. **Run the dependencies script**:
   ```bash
   node .claude/plugins/task/scripts/dependencies.js subtask <parent_id> "<goal>"
   ```

3. **What gets created**:
   - New task directory with standard files (plan.md, checklist.md, etc.)
   - `dependencies.json` linking to parent
   - Parent's `dependencies.json` updated with new child

4. **Confirm to user**:
   - Subtask ID created
   - Parent task linked
   - Ask if they want to switch to the subtask

## Usage Examples

```
/task-subtask "Implement OAuth backend"
/task-subtask "Write unit tests for auth module"
/task-subtask "Design database schema"
```

## File Structure

Each task with dependencies has a `dependencies.json`:
```json
{
  "parent": "task_20260110_100000",
  "children": ["task_20260110_101500", "task_20260110_103000"],
  "blockedBy": [],
  "blocks": []
}
```

## Workflow

1. Start main task: `/task-start "Migrate to OAuth"`
2. Break down: `/task-subtask "Setup OAuth provider"`
3. Break down: `/task-subtask "Backend implementation"`
4. Break down: `/task-subtask "Frontend integration"`
5. View tree: `/task-tree`

```
task_20260110_100000 "Migrate to OAuth"
├── task_20260110_101500 "Setup OAuth provider" ✅
├── task_20260110_103000 "Backend implementation" ⏳
└── task_20260110_105000 "Frontend integration" ⏸️
```

## Notes

- Subtasks inherit context from parent
- Completing all subtasks doesn't auto-complete parent
- Use `/task-switch` to move between parent and subtasks
- Parent task should be completed last
