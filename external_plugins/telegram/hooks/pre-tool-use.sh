#!/bin/bash
set -euo pipefail

# PreToolUse hook for the Telegram channel plugin.
# If the request_permission MCP tool wrote a one-time approval token,
# consume it and auto-allow this tool call.
# If TELEGRAM_SKIP_PERMISSION_PROMPT is set, always auto-allow.

STATE_DIR="${TELEGRAM_STATE_DIR:-$HOME/.claude/channels/telegram}"
TOKEN_FILE="$STATE_DIR/permission-approved"
ENV_FILE="$STATE_DIR/.env"

cat > /dev/null

# Check if permissions are bypassed via .env
if [[ -f "$ENV_FILE" ]]; then
  if grep -q '^TELEGRAM_SKIP_PERMISSION_PROMPT=true' "$ENV_FILE" 2>/dev/null; then
    echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
    exit 0
  fi
fi

if [[ -f "$TOKEN_FILE" ]]; then
  rm -f "$TOKEN_FILE"
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
  exit 0
fi

exit 0
