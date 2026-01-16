---
description: Archive completed session work
allowed-tools: Bash(git:*), Read, Write, Glob, mcp__linear__*
model: haiku
---

# Archive Session

## Step 1: Find Git Root

Run `git rev-parse --show-toplevel` to locate the repository root.

## Step 2: Review Completed Work

Read `<git-root>/.bonfire/index.md` and identify completed work:
- Sessions with merged PRs
- Completed features/tasks
- Work that's no longer active

## Step 3: Create Archive Entry

Move completed session content to `<git-root>/.bonfire/archive/`.

**Naming convention**: `YYYY-MM-DD-<issue-id>-<topic>.md`

Examples:
- `2025-12-22-GTMENG-387-inbound-improvements.md` (with issue ID)
- `2025-12-22-fix-login-redirect.md` (without issue ID)

Use this template:
```markdown
# [TOPIC]

**Date**: [DATE]
**Issue**: [ISSUE-ID or N/A]
**PR**: [PR link if available]
**Status**: Completed

---

## Summary

[Brief description of what was accomplished]

## Accomplished

- [List of completed items]

## Decisions Made

- [Key decisions and rationale]

## Impact

- [Before/after metrics if applicable]
- Files changed: [count]

## Related

- [Links to related docs, specs, or code]
```

## Step 4: Clean Up Index

Update `<git-root>/.bonfire/index.md`:
- Remove archived session entries from Recent Sessions
- Keep Current State focused on active work
- Update Next Session Priorities
- Add link to archive file in Archived Sessions section:
  ```markdown
  ## Archived Sessions

  - [YYYY-MM-DD - Topic](archive/YYYY-MM-DD-issue-topic.md)
  ```

## Step 5: Clean Up Specs (if applicable)

Read `specsLocation` from `<git-root>/.bonfire/config.json` (default `.bonfire/specs/`).

Check if any specs in the configured location are now complete:
- If the spec was fully implemented, delete the spec file (archive has the record)
- If the spec has reusable reference material, move that content to `docs/` first

## Step 6: Update Linear Issue (if applicable)

Read `<git-root>/.bonfire/config.json` and check `linearEnabled`.

**If `linearEnabled` is true**:

1. Check if archived work references a Linear issue (look in session context for `[A-Z]+-[0-9]+` pattern)
2. If Linear issue found, ask user: "Mark Linear issue [ISSUE-ID] as Done?"
3. If user confirms:
   - Use Linear MCP `linear_update_issue` tool with:
     - `id`: The issue ID (e.g., `ENG-123`)
     - `status`: Set to "Done" or completed state
   - Optionally use `linear_add_comment` to add link to archive/PR
4. On failure: Warn user - "Couldn't update Linear issue. You may need to update it manually."

Note: Tool names may vary by Linear MCP implementation.

**If `linearEnabled` is false or not set**: Skip this step.

## Step 7: Commit Archive (if tracked)

Read `gitStrategy` from `<git-root>/.bonfire/config.json`.

**If gitStrategy is "ignore-all"**: Skip committing - archive is local only.

**If gitStrategy is "hybrid" or "commit-all"**:
1. **NEVER use `git add -f`** - respect gitignore
2. Stage unignored files:
   ```bash
   git add .bonfire/
   ```
3. Check if anything was staged before committing:
   ```bash
   git diff --cached --quiet .bonfire/ || git commit -m "docs: archive completed session work"
   ```

## Step 8: Confirm

Report:
- What was archived
- Any specs cleaned up
- Current state of index.md
- Ready for next session
