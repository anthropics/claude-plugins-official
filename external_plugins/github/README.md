# GitHub Plugin for Claude Code

Official GitHub MCP server integration for Claude Code. Interact with GitHub repositories, issues, pull requests, Actions workflows, and more — directly from Claude Code. Authentication and API calls are handled automatically via your personal access token.

## Setup

Set your GitHub personal access token as an environment variable:

```bash
export GITHUB_PERSONAL_ACCESS_TOKEN=your_token_here
```

Your token needs the following scopes depending on what you want to do:
- **repo** — full access to public and private repositories
- **read:org** — read organization data (for org-level queries)
- **workflow** — read and manage GitHub Actions workflows

## Capabilities

### Create Issues

> "Create an issue for the login bug in my-app repo"
> "Open a feature request in my-project for dark mode support"
> "Report a bug: the signup form crashes on Safari"

Claude will ask for any missing details (title, description, labels) and create the issue in the specified repository.

### Review Pull Requests

> "Review the latest PR on my project"
> "Show me the changes in PR #42 on my-app"
> "What does the open pull request on qasimsethi-code/my-app change?"

Claude fetches the PR diff, description, and review comments, then provides a thorough code review.

### Check GitHub Actions Runs

> "Show me failed GitHub Actions runs"
> "Why is the CI failing on my-app?"
> "List recent workflow runs for my-project"

Claude retrieves workflow run history, highlights failures, and summarises the error output.

### Search Repositories

> "Search for repositories about machine learning"
> "Find popular Python repos for data visualisation"
> "Look for open-source projects tagged with 'cli' and 'rust'"

Claude searches GitHub and returns a ranked list of matching repositories with descriptions and stats.

### List Issues

> "List open issues assigned to me"
> "Show all open bugs in my-app"
> "What issues are labelled 'help wanted' in my-project?"

Claude fetches and displays issues filtered by assignee, state, label, or repository.

## Configuration

The plugin connects to GitHub's official MCP server at `https://api.githubcopilot.com/mcp/` using Bearer token authentication sourced from `GITHUB_PERSONAL_ACCESS_TOKEN`.

```json
{
  "github": {
    "type": "http",
    "url": "https://api.githubcopilot.com/mcp/",
    "headers": {
      "Authorization": "Bearer ${GITHUB_PERSONAL_ACCESS_TOKEN}"
    }
  }
}
```

## Author

Built and maintained by [GitHub](https://github.com).
