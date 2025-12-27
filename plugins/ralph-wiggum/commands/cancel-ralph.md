---
description: "Cancel active Ralph Wiggum loop"
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/cancel-ralph.sh:*)"]
hide-from-slash-command-tool: "true"
---

# Cancel Ralph

Run this command to check for an active Ralph loop:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/cancel-ralph.sh"
```

Check the output above:

1. **If FOUND_LOOP=false**:
   - Say "No active Ralph loop found."

2. **If FOUND_LOOP=true**:
   - Use Bash: `rm .claude/ralph-loop.local.md`
   - Report: "Cancelled Ralph loop (was at iteration N)" where N is the ITERATION value from above.
