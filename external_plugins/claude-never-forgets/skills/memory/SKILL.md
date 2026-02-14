---
name: memory
description: Access and use project memories from previous sessions. Use this skill when you need to recall past decisions, check project conventions, or understand user preferences that were established in earlier sessions.
---

# Project Memory

Memories stored in `.claude/memories/project_memory.json`.

## Use When
- Choosing libraries/tools
- Making architecture decisions
- User says "remember when..." or "like before"

## Rules
- Apply silently, don't announce
- Current request > old memory if conflict

## Commands
- `/remember [text]` - Add to manual_memories array
- `/forget [text]` - Remove matching memory
- `/memories` - Show all stored memories
