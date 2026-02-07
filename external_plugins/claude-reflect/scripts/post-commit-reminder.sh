#!/bin/bash
# Checks if a git commit just happened and reminds about /reflect
# Used by PostToolUse hook for Bash tool

QUEUE_FILE="$HOME/.claude/learnings-queue.json"

# Read JSON from stdin into variable
INPUT="$(cat -)"

# Exit if no input
[ -z "$INPUT" ] && exit 0

# Extract the command that was executed
COMMAND="$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)"

# Exit if no command
[ -z "$COMMAND" ] && exit 0

# Check if it was a git commit command (not amend)
if [[ "$COMMAND" == *"git commit"* && "$COMMAND" != *"--amend"* ]]; then
  # Build reminder message
  MSG="Git commit detected!"

  # Check queue
  if [ -f "$QUEUE_FILE" ]; then
    COUNT=$(jq 'length' "$QUEUE_FILE" 2>/dev/null || echo 0)
    if [ "$COUNT" -gt 0 ]; then
      MSG="$MSG You have $COUNT queued learning(s)."
    fi
  fi

  MSG="$MSG Feature complete? Run /reflect to process learnings."

  # Output proper JSON for hook response
  jq -n --arg msg "$MSG" '{
    "hookSpecificOutput": {
      "hookEventName": "PostToolUse",
      "additionalContext": $msg
    }
  }'
fi

exit 0
