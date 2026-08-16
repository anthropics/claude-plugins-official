---
description: Cleans up all git branches marked as [gone] (branches that have been deleted on the remote but still exist locally), including removing associated worktrees.
---

## Your Task

You need to execute the following bash commands to clean up stale local branches that have been deleted from the remote repository.

## Commands to Execute

1. **First, prune stale remote-tracking refs so [gone] status is current**
   Execute this command:
   ```bash
   git fetch --prune
   ```

2. **Next, find all branches whose upstream is gone**
   Execute this command:
   ```bash
   git for-each-ref --format='%(refname:short) %(upstream:track) %(worktreepath)' refs/heads
   ```
   Lines where the second field is `[gone]` are the branches to delete. The third field (if non-empty) is the path of any associated worktree.

3. **Finally, remove worktrees and delete [gone] branches**
   Execute this command:
   ```bash
   git for-each-ref --format='%(refname:short) %(upstream:track) %(worktreepath)' refs/heads \
     | awk '$2 == "[gone]" {print $1, $3}' \
     | while read branch worktree; do
         echo "Processing: $branch"
         # Remove worktree first (without --force to protect uncommitted changes)
         if [ -n "$worktree" ]; then
           if git worktree remove "$worktree" 2>/dev/null; then
             echo "  Removed worktree: $worktree"
           else
             echo "  SKIPPED: worktree $worktree has uncommitted changes. Clean it up manually first."
             continue
           fi
         fi
         # Delete with -d (safe: refuses branches with unmerged commits)
         if git branch -d "$branch" 2>/dev/null; then
           echo "  Deleted branch: $branch"
         else
           echo "  SKIPPED: $branch has unmerged commits. Review with: git log --oneline HEAD..$branch"
         fi
       done
   ```

## Expected Behavior

After executing these commands, you will:

- Prune remote-tracking refs so the [gone] status is accurate
- Identify all branches whose upstream has been deleted
- Remove associated worktrees (skipping any with uncommitted changes)
- Delete all [gone] branches (skipping any with unmerged commits)
- Provide feedback on which branches were removed and which were skipped

If no branches are marked as [gone], report that no cleanup was needed.

