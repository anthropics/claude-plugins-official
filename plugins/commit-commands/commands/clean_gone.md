---
description: Deletes local git branches whose upstream is gone (deleted on the remote). Skips any branch still checked out in a worktree rather than destroying it.
---

## Your Task

Delete local branches whose remote counterpart has been deleted, without touching
any worktree.

## Commands to Execute

1. **Refresh the remote-tracking refs first.** Without this, nothing is marked
   gone and the command silently no-ops.
   ```bash
   git fetch --prune
   ```

2. **Review what is about to be deleted, and what will be skipped.**
   ```bash
   git for-each-ref --format='%(refname:short)%09%(upstream:track)' refs/heads \
     | awk -F'\t' '$2 ~ /gone/ { print $1 }'
   git worktree list
   ```

3. **Delete them.**
   ```bash
   # Branch names come from for-each-ref, NOT from parsing `git branch` output:
   # the track marker renders as "[gone]" under -v but "[origin/x: gone]" under
   # -vv, and a commit subject containing "[gone]" would false-match either way.
   gone=$(git for-each-ref --format='%(refname:short)%09%(upstream:track)' refs/heads \
     | awk -F'\t' '$2 ~ /gone/ { print $1 }')

   # Every branch checked out in ANY worktree. These are off limits: deleting a
   # branch out from under a worktree leaves that checkout on a broken ref, and
   # removing the worktree itself can destroy someone else's uncommitted work.
   inuse=$(git worktree list --porcelain \
     | awk '/^branch /{ sub("refs/heads/","",$2); print $2 }')

   printf '%s\n' "$gone" | while IFS= read -r branch; do
     [ -n "$branch" ] || continue
     if printf '%s\n' "$inuse" | grep -qxF "$branch"; then
       wt=$(git worktree list --porcelain \
         | awk -v b="branch refs/heads/$branch" '/^worktree /{p=$2} $0==b{print p}')
       echo "SKIP    $branch — checked out at $wt"
       continue
     fi
     git branch -D "$branch"
   done
   echo "Done. Skipped branches are listed above; remove those worktrees deliberately if you own them."
   ```

## Notes

- **Worktrees are never removed.** An earlier version of this command ran
  `git worktree remove --force` on the worktree of every gone branch, guarding
  only the *current* toplevel. In a repo with several worktrees — parallel agent
  sessions, review checkouts — that deletes other people's working directories
  along with any uncommitted work in them. Removing a worktree is now the
  operator's call: `git worktree remove <path>` once you know you own it.
- **`git branch -D` is a force delete, on purpose.** A squash-merged branch is
  not an ancestor of `main`, so `-d` refuses it and the command would clean
  nothing. A gone upstream is good evidence the forge merged and deleted the
  branch — but it is evidence, not proof. If the branches matter, confirm each
  one merged first (`gh pr list --head <branch> --state all`) before running
  this. Every deletion prints `(was <sha>)`, so a mistake is recoverable from
  the reflog.
- Branches that are gone but still have an open PR are unusual and worth a look
  before deleting — that combination usually means the remote branch was deleted
  out from under a live PR.

## Expected Behavior

- Branches whose upstream is gone and which no worktree holds are deleted.
- Branches held by a worktree are reported and left alone.
- If nothing is gone, report that no cleanup was needed.
