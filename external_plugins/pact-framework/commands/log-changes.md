---
description: Update `CLAUDE.md` to reflect recent significant changes
argument-hint: [e.g., new auth module, fixed build gotcha]
---
Update `CLAUDE.md` to reflect: $ARGUMENTS

First, read existing CLAUDE.md to understand its structure.

## What to Document

Add things that:
- Save debugging time (gotchas, non-obvious patterns)
- Are needed every session (build commands, key files)
- Can't be easily found in code (architectural "why")

Prefer updating existing sections. Only create new sections when changes genuinely don't fit elsewhere.

## What to Avoid

- Full code blocks (reference source files instead)
- Verbose explanations (keep entries to ~10 lines)
- Content better suited for `.claude/rules/`, `docs/`, or code comments

After updates, remove any outdated information.

Once done, commit changes (push if remote exists).
