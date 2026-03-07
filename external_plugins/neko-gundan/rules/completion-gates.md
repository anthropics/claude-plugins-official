# Completion Gates

Quality checkpoints that must be passed before declaring any task complete. No exceptions, even for single-line changes.

## Start Gate (Before Beginning Work)

Execute before starting any platoon+ mission:

| # | Check | How to verify |
|---|-------|---------------|
| 1 | Task scope is clear | Purpose + success criteria defined |
| 2 | Target files identified | File list exists |
| 3 | No unresolved blockers | Check dashboard/whiteboard |
| 4 | Current state understood | Read target files, `git status` |
| 5 | Related lessons checked | Search dev-lessons for project/tech tags |

## Completion Gate (Before Saying "Done")

Every item must be checked with evidence. "I confirmed it" is not evidence — "Here's the command output showing it works" is.

| # | Check | How to verify | Evidence format |
|---|-------|---------------|-----------------|
| 1 | All success criteria met | Run tests, verify output | Test results / command output |
| 2 | No unintended changes | `git diff` review | Diff output showing only intended changes |
| 3 | Tests pass | Run test suite | Test pass/fail output |
| 4 | No new lint errors | Run linter | Linter output |
| 5 | No uncommitted new files | `git status` | Status output showing clean state |
| 6 | Whiteboard objections resolved | Check `[OBJECTION]` tags | Resolution notes or "no objections" |
| 7 | Documentation updated (if needed) | Check if README/docs need changes | N/A or updated file reference |
| 8 | Existing features not broken | Run full test suite or smoke test | Test results |
| 9 | Files not accidentally deleted | Compare with start state | `git status` / file listing |

## Gate Evidence Format

Record gate results in a table:

```markdown
| # | Item | Status | Evidence |
|---|------|--------|----------|
| 1 | Success criteria | PASS | `npm test` output: 42 passed, 0 failed |
| 2 | No unintended changes | PASS | `git diff` shows only 3 target files |
| ... | ... | ... | ... |
```

## Rules

- All items must be `PASS` or `N/A` (with justification)
- If any item is `FAIL`, fix before declaring complete
- Shigoto-neko executes the gate; kurouto-neko independently verifies
- "I'll check later" is prohibited — check now or don't declare done

## File Deletion Safety

When deleting files:
1. Move to `_deleted/` directory first (never instant-delete)
2. Verify no references to the file remain
3. Next session can confirm and permanently remove
4. This prevents irreversible file loss from AI mistakes
