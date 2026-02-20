#!/bin/bash

# Ralph Loop Cancel Script
# Removes the active Ralph loop state file (session-scoped when possible).

set -euo pipefail

sanitize_id() {
  echo "$1" | sed 's/[^A-Za-z0-9._-]/_/g'
}

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
STATE_DIR="$PROJECT_DIR/.claude"

SESSION_ID_RAW="${CLAUDE_SESSION_ID:-}"
if [[ "$SESSION_ID_RAW" == "null" ]]; then
  SESSION_ID_RAW=""
fi
SESSION_ID_SAFE="$(sanitize_id "$SESSION_ID_RAW")"

STATE_FILE="$STATE_DIR/ralph-loop.local.md"
if [[ -n "$SESSION_ID_SAFE" ]]; then
  STATE_FILE="$STATE_DIR/ralph-loop.${SESSION_ID_SAFE}.local.md"
fi

if [[ ! -f "$STATE_FILE" ]]; then
  echo "No active Ralph loop found."
  exit 0
fi

# Extract iteration from frontmatter if possible
FRONTMATTER=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$STATE_FILE" 2>/dev/null || true)
ITERATION=$(echo "$FRONTMATTER" | grep '^iteration:' | sed 's/iteration: *//' | tr -d '\r')
if [[ -z "$ITERATION" ]]; then
  ITERATION="?"
fi

rm "$STATE_FILE"
echo "Cancelled Ralph loop (was at iteration $ITERATION)"
