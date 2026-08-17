---
description: Cleans up all git branches marked as [gone] (branches that have been deleted on the remote but still exist locally), including removing associated worktrees.
---

## Your Task

Clean up stale local branches whose remote tracking branch has been deleted.

**Deleting branches is destructive.** Follow the verification steps before the deletion step — do not skip ahead to step 5.

## Commands to Execute

1. **Refresh remote state first.** `[gone]` status is only accurate after a prune; without this you will both miss newly-deleted branches and act on stale information.
   ```bash
   git fetch --prune
   ```

2. **List branches with their tracking status**
   ```bash
   git branch -vv
   ```

   Notes on reading this output:
   - The `gone` marker renders differently per verbosity, so the filter must match the flag: `git branch -v` prints the short `[gone]`, while `git branch -vv` prints `[origin/<name>: gone]`. This file uses `-vv` (it names the missing upstream, which is useful context) and therefore filters on `grep '\[[^]]*: gone\]'`.
   - A `+` prefix means the branch is checked out in a worktree; `*` means it is the current branch.

3. **List worktrees**
   ```bash
   git worktree list
   ```

4. **Verify each gone branch is safe to delete.** A branch being `[gone]` means only that its upstream vanished — not that its work landed. Classify every candidate before deleting anything.
   ```bash
   PROTECTED='^(main|master|dev|develop|stage|staging|prod|production|release)$'
   BASES="origin/main origin/master origin/dev origin/develop"   # adjust to this repo's long-lived branches

   git branch -vv | grep '\[[^]]*: gone\]' | sed 's/^[+* ]*//' | awk '{print $1}' | while read -r branch; do
     merged_into=''
     for base in $BASES; do
       git rev-parse --verify "$base" >/dev/null 2>&1 || continue
       if git merge-base --is-ancestor "$branch" "$base"; then merged_into="$base"; break; fi
     done
     pr=$(gh pr list --head "$branch" --state merged --json number -q '.[0].number' 2>/dev/null)

     if echo "$branch" | grep -qE "$PROTECTED"; then
       echo "PROTECTED  $branch  — promotion/long-lived branch, do NOT auto-delete"
     elif [ -n "$merged_into" ]; then
       echo "MERGED     $branch  — ancestor of $merged_into, safe"
     elif [ -n "$pr" ]; then
       echo "SQUASHED   $branch  — merged via PR #$pr, safe"
     else
       echo "UNVERIFIED $branch  — no merge evidence, needs your review"
     fi
   done
   ```

   `git branch -d` is not usable as a safety probe here: it has no `--dry-run`, and under a squash-merge workflow it rejects branches whose work did land. Use the ancestry test above, with the merged-PR lookup as the squash-merge fallback.

   Then:
   - **MERGED / SQUASHED** — safe to delete in step 5.
   - **PROTECTED** — never delete automatically. A missing `origin/stage` usually means that environment is not provisioned yet, not that the branch is retired. Report it and let the user decide.
   - **UNVERIFIED** — stop and ask the user. Show `git log <base>..<branch> --oneline` so they can see what would be lost.

   Note that a non-empty `git diff <base> <branch>` does **not** indicate unique work — the base has moved ahead independently. Use merge evidence, not diff size.

5. **Delete the verified-safe branches, removing their worktrees first.** Substitute the MERGED/SQUASHED branches from step 4 into `SAFE`.
   ```bash
   SAFE="branch-one branch-two"   # from step 4 only
   MAIN_WORKTREE=$(git worktree list | head -1 | awk '{print $1}')

   for branch in $SAFE; do
     echo "Processing branch: $branch"
     worktree=$(git worktree list | grep -F "[$branch]" | awk '{print $1}')
     if [ -n "$worktree" ] && [ "$worktree" != "$MAIN_WORKTREE" ]; then
       echo "  Removing worktree: $worktree"
       git worktree remove --force "$worktree"
     fi
     echo "  Deleting branch: $branch"
     git branch -D "$branch"
   done
   ```

   The main-worktree guard compares against the first entry of `git worktree list`, not `git rev-parse --show-toplevel` — the latter resolves to whichever worktree you happen to be standing in, which would let the real main worktree be removed.

## Expected Behavior

- Remote state is pruned so `[gone]` reflects reality
- Every gone branch is classified as merged, squash-merged, protected, or unverified
- Only merged/squash-merged branches are deleted, along with their worktrees
- Protected and unverified branches are reported to the user for an explicit decision, never deleted silently

If no branches are marked as `[gone]`, report that no cleanup was needed.
