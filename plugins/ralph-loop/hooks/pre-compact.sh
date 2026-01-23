#!/bin/bash
# Ralph Loop PreCompact Hook
# Clears Ralph state to allow context compaction to proceed
#
# When context is exhausted during a Ralph Loop, compaction is triggered.
# Without this hook, the stop hook would block compaction indefinitely.
# This hook ensures Ralph state is cleared BEFORE compaction begins.

set -euo pipefail

# Read hook input from stdin (PreCompact hook API)
HOOK_INPUT=$(cat)

# Extract session ID from transcript path for session-specific state file
# Compatible with both old and new state file naming
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path // empty')
SESSION_ID=""

if [[ -n "$TRANSCRIPT_PATH" ]] && [[ "$TRANSCRIPT_PATH" != "null" ]]; then
  SESSION_ID=$(basename "$TRANSCRIPT_PATH" .jsonl)
fi

# Track if we found and cleared any state
CLEARED=false

# Check for session-specific state file (new format)
if [[ -n "$SESSION_ID" ]]; then
  SESSION_STATE_FILE=".claude/ralph-loop-${SESSION_ID}.local.md"
  if [[ -f "$SESSION_STATE_FILE" ]]; then
    ITERATION=$(grep '^iteration:' "$SESSION_STATE_FILE" | sed 's/iteration: *//' || echo "unknown")
    echo "⚠️  Context compaction triggered during Ralph loop"
    echo "   Session: $SESSION_ID"
    echo "   Iteration: $ITERATION"
    echo "   Clearing Ralph state to allow compaction..."
    rm "$SESSION_STATE_FILE"
    CLEARED=true
  fi
fi

# Also check for legacy state file (old format without session ID)
LEGACY_STATE_FILE=".claude/ralph-loop.local.md"
if [[ -f "$LEGACY_STATE_FILE" ]]; then
  ITERATION=$(grep '^iteration:' "$LEGACY_STATE_FILE" | sed 's/iteration: *//' || echo "unknown")
  echo "⚠️  Context compaction triggered during Ralph loop"
  echo "   Iteration: $ITERATION"
  echo "   Clearing Ralph state (legacy format) to allow compaction..."
  rm "$LEGACY_STATE_FILE"
  CLEARED=true
fi

if [[ "$CLEARED" == "true" ]]; then
  echo ""
  echo "   Ralph loop has been stopped. After compaction completes,"
  echo "   you can restart the loop with /ralph-loop if needed."
fi

# Always exit 0 to allow compaction to proceed
exit 0
