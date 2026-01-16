---
description: Read project session context from .bonfire/index.md to understand ongoing work, previous decisions, blockers, and history. Use when the user asks about project context, previous sessions, what was worked on before, architectural decisions, blockers, or when they reference "last time", "previously", "the session", or "what we decided".
allowed-tools: Read, Glob
---

# Bonfire Context

This project may use the Bonfire pattern to maintain continuity across AI coding sessions. Context is stored in `.bonfire/index.md` rather than relying on conversation memory.

## When to Use This Skill

Read session context when the user:
- Asks about previous work or decisions
- References "last time", "previously", "before"
- Wants to know about blockers or pending issues
- Asks what the project status is
- Starts a significant task that might have prior context

## Instructions

1. Find the git root: `git rev-parse --show-toplevel`

2. Check if `.bonfire/index.md` exists at the git root

3. If it exists, read it to understand:
   - Current project status and recent work
   - Active decisions and their rationale
   - Known blockers or pending issues
   - Links to relevant specs or documentation

4. Check `.bonfire/specs/` if the user asks about implementation specs

5. Check `.bonfire/docs/` if the user asks about documented topics

## File Structure

```
.bonfire/
├── index.md          # Main session context (read this first)
├── config.json       # Project settings
├── archive/          # Completed work history
├── docs/             # Topic documentation
└── specs/            # Implementation specs
```

## Important

- This skill is for **reading** context, not updating it
- Session updates happen via `/bonfire:end` command
- Don't modify `.bonfire/index.md` unless explicitly asked
- If `.bonfire/` doesn't exist, the project may not use this pattern
