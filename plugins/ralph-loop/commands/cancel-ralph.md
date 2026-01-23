---
description: "Cancel active Ralph Loop"
allowed-tools: ["Bash(ls .claude/ralph-loop-*.local.md:*)", "Bash(rm .claude/ralph-loop-*.local.md)", "Read(.claude/ralph-loop-*.local.md)"]
hide-from-slash-command-tool: "true"
---

# Cancel Ralph

Ralph state files are now session-specific to prevent context bleeding between concurrent sessions.

To cancel the Ralph loop for the CURRENT session:

1. Derive the session ID by running this Bash command:
   ```bash
   PROJECT_DIR="${HOME}/.claude/projects/$(pwd | tr '/' '-' | tr '.' '-')"
   CURRENT_TRANSCRIPT=$(ls -t "$PROJECT_DIR"/*.jsonl 2>/dev/null | grep -v '/agent-' | head -1)
   if [[ -n "$CURRENT_TRANSCRIPT" ]]; then
     SESSION_ID=$(basename "$CURRENT_TRANSCRIPT" .jsonl)
     STATE_FILE=".claude/ralph-loop-${SESSION_ID}.local.md"
     if [[ -f "$STATE_FILE" ]]; then
       ITERATION=$(grep '^iteration:' "$STATE_FILE" | sed 's/iteration: *//')
       rm "$STATE_FILE"
       echo "CANCELLED iteration=$ITERATION"
     else
       echo "NOT_FOUND"
     fi
   else
     echo "SESSION_UNKNOWN"
   fi
   ```

2. **If CANCELLED**: Report "Cancelled Ralph loop (was at iteration N)"

3. **If NOT_FOUND**: Say "No active Ralph loop found for this session."

4. **If SESSION_UNKNOWN**: Say "Could not determine session ID. Check if any ralph loops are active: `ls .claude/ralph-loop-*.local.md`"
