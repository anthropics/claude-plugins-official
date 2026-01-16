---
description: Create a git commit with generateing clear commit messages from git diffs. Use when writing commit messages or reviewing staged changes.
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
---


## Context

- Current git status: !`git status`
- Current git diff (staged and unstaged changes): !`git diff HEAD`
- Current branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -10`

## Your task

Based on the above changes, create a single git commit with a commit message containing:
   - Summary under 50 characters
   - Detailed description
   - Affected components

You have the capability to call multiple tools in a single response. Stage and create the commit using a single message. Do not use any other tools or do anything else. Do not send any other text or messages besides these tool calls.


## Best practices

- Use present tense
- Explain what and why, not how
- use “Conventional Commits” style from Angularjs as below
```
<type>(<scope>): <subject>
<empty_line>
<body>
<empty_line>
<footer>
```

## Examples
```
feat(auth): add third party SSO.

Implement OAuth2.0 interface to allow wechat user login.

Closes issue #123
```
