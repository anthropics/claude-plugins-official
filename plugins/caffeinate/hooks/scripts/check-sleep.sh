#!/bin/bash
# Caffeinate hook: Blocks sleep commands and suggests background tasks
set -euo pipefail

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')

if [[ -z "$command" ]]; then
  exit 0
fi

# Allow sleep if run_in_background is true - that's the whole point!
run_in_bg=$(echo "$input" | jq -r '.tool_input.run_in_background // false')
if [[ "$run_in_bg" == "true" ]]; then
  exit 0
fi

block_message='ACTION REQUIRED: Your sleep command was blocked. You MUST now call Bash again with the SAME command but add the parameter run_in_background: true. Do this immediately in your next tool call. Do not explain or apologize - just retry with run_in_background: true.'

output_block() {
  # Output JSON to stdout for blocking decision
  # Output message to stderr to feed back to Claude
  cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "$block_message"
  }
}
EOF
  exit 0
}

# Remove all quoted strings to avoid false positives
# Replace single and double quoted strings with placeholder
cmd_no_quotes=$(echo "$command" | sed -E "s/\"[^\"]*\"//g; s/'[^']*'//g")

# Check for sleep command patterns in the de-quoted command
# Pattern 1: Command starts with sleep
if [[ "$cmd_no_quotes" =~ (^|[[:space:]])sleep[[:space:]]+[0-9] ]]; then
  output_block
fi

# Pattern 2: sleep after any common separator (&&, ||, ;, |, do, then)
if [[ "$cmd_no_quotes" =~ (\&\&|;\||[[:space:]]do[[:space:]]|[[:space:]]then[[:space:]])[[:space:]]*sleep[[:space:]] ]]; then
  output_block
fi

# Pattern 3: Simple contains check - if "sleep " followed by number appears anywhere
if [[ "$cmd_no_quotes" =~ sleep[[:space:]]+[0-9] ]]; then
  output_block
fi

# Pattern 4: sleep with variable like $TIMEOUT or ${DELAY}
if [[ "$cmd_no_quotes" =~ sleep[[:space:]]+\$ ]]; then
  output_block
fi

# No sleep command detected - allow
exit 0
