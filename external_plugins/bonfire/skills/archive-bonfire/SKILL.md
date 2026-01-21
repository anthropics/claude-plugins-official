---
description: Suggest archiving completed work when PRs are merged or work is completed. Triggers when user asks to merge a PR ("merge it", "merge the PR"), after successful gh pr merge, or mentions completion ("shipped", "done with X", "merged to main"). Does NOT archive automatically - suggests running /bonfire:archive.
allowed-tools: Read, Glob, Bash(gh:*)
---

# Archive Bonfire Awareness

This skill detects when session work may be ready for archiving and suggests the appropriate action.

## When to Use This Skill

Trigger when:
- User asks to merge: "merge it", "merge the PR", "go ahead and merge", "ship it"
- After you successfully run `gh pr merge`
- User mentions completion: "PR merged", "shipped", "done with X", "finished"
- User references merged state: "merged to main", "closed the issue"

## Instructions

1. If user asks to merge a PR:
   - Perform the merge as requested
   - On success, continue to step 2
   - On failure, help resolve the issue (don't suggest archiving)

2. Find git root and check if `.bonfire/index.md` exists

3. If it exists, read it to assess work state

4. If user provided a PR URL/number (or you just merged one), verify status:
   ```
   gh pr view [URL/number] --json state,mergedAt,title
   ```

5. Assess if work appears complete:
   - PR merged?
   - Related tasks marked done in session notes?
   - No obvious follow-up work mentioned?

6. If work appears complete, suggest archiving:
   > "PR merged successfully. This session's work looks complete - want me to archive it?
   > Run `/bonfire:archive` to move completed work to the archive."

7. If there's more work in the session:
   > "PR merged. I see there's still [X, Y] in the session notes - want to continue
   > with those or archive what's done so far?"

## Important

- This skill **suggests** archiving, it does NOT archive automatically
- User must explicitly run `/bonfire:archive` to perform the archive
- Trigger AFTER merge succeeds, not before
- Multiple PRs may be part of one logical session - check context
- If `.bonfire/` doesn't exist, don't suggest archiving
