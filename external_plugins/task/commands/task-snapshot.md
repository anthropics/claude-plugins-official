# Create a task snapshot

## Instructions

When the user runs `/task-snapshot [label]`, create a checkpoint of the current state:

1. **Run the snapshot script**
   ```bash
   node .claude/plugins/task/scripts/snapshot.js create [label]
   ```

2. **What gets saved:**
   - `plan.md` - Current task plan
   - `checklist.md` - Current progress
   - `handoff.md` - Current handoff notes
   - `decisions.log` - All decisions so far
   - Git stash of code changes (optional, if git available)

3. **Confirm to user:**
   - Snapshot ID (format: `snap_YYYY-MM-DDTHH-MM-SS`)
   - Label if provided
   - Files included

4. **List existing snapshots** if user just runs `/task-snapshot` without args:
   ```bash
   node .claude/plugins/task/scripts/snapshot.js list
   ```

## Usage Examples

```
/task-snapshot                        # List snapshots
/task-snapshot Before refactor        # Create with label
/task-snapshot Backup before risky change
```

## Storage

Snapshots are stored in the task directory:
```
.claude/task/<task_id>/snapshots/
├── manifest.json           # List of all snapshots
├── snap_2026-01-10T15-00-00/
│   ├── manifest.json       # Snapshot metadata
│   ├── plan.md
│   ├── checklist.md
│   ├── handoff.md
│   └── decisions.log
└── snap_2026-01-10T16-30-00/
    └── ...
```

## Benefits

- **Safety net** before risky changes
- **Experimentation** - try approaches without losing progress
- **Recovery** - restore if something goes wrong
- **History** - see how the task evolved

## Notes

- Max 20 snapshots per task
- Old snapshots auto-cleaned when creating new ones
- Git stash is created but immediately re-applied (non-destructive)
