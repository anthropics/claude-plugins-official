---
description: Cleans up all git branches marked as [gone] (branches that have been deleted on the remote but still exist locally), including removing associated worktrees.
---

## Your Task

You need to execute the following bash commands to clean up stale local branches that have been deleted from the remote repository.

## Commands to Execute

1. **First, list branches to identify any with [gone] status**
   Execute this command:
   ```bash
   git branch -vv
   ```

   Note: `-vv` (not `-v`) is required — the upstream-tracking column that
   carries the `[gone]` marker is only printed at the second level of verbosity.
   
   Note: Branches with a '+' prefix have associated worktrees and must have their worktrees removed before deletion.

2. **Next, identify worktrees that need to be removed for [gone] branches**
   Execute this command:
   ```bash
   git worktree list
   ```

3. **Finally, delete the [gone] branches whose work is already merged**
   Execute this command:
   ```bash
   # Resolve the default branch rather than assuming 'main'.
   default=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')
   default=${default:-main}
   echo "Checking [gone] branches against '$default'"

   while read -r branch; do
     [ -z "$branch" ] && continue
     echo "Processing branch: $branch"

     # Is this branch's work already in the default branch? Two ways it can be.
     # An ordinary merge leaves its commits reachable, which --is-ancestor sees.
     # A squash or rebase merge does not: no commit survives verbatim, so the
     # branch looks unmerged to every commit-based test. That is the common case
     # on GitHub, and it is exactly why `git branch -d` alone is not enough here.
     # The second test compares CONTENT: replay the branch's tree onto the merge
     # base as a throwaway commit and ask whether that patch is already upstream.
     merged=no
     if git merge-base --is-ancestor "$branch" "$default" 2>/dev/null; then
       merged=yes
     else
       base=$(git merge-base "$default" "$branch" 2>/dev/null)
       if [ -n "$base" ]; then
         tree=$(git rev-parse "$branch^{tree}")
         probe=$(git commit-tree "$tree" -p "$base" -m _)
         git cherry "$default" "$probe" | grep -q '^-' && merged=yes
       fi
     fi

     if [ "$merged" != yes ]; then
       echo "  SKIPPED - holds work not in '$default'. Inspect it, then delete by hand:"
       echo "      git log $default..$branch"
       echo "      git branch -D $branch"
       continue
     fi

     # Only now is force-deleting safe: the work is provably upstream.
     worktree=$(git worktree list | grep "\[$branch\]" | awk '{print $1}')
     if [ -n "$worktree" ] && [ "$worktree" != "$(git rev-parse --show-toplevel)" ]; then
       echo "  Removing worktree: $worktree"
       git worktree remove --force "$worktree"
     fi
     echo "  Deleting branch: $branch"
     git branch -D "$branch"
   done < <(git branch -vv | grep '\[[^]]*: gone\]' | sed 's/^[+* ]//' | awk '{print $1}')
   ```

## Expected Behavior

After executing these commands, you will:

- See a list of all local branches with their upstream status
- Delete each [gone] branch whose work is already in the default branch, by
  ordinary merge or by squash/rebase merge, removing any worktree first
- **Skip** any [gone] branch holding work that is not upstream, and print the
  commands to inspect and delete it by hand
- Provide feedback on which worktrees and branches were removed, and which were
  skipped and why

If no branches are marked as [gone], report that no cleanup was needed.

Note: a branch is only marked [gone] after the deleted remote branch has been
pruned locally. If you expect one and do not see it, run `git fetch --prune`
first.
