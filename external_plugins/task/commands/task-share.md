# Share a task

## Instructions

When the user runs `/task-share [task_id]`, export the task for sharing:

1. **Get the task ID** (default: active task)

2. **Run the collaboration script**:
   ```bash
   node .claude/plugins/task/scripts/collaboration.js share <task_id>
   ```

3. **Output**: Creates `<task_id>.task.json` file containing:
   - All task files (plan.md, checklist.md, handoff.md, decisions.log)
   - Dependencies if any
   - Comments if any
   - Export metadata

4. **Tell the user**:
   - File location
   - How to share (send file, upload, etc.)
   - How recipient can import

## Usage Examples

```
/task-share                           # Share active task
/task-share task_20260110_100000      # Share specific task
```

## Export File Format

`task_20260110_100000.task.json`:
```json
{
  "version": "1.0",
  "taskId": "task_20260110_100000",
  "exportedAt": "2026-01-10T15:00:00.000Z",
  "files": {
    "plan.md": "# Task Plan\n...",
    "checklist.md": "# Task Checklist\n...",
    "handoff.md": "# Handoff Notes\n...",
    "decisions.log": "[2026-01-10] Task created..."
  },
  "dependencies": {
    "parent": null,
    "children": []
  },
  "comments": {
    "comments": []
  }
}
```

## Sharing Methods

1. **Direct file share**
   - Send `.task.json` file via Slack, email, etc.
   - Recipient imports with `/task-import`

2. **GitHub Gist**
   - Create a gist with the JSON content
   - Share the gist URL

3. **Cloud storage**
   - Upload to Dropbox, Google Drive, etc.
   - Share the download link

## Privacy Note

The exported file contains:
- Full task plan and approach
- Complete decision history
- All comments

Review the content before sharing to ensure no sensitive information is included.
