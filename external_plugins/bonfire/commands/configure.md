---
description: Change project settings (locations, git strategy, Linear)
allowed-tools: Bash(git:*), Read, Write, AskUserQuestion
model: haiku
---

# Configure Bonfire

Always runs interactively - asks all configuration questions regardless of arguments.

## Step 1: Find Git Root

Run `git rev-parse --show-toplevel` to locate the repository root.

## Step 2: Check for Bonfire Directory

If `<git-root>/.bonfire/` does not exist, tell the user to run `/bonfire:start` first.

## Step 3: Read Current Config

Read `<git-root>/.bonfire/config.json` if it exists to see current settings.

## Step 4: Ask All Configuration Questions

Use AskUserQuestion to ask configuration questions (4 questions, one round):

1. "Where should specs be saved?" (Header: "Specs")
   - .bonfire/specs/ (Recommended) - Keep with session context
   - specs/ - Project root level

2. "Where should docs be saved?" (Header: "Docs")
   - .bonfire/docs/ (Recommended) - Keep with session context
   - docs/ - Project root level

3. "How should `.bonfire/` be handled in git?" (Header: "Git")
   - ignore-all (Recommended) - Keep sessions private/local
   - hybrid - Commit docs/specs, keep notes private
   - commit-all - Share everything with team

4. "Enable Linear MCP integration?" (Header: "Linear")
   - No (Recommended) - Skip Linear integration
   - Yes - Fetch/create Linear issues (requires Linear MCP)

## Step 5: Update Config

**Completely overwrite** `<git-root>/.bonfire/config.json` with only these fields (do not preserve old fields like `models`):

```json
{
  "specsLocation": "<user-answer>",
  "docsLocation": "<user-answer>",
  "gitStrategy": "<user-answer>",
  "linearEnabled": <true-or-false>
}
```

## Step 6: Update Git Strategy

If git strategy or locations changed, update `<git-root>/.bonfire/.gitignore`:

**Ignore all**:
```
*
!.gitignore
```

**Hybrid** (only include dirs that are inside .bonfire/):
```
*
!.gitignore
```
If docsLocation is `.bonfire/docs/`, add:
```
!docs/
!docs/**
```
If specsLocation is `.bonfire/specs/`, add:
```
!specs/
!specs/**
```

**Commit all**:
```
data/
scratch/
scripts/
```

If switching FROM commit/hybrid TO ignore:
- Warn user that existing tracked files will remain tracked
- Offer to run: `git rm -r --cached .bonfire/`

## Step 7: Confirm

Report:
- Settings updated
- Any manual steps needed (git cleanup)
- New configuration summary
