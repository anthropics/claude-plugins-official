---
description: Cleans up all git branches marked as [gone] (branches that have been deleted on the remote but still exist locally), including removing associated worktrees.
---

## Your Task

Delete local branches whose upstream has been deleted on the remote, along with any
worktrees holding them.

## Step 1 — Prune, so `gone` exists at all

`gone` is not a state git works out on its own. It appears only after a fetch that
prunes deleted remote-tracking refs; until then a branch whose remote was deleted
still looks entirely normal.

```bash
git fetch --prune
```

## Step 2 — List the gone branches

`git branch -v` marks them with a bare `[gone]`. (`-vv` prints the upstream ref as
well — `[origin/my-branch: gone]` — so a pattern written for one verbosity will not
match the other. The commands below are written for `-v`.)

```bash
git branch -v | grep '\[gone\]'
```

If nothing prints, report that no cleanup is needed and stop.

## Step 3 — Get off any branch about to be deleted

Git will not delete a branch that is checked out in any worktree, including the
current one — and standing on a gone branch is the normal case, since you have just
merged its pull request. Without this step the script reports
`cannot delete branch 'x' used by worktree at ...` and leaves the branch behind.

If the current branch appears in step 2, switch to the default branch and bring it
up to date first:

```bash
git checkout main 2>/dev/null || git checkout master
git merge --ff-only @{u}
```

## Step 4 — Remove worktrees and delete

Two things to get right:

**Parse worktrees with `--porcelain`.** The human-readable `git worktree list` is
whitespace-separated, so `awk '{print $1}'` truncates any path containing a space —
`/Users/me/my work tree` becomes `/Users/me/my`. `git worktree remove` then fails on
the wrong path, the worktree survives, and the branch delete fails after it.

**Try `-d` before `-D`.** A remote branch usually disappears because its pull request
merged, but a closed pull request and a hand-deleted branch are also `gone`, and
force-deleting one of those throws work away. `git branch -d` succeeds exactly when
the branch is already an ancestor, so it is free to attempt.

```bash
git branch -v | grep '\[gone\]' | sed 's/^[+* ]*//' | awk '{print $1}' | while read -r branch; do
  echo "Processing branch: $branch"

  # Find a worktree holding this branch, tolerating spaces in the path.
  worktree=$(git worktree list --porcelain | awk -v b="refs/heads/$branch" '
    /^worktree /  { path = substr($0, 10) }
    /^branch /    { if (substr($0, 8) == b) { print path; exit } }
  ')
  if [ -n "$worktree" ] && [ "$worktree" != "$(git rev-parse --show-toplevel)" ]; then
    echo "  Removing worktree: $worktree"
    git worktree remove --force "$worktree"
  fi

  if git branch -d "$branch" 2>/dev/null; then
    echo "  Deleted (merged): $branch"
  else
    echo "  NOT an ancestor of the current branch — check step 5 before deleting"
  fi
done
```

## Step 5 — Decide about anything left behind

A branch `-d` refused is not necessarily unmerged. A **squash-merged or rebased**
pull request puts the content on the default branch under a different commit, so no
ancestry exists to find and `-d` will always refuse — which is why this is a question
rather than an error.

Ask the forge:

```bash
gh pr list --state all --head <branch> --json number,state,mergeCommit
```

`MERGED` means the work landed; force-delete it:

```bash
git branch -D <branch>
```

Anything else — `CLOSED`, `OPEN`, or no pull request at all — means stop and ask the
user. Without `gh`, compare trees instead: an empty `git diff --stat <default> <branch>`
means the content is already there. A non-empty diff is not proof of loss, since it
also appears once the default branch has moved on past the merge, so read
`git log <default>..<branch>` before deciding.

## Report

Say which branches were deleted, which worktrees were removed, and which branches were
left behind and why. If nothing was marked gone, say no cleanup was needed.
