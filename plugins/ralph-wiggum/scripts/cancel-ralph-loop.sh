#!/bin/bash

# Cancel Ralph Wiggum Loop Script
# Removes the ralph-loop state file to stop the loop

RALPH_STATE_FILE=".claude/ralph-loop.local.md"

if [[ -f "$RALPH_STATE_FILE" ]]; then
  # Extract iteration count before deleting
  ITERATION=$(grep '^iteration:' "$RALPH_STATE_FILE" | sed 's/iteration: *//')

  # Remove the state file
  rm "$RALPH_STATE_FILE"

  echo "✅ Ralph loop cancelled (was at iteration $ITERATION)"
else
  echo "ℹ️  No active Ralph loop found."
fi
