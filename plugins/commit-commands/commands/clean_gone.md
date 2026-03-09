---
description: Cleans up all git branches marked as [gone] (branches that have been deleted on the remote but still exist locally), including removing associated worktrees.
---

## Your Task

You need to execute the following bash commands to clean up stale local branches that have been deleted from the remote repository.

## Commands to Execute

1. **First, update remote tracking info to detect deleted remote branches**
   Execute this command:
   ```bash
   git fetch --prune
   ```

2. **Next, list branches to identify any with [gone] status**
   Execute this command:
   ```bash
   git branch -v
   ```

   Note: Branches with a '+' prefix have associated worktrees and must have their worktrees removed before deletion.

3. **Then, identify worktrees that need to be removed for [gone] branches**
   Execute this command:
   ```bash
   git worktree list
   ```

4. **If the current branch is [gone], switch to the default branch first**
   Execute this command:
   ```bash
   current=$(git branch --show-current)
   if git branch -v | grep "^\* " | grep -q '\[gone\]'; then
     default=$(git remote show origin | grep 'HEAD branch' | awk '{print $NF}')
     echo "Current branch '$current' is [gone]. Switching to '$default'..."
     git switch "$default"
     git pull --ff-only
   fi
   ```

5. **Finally, remove worktrees and delete [gone] branches (handles both regular and worktree branches)**
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

- Prune stale remote-tracking references so `[gone]` branches are properly detected
- See a list of all local branches with their status
- If the current branch is `[gone]`, safely switch to the default branch first
- Identify and remove any worktrees associated with [gone] branches
- Delete all branches marked as [gone]
- Provide feedback on which worktrees and branches were removed

If no branches are marked as [gone], report that no cleanup was needed.
