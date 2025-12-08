---
description: Remove something from project memory
argument-hint: [what to forget]
---

Read `.claude/memories/project_memory.json`, find and remove entries matching "$ARGUMENTS" from `manual_memories` or `realtime_memories`.

Confirm: `✓ Forgot: "<matched>"`

If not found: `No memory found matching "$ARGUMENTS". Use /memories to see all.`
