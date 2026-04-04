#!/bin/bash

# Remote Control Stop Hook
# Polls for incoming remote commands by injecting a prompt that instructs
# Claude to call the RemoteTrigger API (OAuth is only available in-process).

set -euo pipefail

# Read hook input from stdin
HOOK_INPUT=$(cat)

STATE_FILE=".claude/remote-control.local.md"

if [[ ! -f "$STATE_FILE" ]]; then
  # No active remote-control session - allow exit
  exit 0
fi

# Parse YAML frontmatter (between the two --- markers)
FRONTMATTER=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$STATE_FILE")

ACTIVE=$(echo "$FRONTMATTER" | grep '^active:' | sed 's/active: *//')
TRIGGER_ID=$(echo "$FRONTMATTER" | grep '^trigger_id:' | sed 's/trigger_id: *//')
STATE_SESSION=$(echo "$FRONTMATTER" | grep '^session_id:' | sed 's/session_id: *//' || true)
HOOK_SESSION=$(echo "$HOOK_INPUT" | jq -r '.session_id // ""')
MAX_COMMANDS=$(echo "$FRONTMATTER" | grep '^max_commands:' | sed 's/max_commands: *//')
COMMANDS_EXECUTED=$(echo "$FRONTMATTER" | grep '^commands_executed:' | sed 's/commands_executed: *//')

# Session isolation: only the session that created the trigger should poll
if [[ -n "$STATE_SESSION" ]] && [[ "$STATE_SESSION" != "$HOOK_SESSION" ]]; then
  exit 0
fi

# If active is explicitly false, allow exit
if [[ "$ACTIVE" == "false" ]]; then
  rm -f "$STATE_FILE"
  exit 0
fi

# Validate trigger_id exists
if [[ -z "$TRIGGER_ID" ]] || [[ "$TRIGGER_ID" == "null" ]] || [[ "$TRIGGER_ID" == "PENDING" ]]; then
  echo "⚠️  Remote control: No trigger_id in state file. Allowing exit." >&2
  exit 0
fi

# Check max_commands limit
if [[ "$MAX_COMMANDS" =~ ^[0-9]+$ ]] && [[ "$MAX_COMMANDS" -gt 0 ]]; then
  if [[ "$COMMANDS_EXECUTED" =~ ^[0-9]+$ ]] && [[ $COMMANDS_EXECUTED -ge $MAX_COMMANDS ]]; then
    echo "🛑 Remote control: Max commands ($MAX_COMMANDS) executed. Shutting down." >&2
    rm -f "$STATE_FILE"
    exit 0
  fi
fi

# Update last_poll_at timestamp in state file (portable: works on Linux and macOS)
TEMP_FILE="${STATE_FILE}.tmp.$$"
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
sed "s/^last_poll_at: .*/last_poll_at: \"$NOW\"/" "$STATE_FILE" > "$TEMP_FILE"
mv "$TEMP_FILE" "$STATE_FILE"

# Build system message
COMMANDS_INFO=""
if [[ "$MAX_COMMANDS" =~ ^[0-9]+$ ]] && [[ "$MAX_COMMANDS" -gt 0 ]]; then
  COMMANDS_INFO=" | Commands: ${COMMANDS_EXECUTED:-0}/$MAX_COMMANDS"
fi
SYSTEM_MSG="🔌 Remote control listening (trigger: ${TRIGGER_ID})${COMMANDS_INFO} | Send commands via RemoteTrigger API"

# Build the poll prompt. Claude (in-session) will call RemoteTrigger directly
# since it has the OAuth token available that shell scripts cannot access.
POLL_PROMPT="You have an active remote-control session.

**Action required:** Use the RemoteTrigger tool to poll for pending commands:
- action: run
- trigger_id: ${TRIGGER_ID}

Then handle the API response as follows:

**If no command is pending** (empty response, null command, or status indicates no work):
- Output: \"🔌 Remote control: No pending commands. Listening for input on trigger \`${TRIGGER_ID}\`.\"
- Do NOT take any other action.

**If the response contains a command** (non-empty \`command\` or \`prompt\` field):
- Announce: \"📨 Received remote command: [command text]\"
- Execute the command faithfully as instructed
- After completing, increment commands_executed in the state file:
  \`\`\`bash
  CURRENT=\$(grep '^commands_executed:' ${STATE_FILE} | sed 's/commands_executed: *//')
  sed -i \"s/^commands_executed: .*/commands_executed: \$((CURRENT + 1))/\" ${STATE_FILE}
  \`\`\`

**If the command text is exactly \`SHUTDOWN\` or the response contains \`shutdown: true\`**:
- Set active to false in the state file: \`sed -i 's/^active: .*/active: false/' ${STATE_FILE}\`
- Output: \"🛑 Remote control session terminated by external command.\"
- Do NOT execute anything else.

**If the API call fails** (error, timeout, non-200 response):
- Output the error clearly
- Do NOT modify the state file
- The session will remain active and listening.

After handling the response, you are done. The stop hook will fire again on the next natural exit."

# Output JSON to block exit and inject the poll prompt
jq -n \
  --arg prompt "$POLL_PROMPT" \
  --arg msg "$SYSTEM_MSG" \
  '{
    "decision": "block",
    "reason": $prompt,
    "systemMessage": $msg
  }'

exit 0
