---
description: Cleans up all git branches marked as [gone] (branches that have been deleted on the remote but still exist locally), including removing associated worktrees.
---

## Your Task

You need to execute the following bash commands to clean up stale local branches that have been deleted from the remote repository.

**Important:** every `git` invocation below is prefixed with `LC_ALL=C`. Git translates its
tracking-status strings, so on a non-English locale the branch is reported as e.g. `[없음]`
instead of `[gone]` and a naive `grep '\[gone\]'` silently matches nothing while still exiting 0.
Do not drop the `LC_ALL=C` prefix.

## Commands to Execute

1. **First, list branches to identify any with [gone] status**
   Execute this command:
   ```bash
   LC_ALL=C git branch -vv
   ```

   Note: `-vv` (not `-v`) is required — only `-vv` prints the upstream tracking field that
   carries the `: gone]` marker. Branches with a '+' prefix have associated worktrees and must
   have their worktrees removed before deletion.

2. **Next, identify worktrees that need to be removed for [gone] branches**
   Execute this command:
   ```bash
   git worktree list
   ```

3. **Finally, remove worktrees and delete [gone] branches (handles both regular and worktree branches)**
   Execute this command:
   ```bash
   # Collect [gone] branches. LC_ALL=C keeps git's status strings untranslated; -vv exposes them.
   # awk strips the '*' (current) / '+' (worktree) marker column without guessing at padding.
   gone=$(LC_ALL=C git branch -vv \
     | grep '\[[^]]*: gone\]' \
     | awk '{ if ($1 == "*" || $1 == "+") print $2; else print $1 }')

   if [ -z "$gone" ]; then
     echo "No [gone] branches found — nothing to clean up."
   else
     current=$(git rev-parse --abbrev-ref HEAD)
     main_tree=$(git rev-parse --show-toplevel)

     echo "$gone" | while read -r branch; do
       echo "Processing branch: $branch"

       # Refuse to delete the branch we are standing on — `git branch -D` would fail.
       if [ "$branch" = "$current" ]; then
         echo "  SKIPPED: currently checked out. Switch away first (e.g. git switch main), then re-run."
         continue
       fi

       # Record the tip SHA so the deletion stays recoverable (git branch <name> <sha>).
       sha=$(git rev-parse --short "$branch")

       # Exact refname match via porcelain output — robust against regex metacharacters
       # in branch names, unlike grep "\[$branch\]" against the human-readable listing.
       worktree=$(git worktree list --porcelain \
         | awk -v ref="branch refs/heads/$branch" '/^worktree /{wt=$2} $0==ref {print wt}')

       if [ -n "$worktree" ] && [ "$worktree" != "$main_tree" ]; then
         echo "  Removing worktree: $worktree"
         git worktree remove --force "$worktree" || {
           echo "  FAILED to remove worktree — leaving branch $branch in place."
           continue
         }
       fi

       echo "  Deleting branch: $branch (was $sha)"
       git branch -D "$branch"
     done
   fi
   ```

   Note: `-D` (force) rather than `-d` is required because squash-merged branches are not
   ancestors of the target branch, so `-d` reports them as unmerged and refuses. Before
   accepting the deletion, confirm the work really landed by content rather than by ancestry —
   e.g. `git diff <upstream> -- <paths>` coming back empty, or `gh pr view <n> --json state`.
   The printed SHA stays reachable via reflog (default 30 days) if you need to restore a branch.

4. **Verify the cleanup**
   Execute this command:
   ```bash
   LC_ALL=C git branch -vv | grep '\[[^]]*: gone\]' && echo "WARNING: [gone] branches remain" \
     || echo "Clean — no [gone] branches remain."
   git worktree list
   ```

## Expected Behavior

After executing these commands, you will:

- See a list of all local branches with their upstream tracking status
- Identify and remove any worktrees associated with [gone] branches
- Delete all branches marked as [gone], reporting the SHA of each deleted tip
- Skip (with an explicit warning) any [gone] branch that is currently checked out
- Confirm in step 4 that no [gone] branches remain

If no branches are marked as [gone], report that no cleanup was needed. Distinguish this from a
failed match: step 1's output shows the real tracking state, so if it displays a `: gone]` entry
that step 3 did not process, treat that as a bug in the command rather than as "nothing to do".
