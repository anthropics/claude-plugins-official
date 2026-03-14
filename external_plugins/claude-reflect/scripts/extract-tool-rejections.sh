#!/bin/bash
# Extract corrections from tool rejections in Claude Code session files
# Usage: extract-tool-rejections.sh <session-file>
#
# Tool rejections contain high-quality corrections because the user
# explicitly stopped a tool and provided guidance.

SESSION_FILE="$1"

if [ -z "$SESSION_FILE" ]; then
  echo "Usage: extract-tool-rejections.sh <session-file>"
  exit 1
fi

if [ ! -f "$SESSION_FILE" ]; then
  echo "Error: Session file not found: $SESSION_FILE"
  exit 1
fi

# Extract the user's correction from tool rejections
# Pattern: "The user doesn't want to proceed... the user said:\n[CORRECTION]"
# The correction is on the line AFTER "the user said:"
jq -r '
  select(.type=="user") |
  select(.message.content | type == "array") |
  .message.content[] |
  select(.type=="tool_result") |
  select(.is_error==true) |
  select(.content | type == "string") |
  select(.content | contains("The user doesn'\''t want to proceed")) |
  .content
' "$SESSION_FILE" 2>/dev/null \
  | awk '/the user said:/{getline; print}' \
  | grep -v '^$'
