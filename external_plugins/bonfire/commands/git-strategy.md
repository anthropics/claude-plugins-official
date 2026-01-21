---
description: Change how .bonfire/ is handled in git
allowed-tools: Bash(git:*), Read, Write, AskUserQuestion
model: haiku
---

# Change Git Strategy

## Step 1: Find Git Root

Run `git rev-parse --show-toplevel` to locate the repository root.

## Step 2: Read Current Config

Read `<git-root>/.bonfire/config.json` to check current `specsLocation` and `docsLocation` settings.

## Step 3: Explain Options

Present the git strategy options:

1. **Ignore all** - Keep sessions completely local
   - Everything in .bonfire/ is gitignored
   - Most private, nothing shared
   - Good for: solo work, sensitive projects

2. **Hybrid** - Commit docs/specs, keep notes private
   - docs/ and specs/ are committed
   - index.md and archive/ stay local
   - Good for: teams that want shared docs but private notes

3. **Commit all** - Share everything with team
   - All session content is committed
   - Only data/ and scratch/ ignored
   - Good for: full transparency, team continuity

## Step 4: Get User Choice

Use AskUserQuestion to ask which strategy:

"Which git strategy for `.bonfire/`?" (Header: "Git")
- ignore-all (Recommended) - Keep sessions private/local
- hybrid - Commit docs/specs, keep notes private
- commit-all - Share everything with team

## Step 5: Update .gitignore

Write the appropriate `.gitignore` to `<git-root>/.bonfire/.gitignore`:

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

## Step 6: Handle Git Tracking

If switching FROM commit/hybrid TO ignore:
- Warn user that existing tracked files will remain tracked
- Offer to run: `git rm -r --cached .bonfire/` (removes from git but keeps files)
- They'll need to commit this change

If switching TO commit/hybrid:
- Files will be picked up on next commit
- No special action needed

## Step 7: Confirm

Report:
- New strategy applied
- Any manual steps needed
- How to verify the change
