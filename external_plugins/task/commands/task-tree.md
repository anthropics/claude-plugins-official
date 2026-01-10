# Show task dependency tree

## Instructions

When the user runs `/task-tree [task_id]`, display the task hierarchy:

1. **Get the task ID** (default: active task)

2. **Run the dependencies script**:
   ```bash
   node .claude/plugins/task/scripts/dependencies.js tree [task_id]
   ```

3. **Display the tree**:
   - Find the root parent (traverse up)
   - Show all children recursively
   - Include status icons and blockers

## Output Format

```
🌳 TASK TREE

✅ task_20260110_100000
   "Migrate to OAuth"
   ├── ✅ task_20260110_101500
   │   "Setup OAuth provider"
   ├── ⏳ task_20260110_103000
   │   "Backend implementation"
   │   ├── ✅ task_20260110_103500
   │   │   "Create auth middleware"
   │   └── ⏳ task_20260110_104000
   │       "Implement token refresh"
   └── ⏸️ task_20260110_105000
       "Frontend integration"
       ⚠️ Blocked by: task_20260110_103000
```

## Status Icons

- ✅ Completed
- ⏳ In Progress
- ❌ Abandoned
- ⏸️ Blocked (has unresolved blockers)

## Usage Examples

```
/task-tree                    # Tree for active task
/task-tree task_20260110_100000  # Tree for specific task
```

## Blocking Tasks

To mark a task as blocking another:
```
# In your conversation
"task_20260110_103000 blocks task_20260110_105000"
```

This will:
1. Update `dependencies.json` for both tasks
2. Show warning in tree view
3. Remind when trying to start blocked task

## Benefits

- **Visualize progress** on complex tasks
- **Identify blockers** before they stall work
- **Plan work order** based on dependencies
- **Track completion** across subtasks
