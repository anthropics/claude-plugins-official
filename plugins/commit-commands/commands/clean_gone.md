---
description: Cleans up all git branches marked as [gone] (branches that have been deleted on the remote but still exist locally), including removing associated worktrees.
---

## Your Task

You need to execute the following bash commands to clean up stale local branches that have been deleted from the remote repository.

## Commands to Execute

1. **First, refresh remote-tracking refs so [gone] status is accurate**
   Execute this command:
   ```bash
   git fetch --all --prune
   ```

   This is required. A branch is only marked [gone] once its stale remote-tracking
   ref has been pruned. Without this step, branches deleted on the remote still
   look alive locally and the cleanup below silently finds nothing.

2. **Next, list branches to identify any with [gone] status**
   Execute this command:
   ```bash
   git branch -v
   ```
   
   Note: Branches with a '+' prefix have associated worktrees and must have their worktrees removed before deletion.

   Note: use `-v`, not `-vv`. `-v` renders the marker as `[gone]`, which is what the
   grep below matches; `-vv` renders it as `[origin/<branch>: gone]` and would not match.

3. **Next, identify worktrees that need to be removed for [gone] branches**
   Execute this command:
   ```bash
   git worktree list
   ```

4. **Finally, remove worktrees and delete [gone] branches (handles both regular and worktree branches)**
   Execute this command:
   ```bash
   # Process all [gone] branches, removing '+' prefix if present
   git branch -v | grep '\[gone\]' | sed 's/^[+* ]//' | awk '{print $1}' | while read branch; do
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

- Prune stale remote-tracking refs so [gone] status reflects the real remote
- See a list of all local branches with their status
- Identify and remove any worktrees associated with [gone] branches
- Delete all branches marked as [gone]
- Provide feedback on which worktrees and branches were removed

If no branches are marked as [gone], report that no cleanup was needed.

