# gh-dash - GitHub PR Dashboard

A Claude Code plugin that displays GitHub PR status, CI/CD checks, and merge capability directly in your terminal.

## Features

- Visual CI/CD progress bar with live updates
- Bot comment detection (CodeRabbit, Cursor Bugbot, Coverage)
- Files changed and lines added/removed stats
- Merge conflict detection
- Merge PRs directly from terminal (squash/merge/rebase)

## Prerequisites

Requires [GitHub CLI](https://cli.github.com/):

```bash
brew install gh
gh auth login
```

## Usage

```
/gh-dash:pr              # View PR for current branch
/gh-dash:pr --merge      # Squash merge (default)
/gh-dash:pr --merge merge    # Merge commit
/gh-dash:pr --merge rebase   # Rebase
```

## Links

- **Source**: https://github.com/jakozloski/claude-code-gh-dash
- **Author**: [@jakozloski](https://github.com/jakozloski)
