#!/bin/bash
# Extract user messages from a Claude Code session file
# Usage: extract-session-learnings.sh <session-file> [--corrections-only]

SESSION_FILE="$1"
CORRECTIONS_ONLY="$2"

if [ -z "$SESSION_FILE" ]; then
  echo "Usage: extract-session-learnings.sh <session-file> [--corrections-only]"
  exit 1
fi

if [ ! -f "$SESSION_FILE" ]; then
  echo "Error: Session file not found: $SESSION_FILE"
  exit 1
fi

# Extract user messages, excluding meta/system messages and tool results
# Filter: type=user, not isMeta, extract text from content array
extract_messages() {
  jq -r '
    select(.type=="user" and .isMeta != true) |
    .message.content[]? |
    select(.type=="text") |
    .text
  ' "$SESSION_FILE" 2>/dev/null \
    | grep -v '^$' \
    | grep -v '^<' \
    | grep -v '^\[' \
    | grep -v '^{' \
    | grep -v 'tool_result' \
    | grep -v 'tool_use_id' \
    | grep -v '<command-' \
    | grep -v 'This session is being continued' \
    | grep -v '^Analysis:' \
    | grep -v '^\*\*' \
    | grep -v '^   -'
}

if [ "$CORRECTIONS_ONLY" = "--corrections-only" ]; then
  # Only messages with correction patterns
  extract_messages | grep -iE "(no,? use|don't use|stop using|never use|that's wrong|that's incorrect|not right|not correct|actually[,. ]|I meant|I said|I told you|I already told|you should use|you need to use|use .+ not|not .+, use|remember:)"
else
  # All user messages
  extract_messages
fi
