# Task Plugin

Complex Task Mode for Claude Code — Full-featured task management with templates, analytics, achievements, and collaboration.

## Problem Solved

- Claude drifts from original goal
- Context lost after crash/compact
- No way to track progress on complex tasks
- No gamification or productivity insights

## Features

| Command | Description |
|---------|-------------|
| `/task-start` | Create a task with plan, checklist, handoff, decisions log |
| `/task-status` | Show progress and recent decisions |
| `/task-switch` | Switch between multiple tasks |
| `/task-done` | Complete and archive task |
| `/task-template` | Start from predefined templates (bugfix, feature, refactor) |
| `/task-achievements` | View badges and streaks |
| `/task-stats` | Analytics dashboard |
| `/task-snapshot` | Create checkpoints before risky changes |
| `/task-restore` | Restore from checkpoint |
| `/task-test-mode` | Add testing checklists |
| `/task-subtask` | Create subtasks |
| `/task-tree` | View task hierarchy |
| `/task-recommend` | AI-powered suggestions |
| `/task-export` | Export to HTML portfolio or JSON |
| `/task-share` | Share tasks with teammates |
| `/task-import` | Import shared tasks |
| `/task-comment` | Add comments |
| `/task-voice-note` | Voice dictation support |

## Quick Start

```bash
/task-start "Implement user authentication"
# ... work on the task ...
/task-status
/task-done
```

## Files Structure

```
.claude/task/<task_id>/
├── plan.md           # Task plan and approach
├── checklist.md      # Progress tracking
├── handoff.md        # Auto-updated before compact
├── decisions.log     # Append-only audit trail
└── snapshots/        # Task checkpoints
```

## Author

[mmmprod](https://github.com/mmmprod)

## Homepage

https://github.com/mmmprod/task-plugin

## License

MIT
