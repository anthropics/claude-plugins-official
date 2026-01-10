# Export tasks and generate portfolio

## Instructions

When the user runs `/task-export [format] [options]`, export tasks in the requested format:

1. **Determine format**:
   - `portfolio` (default) - HTML portfolio page
   - `json` - JSON export of all tasks
   - `task <task_id>` - Single task JSON export

2. **Run the export script**:
   ```bash
   node .claude/plugins/task/scripts/export.js [format] [options]
   ```

3. **Show output location** and next steps

## Formats

### Portfolio (default)
```
/task-export
/task-export portfolio "My Projects"
```

Generates `portfolio.html`:
- Professional HTML page
- Stats: completed tasks, total time, skills
- Skills progress bars
- Projects grouped by month
- Mobile responsive
- GitHub Pages ready

**To deploy:**
1. Rename to `index.html`
2. Push to `gh-pages` branch
3. Enable GitHub Pages in repo settings

### JSON (all tasks)
```
/task-export json
```

Generates `tasks-export.json`:
```json
[
  {
    "id": "task_20260110_100000",
    "date": "2026-01-10T10:00:00.000Z",
    "status": "completed",
    "type": "feature",
    "goal": "Add OAuth login",
    "duration": 14400000,
    "durationStr": "4h 0m"
  },
  ...
]
```

### Single Task
```
/task-export task task_20260110_100000
```

Generates `task_20260110_100000.json`:
```json
{
  "id": "task_20260110_100000",
  "plan": "# Task Plan\n...",
  "checklist": "# Task Checklist\n...",
  "handoff": "# Handoff Notes\n...",
  "decisions": "[2026-01-10T10:00:00] Task created..."
}
```

## Portfolio Features

The generated portfolio includes:

**Header:**
- Project name
- Generated with Claude Code Task Plugin

**Stats Cards:**
- Projects Completed
- Total Development Time
- Skill Areas

**Skills Section:**
- Progress bars by task type
- Sorted by frequency

**Projects List:**
- Grouped by month
- Shows: goal, type badge, date, duration
- Truncated approach text

**Footer:**
- Link to task plugin repo
- Last updated date

## Usage Examples

```
/task-export                           # Generate portfolio.html
/task-export portfolio "John's Work"   # Custom project name
/task-export json                      # Export all tasks to JSON
/task-export task task_20260110_100000 # Export single task
```

## Output Files

| Format | Output File |
|--------|-------------|
| portfolio | `portfolio.html` |
| json | `tasks-export.json` |
| task | `<task_id>.json` |

Files are created in the project root directory.

## Customization

The portfolio HTML is self-contained. To customize:
1. Export with `/task-export`
2. Edit the HTML/CSS as needed
3. Deploy wherever you want

## Benefits

- **Automatic portfolio** from your daily work
- **No manual updates** - just export periodically
- **Professional appearance** ready to share
- **Skills tracking** visualized automatically
- **Time investment** documented
