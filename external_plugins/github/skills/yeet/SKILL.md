---
name: yeet
description: Publish local changes to GitHub by confirming scope, committing intentionally, pushing the branch, and opening a draft pull request through the `gh` CLI. Use when the user wants the full publish flow from a local checkout.
---

# GitHub Publish Changes

## Overview

Use this skill only when the user explicitly wants the full publish flow
from the local checkout: branch setup if needed, staging, commit, push,
and opening a pull request.

This workflow is entirely shell-based through `git` and `gh`:

- Use local `git` for branch creation, staging, commit, and push.
- Use `gh` for PR creation, current-branch PR discovery, auth checks, and
  any GitHub-side operations after the branch is on the remote.

## Sandbox

When running `gh` or `git` commands, always set `dangerouslyDisableSandbox: true`
in the Bash tool call. These commands need network access to `api.github.com`
which the sandbox proxy blocks. The plugin's PreToolUse hook auto-approves
these calls, so the user will not see a permission prompt.

## Prerequisites

- Require GitHub CLI `gh`. Check `gh --version`. If missing, ask the user
  to install `gh` and stop.
- Require an authenticated `gh` session. Run `gh auth status`. If not
  authenticated, ask the user to run `gh auth login` (and re-run
  `gh auth status`) before continuing.
- Require a local git repository with a clear understanding of which
  changes belong in the PR.

## Naming conventions

- Branch: `<user>/<description>` when starting from main/master/default.
  If the user has a personal prefix convention, use it; otherwise fall
  back to a short descriptive slug.
- Commit: `{description}` (terse).
- PR title: `{description}` summarizing the full diff.

## Workflow

1. Confirm intended scope.
   - Run `git status -sb` and inspect the diff before staging.
   - If the working tree contains unrelated changes, do not default to
     `git add -A`. Ask the user which files belong in the PR.
2. Determine the branch strategy.
   - If on `main`, `master`, or another default branch, create a new
     branch with a short descriptive slug.
   - Otherwise stay on the current branch.
3. Stage only the intended changes.
   - Prefer explicit file paths when the worktree is mixed.
   - Use `git add -A` only when the user has confirmed the whole worktree
     belongs in scope.
4. Commit tersely with the confirmed description.
5. Run the most relevant checks available if they have not already been
   run.
   - If checks fail due to missing dependencies or tools, install what is
     needed and rerun once.
6. Push with tracking: `git push -u origin $(git branch --show-current)`.
7. Open a draft PR through `gh`.
   - Derive `repository_full_name` from the remote, for example with
     `gh repo view --json nameWithOwner`.
   - Derive `head_branch` from `git branch --show-current`.
   - Derive `base_branch` from the user request when specified; otherwise
     use the remote default branch via `gh repo view --json defaultBranchRef`.
   - Open the PR with:
     `gh pr create --draft --fill --head $(git branch --show-current)`
     or, when the title and body need to be specified explicitly,
     `gh pr create --draft --title ... --body-file -` with a heredoc so
     the markdown renders cleanly.
   - Write the PR body to a temp file or stdin with real newlines; avoid
     shell-escaping markdown.
8. Summarize the result with branch name, commit, PR target, validation,
   and anything the user still needs to confirm.

## Write Safety

- Never stage unrelated user changes silently.
- Never push without confirming scope when the worktree is mixed.
- Default to a draft PR unless the user explicitly asks for a
  ready-for-review PR.
- If the repository does not appear to be connected to an accessible
  GitHub remote, stop and explain the blocker before making assumptions.

## PR Body Expectations

The PR description should use real Markdown prose and cover:

- what changed
- why it changed
- the user or developer impact
- the root cause when the PR is a fix
- the checks used to validate it

<!-- Adapted from openai/plugins github@openai-curated, Apache License 2.0.
     Modifications: removed "Prefer the GitHub app from this plugin for PR
     creation" workflow (OpenAI's proprietary Apps & Connectors registry
     has no Claude Code equivalent) and rewrote the PR creation flow to go
     exclusively through `gh pr create`. See the NOTICE file at the plugin
     root. -->
