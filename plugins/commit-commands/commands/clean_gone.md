---
description: Cleans up all git branches marked as [gone] (branches that have been deleted on the remote but still exist locally), including removing associated worktrees.
---

## Your Task

You need to execute the following bash commands to clean up stale local branches that have been deleted from the remote repository.

## Commands to Execute

1. **First, refresh remote-tracking refs and list branches with their upstream status**
   Execute this command:
   ```bash
   git fetch --prune
   git branch -vv
   ```

   Notes:
   - `git fetch --prune` deletes stale remote-tracking refs so the `[gone]` status is accurate. Without it, a branch deleted on the remote since the last fetch is not yet flagged `[gone]`, and the cleanup silently misses it.
   - The `[<upstream>: gone]` marker only appears with `git branch -vv` (two `v`s). Plain `git branch -v` (one `v`) never shows upstream/gone status.
   - Branches with a '+' prefix have associated worktrees and must have their worktrees removed before deletion.

2. **Next, identify worktrees that need to be removed for [gone] branches**
   Execute this command:
   ```bash
   git worktree list
   ```

3. **Finally, remove worktrees and delete [gone] branches (handles both regular and worktree branches)**
   Execute this command:
   ```bash
   # Step 1's `git fetch --prune` must have run first so [gone] is accurate.
   # Process all [gone] branches (matched via the `-vv` "[<upstream>: gone]"
   # marker), removing any '+'/'*' prefix.
   git branch -vv | grep ': gone]' | sed 's/^[+* ]//' | awk '{print $1}' | while read branch; do
     echo "Processing branch: $branch"
     # Find and remove worktree if it exists
     worktree=$(git worktree list | grep "\\[$branch\\]" | awk '{print $1}')
     if [ ! -z "$worktree" ] && [ "$worktree" != "$(git rev-parse --show-toplevel)" ]; then
       echo "  Removing worktree: $worktree"
       git worktree remove --force "$worktree"
     fi
     # Delete the branch
     echo "  Deleting branch: $branch"
     git branch -D "$branch"
   done
   ```

## Expected Behavior

After executing these commands, you will:

- Prune stale remote-tracking refs so the `[gone]` detection reflects the current remote
- See a list of all local branches with their upstream (`-vv`) status
- Identify and remove any worktrees associated with [gone] branches
- Delete all branches marked as [gone]
- Provide feedback on which worktrees and branches were removed

If no branches are marked as [gone], report that no cleanup was needed.

