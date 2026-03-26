# beyga-git-commands

Opinionated git workflow commands for Claude Code — covering the full lifecycle from branching to PR submission.

## Commands

### `/beyga-branch-and-pr`

Creates a new branch, commits changes, and opens a pull request in one flow.

- Asks for branch type, optional task ID, and branch name
- Runs Biome formatter if configured in the project
- Analyzes changes and splits into logical commits by feature/component/concern
- Pushes the branch and opens a PR with a structured summary and test plan
- Skips PR creation if there are no commits ahead of the base branch

### `/beyga-create-pr`

Opens a pull request for the current branch.

- Warns if no changes were made in the session
- Auto-detects base branch; presents a numbered selection list when multiple candidates exist
- Handles uncommitted changes with optional commit (including logical splitting)
- Derives PR type and task ID from the branch name automatically

## Conventions

**Branch naming:** `<type>/<name>` or `<type>/<TASK-ID>-<name>`
- Types: `feat`, `fix`, `chore`, `refactor`, `delete`
- Example: `feat/TASK-123-add-login`

**PR titles:** `[TYPE] Description` or `[TYPE][TASK-ID] Description`
- Example: `[FEAT][TASK-123] Add login screen`

## Installation

```
/plugin install beyga-git-commands@claude-plugins-official
```
