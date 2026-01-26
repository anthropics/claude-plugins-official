#!/bin/bash
# migrate-to-sessions.sh - Migrate from single-file state to session-based state

set -e

STATE_DIR="$HOME/.claude/spire"
OLD_STATE_FILE="$STATE_DIR/state.json"
OLD_BACKUP_DIR="$STATE_DIR/backups"
SESSIONS_DIR="$STATE_DIR/sessions"

# Check if legacy state exists
if [[ ! -f "$OLD_STATE_FILE" ]]; then
  echo "No legacy state file found. Nothing to migrate."
  exit 0
fi

# Check if already migrated
if [[ -f "$SESSIONS_DIR/default/state.json" ]]; then
  echo "Migration already completed."
  echo "Session state at: $SESSIONS_DIR/default/state.json"
  exit 0
fi

# Create sessions directory
mkdir -p "$SESSIONS_DIR"

# Create 'default' session for legacy state
DEFAULT_SESSION_DIR="$SESSIONS_DIR/default"
mkdir -p "$DEFAULT_SESSION_DIR/backups"

# Copy state file (preserve original)
echo "Migrating legacy state to 'default' session..."
cp "$OLD_STATE_FILE" "$DEFAULT_SESSION_DIR/state.json"

# Update metadata to mark as migrated
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
jq --arg ts "$TIMESTAMP" \
  '.metadata.migratedFrom = "legacy" | .metadata.migratedAt = $ts' \
  "$DEFAULT_SESSION_DIR/state.json" > "${DEFAULT_SESSION_DIR}/state.json.tmp"
mv "${DEFAULT_SESSION_DIR}/state.json.tmp" "$DEFAULT_SESSION_DIR/state.json"

# Copy backups
if [[ -d "$OLD_BACKUP_DIR" ]] && [[ -n "$(ls -A "$OLD_BACKUP_DIR" 2>/dev/null)" ]]; then
  echo "Migrating $(ls "$OLD_BACKUP_DIR" | wc -l) backup files..."
  cp -r "$OLD_BACKUP_DIR"/* "$DEFAULT_SESSION_DIR/backups/" 2>/dev/null || true
fi

# Create marker file
echo "migrated" > "$DEFAULT_SESSION_DIR/.migrated-from-legacy"

echo ""
echo "✓ Migration complete!"
echo "  Legacy state: $OLD_STATE_FILE"
echo "  New location: $DEFAULT_SESSION_DIR/state.json"
echo ""
echo "The old files are preserved. You can delete them manually after verifying:"
echo "  rm $OLD_STATE_FILE"
echo "  rm -rf $OLD_BACKUP_DIR"