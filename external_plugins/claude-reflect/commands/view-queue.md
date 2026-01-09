---
description: View the learnings queue without processing
allowed-tools: Bash
---

## Context
- Queue file: `~/.claude/learnings-queue.json`

## Your Task

Display the current learnings queue in a readable format:

```
════════════════════════════════════════════════════════════
LEARNINGS QUEUE: [N] items
════════════════════════════════════════════════════════════

1. [type] "first 80 chars of message..."
   Patterns: [patterns matched]
   Project: [project path]
   Time: [timestamp]

2. [type] "first 80 chars of message..."
   ...

════════════════════════════════════════════════════════════
Commands:
  /reflect        - Process and save learnings
  /skip-reflect   - Discard all learnings
════════════════════════════════════════════════════════════
```

If queue is empty:
```
════════════════════════════════════════════════════════════
LEARNINGS QUEUE: Empty
════════════════════════════════════════════════════════════
No learnings queued. Use "remember: <learning>" to add items,
or corrections will be auto-detected. Run /reflect to process.
════════════════════════════════════════════════════════════
```

## Implementation

Read and format the queue:
```bash
cat ~/.claude/learnings-queue.json 2>/dev/null || echo "[]"
```

Parse each item and display:
- `type`: "explicit" or "auto"
- `message`: truncated to 80 chars with "..." if longer
- `patterns`: what triggered detection
- `project`: where it was captured
- `timestamp`: when it was captured
