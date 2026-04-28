# Greptile

[Greptile](https://greptile.com) is an AI code review agent for GitHub and GitLab that automatically reviews pull requests. This plugin connects Claude Code to your Greptile account, letting you view and resolve Greptile's review comments directly from your terminal.

## Setup

### 1. Create a Greptile Account

Sign up at [greptile.com](https://greptile.com) and connect your GitHub or GitLab repositories.

### 2. Get Your API Key

1. Go to [API Settings](https://app.greptile.com/settings/api)
2. Generate a new API key
3. Copy the key

### 3. Set Environment Variable

Add to your shell profile (`.bashrc`, `.zshrc`, etc.):

```bash
export GREPTILE_API_KEY="your-api-key-here"
```

Then reload your shell or run `source ~/.zshrc`.

## Available Tools

### Pull Request Tools
- `list_pull_requests` - List PRs with optional filtering by repo, branch, author, or state
- `get_merge_request` - Get detailed PR info including review analysis
- `list_merge_request_comments` - Get all comments on a PR with filtering options

### Code Review Tools
- `list_code_reviews` - List code reviews with optional filtering
- `get_code_review` - Get detailed code review information
- `trigger_code_review` - Start a new Greptile review on a PR

### Comment Search
- `search_greptile_comments` - Search across all Greptile review comments

### Custom Context Tools
- `list_custom_context` - List your organization's coding patterns and rules
- `get_custom_context` - Get details for a specific pattern
- `search_custom_context` - Search patterns by content
- `create_custom_context` - Create a new coding pattern

## Example Usage

Ask Claude Code to:
- "Show me Greptile's comments on my current PR and help me resolve them"
- "What issues did Greptile find on PR #123?"
- "Trigger a Greptile review on this branch"

## Documentation

For more information, visit [greptile.com/docs](https://greptile.com/docs).
