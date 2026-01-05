---
description: "Cancel active Ralph Wiggum loop"
allowed-tools: ["Bash"]
hide-from-slash-command-tool: "true"
---

# Cancel Ralph

**FIRST**: Execute this command using the Bash tool to cancel any active loop:

```
"${CLAUDE_PLUGIN_ROOT}/scripts/cancel-ralph-loop.sh"
```

The script handles everything - it will:
- Find and delete the loop state file if it exists
- Report whether a loop was cancelled and at what iteration
- Show the expected file location if no loop was found

Simply report the output to the user. No additional commands needed.
