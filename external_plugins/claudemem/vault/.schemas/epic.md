# Epic Schema

## File Location
`Projects/{project-id}/Epics/{nn}-{epic-name}.md`

Example: `Projects/recall/Epics/01-foundation.md`

## Required Frontmatter

```yaml
---
type: epic
id: string           # Format: {nn}-{name} (e.g., "01-foundation")
project: string      # Parent project id
status: string       # pending | in-progress | completed | blocked
priority: string     # P0 | P1 | P2
created: string      # ISO date
---
```

## Optional Frontmatter

```yaml
target_date: string  # Target completion date
milestone: string    # Associated milestone
blocked_by: array    # Epic IDs this is blocked by
```

## Required Sections

```markdown
# {Epic Title}

## Description
{What this epic accomplishes}

## Tasks

- [ ] Task description #pending
- [ ] Task description #pending

## Acceptance Criteria
- {Criterion 1}
- {Criterion 2}
```

## Task Format

```markdown
- [ ] Task description #status #priority
- [ ] Task description #blocked-by:{task-id}
- [x] Completed task #done
```

### Task Statuses (as tags)
- `#pending` - Not started
- `#in-progress` - Currently working
- `#done` - Completed (use [x] checkbox too)
- `#blocked` - Waiting on something
- `#deferred` - Postponed

### Task Priorities (as tags)
- `#P0` - Critical
- `#P1` - High
- `#P2` - Normal (default, can omit)

### Task Dependencies
- `#blocked-by:{task-id}` - This task is blocked by another
- `#blocks:{task-id}` - This task blocks another

## Rules

1. Epic filenames start with 2-digit number for ordering (01, 02, etc.)
2. Tasks are checkboxes within the epic file
3. Mark [x] when complete, add #done tag
4. Update epic status when all tasks complete
