---
name: list-github-issues
description: Use this skill when the user wants to see GitHub issues, list open or closed issues, view their assigned issues, or browse issues in a repository. Trigger phrases include "list open issues", "show issues assigned to me", "my issues", "show open bugs in [repo]", "what issues are labelled help wanted", or "list issues in [repo]".
---

# List GitHub Issues

Use the GitHub MCP server to fetch and display GitHub issues filtered by the user's criteria.

## Steps

1. **Determine the scope** — extract the key parameters from the user's request:
   - **Repository** (optional): `owner/repo` — if not specified, search across all repositories the user has access to
   - **Assignee** (optional): a GitHub username, or `@me` for the authenticated user
   - **State** (optional): `open` (default), `closed`, or `all`
   - **Labels** (optional): one or more label names (e.g. `bug`, `help wanted`)
   - **Milestone** (optional): milestone title or number
2. **Fetch issues** using the GitHub MCP tools:
   - Use the **list issues** tool when querying a single repository with simple filters (state, assignee, label, milestone). This is more efficient for repository-scoped queries.
   - Use the **search issues** tool when looking across multiple repositories, combining complex filters, or searching by keyword. Suitable for "my issues across all repos" or "find issues mentioning a specific error".
3. **Present the results** in a clear list for each issue:
   - **Number and title**: `#42 — Login fails with OAuth provider`
   - **State**: open / closed
   - **Assignees**: who is responsible
   - **Labels**: categorisation tags
   - **Created / Updated**: age and recency
   - **URL**: direct link
4. **Offer next actions** — the user can ask to create an issue, close one, add a comment, or drill into a specific issue.

## Example Interactions

> User: "List open issues assigned to me"

1. Call `list_issues` with `assignee: @me` and `state: open`.
2. Display a numbered list with title, labels, and age.
3. Offer: "Would you like to filter by label, repository, or milestone?"

> User: "Show all open bugs in my-app"

1. Call `list_issues` with `owner/repo: .../my-app`, `state: open`, `labels: bug`.
2. Display matching issues with title, assignees, and date opened.

## Notes

- Default to `state: open` unless the user asks for closed or all issues.
- If no repository is specified and the user says "my issues", use `assignee: @me` to find issues assigned to the authenticated user across all repos.
- If results exceed 20, summarise by count per repository or label and offer to paginate.
