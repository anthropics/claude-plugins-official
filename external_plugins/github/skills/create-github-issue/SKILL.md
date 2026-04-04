---
name: create-github-issue
description: Use this skill when the user wants to create a GitHub issue, report a bug, open a feature request, or add a task to a repository. Trigger phrases include "create an issue", "report a bug", "open an issue for", "add a ticket", "create a ticket for", or "log a bug in [repo]".
---

# Create GitHub Issue

Use the GitHub MCP server to create a new issue in the specified repository.

## Steps

1. **Identify the repository** — extract the owner and repo name from the user's request (e.g. `my-app` → ask for the owner if missing, or infer from context).
2. **Collect issue details** — if the user has not provided them, ask for:
   - **Title** (required): a short, descriptive summary
   - **Body** (optional but recommended): steps to reproduce, expected vs actual behaviour, environment details
   - **Labels** (optional): e.g. `bug`, `enhancement`, `help wanted`
   - **Assignees** (optional): GitHub usernames to assign
3. **Create the issue** using the GitHub MCP `create_issue` tool.
4. **Confirm success** — report the new issue URL back to the user.

## Example Interaction

> User: "Create an issue for the login bug in my-app repo"

1. Ask: "What should the issue title be? (e.g. 'Login fails with OAuth provider')"
2. Ask: "Can you describe the bug — steps to reproduce and any error messages?"
3. Create the issue with title, body, and label `bug`.
4. Reply: "Issue #42 created: https://github.com/owner/my-app/issues/42"

## Notes

- If the repository does not exist or the token lacks permission, report the error clearly and suggest checking the `GITHUB_PERSONAL_ACCESS_TOKEN` scopes (`repo` scope required for private repos).
- Prefer creating well-structured issues with enough context for the maintainer to act on them.
