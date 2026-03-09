---
allowed-tools: Bash(git checkout --branch:*), Bash(git add:*), Bash(git status:*), Bash(git push:*), Bash(git commit:*), Bash(gh pr create:*), Bash(git log:*)
description: Commit, push, and open a PR
---

## Context

- Current git status: !`git status`
- Current git diff (staged and unstaged changes): !`git diff HEAD`
- Current branch: !`git branch --show-current`
- Recent commits (for style matching): !`git log --oneline -10`

## Your task

Based on the above changes:

1. Create a new branch if on main
2. Create a single commit with an appropriate message that matches the repo's commit style
3. Push the branch to origin
4. Create a pull request using `gh pr create` with a structured description using this template:
   ```
   ## Summary
   - <1-3 bullet points describing changes>

   ## Test plan
   - [ ] <checklist of testing steps>
   ```
5. When writing the PR description, analyze ALL commits in the branch (not just the latest) using `git log main..HEAD` to capture the full scope of changes
6. Do not stage files that may contain secrets (.env, credentials.json, etc.)
7. You have the capability to call multiple tools in a single response. You MUST do all of the above in a single message. Do not use any other tools or do anything else. Do not send any other text or messages besides these tool calls.
