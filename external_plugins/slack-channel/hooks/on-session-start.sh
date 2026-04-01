#!/bin/bash
# Hook: SessionStart — writes conversation ID so the slack-channel MCP server can find it.
# Receives JSON on stdin with session_id (stable across --resume).
# Writes to ~/.config/slack-channel/sessions/{pid}.json where pid is Claude Code's PID.

set -euo pipefail

STATE_DIR="${HOME}/.config/slack-channel/sessions"
mkdir -p "$STATE_DIR"

# Read hook input from stdin — use python3 instead of jq for portability
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('session_id',''))" 2>/dev/null)

if [ -z "$SESSION_ID" ]; then
    exit 0
fi

# Write conversation ID keyed by Claude Code's PID.
# Hooks are spawned by Claude Code, so $PPID = Claude Code's PID.
# The MCP server is also a child of Claude Code, so it reads this via os.getppid().
echo "{\"conversation_id\": \"$SESSION_ID\"}" > "$STATE_DIR/$PPID.json"
