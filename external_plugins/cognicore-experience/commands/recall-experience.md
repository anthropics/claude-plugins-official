---
allowed-tools: mcp__cognicore_experience__cognicore_recall_experience, Bash(git status:*), Bash(git log:*)
description: Query CogniCore persistent memory for verified solutions and failure warnings related to the current task
---

## Context
- Recent commits: !`git log --oneline -5`

## Your Task
1. Analyze the user's current request or bug description.
2. Call `cognicore_recall_experience` with the query and include failure warnings (`include_failures=True`).
3. If failure warnings are returned, explicitly highlight which approaches should NOT be repeated.
4. If verified solutions are returned, use them to guide the implementation.
