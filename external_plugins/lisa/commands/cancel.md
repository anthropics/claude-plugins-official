---
description: "Cancel active Lisa loop"
allowed-tools: ["Bash(test -f .claude/lisa-loop.local.md:*)", "Bash(rm .claude/lisa-loop.local.md)", "Read(.claude/lisa-loop.local.md)"]
hide-from-slash-command-tool: "true"
---

# Cancel Lisa

To cancel the Lisa loop:

1. Check if `.claude/lisa-loop.local.md` exists using Bash: `test -f .claude/lisa-loop.local.md && echo "EXISTS" || echo "NOT_FOUND"`

2. **If NOT_FOUND**: Say "No active Lisa loop found."

3. **If EXISTS**:
   - Read `.claude/lisa-loop.local.md` to get the current iteration number from the `iteration:` field
   - Remove the file using Bash: `rm .claude/lisa-loop.local.md`
   - Report: "Cancelled Lisa loop (was at iteration N)" where N is the iteration value
