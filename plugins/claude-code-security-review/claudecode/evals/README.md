# SAST Evaluation Tool

This directory contains a tool for evaluating the SAST (Static Application Security Testing) tool on individual GitHub pull requests.

## Overview

The evaluation tool allows you to run the Claude Code Security Reviewer on any GitHub PR to analyze its security findings. This is useful for:
- Testing the tool on specific PRs
- Evaluating performance and accuracy
- Debugging security analysis issues

## Requirements

- Python 3.9+
- Git 2.20+ (for worktree support)
- GitHub CLI (`gh`) for API access
- Environment variables:
  - `ANTHROPIC_API_KEY`: Required for Claude API access
  - `GITHUB_TOKEN`: Recommended for GitHub API rate limits

## Usage

Run an evaluation on a single PR:

```bash
python -m claudecode.evals.run_eval example/repo#123 --verbose
```

### Command-line Options

- PR specification: Required positional argument in format `owner/repo#pr_number`
- `--output-dir PATH`: Directory for results (default: `./eval_results`)
- `--work-dir PATH`: Directory where git repositories will be cloned and stored (default: `~/code/audit`)
- `--verbose`: Enable verbose logging to see detailed progress

## Output

The evaluation generates a JSON file in the output directory with:
- Success/failure status
- Runtime metrics
- Security findings count
- Detailed findings with file, line, severity, and descriptions

Example output file: `pr_example_repo_123.json`

## Architecture

The evaluation tool uses git worktrees for efficient repository management:
1. Clones the repository once as a base
2. Creates lightweight worktrees for each PR evaluation
3. Automatically handles cleanup of worktrees
4. Runs the SAST audit in the PR-specific worktree