---
name: github-actions-status
description: Use this skill when the user asks about GitHub Actions workflow runs, CI/CD status, failed builds, or test results. Trigger phrases include "show failed GitHub Actions runs", "check CI status", "why is the build failing", "list workflow runs", "show me failed tests", or "what workflows are failing".
---

# GitHub Actions Status

Use the GitHub MCP server to retrieve workflow run information and highlight failures.

## Steps

1. **Identify the repository** — extract the owner and repo name from the user's request.
2. **Fetch workflow runs** using the GitHub MCP tools:
   - `list_workflow_runs` — recent runs across all workflows (or a specific workflow if named)
   - Filter by `status: failure` when the user asks specifically about failures
3. **Summarise the results**:
   - List each run with: workflow name, run number, trigger event, branch, status, and duration
   - For failed runs, highlight them prominently
4. **Drill into failures** if the user wants more detail:
   - List the individual jobs within the failed run to identify which job failed
   - Retrieve the log output for failed jobs
   - Identify the failing step and surface the key error message
5. **Report findings** clearly, grouping by workflow when multiple are shown.

## Example Interaction

> User: "Show me failed GitHub Actions runs"

1. Fetch the 10 most recent workflow runs filtered to failures.
2. Display a table: workflow name, branch, trigger, time, and failure reason.
3. Offer to drill into a specific run's logs for root-cause detail.

## Notes

- When no specific time range is given, show the last 10 runs.
- Surface the first error line from failed step logs — avoid dumping hundreds of log lines.
- If the token lacks the `workflow` scope, advise the user to add it to `GITHUB_PERSONAL_ACCESS_TOKEN`.
