---
description: Deletes local branches whose upstream is gone (deleted on the remote), removing any attached worktree first, after checking each one for work that exists nowhere else.
---

## Your Task

Delete local branches whose upstream has been deleted on the remote, after confirming each one's
work is safe to lose.

**Read the whole command before running anything.** `git branch -D` and `git worktree remove
--force` both destroy work in ways git cannot undo.

## Commands to Execute

1. **Prune every remote.** A branch is only marked gone once its deleted remote ref has been
   pruned locally, and a branch tracking a second remote is missed when only `origin` is pruned:
   ```bash
   git fetch --all --prune
   ```

2. **Select gone branches from git's structured upstream field:**
   ```bash
   git for-each-ref --format='%(refname:short)|%(upstream:track)' refs/heads \
     | grep '|\[gone\]$' | cut -d'|' -f1
   ```

   Do **not** find them by grepping `git branch -v` or `git branch -vv`:

   - `git branch -v` does not print upstream tracking information at all, so no branch ever
     appears gone and the command silently deletes nothing.
   - `git branch -vv` does print it, but puts the commit subject on the same line, so a pattern
     matching that line also matches a **live** branch whose subject contains the marker text. A
     branch with the subject `docs: explain the [origin/foo: gone] marker` is selected by
     `grep ': gone]'` and force-deleted, taking its unpushed commits with it.

   `%(upstream:track)` is the field itself and yields exactly `[gone]`, so no subject text can
   reach it.

3. **List worktrees in porcelain form,** which gives one `branch refs/heads/<name>` line per
   worktree for exact comparison:
   ```bash
   git worktree list --porcelain
   ```

4. **Check each gone branch for work that exists nowhere else, BEFORE deleting anything:**
   ```bash
   git log --oneline "<default-branch>..<branch>"
   ```

   Commits listed here are **not** proof of lost work: a squash-merged or rebase-merged pull
   request relands the content under a new SHA, so the original commits are never ancestors of the
   default branch even though the work shipped. Confirm where the branch went:
   ```bash
   gh pr list --state all --head <branch> --json number,state,mergedAt,mergeCommit,headRefOid,url
   ```

   - Pull request merged **and** `headRefOid` equals the local tip -> safe to delete.
   - Merged but the local tip is **ahead** of `headRefOid` -> commits were added after the merge
     and shipped nowhere. **Stop and ask the user.**
   - No pull request, or closed unmerged -> **stop and ask the user.**

   Carry the approved branch names and tip SHAs forward. Deletion must act on that list rather
   than re-deriving it, or a branch that becomes gone between the check and the delete is removed
   unreviewed.

5. **For each approved branch, handle its worktree, then delete the branch.** Work through the
   approved list one branch at a time rather than piping discovery into a delete loop:

   - **Current branch:** if it is the one checked out here (`git branch --show-current`), git
     refuses to delete it. Report it as skipped and ask the user to switch first.
   - **Worktree:** find it by exact match on `branch refs/heads/<name>` in the porcelain output.
     Never match with `grep "\[$branch\]"` — an unquoted branch name is a regular expression, so
     `foo.bar` matches a `fooXbar` worktree and removes the wrong one.
   - **Check the worktree is clean before removing it** (`git -C "$wt" status --porcelain`). A
     merged branch can still hold uncommitted edits or untracked files, and `git worktree remove
     --force` deletes them with no backup that branch recovery can restore. If it is not clean,
     show the user what is there and ask. Use plain `git worktree remove` for a clean one.
   - **Then** `git branch -D "$branch"`, recording the `was <sha>` it prints.

   Never remove the worktree you are currently running in.

## Expected Behavior

- Only branches whose upstream field is exactly `[gone]` are considered.
- Each is checked for unshipped work before anything is deleted; anything doubtful is left in
  place and reported.
- A worktree is removed only after it is confirmed clean, and never the current one.
- Report every branch deleted with its SHA, and every branch skipped with the reason.

If no branch has a `[gone]` upstream, report that no cleanup was needed.

## Recovery

Print each deleted branch's SHA so the user can restore it:

```bash
git branch <branch> <sha>
```

Do not promise this works for 90 days. Deleting a branch deletes its reflog too, and once its
commits are unreachable they can be garbage-collected before the default expiry. If a branch must
stay recoverable, keep a real ref rather than relying on the reflog:

```bash
git tag archive/<branch> <sha>
```

Uncommitted and untracked files in a removed worktree are not recoverable by any of this.
