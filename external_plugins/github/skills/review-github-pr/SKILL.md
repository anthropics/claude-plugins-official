---
name: review-github-pr
description: Use this skill when the user asks to review a pull request, check the latest PR, look at code changes, or analyse a GitHub PR. Trigger phrases include "review the latest PR", "review PR #123", "look at the pull request", "check the PR on my project", or "what does PR #42 change".
---

# Review GitHub Pull Request

Use the GitHub MCP server to fetch pull request details and provide a thorough code review.

## Steps

1. **Identify the pull request** — extract the owner, repo, and PR number from the user's request.
   - If no PR number is given, use the GitHub MCP `list_pull_requests` tool to find the most recently updated open PR.
2. **Fetch PR data** using the GitHub MCP tools:
   - Get the pull request details — title, description, author, base/head branches, status
   - List the changed files — file paths with additions/deletions counts
   - Retrieve the unified diff — full code changes across all files
   - List the commits — commit history for the PR
   - List existing reviews and review comments — prior feedback already given
3. **Analyse the changes** and provide feedback covering:
   - **Summary**: what the PR does and why
   - **Code quality**: readability, naming, duplication
   - **Correctness**: logic errors, edge cases, off-by-one errors
   - **Tests**: whether new code is adequately tested
   - **Security**: any potential vulnerabilities introduced
   - **Suggestions**: actionable inline comments or improvements
4. **Report findings** in a structured format with a clear overall verdict (Approve / Request Changes / Comment).

## Example Interaction

> User: "Review the latest PR on my project"

1. Fetch the most recent open PR.
2. Retrieve the diff and existing reviews.
3. Respond with a structured review including summary, findings, and recommendation.

## Notes

- Focus on substance over style — flag genuine issues rather than stylistic preferences unless the project has a linter config.
- If the PR is large (> 500 changed lines), summarise by file or module and highlight the highest-risk areas.
- Respect existing review comments — do not repeat feedback already given.
