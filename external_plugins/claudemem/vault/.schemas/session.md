# Session Schema

## File Location
`Sessions/{YYYY-MM-DD}.md`

For multiple sessions per day: `Sessions/{YYYY-MM-DD}-{n}.md`

## Required Frontmatter

```yaml
---
type: session
date: string         # ISO date
project: string      # Primary project worked on (or "multiple")
started: string      # ISO timestamp
ended: string        # ISO timestamp (filled at session end)
---
```

## Required Sections

```markdown
# Session: {YYYY-MM-DD}

## Summary
{2-3 sentence summary of what was accomplished}

## Completed
- [x] Task or action completed
- [x] Another completed item

## In Progress
- [ ] Task that was started but not finished

## Decisions Made
- **{Topic}**: {Decision and brief rationale}

## Blockers Encountered
- {Blocker description} → {Resolution or "Unresolved"}

## Next Session
- [ ] First thing to do next time
- [ ] Second priority

## Notes
{Any additional context, learnings, or observations}
```

## Rules

1. One session file per working session
2. Create at session end, not start
3. Session file is never modified after creation (append-only history)
4. Summary should be scannable in 5 seconds
5. "Next Session" section is critical for continuity
