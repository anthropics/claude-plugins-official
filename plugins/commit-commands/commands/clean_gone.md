---
description: Cleans up all git branches marked as [gone] (branches that have been deleted on the remote but still exist locally), including removing associated worktrees.
---

## Your Task

Clean up stale local branches whose remote counterpart has been deleted, and remove
their worktrees — while refusing to destroy unsaved work or the worktree you are
currently running in.

## Commands to Execute

1. **Refresh the remote-tracking refs.** The `gone` marker only appears after a prune,
   so without this the cleanup can report "nothing to do" for a stale reason.
   ```bash
   git fetch --prune
   ```

2. **List branches with their upstream tracking info.**
   ```bash
   git branch -vv
   ```

   Notes on reading this output:
   - `-vv` (two v's) is required. Plain `git branch -v` does **not** print upstream
     tracking info at all, so no `gone` marker can ever appear in it.
   - Git prints the upstream inside the brackets as
     `[origin/my-branch: gone]` — so the matchable substring is `: gone]`,
     **not** `[gone]`.
   - A `+` prefix means the branch is checked out in a worktree; its worktree must be
     removed before the branch can be deleted.

3. **List worktrees.**
   ```bash
   git worktree list
   ```

4. **Remove worktrees and delete the gone branches.**
   ```bash
   set -u

   current_branch=$(git rev-parse --abbrev-ref HEAD)
   here=$(git rev-parse --show-toplevel)
   main_wt=$(cd "$(git rev-parse --git-common-dir)/.." && pwd)

   branches=$(git branch -vv | grep ': gone]' | sed 's/^[+* ]*//' | awk '{print $1}')

   if [ -z "$branches" ]; then
     echo "No branches are marked as gone. Nothing to clean up."
   fi

   for branch in $branches; do
     echo "Processing branch: $branch"

     # Guard 1: never delete the branch this session is running on — removing its
     # worktree would destroy the live working directory mid-run.
     if [ "$branch" = "$current_branch" ]; then
       echo "  SKIP: currently checked out in this worktree ($here)"
       continue
     fi

     # Robust worktree lookup: exact ref match, so branch names that are substrings
     # of each other cannot cross-match.
     wt=$(git worktree list --porcelain | awk -v b="refs/heads/$branch" '/^worktree /{w=$2} /^branch /{if ($2==b) print w}')

     if [ -n "$wt" ]; then
       if [ "$wt" = "$here" ] || [ "$wt" = "$main_wt" ]; then
         echo "  SKIP: worktree is the current or main worktree ($wt)"
         continue
       fi

       # Guard 2: a gone remote does NOT mean the local worktree has nothing unsaved.
       dirty=$(git -C "$wt" status --porcelain)
       if [ -n "$dirty" ]; then
         echo "  SKIP: worktree has uncommitted changes ($wt)"
         echo "$dirty" | sed 's/^/      /'
         continue
       fi

       # Unpushed commits. The upstream ref is usually already pruned away, so fall
       # back to the remote's default branch as the comparison base.
       unpushed=$(git -C "$wt" log --oneline '@{u}..HEAD' 2>/dev/null) || unpushed=""
       if [ -z "$unpushed" ]; then
         base=$(git -C "$wt" symbolic-ref -q --short refs/remotes/origin/HEAD || echo origin/main)
         unpushed=$(git -C "$wt" log --oneline "$base..HEAD" 2>/dev/null) || unpushed=""
       fi
       if [ -n "$unpushed" ]; then
         echo "  SKIP: worktree has commits not on the remote ($wt)"
         echo "$unpushed" | sed 's/^/      /'
         continue
       fi

       echo "  Removing worktree: $wt"
       git worktree remove "$wt" || { echo "  SKIP: worktree removal failed"; continue; }
     fi

     echo "  Deleting branch: $branch"
     git branch -D "$branch"
   done
   ```

## Expected Behavior

After executing these commands, you will:

- See every local branch with its upstream tracking state
- Remove the worktrees of branches whose remote is gone
- Delete those branches
- Report per branch what was removed, and **explicitly report anything that was
  skipped and why**

Report the skipped branches to the user — do not silently swallow them. Skips are
intentional and each needs a human decision:

- **currently checked out in this worktree** — the session's own branch was merged and
  pruned. Clean it from a different worktree, or after the session ends.
- **uncommitted changes** / **commits not on the remote** — there is unsaved work. The
  user must commit, push, or knowingly discard it, then re-run. If the branch was
  *squash*-merged, its individual commits legitimately do not exist on the remote and
  will always look unpushed; in that case removing it by hand
  (`git worktree remove --force <path> && git branch -D <branch>`) is the way forward.

If no branches are marked as gone, report that no cleanup was needed.
