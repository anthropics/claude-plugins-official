---
description: Cleans up all git branches marked as [gone] (branches that have been deleted on the remote but still exist locally), including removing associated worktrees.
---

## Your Task

You need to execute the following bash commands to clean up stale local branches whose upstream remote branch has been deleted (typically after a PR is merged).

IMPORTANT: A branch only reports `[gone]` after its stale remote-tracking ref is pruned locally, and only `git branch -vv` (two v's) shows the gone marker — `git branch -v` (one v) never does. The marker looks like `[origin/foo: gone]`, so grep for `: gone]`, not `[gone]`.

## Commands to Execute

1. **First, prune stale remote-tracking refs so merged/deleted branches surface as [gone]**
   Execute this command (needs network access to the remote):
   ```bash
   git fetch --prune 2>&1 || echo "WARN: fetch --prune failed (offline?) — relying on already-pruned state"
   ```

   Note: This only removes stale remote-tracking refs (refs/remotes/origin/*). It does not touch any local branch or working tree.

2. **Next, list branches to see which are now [gone], and list worktrees**
   Execute these commands:
   ```bash
   git branch -vv
   git worktree list
   ```

   Note: Branches with a `+` prefix have an associated worktree that must be removed before the branch can be deleted.

3. **Finally, for each [gone] branch: warn if unmerged, remove its worktree, delete the branch**
   Execute this command:
   ```bash
   # A [gone] branch's marker is `[origin/xxx: gone]` — detect with `git branch -vv` and
   # grep ': gone]'. Strip the leading status column (*, +, or space) before the name.

   # Determine the default branch so we can warn about unmerged work before force-deleting.
   default_branch=$(git symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')

   git branch -vv | grep ': gone\]' | sed 's/^[*+ ]*//' | awk '{print $1}' | while read branch; do
     echo "Processing branch: $branch"

     # A [gone] branch is NOT guaranteed to be merged (the remote branch could have been
     # deleted without merging). Warn before force-deleting potentially unmerged work.
     if [ -n "$default_branch" ] && git rev-parse --verify -q "origin/$default_branch" >/dev/null; then
       if ! git merge-base --is-ancestor "$branch" "origin/$default_branch"; then
         echo "  WARNING: '$branch' is NOT merged into origin/$default_branch — its commits will be lost on deletion."
       fi
     fi

     # Remove the associated worktree if one exists (never the main worktree).
     worktree=$(git worktree list | grep "\\[$branch\\]" | awk '{print $1}')
     if [ -n "$worktree" ] && [ "$worktree" != "$(git rev-parse --show-toplevel)" ]; then
       echo "  Removing worktree: $worktree"
       git worktree remove --force "$worktree"
     fi

     echo "  Deleting branch: $branch"
     git branch -D "$branch"
   done
   ```

## Expected Behavior

After executing these commands, you will:

- Prune stale remote-tracking refs so recently-merged branches surface as `[gone]`
- See all local branches with upstream/gone status and all worktrees
- Warn about any `[gone]` branch that is not merged into the default branch (unmerged commits would be lost)
- Remove any worktrees associated with `[gone]` branches, then delete those branches
- Provide feedback on which worktrees and branches were removed

If no branches are marked as `[gone]` after pruning, report that no cleanup was needed.
