#!/bin/bash

# Ralph Loop Permission Setup
# Adds Edit/Write permission rules for .claude/ralph-loop.local.md
# to the user's global Claude Code settings so loops run without
# being interrupted by permission prompts.

set -euo pipefail

SETTINGS_FILE="$HOME/.claude/settings.json"
RULE_EDIT='Edit(.claude/ralph-loop.local.md)'
RULE_WRITE='Write(.claude/ralph-loop.local.md)'

# Ensure ~/.claude directory exists
mkdir -p "$HOME/.claude"

# Create settings.json if it doesn't exist
if [[ ! -f "$SETTINGS_FILE" ]]; then
  echo '{}' > "$SETTINGS_FILE"
fi

# Read current settings
CURRENT=$(cat "$SETTINGS_FILE")

# Validate JSON
if ! echo "$CURRENT" | jq empty 2>/dev/null; then
  echo "Error: $SETTINGS_FILE contains invalid JSON." >&2
  echo "Please fix the file manually before running this script." >&2
  exit 1
fi

# Check if rules already exist
HAS_EDIT=$(echo "$CURRENT" | jq -r --arg rule "$RULE_EDIT" '.permissions.allow // [] | map(select(. == $rule)) | length')
HAS_WRITE=$(echo "$CURRENT" | jq -r --arg rule "$RULE_WRITE" '.permissions.allow // [] | map(select(. == $rule)) | length')

if [[ "$HAS_EDIT" -gt 0 ]] && [[ "$HAS_WRITE" -gt 0 ]]; then
  echo "Permissions already configured in $SETTINGS_FILE"
  echo ""
  echo "Found:"
  echo "  - $RULE_EDIT"
  echo "  - $RULE_WRITE"
  echo ""
  echo "No changes needed."
  exit 0
fi

# Build list of rules to add (for reporting)
RULES_ADDED=()
if [[ "$HAS_EDIT" -eq 0 ]]; then
  RULES_ADDED+=("$RULE_EDIT")
fi
if [[ "$HAS_WRITE" -eq 0 ]]; then
  RULES_ADDED+=("$RULE_WRITE")
fi

# Add missing rules to settings (merge with existing allow array)
UPDATED=$(echo "$CURRENT" | jq \
  --arg edit "$RULE_EDIT" \
  --arg write "$RULE_WRITE" \
  --argjson has_edit "$HAS_EDIT" \
  --argjson has_write "$HAS_WRITE" \
  '
  .permissions //= {} |
  .permissions.allow //= [] |
  if $has_edit == 0 then .permissions.allow += [$edit] else . end |
  if $has_write == 0 then .permissions.allow += [$write] else . end
  ')

# Write updated settings atomically via temp file
TEMP_FILE="${SETTINGS_FILE}.tmp.$$"
echo "$UPDATED" > "$TEMP_FILE"
mv "$TEMP_FILE" "$SETTINGS_FILE"

echo "Permissions added to $SETTINGS_FILE"
echo ""
echo "Added:"
for rule in "${RULES_ADDED[@]}"; do
  echo "  - $rule"
done
echo ""
echo "Ralph Loop can now create and update its state file without"
echo "prompting for permission in any project."
