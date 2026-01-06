# Lisa Clean

Clean up Lisa artifacts and stale files from the project.

## What This Cleans

1. **State files**: `.claude/lisa-loop.local.md` (leftover from canceled/crashed loops)
2. **Log files**: `.claude/lisa-loop.log` (iteration logs from previous runs)
3. **Orphaned prompts**: Untracked `PROMPT*.md` and `IMPLEMENTATION_PLAN*.md` files in project root
4. **Plugin caches**: Old cached versions in `~/.claude/plugins/cache/`
5. **Orphaned skills**: Duplicate lisa-guide outside the plugin

## Process

When user invokes `/lisa-clean`:

### Step 1: Check for active loop

```bash
test -f .claude/lisa-loop.local.md && echo "ACTIVE" || echo "NO_LOOP"
```

If ACTIVE, warn user:
> "There's an active Lisa loop. Cancel it first with `/lisa-cancel` or use `--force` to clean anyway."

### Step 2: Clean state and log files (if no active loop or --force)

```bash
rm -f .claude/lisa-loop.local.md
rm -f .claude/lisa-loop.log
```

Report: "Removed state file and logs"

### Step 3: Detect orphaned prompt files

Look for untracked PROMPT and IMPLEMENTATION_PLAN files:

```bash
# Find untracked PROMPT*.md files
for f in PROMPT*.md IMPLEMENTATION_PLAN*.md; do
  if [[ -f "$f" ]] && ! git ls-files --error-unmatch "$f" &>/dev/null; then
    echo "ORPHAN: $f"
  fi
done
```

For each orphaned file found:
1. Show the file name and first 3 lines of content
2. Ask user: "Delete [filename]? (y/n)"
3. If yes, delete it

If `--all` flag is provided, delete all orphaned files without prompting.

### Step 4: Clean plugin caches

```bash
rm -rf ~/.claude/plugins/cache/*/lisa/*
```

Report: "Cleared plugin cache"

### Step 5: Check for orphaned skills

```bash
test -d ~/.claude/skills/lisa-guide && echo "ORPHAN" || echo "CLEAN"
```

If ORPHAN exists, remove it:
```bash
rm -rf ~/.claude/skills/lisa-guide
```

Report: "Removed orphaned skill"

### Step 6: Summary

```
Lisa cleanup complete!

Removed:
  - State file: .claude/lisa-loop.local.md
  - Log file: .claude/lisa-loop.log (847 lines)
  - Orphaned prompts: PROMPT-EXPANSION.md, IMPLEMENTATION_PLAN-DOCS.md
  - Plugin cache: 3 old versions (140KB)

Project is clean.
```

## Options

- `--force` - Clean state file even if a loop appears active
- `--all` - Delete all orphaned prompt files without prompting
- `--keep-logs` - Preserve log file for analysis
- `--dry-run` - Show what would be cleaned without doing it

## Why Prompt Files Become Orphaned

Lisa loops use `PROMPT.md` files to define tasks. These files are:
- Created manually by the user before starting a loop
- Never automatically deleted when the loop completes
- Left behind if the session crashes or is force-quit

Over time, completed task prompts accumulate as clutter. This command helps clean them up.
