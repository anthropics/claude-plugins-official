---
description: Cleans up all git branches marked as [gone] (branches that have been deleted on the remote but still exist locally), including removing associated worktrees.
---

## Your Task

You need to execute the following bash commands to clean up stale local branches that have been deleted from the remote repository.

## Commands to Execute

1. **First, prune stale remote refs, then list branches to identify any with [gone] status**
   Execute this command:
   ```bash
   git fetch --prune
   git branch -vv
   ```

   Note: `git fetch --prune` deletes remote-tracking refs whose upstream is
   gone — without it, no branch is annotated `[gone]` yet. The `[gone]` marker
   is part of the upstream-tracking info, so it only appears under `-vv` (two
   v's), not `-v`. Branches with a `+` prefix have an associated worktree,
   which must be removed before the branch can be deleted.

2. **Next, identify worktrees that need to be removed for [gone] branches**
   Execute this command:
   ```bash
   git worktree list
   ```

3. **Finally, remove worktrees and delete [gone] branches (handles both regular and worktree branches)**
   Execute this command:
   ```bash
   # Process all [gone] branches, stripping any leading '+'/'*'/space markers.
   # Git annotates a deleted upstream as "[<upstream-name>: gone]", so the
   # branch name and the word "gone" are NOT adjacent — the pattern must match
   # ": gone]", not "[gone]". The marker also only shows under "git branch -vv".
   git branch -vv | grep ': gone\]' | sed 's/^[+* ]*//' | awk '{print $1}' | while read branch; do
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

- See a list of all local branches with their status
- Identify and remove any worktrees associated with [gone] branches
- Delete all branches marked as [gone]
- Provide feedback on which worktrees and branches were removed

If no branches are marked as [gone], report that no cleanup was needed.

