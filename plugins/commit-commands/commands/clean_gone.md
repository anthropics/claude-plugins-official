---
description: Cleans up all git branches marked as [gone] (branches that have been deleted on the remote but still exist locally), including removing associated worktrees.
---

## Your Task

You need to execute the following bash commands to clean up stale local branches that have been deleted from the remote repository.

## Commands to Execute

1. **First, prune stale remote-tracking refs, then list branches to identify any with [gone] status**
   Execute this command:
   ```bash
   git fetch --prune origin && git branch -v
   ```

   The `--prune` step is required: branches deleted on the remote (e.g. by GitHub's auto-delete-after-merge) only show up as `[gone]` locally after `git fetch --prune` updates the remote-tracking refs. Without it, deleted branches still appear as `[behind N]` and the cleanup loop below silently skips them.

   Note: Branches with a '+' prefix have associated worktrees and must have their worktrees removed before deletion.

2. **Next, identify worktrees that need to be removed for [gone] branches**
   Execute this command:
   ```bash
   git worktree list
   ```

3. **Finally, remove worktrees and delete [gone] branches (handles both regular and worktree branches)**
   Execute this command:
   ```bash
   # Process all [gone] branches, removing '+' / '*' / ' ' prefix marker if present.
   # Notes:
   #   - We use `read -r branch _` instead of `awk '{print $1}'` because the slash-command
   #     harness substitutes `$1` (positional arg) and would strip it from the rendered prompt.
   #   - We parse `git worktree list --porcelain` instead of plain `git worktree list`
   #     because the plain output is space-separated and breaks on worktree paths
   #     containing spaces (e.g. "/Users/me/My Project/...").
   git branch -v | grep '\[gone\]' | sed 's/^[+* ]//' | while read -r branch _; do
     echo "Processing branch: $branch"
     # Find the worktree (if any) for this branch using porcelain output.
     # Porcelain emits 3-line records: `worktree <path>`, `HEAD <sha>`, `branch refs/heads/<name>`.
     worktree=$(git worktree list --porcelain | grep -B 2 "^branch refs/heads/${branch}$" | sed -n 's/^worktree //p')
     if [ -n "$worktree" ] && [ "$worktree" != "$(git rev-parse --show-toplevel)" ]; then
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

