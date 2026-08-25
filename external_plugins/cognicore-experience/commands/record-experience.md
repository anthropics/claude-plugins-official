---
allowed-tools: mcp__cognicore_experience__cognicore_record_experience, mcp__cognicore_experience__cognicore_verify_experience, Bash(git diff:*), Bash(git log:*)
description: Record the completed task into CogniCore structured experience memory and submit verification evidence
---

## Context
- Git diff: !`git diff HEAD~1`
- Git commit: !`git rev-parse --short HEAD`

## Your Task
1. Structure the completed task: problem statement, attempted approaches (with failures and reasons), and working solution.
2. Call `cognicore_record_experience` to store candidate experience.
3. Call `cognicore_verify_experience` with the test command execution evidence to promote it to `VERIFIED`.
4. Report the resulting experience ID and verification status.
