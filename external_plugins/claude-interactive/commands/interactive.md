---
description: Toggle interactive search mode (human-in-the-loop result filtering)
argument-hint: [auto on|off|status]
allowed-tools: Bash, Read
---

# /interactive - Interactive Search Mode Control

Control how Claude handles search result filtering.

## Usage

- `/interactive` or `/interactive status` - Show current status
- `/interactive auto on` - Enable auto-mode (all searches become interactive)
- `/interactive auto off` - Disable auto-mode (use trigger phrases)

## Execute

Parse the argument and run the appropriate action:

### If argument is empty, "status", or "auto status"

Check if `.claude-interactive-automode` exists in project root:

```bash
if [ -f ".claude-interactive-automode" ]; then
  echo "[STATUS] Auto-mode is ENABLED"
  echo "All Grep, Glob, and WebSearch operations will prompt for result filtering."
else
  echo "[STATUS] Auto-mode is DISABLED"
  echo "Use trigger phrases like 'interactively' or 'let me pick' to filter results."
fi
```

Report the status to the user.

### If argument is "auto on"

Create the flag file:

```bash
touch ".claude-interactive-automode"
```

Report: "Auto-mode ENABLED. All search operations will now prompt for result filtering."

### If argument is "auto off"

Remove the flag file:

```bash
rm -f ".claude-interactive-automode"
```

Report: "Auto-mode DISABLED. Use trigger phrases to filter results."

## How Interactive Mode Works

1. You request a search (Grep, Glob, WebSearch)
2. Claude runs the search and shows numbered results
3. Claude asks which results to keep (via AskUserQuestion)
4. You pick: "1,3,5" or "All" or "None"
5. Claude continues using ONLY your selected results

This prevents irrelevant search results from polluting your context window.

## Trigger Phrases

When auto-mode is OFF, say:
- "search for X **interactively**"
- "find Y and **let me pick**"
- "grep for Z, **filter results** first"
