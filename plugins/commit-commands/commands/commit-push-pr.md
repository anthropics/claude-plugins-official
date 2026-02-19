---
allowed-tools: Bash(git checkout --branch:*), Bash(git add:*), Bash(git status:*), Bash(git push:*), Bash(git commit:*), Bash(gh pr create:*)
description: Commit, push, and open a PR
argument-hint: Optional path to a plan/prompt file to include in the PR body
---

## Context

- Current git status: !`git status`
- Current git diff (staged and unstaged changes): !`git diff HEAD`
- Current branch: !`git branch --show-current`
- Plan/prompt context: !`cat "$ARGUMENTS" 2>/dev/null || cat PLAN.md 2>/dev/null || cat .plan.md 2>/dev/null || ls -t ~/.claude/plans/*.md 2>/dev/null | head -1 | xargs cat 2>/dev/null || echo ""`

## Your task

Based on the above changes:

1. Create a new branch if on main
2. Create a single commit with an appropriate message
3. Push the branch to origin
4. Create a pull request using `gh pr create`. The PR body MUST include:
   - A summary of the changes (1-3 bullet points)
   - A test plan checklist
   - If the **Plan/prompt context** above is non-empty, include it verbatim under a `## Context` section at the top of the PR body
5. You have the capability to call multiple tools in a single response. You MUST do all of the above in a single message. Do not use any other tools or do anything else. Do not send any other text or messages besides these tool calls.
