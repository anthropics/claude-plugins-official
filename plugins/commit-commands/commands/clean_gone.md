---
description: Cleans up all git branches marked as [gone] (branches that have been deleted on the remote but still exist locally), including removing associated worktrees.
---

## Your Task

Delete local branches whose upstream has been deleted on the remote, along with any worktree holding one.

## Commands to Execute

1. **Prune stale remote-tracking refs first.**
   A branch is marked `[gone]` only once its remote-tracking ref is absent locally. Skip this and a repo
   whose remote branches were all deleted still reports nothing to clean.
   ```bash
   git fetch --prune
   ```

2. **List branches with their upstream status.**
   `-vv` is required: `git branch -v` omits the upstream column entirely, so `[gone]` never appears in it.
   ```bash
   git branch -vv
   ```

   A `+` prefix marks a branch checked out in a worktree; that worktree must go before the branch can.

3. **Verify each `[gone]` branch is already merged, then remove its worktree and delete it.**
   The marker prints as `[origin/<name>: gone]`, so the pattern must match `: gone]` rather than a bare `[gone]`.

   Deletion uses `git branch -D`, which does not check whether the work survived. `-d` is not an option
   here: a squash-merged branch is not an ancestor of `HEAD`, so `-d` refuses every branch this command
   exists to clean. The guard is therefore a content comparison — the files the branch touched must be
   byte-identical between the branch and `HEAD`. A branch that fails is left in place and reported.

   Run this from the integration branch (usually `main`), since `HEAD` is what each branch is compared against.
   ```bash
   git branch -vv | grep ': gone\]' | sed 's/^[+* ]*//' | awk '{print $1}' | while read branch; do
     echo "Processing branch: $branch"

     # Is the branch's work already in HEAD? Compare only the paths it touched.
     base=$(git merge-base HEAD "$branch")
     if git diff --quiet "$base" "$branch"; then
       echo "  verified: adds nothing beyond the merge base"
     elif git diff --quiet HEAD "$branch" -- $(git diff --name-only "$base" "$branch"); then
       echo "  verified: touched files are identical in HEAD"
     else
       echo "  SKIPPED: carries content not in HEAD — delete by hand after reviewing"
       continue
     fi

     # Find and remove worktree if it exists
     worktree=$(git worktree list | grep "\\[$branch\\]" | awk '{print $1}')
     if [ ! -z "$worktree" ] && [ "$worktree" != "$(git rev-parse --show-toplevel)" ]; then
       echo "  Removing worktree: $worktree"
       git worktree remove --force "$worktree"
     fi

     echo "  Deleting branch: $branch"
     git branch -D "$branch"
   done
   ```

## Expected Behavior

Report which worktrees and branches were removed, and list any branch the guard skipped along with the
reason — a skip is the interesting result, so surface it rather than burying it in the log.

If no branches are marked `[gone]`, report that no cleanup was needed, and say whether step 1 pruned
anything, so "the repo was already clean" is distinguishable from "the refs were stale until just now".
