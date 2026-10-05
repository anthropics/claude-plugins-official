---
description: Cleans up all git branches marked as [gone] (branches that have been deleted on the remote but still exist locally), including removing associated worktrees.
---

## Your Task

Delete local branches whose upstream has been deleted on the remote, along with any
worktrees holding them.

Two of these steps protect work that cannot be recovered afterwards. Read the
**Safety** section before changing them.

## Commands to Execute

1. **Prune remote-tracking refs first.**

   ```bash
   git fetch --all --prune
   ```

   A branch is not reported as gone until the remote-tracking ref it follows has been
   removed locally. Without this step a branch whose PR merged minutes ago still looks
   healthy, and the command reports "no cleanup needed" having found nothing.

2. **List the gone branches, so everything is visible before anything is deleted.**

   ```bash
   git for-each-ref --format='%(refname:short) %(upstream:track)' refs/heads | grep '\[gone\]'
   ```

   `git branch -v` also prints a bare `[gone]` and works with this grep, but
   `git branch -vv` prints `[<remote>/<name>: gone]`, which this pattern does **not**
   match — so "upgrading" `-v` to `-vv` makes the command silently find nothing and
   report success. `%(upstream:track)` emits a literal `[gone]` either way.

3. **List worktrees**, so branches checked out elsewhere can be released before deletion.

   ```bash
   git worktree list
   ```

4. **Remove the worktrees and delete the branches.**

   ```bash
   current=$(git symbolic-ref --quiet --short HEAD || echo "")
   git for-each-ref --format='%(refname:short) %(upstream:track)' refs/heads \
     | grep '\[gone\]' | cut -d' ' -f1 | while read -r branch; do
       if [ "$branch" = "$current" ]; then
         echo "SKIP $branch: it is the branch you are on"
         continue
       fi
       echo "Processing branch: $branch"
       worktree=$(git worktree list | grep "\[$branch\]" | cut -d' ' -f1)
       if [ -n "$worktree" ] && [ "$worktree" != "$(git rev-parse --show-toplevel)" ]; then
         dirty=$(git -C "$worktree" status --porcelain 2>/dev/null | wc -l)
         if [ "$dirty" -gt 0 ]; then
           echo "  SKIP $branch: worktree $worktree has $dirty uncommitted file(s)"
           continue
         fi
         echo "  Removing worktree: $worktree"
         if ! git worktree remove "$worktree"; then
           echo "  SKIP $branch: could not remove worktree $worktree"
           continue
         fi
       fi
       git branch -d "$branch" 2>/dev/null \
         || echo "  KEPT $branch: it holds commits that are not merged anywhere"
     done
   ```

## Safety

Three refusals in step 4 are deliberate. Each one guards work that `git reflog` is the
only way back from, if it is recoverable at all.

**`git branch -d`, not `-D`.** A remote branch disappears for several reasons and only
one of them means the work landed: a merged PR, yes — but equally a closed PR, an
abandoned branch someone tidied up, or a remote-side rename. `[gone]` says the upstream
vanished; it says nothing about whether the commits survive anywhere else. `-D` across
that whole set destroys the only copy without asking. `-d` refuses exactly the branches
worth keeping. When one is refused, report it by name and let the user decide; if they
confirm, `git branch -D <name>` on that single branch is right — never a blanket force.

**Skip a worktree with uncommitted changes.** A merged branch does not imply a clean
worktree: someone can merge a PR and keep editing in the same checkout. Removing it
with `--force` discards those edits silently, and they were never committed, so no
reflog entry exists and nothing can bring them back. Check `status --porcelain` first
and skip.

**`git worktree remove` without `--force`.** Plain `remove` already handles a clean
worktree; `--force` only adds the ability to destroy a dirty one, which is what the
check above exists to prevent. If removal fails for some other reason, skip the branch
rather than falling through to a `git branch -d` that cannot succeed anyway — the
branch is still checked out there.

A note for shared checkouts: a branch can be checked out in a worktree that another
person or another agent session is working in right now, and `git worktree list` is a
snapshot that may already be stale. The uncommitted-changes check is what makes that
survivable.

## Expected Behavior

- Remote-tracking refs are pruned, so the gone list is accurate
- Every gone branch is listed before anything is deleted
- Worktrees holding gone branches are removed first, unless they hold uncommitted work
- Merged gone branches are deleted; unmerged ones are kept and reported by name
- The currently checked-out branch is skipped rather than failing the run

Report what was deleted, and name anything skipped along with the reason. If nothing is
marked gone, report that no cleanup was needed.
