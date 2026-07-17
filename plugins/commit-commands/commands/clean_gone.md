---
description: Cleans up all git branches marked as [gone] (branches that have been deleted on the remote but still exist locally), including removing associated worktrees.
---

## Your Task

You need to execute the following bash commands to clean up stale local branches that have been deleted from the remote repository.

## Commands to Execute

1. **First, prune deleted remote branches so [gone] status is current**
   Execute this command:
   ```bash
   git fetch --prune
   ```

2. **Next, list branches with tracking status to identify any marked [gone]**
   Execute this command:
   ```bash
   git branch -vv
   ```

   Note: `-vv` is required — plain `-v` does not print upstream tracking status. Branches with a '+' prefix have associated worktrees and must have their worktrees removed before deletion. The gone marker appears as `[origin/<branch>: gone]`.

3. **Next, identify worktrees that may need to be removed for [gone] branches**
   Execute this command:
   ```bash
   git worktree list
   ```

4. **Finally, remove worktrees and delete [gone] branches (handles both regular and worktree branches)**
   Execute this command:
   ```bash
   # for-each-ref emits exactly "[gone]" for a deleted upstream — no fragile
   # parsing of `git branch` porcelain output.
   git for-each-ref --format='%(refname:short)%09%(upstream:track)' refs/heads |
   awk -F'\t' '$2=="[gone]"{print $1}' | while read -r branch; do
     echo "Processing branch: $branch"
     # Find the worktree checked out on this branch, if any (porcelain format
     # is stable and handles paths with spaces).
     worktree=$(git worktree list --porcelain | awk -v b="refs/heads/$branch" '
       /^worktree /{w=substr($0,10)} $0=="branch "b{print w}')
     if [ -n "$worktree" ] && [ "$worktree" != "$(git rev-parse --show-toplevel)" ]; then
       if [ -n "$(git -C "$worktree" status --porcelain 2>/dev/null)" ]; then
         echo "  SKIPPING $branch: worktree $worktree has uncommitted or untracked changes"
         continue
       fi
       echo "  Removing worktree: $worktree"
       git worktree remove "$worktree" || { echo "  worktree removal failed; skipping branch"; continue; }
     fi
     echo "  Deleting branch: $branch"
     git branch -D "$branch"
   done
   git worktree prune
   ```

## Expected Behavior

After executing these commands, you will:

- See a list of all local branches with their tracking status
- Identify and remove any clean worktrees associated with [gone] branches
- Delete all branches marked as [gone] whose worktrees (if any) were clean
- Report any branches skipped because their worktree held uncommitted or untracked changes — surface these to the user instead of force-deleting their work
- Provide feedback on which worktrees and branches were removed

If no branches are marked as [gone], report that no cleanup was needed.
