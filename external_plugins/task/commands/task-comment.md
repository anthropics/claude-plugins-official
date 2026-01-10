# Add a comment to a task

## Instructions

When the user runs `/task-comment "<message>"`, add a comment to the active task:

1. **Get active task** (or ask for task ID)

2. **Get author name** from the user or use a default

3. **Run the collaboration script**:
   ```bash
   node .claude/plugins/task/scripts/collaboration.js comment <task_id> <author> "<message>"
   ```

4. **What happens**:
   - Comment added to `comments.json`
   - Summary logged to `decisions.log`
   - Timestamp recorded

5. **Confirm** the comment was added

## Usage Examples

```
/task-comment "Need help with the auth flow"
/task-comment "Blocked waiting for API access"
/task-comment "Performance looks good after optimization"
```

## View Comments

To see all comments on a task:
```
/task-comments [task_id]
```

Or run directly:
```bash
node .claude/plugins/task/scripts/collaboration.js comments <task_id>
```

## Comment Format

Comments are stored in `comments.json`:
```json
{
  "comments": [
    {
      "id": "lxyz123",
      "author": "alice",
      "message": "Need help with the auth flow",
      "timestamp": "2026-01-10T15:30:00.000Z"
    },
    {
      "id": "lxyz456",
      "author": "bob",
      "message": "I can help tomorrow",
      "timestamp": "2026-01-10T16:00:00.000Z"
    }
  ]
}
```

## Use Cases

- **Collaboration** - Communicate with team members
- **Notes to self** - Remember important details
- **Handoff** - Leave notes for the next person
- **Progress updates** - Document milestones
- **Blockers** - Flag issues that need attention

## Display Format

```
💬 COMMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@alice - 1/10/2026, 3:30:00 PM
Need help with the auth flow

@bob - 1/10/2026, 4:00:00 PM
I can help tomorrow
```

## Notes

- Comments are preserved when sharing tasks
- Comments are imported with shared tasks
- Each comment has a unique ID for reference
- Comments are also summarized in decisions.log
