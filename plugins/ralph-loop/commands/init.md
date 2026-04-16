---
description: "Configure permissions for seamless Ralph Loop operation"
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/init-permissions.sh:*)"]
---

# Ralph Loop Init

The Ralph Loop plugin needs to write to `.claude/ralph-loop.local.md` in each project to track loop state (iteration count, prompt, completion promise, etc.). By default, Claude Code will prompt for permission every time this file needs to be created or updated — which interrupts the loop flow and defeats the purpose of autonomous iteration.

This init command adds two permission rules to the user's **global** Claude Code settings (`~/.claude/settings.json`):

- `Edit(.claude/ralph-loop.local.md)` — allows updating the state file (e.g. incrementing iteration count)
- `Write(.claude/ralph-loop.local.md)` — allows creating the state file when starting a new loop

These rules apply across all projects so the user only needs to do this once.

**Before running the setup script, you MUST ask the user for confirmation.** Explain clearly what permissions will be added and where (`~/.claude/settings.json`), then ask if they would like to proceed. Only run the script below if they explicitly confirm.

If the user confirms, execute:

```!
"${CLAUDE_PLUGIN_ROOT}/scripts/init-permissions.sh"
```

After the script runs, relay its output to the user.
