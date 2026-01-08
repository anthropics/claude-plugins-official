# Project Schema

## File Location
`Projects/{id}/_index.md`

## Required Frontmatter

```yaml
---
type: project
id: string           # kebab-case, unique (e.g., "recall", "townsquare")
name: string         # Human-readable name
status: string       # active | paused | completed | archived
priority: string     # P0 | P1 | P2
created: string      # ISO date (YYYY-MM-DD)
---
```

## Optional Frontmatter

```yaml
brief: string        # 1-3 sentence description
repository: string   # Path to code repository
stack: array         # Technologies used
target_date: string  # Target completion date
milestone: string    # Current milestone name
```

## Required Sections

```markdown
# {Project Name}

## Overview
{Brief description}

## Current State
- **Active Epic**: {epic name or "None"}
- **Active Task**: {task name or "None"}
- **Blockers**: {blocker list or "None"}

## Epics
<!-- List of epics with status -->

## Quick Links
- [PRD](./PRD.md)
- [Decisions](./Decisions.md)
```

## Rules

1. One project = one folder in `Projects/`
2. Folder name must match `id` field
3. Never create duplicate project folders
4. `_index.md` is the entry point, always exists
