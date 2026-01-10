# Restore a task snapshot

## Instructions

When the user runs `/task-restore <snapshot_id>`, restore a previous checkpoint:

1. **List available snapshots** if no ID provided:
   ```bash
   node .claude/plugins/task/scripts/snapshot.js list
   ```

2. **Restore the snapshot**:
   ```bash
   node .claude/plugins/task/scripts/snapshot.js restore <snapshot_id>
   ```

3. **What happens:**
   - Current state is automatically backed up first
   - Task files are restored from snapshot:
     - `plan.md`
     - `checklist.md`
     - `handoff.md`
     - `decisions.log`
   - A log entry is added: "Restored from snapshot: snap_..."

4. **Confirm to user:**
   - Restored snapshot ID
   - Auto-backup ID (in case they want to undo)
   - Remind them to review the restored state

## Usage Examples

```
/task-restore                              # List snapshots to choose from
/task-restore snap_2026-01-10T15-00-00     # Restore specific snapshot
```

## Safety

- **Auto-backup**: Current state is saved before restore
- **Non-destructive**: Original snapshot is preserved
- **Logged**: Restore action is logged in decisions.log

## After Restore

1. Review the restored `checklist.md` for current progress
2. Check `plan.md` to remember the approach
3. Read recent `decisions.log` entries
4. Continue working from the restored point

## Undo Restore

If you restore and want to go back:
```
/task-restore <auto-backup-id>
```
The auto-backup ID is shown after each restore.
