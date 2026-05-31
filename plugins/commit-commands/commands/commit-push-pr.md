---
allowed-tools: Bash(git checkout --branch:*), Bash(git add:*), Bash(git status:*), Bash(git push:*), Bash(git commit:*), Bash(gh pr create:*)
description: Commit, push, and open a PR
---

## Context

- Current git status: !`git status`
- Current git diff (staged and unstaged changes): !`git diff HEAD`
- Current branch: !`git branch --show-current`
- Recent commits for context: !`git log --oneline -10`

## Your task

Based on the above changes:

1. If on `main` or `master`, create a new branch with a descriptive name (kebab-case, based on the diff content)
2. Stage all changes and create a single commit with a conventional-commit message (e.g., `feat:`, `fix:`, `refactor:`, `chore:`)
3. Push the branch to origin using `--set-upstream`
4. Create a pull request using `gh pr create --fill` (auto-fills title/body from commit)
5. You have the capability to call multiple tools in a single response. You MUST do all of the above in a single message. Do not use any other tools or do anything else. Do not send any other text or messages besides these tool calls.

## Notes

- If you only need to commit without pushing (e.g., work-in-progress), use the `/commit` command instead
- For force-push scenarios (amend/ rebase), use `git push --force-with-lease` manually
