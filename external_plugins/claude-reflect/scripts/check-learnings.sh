#!/bin/bash
# V3: INFORMS about learnings and saves backup (does NOT block)
# Used by PreCompact hook

QUEUE_FILE="$HOME/.claude/learnings-queue.json"
BACKUP_DIR="$HOME/.claude/learnings-backups"

if [ -f "$QUEUE_FILE" ]; then
  COUNT=$(jq 'length' "$QUEUE_FILE" 2>/dev/null || echo 0)
  if [ "$COUNT" -gt 0 ]; then
    # Create backup directory if needed
    mkdir -p "$BACKUP_DIR"

    # Save learnings to timestamped backup file
    BACKUP_FILE="$BACKUP_DIR/pre-compact-$(date +%Y%m%d-%H%M%S).json"
    cp "$QUEUE_FILE" "$BACKUP_FILE"

    # Output informational message (no blocking)
    echo ""
    echo "Note: $COUNT learning(s) backed up to $BACKUP_FILE"
    echo "Run /reflect in new session to process."
    echo ""
  fi
fi

exit 0
