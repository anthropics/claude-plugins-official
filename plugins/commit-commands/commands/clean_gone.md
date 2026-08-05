---
description: Use when local branches remain after their remotes were deleted (merged PR branches piling up) and you want them removed, including any worktrees still holding them.
---

## Your Task

Delete the local branches whose upstream is gone, and any worktrees holding them.

**Select branches by upstream state, never by matching text.** `git branch -v`
prints the `[gone]` marker immediately before the commit subject, so a branch
whose tip subject merely *mentions* `[gone]` matches the same grep and gets
force-deleted with its unmerged work. `%(upstream:track)` is a structured field
and cannot collide with commit text.

## Commands to Execute

1. **Refresh the upstream state.** The `gone` marker only appears after a
   pruning fetch — without this, recently deleted remotes still look alive.
   ```bash
   git fetch --prune
   ```

2. **List what will be deleted, and confirm it looks right.**
   ```bash
   git for-each-ref --format='%(refname:short) %(upstream:track)' refs/heads \
     | awk '$2 == "[gone]" {print $1}'
   ```

3. **Delete them, removing any worktree first.**
   ```bash
   # Drop worktrees whose directory is already gone; `git worktree remove`
   # refuses to operate on those, which would wedge the loop.
   git worktree prune

   git for-each-ref --format='%(refname:short) %(upstream:track)' refs/heads \
     | awk '$2 == "[gone]" {print $1}' \
     | while read -r branch; do
     echo "Processing branch: $branch"
     # Match the worktree on its exact ref. Parsing `git worktree list` instead
     # breaks two ways: a path containing a space is truncated by awk, and a
     # branch name containing `.` or `+` is a regex to grep.
     worktree=$(git worktree list --porcelain \
       | awk -v br="refs/heads/$branch" '/^worktree /{p=substr($0,10)} $0=="branch "br{print p}')
     if [ -n "$worktree" ] && [ "$worktree" != "$(git rev-parse --show-toplevel)" ]; then
       echo "  Removing worktree: $worktree"
       git worktree remove --force "$worktree" || continue
     fi
     echo "  Deleting branch: $branch"
     git branch -D "$branch"
   done
   ```

## Expected Behavior

- Only branches whose upstream is reported `gone` are deleted.
- Branches with no upstream at all are left alone — never pushed is not the same
  as remote deleted, and they are the ones most likely to hold unpushed work.
- Worktrees holding a gone branch are removed first; stale worktree entries whose
  directory no longer exists are pruned rather than erroring.
- The branch currently checked out in the main working tree is never removed as a
  worktree, so `git branch -D` reports the conflict instead of the repo losing it.

If no branch reports `gone`, report that no cleanup was needed.

## Common Mistakes

| Mistake | Why it bites |
|---|---|
| `git branch -v \| grep '\[gone\]'` | Also matches any branch whose commit subject contains `[gone]`, then `-D` force-deletes it. |
| Same grep against `git branch -vv` | `-vv` prints `[origin/name: gone]`, so the pattern matches nothing and the command silently reports "nothing to clean". |
| Skipping `git fetch --prune` | Branches deleted on the remote still look alive; the command finds nothing. |
| `git worktree list \| awk '{print $1}'` | Truncates any worktree path containing a space. |
| `git worktree remove` before `prune` | Fails on an entry whose directory was deleted, leaving the branch behind. |

