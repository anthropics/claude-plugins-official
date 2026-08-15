---
description: Cleans up all git branches marked as [gone] (branches that have been deleted on the remote but still exist locally), including removing associated worktrees.
---

## Your Task

You need to execute the following bash commands to clean up stale local branches that have been deleted from the remote repository.

## Commands to Execute

1. **First, refresh the remote-tracking refs so `[gone]` is accurate**
   Execute this command:
   ```bash
   git fetch --prune
   ```

   This step is load-bearing, not hygiene. A branch deleted on the remote by
   someone else (GitHub's delete-on-merge, a teammate) keeps a live-looking
   upstream locally until its remote-tracking ref is pruned, so `[gone]` does
   not appear and every command below finds nothing. Skipping this makes the
   whole command report "no cleanup was needed" while stale branches sit there.
   (`git push origin --delete` from *this* clone prunes as a side effect, which
   is why the gap is easy to miss when testing locally.)

2. **Next, list branches to identify any with [gone] status**
   Execute this command:
   ```bash
   git branch -v
   ```

   Note: `*` marks the branch checked out here; `+` marks a branch held by
   another worktree. Both must be handled before the branch can be deleted.
   Use `git branch -v` (not `-vv`) with the `[gone]` pattern below — `-vv`
   prints `[origin/<branch>: gone]` instead, which that pattern will not match.

3. **Next, identify worktrees that need to be removed for [gone] branches**
   Execute this command:
   ```bash
   git worktree list
   ```

4. **Finally, remove worktrees and delete [gone] branches**
   Execute this command:
   ```bash
   ROOT=$(git rev-parse --show-toplevel)
   CURRENT=$(git branch --show-current)
   DEFAULT=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')
   DEFAULT=${DEFAULT:-main}
   failed=0
   cleaned=0

   # Input redirection, not a pipe: a `while` on the right of a pipe runs in a
   # subshell, and the counters below would be discarded when it exits.
   while read -r branch; do
     [ -z "$branch" ] && continue
     echo "Processing branch: $branch"
     sha=$(git rev-parse --short "$branch")

     # Locate a holding worktree via --porcelain. `git worktree list | awk '{print $1}'`
     # truncates any path containing a space, so the removal silently targets a
     # path that does not exist and the branch delete then fails.
     wt=$(git worktree list --porcelain | awk -v b="branch refs/heads/$branch" '
            /^worktree /{p=substr($0,10)} $0==b{print p}')
     if [ -n "$wt" ] && [ "$wt" != "$ROOT" ]; then
       echo "  removing worktree: $wt"
       if ! git worktree remove --force "$wt"; then
         echo "  ✗ worktree removal FAILED — leaving $branch in place"
         failed=$((failed + 1)); continue
       fi
     fi

     # A branch checked out in THIS worktree cannot be deleted. Step off it
     # first — but never discard uncommitted work to do so.
     if [ "$branch" = "$CURRENT" ]; then
       if [ -n "$(git status --porcelain)" ]; then
         echo "  ✗ SKIP: checked out here and the tree is dirty — commit or stash, then re-run"
         failed=$((failed + 1)); continue
       fi
       echo "  checked out here — switching to $DEFAULT first"
       if ! git switch "$DEFAULT"; then
         echo "  ✗ could not switch off $branch"
         failed=$((failed + 1)); continue
       fi
       CURRENT="$DEFAULT"
     fi

     # -D, not -d: a squash-merged branch is not an ancestor of the default
     # branch, so -d refuses exactly the branches this command exists to clean.
     # The sha is printed so any surprise is recoverable.
     if git branch -D "$branch"; then
       echo "  ✓ deleted $branch ($sha) — recover with: git branch $branch $sha"
       cleaned=$((cleaned + 1))
     else
       echo "  ✗ FAILED to delete $branch"
       failed=$((failed + 1))
     fi
   done < <(git branch -v | grep '\[gone\]' | sed 's/^[+* ]*//' | awk '{print $1}')

   echo "----"
   echo "cleaned: $cleaned   failed: $failed"
   [ "$failed" -eq 0 ] || echo "✗ some [gone] branches were NOT removed — see above"
   ```

## Expected Behavior

After executing these commands, you will:

- Refresh remote-tracking refs so `[gone]` reflects the remote's actual state
- See a list of all local branches with their status
- Identify and remove any worktrees associated with [gone] branches
- Delete the [gone] branches, printing each deleted sha so it can be restored
- Get an explicit `cleaned` / `failed` tally

If no branches are marked as [gone] **after the fetch in step 1**, report that no
cleanup was needed. Do not report success from a run that skipped the fetch —
that is indistinguishable from having nothing to clean.

Report any branch in the `failed` tally to the user rather than treating a
zero exit code as success; the loop deliberately continues past a failure so one
stuck branch does not block the rest.
