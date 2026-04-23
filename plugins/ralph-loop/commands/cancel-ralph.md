---
description: "Cancel active Ralph Loop"
allowed-tools: ["Bash(ls .claude/ralph-loop-*.local.md 2>/dev/null:*)", "Bash(test -f .claude/ralph-loop-*.local.md:*)", "Bash(rm .claude/ralph-loop-*.local.md)", "Read(.claude/ralph-loop-*.local.md)", "Bash(grep -l * .claude/:*)"]
hide-from-slash-command-tool: "true"
---

# Cancel Ralph

To cancel the Ralph loop for this session:

1. Find the active state file for this session using Bash:
   ```
   ls .claude/ralph-loop-*.local.md 2>/dev/null || echo "NOT_FOUND"
   ```

2. **If NOT_FOUND**: Say "No active Ralph loop found."

3. **If files exist**, determine which belongs to this session:
   - Session-scoped file (default): `.claude/ralph-loop-${CLAUDE_CODE_SESSION_ID}.local.md`
   - Named loops: check each file's `session_id:` field in the frontmatter to match this session

4. **Once found**:
   - Read the file to get the current `iteration:` and `loop_id:` fields
   - Remove the file using Bash: `rm <filepath>`
   - Report: "Cancelled Ralph loop '<loop_id>' (was at iteration N)"

5. **If multiple loops are active** (named loops from multiple sessions):
   - List all active loops with their loop_id and iteration count
   - Cancel only the one belonging to this session (matching session_id)
   - Ask the user if they want to cancel others too
