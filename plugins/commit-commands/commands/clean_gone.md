---
description: Cleans up all git branches whose upstream is gone (branches that have been deleted on the remote but still exist locally), including removing associated worktrees.
---

## Your Task

You need to execute the following bash commands to clean up stale local branches that have been deleted from the remote repository.

## Commands to Execute

1. **First, refresh the remote state.** Without this, git still considers deleted remote branches to exist and nothing is reported as gone.
   Execute this command:
   ```bash
   git fetch --prune
   ```

2. **Next, list branches to identify any whose upstream is gone**
   Execute this command:
   ```bash
   git branch -vv | grep ': gone\]'
   ```

   Note: `-vv` is required — the single `-v` form does not print upstream tracking information at all. The marker git writes is `[origin/<branch>: gone]`, so the pattern must match `: gone]`.

   Note: Branches with a '+' prefix have associated worktrees and must have their worktrees removed before deletion. Branches with no upstream at all (never pushed) do not appear here and are left untouched.

3. **Next, identify worktrees that need to be removed for gone branches**
   Execute this command:
   ```bash
   git worktree list
   ```

4. **Finally, remove worktrees and delete the gone branches (handles both regular and worktree branches)**
   Execute this command:
   ```bash
   # Process all branches whose upstream is gone, removing '+' prefix if present
   git branch -vv | grep ': gone\]' | sed 's/^[+* ]//' | awk '{print $1}' | while read branch; do
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

- See a list of local branches whose upstream no longer exists
- Identify and remove any worktrees associated with those branches
- Delete them
- Provide feedback on which worktrees and branches were removed

If no branches have a gone upstream, report that no cleanup was needed.

