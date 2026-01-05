#!/bin/bash

# Cancel Ralph Loop Script
# Finds and removes the Ralph loop state file to stop the loop

set -euo pipefail

RALPH_STATE_FILE=".claude/ralph-loop.local.md"

if [[ -f "$RALPH_STATE_FILE" ]]; then
  # Extract iteration before deleting
  ITERATION=$(grep '^iteration:' "$RALPH_STATE_FILE" | sed 's/iteration: *//' || echo "unknown")

  # Actually delete the file to cancel the loop
  rm -f "$RALPH_STATE_FILE"

  echo "CANCELLED=true"
  echo "ITERATION=$ITERATION"
  echo ""
  echo "Ralph loop cancelled at iteration $ITERATION."
else
  echo "CANCELLED=false"
  echo ""
  echo "No active Ralph loop found in current directory."
  echo "State file location: $(pwd)/$RALPH_STATE_FILE"
fi
