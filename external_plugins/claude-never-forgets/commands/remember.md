---
description: Manually add something to project memory
argument-hint: [what to remember]
---

Add to `.claude/memories/project_memory.json` in `manual_memories` array:

```json
{"type": "manual", "content": "$ARGUMENTS", "added_at": "<timestamp>", "source": "user_command"}
```

Confirm: `✓ Remembered: "$ARGUMENTS"`
