---
description: Perform code review to identify security and quality issues with Autofix Bot.
allowed-tools: mcp__autofix__CheckAuthStatus, mcp__autofix__Authenticate, mcp__autofix__ReviewCode
---

IMPORTANT: You MUST use the Autofix Bot MCP tools for this task. Do NOT perform your own code review or analysis.

## Instructions

1. Call `mcp__autofix__CheckAuthStatus` to check authentication status
2. If not authenticated, call `mcp__autofix__Authenticate` to log in
3. Ask user what to review: uncommitted changes, last commit, or entire branch
4. Call `mcp__autofix__ReviewCode` with the user's selected target
5. Present the issues returned by ReviewCode in a clear format

Do NOT skip any tool calls. Do NOT substitute your own analysis for the tool results.
