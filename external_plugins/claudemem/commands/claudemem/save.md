---
description: Save session notes and update manifest
allowed-tools: Read, Write, Edit, Bash
---

# ClaudeMem Save

Write session notes capturing what was accomplished.

## Steps

1. **Gather Session Data**
   - Read `~/Vault/_manifest.md` for context
   - Review conversation for:
     - What was discussed
     - What was built/changed
     - Decisions made
     - Problems encountered
     - What's next

2. **Create Session File**

File: `~/Vault/Sessions/{YYYY-MM-DD}.md`

If file exists for today, create `{YYYY-MM-DD}-2.md` etc.

```yaml
---
type: session
date: {YYYY-MM-DD}
project: {active project or "general"}
started: {session start time if known}
ended: {now}
---

# Session: {YYYY-MM-DD}

## Summary
{2-3 sentence summary of the session}

## Completed
- [x] {Task or action completed}
- [x] {Another completed item}

## In Progress
- [ ] {Unfinished work}

## Decisions Made
- **{Topic}**: {Decision and rationale}

## Blockers Encountered
- {Blocker} → {Resolution or "Unresolved"}

## Next Session
- [ ] {First priority for next time}
- [ ] {Second priority}

## Notes
{Any additional observations, learnings, context}
```

3. **Update Manifest**
   - Add entry to Recent Sessions table
   - Keep only last 10 sessions in table
   - Update timestamp

4. **Announce**

```
SESSION SAVED: {date}

Summary: {brief summary}

Completed: {n} items
Next time: {first next item}

Session notes: ~/Vault/Sessions/{date}.md
```

## Auto-Save Triggers

Consider saving when:
- User says "done for today" / "stopping" / "that's it"
- Switching to a different project
- Before `/claudemem switch`
- Long pause in conversation
