---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
description: Create a git commit
---

## Context

- Current git status: !`git status`
- Current git diff (staged and unstaged changes): !`git diff HEAD`
- Current branch: !`git branch --show-current`
- Recent commits for context: !`git log --oneline -10`

## Your task

Based on the above changes, create a single git commit.

**Use this command when** you only want to commit locally (work-in-progress, partial saves, experimenting). **Use `/commit-push-pr`** when you want the full workflow (branch → commit → push → PR).

You have the capability to call multiple tools in a single response. Stage and create the commit using a single message. Do not use any other tools or do anything else. Do not send any other text or messages besides these tool calls.
