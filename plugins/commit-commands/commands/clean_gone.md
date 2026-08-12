---
description: Cleans up local git branches whose remote branch was deleted (shown by git as "gone"), including their worktrees — skipping anything with uncommitted work or currently checked out.
---

## Your Task

Delete local branches whose upstream remote branch no longer exists, and remove their worktrees — without destroying any work.

## Commands to Execute

1. **Refresh remote state first.** Without this the "gone" markers are stale or absent entirely.

   ```bash
   git fetch --prune origin
   ```

2. **List the branches that qualify.** Note this uses `-vv`, not `-v`: the gone marker only appears with two `v`s, and git prints it as `[origin/<branch>: gone]`, so the pattern must be `: gone]` and not `[gone]`.

   ```bash
   git branch -vv | grep ': gone\]'
   ```

   If nothing matches, report that no cleanup was needed and stop.

3. **Delete them, skipping anything unsafe.** This writes a recovery list first, then skips the current branch and any worktree holding uncommitted work.

   ```bash
   current=$(git symbolic-ref --short -q HEAD)
   mkdir -p .git/clean_gone
   rec=".git/clean_gone/deleted-$(date +%Y-%m-%d-%H%M%S).txt"
   git branch -vv | grep ': gone\]' | cut -c3- | awk '{print $1, $2}' > "$rec"
   echo "Recovery list ($(wc -l < "$rec" | tr -d ' ') branches with SHAs): $rec"

   git branch -vv | grep ': gone\]' | cut -c3- | awk '{print $1}' | while read -r b; do
     # Never touch the branch that is checked out here.
     if [ "$b" = "$current" ]; then
       echo "SKIP  $b — currently checked out"
       continue
     fi

     # Find this branch's worktree, if it has one.
     wt=$(git worktree list --porcelain | awk -v br="refs/heads/$b" '
       /^worktree /{w=$2} /^branch /{if ($2==br) print w}')

     if [ -n "$wt" ]; then
       # Uncommitted work is the one thing this command must never destroy.
       # node_modules is ignored because worktrees routinely carry it untracked.
       dirty=$(git -C "$wt" status --porcelain | grep -v node_modules | wc -l | tr -d ' ')
       if [ "$dirty" != "0" ]; then
         echo "SKIP  $b — $dirty uncommitted file(s) in $wt"
         git -C "$wt" status --porcelain | grep -v node_modules | sed 's/^/        /'
         continue
       fi
       git worktree remove --force "$wt" || { echo "SKIP  $b — could not remove $wt"; continue; }
       echo "      removed worktree $wt"
     fi

     git branch -D "$b" >/dev/null && echo "DEL   $b"
   done
   ```

4. **Report what was skipped.** Anything printed as `SKIP` still exists and needs a human decision — usually either committing the work or confirming it can be thrown away.

## Recovering a branch deleted by mistake

The recovery file records every branch name with the commit it pointed at, so any of them can be restored while the objects remain in the reflog:

```bash
git branch <name> <sha>
```

## Notes

- **A "gone" branch is not necessarily merged.** The remote branch is usually deleted when its pull request merges, but a branch can also go gone because the remote was deleted manually, or because work continued locally *after* the pull request merged. Those later commits exist nowhere else. If it matters, check before deleting: `git cherry -v origin/main <branch>` marks with `-` the commits already in main and `+` the ones unique to the branch.
- **Squash-merged branches always look unmerged.** Squashing rewrites the commits into a new one with a different SHA, so `git branch --merged` and any `origin/main..<branch>` count will report work as missing when it actually landed. Compare by patch (`git cherry`) or by pull request, not by commit count.
