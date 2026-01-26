#!/bin/bash
# state-helpers.sh - State management functions for spire
# This script provides helper functions for managing ~/.claude/spire/state.json

# State file location
STATE_DIR="${STATE_DIR:-$HOME/.claude/spire}"
STATE_FILE="${STATE_FILE:-$STATE_DIR/state.json}"
BACKUP_DIR="${BACKUP_DIR:-$STATE_DIR/backups}"

# Get current Claude session ID
get_current_session_id() {
  local session_env_dir="$HOME/.claude/session-env"

  if [[ -d "$session_env_dir" ]]; then
    # Return most recently modified session directory name
    ls -t "$session_env_dir" 2>/dev/null | head -1
  else
    # Fallback for development/testing or edge cases
    echo "default"
  fi
}

# Ensure state directory exists
ensure_state_dir() {
  mkdir -p "$STATE_DIR"
  mkdir -p "$BACKUP_DIR"

  # Create sessions directory
  mkdir -p "$STATE_DIR/sessions"

  # Auto-migrate legacy state if detected
  local legacy_state_file="$STATE_DIR/state.json"
  local default_session_dir="$STATE_DIR/sessions/default"

  if [[ -f "$legacy_state_file" ]] && [[ ! -f "$default_session_dir/state.json" ]]; then
    echo "Detected legacy state file. Migrating to session-based system..."

    # Create default session directory
    mkdir -p "$default_session_dir/backups"

    # Copy state file (preserve original)
    cp "$legacy_state_file" "$default_session_dir/state.json"

    # Update metadata to mark as migrated
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    jq --arg ts "$timestamp" \
      '.metadata.migratedFrom = "legacy" | .metadata.migratedAt = $ts' \
      "$default_session_dir/state.json" > "${default_session_dir}/state.json.tmp" && \
      mv "${default_session_dir}/state.json.tmp" "$default_session_dir/state.json"

    # Copy backups
    if [[ -d "$STATE_DIR/backups" ]] && [[ -n "$(ls -A "$STATE_DIR/backups" 2>/dev/null)" ]]; then
      echo "Migrating $(ls "$STATE_DIR/backups" | wc -l) backup files..."
      cp -r "$STATE_DIR/backups"/* "$default_session_dir/backups/" 2>/dev/null || true
    fi

    # Create marker file
    echo "migrated" > "$default_session_dir/.migrated-from-legacy"

    echo "✓ Migration complete!"
    echo "  Legacy state: $legacy_state_file"
    echo "  New location: $default_session_dir/state.json"
    echo ""
    echo "The old files are preserved. You can delete them manually after verifying:"
    echo "  rm $legacy_state_file"
    echo "  rm -rf $STATE_DIR/backups"
  fi
}

# Load current state from file
# Returns: JSON content of state file, or empty state if file doesn't exist
# Args: [session_id] - optional, defaults to current session
load_state() {
  ensure_state_dir
  local session_id="${1:-$(get_current_session_id)}"
  local state_file="$STATE_DIR/sessions/$session_id/state.json"

  mkdir -p "$(dirname "$state_file")"

  if [[ -f "$state_file" ]]; then
    cat "$state_file"
  else
    # Return empty state structure
    echo '{
      "version": "2.0.0",
      "run": {"active": false},
      "player": {},
      "deck": {},
      "relics": {},
      "map": {},
      "combat": {},
      "rewards": {},
      "shop": {},
      "event": {},
      "history": {},
      "preferences": {},
      "metadata": {"createdAt": null, "lastUpdate": null, "screenshots": [], "migratedFrom": null}
    }'
  fi
}

# Save state to file with automatic backup
# Args: new_state (JSON string)
# Args: [session_id] - optional, defaults to current session
save_state() {
  local new_state="$1"
  local session_id="${2:-$(get_current_session_id)}"
  local state_file="$STATE_DIR/sessions/$session_id/state.json"
  local backup_dir="$STATE_DIR/sessions/$session_id/backups"

  # Create session directories
  mkdir -p "$(dirname "$state_file")"
  mkdir -p "$backup_dir"

  # Backup existing state (if any)
  if [[ -f "$state_file" ]]; then
    local timestamp
    timestamp=$(date +%Y%m%d-%H%M%S)
    cp "$state_file" "$backup_dir/state-$timestamp.json"
    rotate_backups "$backup_dir"
  fi

  # Write new state
  echo "$new_state" > "$state_file"

  # Update metadata timestamp
  local now
  now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  jq --arg ts "$now" '.metadata.lastUpdate = $ts' "$state_file" > "${state_file}.tmp" && mv "${state_file}.tmp" "$state_file"
}

# Update specific field in state using jq
# Args: jq_filter (e.g., '.run.floor = 7')
# Args: [session_id] - optional, defaults to current session
update_state() {
  local jq_filter="$1"
  local session_id="${2:-$(get_current_session_id)}"
  local state_file="$STATE_DIR/sessions/$session_id/state.json"
  local backup_dir="$STATE_DIR/sessions/$session_id/backups"

  ensure_state_dir

  # Apply jq filter
  if [[ -f "$state_file" ]]; then
    # Create backup before modifying
    local timestamp
    timestamp=$(date +%Y%m%d-%H%M%S)
    cp "$state_file" "$backup_dir/state-$timestamp.json"

    # Apply jq filter
    jq "$jq_filter" "$state_file" > "${state_file}.tmp" && mv "${state_file}.tmp" "$state_file"

    # Update metadata timestamp
    local now
    now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    jq --arg ts "$now" '.metadata.lastUpdate = $ts' "$state_file" > "${state_file}.tmp" && mv "${state_file}.tmp" "$state_file"

    rotate_backups "$backup_dir"
  fi
}

# Get specific value from state
# Args: jq_expression (e.g., '.run.character')
# Args: [session_id] - optional, defaults to current session
get_state_value() {
  local jq_expression="$1"
  local session_id="${2:-$(get_current_session_id)}"
  load_state "$session_id" | jq -r "$jq_expression"
}

# List all sessions
# Args: [days] - optional, filter sessions older than N days
list_sessions() {
  local days="${1:-}"
  local sessions_dir="$STATE_DIR/sessions"

  if [[ ! -d "$sessions_dir" ]] || [[ -z "$(ls -A "$sessions_dir" 2>/dev/null)" ]]; then
    echo "No sessions found."
    return 0
  fi

  echo "=== Spire-V2 Sessions ==="
  for session_dir in "$sessions_dir"/*/; do
    local session_id=$(basename "$session_dir")
    local state_file="$session_dir/state.json"

    if [[ -f "$state_file" ]]; then
      local character=$(jq -r '.run.character // "Unknown"' "$state_file")
      local floor=$(jq -r '.run.floor // "0"' "$state_file")
      local active=$(jq -r '.run.active // false' "$state_file")
      local last_update=$(jq -r '.metadata.lastUpdate // "Never"' "$state_file")

      echo ""
      echo "Session: $session_id"
      echo "  Character: $character"
      echo "  Floor: $floor"
      echo "  Active: $active"
      echo "  Last Update: $last_update"
    fi
  done
}

# Display a specific session's state
# Args: session_id
switch_session() {
  local target_session_id="$1"
  local sessions_dir="$STATE_DIR/sessions"
  local target_dir="$sessions_dir/$target_session_id"

  if [[ ! -d "$target_dir" ]]; then
    echo "Error: Session '$target_session_id' not found."
    echo "Use 'list_sessions' to see available sessions."
    return 1
  fi

  # Note: This doesn't change the current Claude session
  # It just displays the requested session's state
  echo "Displaying session: $target_session_id"
  show_state "$target_session_id"
}

# Cleanup sessions older than N days
# Args: [days] - optional, default 30
cleanup_sessions() {
  local days_old="${1:-30}"
  local sessions_dir="$STATE_DIR/sessions"

  echo "Cleaning up sessions older than $days_old days..."

  local count=0
  find "$sessions_dir" -maxdepth 1 -type d -mtime +$days_old | while read -r session_dir; do
    local session_id=$(basename "$session_dir")
    if [[ "$session_id" != "sessions" ]]; then  # Skip parent dir
      echo "Removing old session: $session_id"
      rm -rf "$session_dir"
      ((count++))
    fi
  done

  echo "Cleanup complete. $count sessions removed."
}

# Delete a specific session
# Args: session_id
delete_session() {
  local session_id="$1"
  local session_dir="$STATE_DIR/sessions/$session_id"

  if [[ ! -d "$session_dir" ]]; then
    echo "Error: Session '$session_id' not found."
    return 1
  fi

  echo "WARNING: This will permanently delete session '$session_id' and all its state."
  echo "Press Ctrl+C to cancel, or Enter to continue..."
  read

  rm -rf "$session_dir"
  echo "Session deleted: $session_id"
}

# Clear transient state (combat, rewards, shop, event)
# Useful when moving between game screens
clear_transient() {
  update_state '
    .combat = {} |
    .rewards = {"cards": [], "relics": []} |
    .shop = {"cards": [], "relics": [], "potions": [], "purgeCost": null} |
    .event = {}
  '
}

# Reset all state (for new run or manual reset)
reset_state() {
  ensure_state_dir

  # Backup current state before reset
  if [[ -f "$STATE_FILE" ]]; then
    local timestamp
    timestamp=$(date +%Y%m%d-%H%M%S)
    cp "$STATE_FILE" "$BACKUP_DIR/state-reset-$timestamp.json"
  fi

  # Write empty state
  cat > "$STATE_FILE" << 'EOF'
{
  "version": "2.0.0",
  "run": {
    "id": null,
    "active": false,
    "character": null,
    "ascension": null,
    "floor": null,
    "act": null,
    "screen": null
  },
  "player": {
    "hp": {"current": null, "max": null},
    "gold": null,
    "potions": {"slots": 2, "slot1": null, "slot2": null, "slot3": null}
  },
  "deck": {
    "cards": [],
    "size": 0,
    "attacks": [],
    "skills": [],
    "powers": [],
    "status": [],
    "curses": [],
    "seen": [],
    "acquired": {}
  },
  "relics": {
    "owned": [],
    "starter": null,
    "boss": null,
    "acquired": {}
  },
  "map": {
    "path": [],
    "currentNode": null,
    "upcoming": [],
    "actNodes": {"act1": 0, "act2": 0, "act3": 0, "act4": 0}
  },
  "combat": {
    "enemies": [],
    "hand": [],
    "energy": null,
    "block": null,
    "turn": null
  },
  "rewards": {
    "cards": [],
    "relics": []
  },
  "shop": {
    "cards": [],
    "relics": [],
    "potions": [],
    "purgeCost": null
  },
  "event": {
    "name": null,
    "choices": [],
    "context": {}
  },
  "history": {
    "floors": [],
    "choices": [],
    "events": [],
    "cardsTaken": {},
    "relicsTaken": {}
  },
  "preferences": {
    "riskTolerance": "medium",
    "deckSizePref": "medium",
    "favoriteArchetypes": [],
    "cardTierOverrides": {}
  },
  "metadata": {
    "createdAt": null,
    "lastUpdate": null,
    "screenshots": [],
    "migratedFrom": null
  }
}
EOF

  echo "State reset. Backup saved as state-reset-$timestamp.json"
}

# Keep only last 10 backups, delete older ones
rotate_backups() {
  ensure_state_dir
  ls -t "$BACKUP_DIR"/state-*.json 2>/dev/null | tail -n +11 | xargs -r rm -f
}

# List all backups
list_backups() {
  ensure_state_dir
  if [[ -d "$BACKUP_DIR" ]] && [[ -n "$(ls -A "$BACKUP_DIR" 2>/dev/null)" ]]; then
    echo "Available backups:"
    ls -lh "$BACKUP_DIR"/state-*.json 2>/dev/null | awk '{print "  " $9 " (" $5 " - " $6 " " $7 " " $8 ")"}'
  else
    echo "No backups found."
  fi
}

# Restore from specific backup
# Args: backup_filename (e.g., "state-20250125-143000.json")
restore_backup() {
  local backup_file="$1"
  local backup_path="$BACKUP_DIR/$backup_file"

  if [[ -f "$backup_path" ]]; then
    # Backup current state before restoring
    local timestamp
    timestamp=$(date +%Y%m%d-%H%M%S)
    cp "$STATE_FILE" "$BACKUP_DIR/state-pre-restore-$timestamp.json"

    # Restore backup
    cp "$backup_path" "$STATE_FILE"
    echo "Restored from $backup_file"
    echo "Previous state backed up as state-pre-restore-$timestamp.json"
  else
    echo "Backup file not found: $backup_path"
    return 1
  fi
}

# Validate state file JSON
validate_state() {
  if ! jq empty "$STATE_FILE" 2>/dev/null; then
    echo "Error: Invalid JSON in $STATE_FILE"
    return 1
  fi

  # Check required fields
  local missing
  missing=$(jq -r '
    if .version == null then "version" else empty end,
    if .run == null then "run" else empty end,
    if .player == null then "player" else empty end,
    if .deck == null then "deck" else empty end,
    if .relics == null then "relics" else empty end
  ' "$STATE_FILE" 2>/dev/null)

  if [[ -n "$missing" ]]; then
    echo "Warning: State missing top-level fields: $missing"
    return 1
  fi

  echo "State file is valid."
  return 0
}

# Show state summary (for debugging)
show_state() {
  echo "=== Spire-V2 State ==="
  echo "File: $STATE_FILE"
  echo ""

  if [[ -f "$STATE_FILE" ]]; then
    echo "Run:"
    jq '{id, active, character, ascension, floor, act, screen}' "$STATE_FILE" 2>/dev/null || echo "  (invalid JSON)"
    echo ""

    echo "Player:"
    jq '.player' "$STATE_FILE" 2>/dev/null || echo "  (invalid JSON)"
    echo ""

    echo "Deck:"
    jq '{size: .deck.size, attacks: (.deck.attacks | length), skills: (.deck.skills | length)}' "$STATE_FILE" 2>/dev/null || echo "  (invalid JSON)"
    echo ""

    echo "Relics:"
    jq '{owned: (.relics.owned | length), starter, boss}' "$STATE_FILE" 2>/dev/null || echo "  (invalid JSON)"
  else
    echo "State file does not exist."
  fi
}

# Export current state to markdown (for run tracker)
# Args: output_file (optional, defaults to ~/Documents/STS-Runs/[run-id].md)
export_to_markdown() {
  local output_file="${1:-}"
  local run_id
  run_id=$(get_state_value '.run.id // "unknown"')

  if [[ -z "$output_file" ]]; then
    local run_dir="$HOME/Documents/STS-Runs"
    mkdir -p "$run_dir"
    output_file="$run_dir/${run_id}.md"
  fi

  # Generate markdown from state
  cat > "$output_file" << EOF
# Slay the Spire Run Tracker

**Run ID:** $run_id
**Generated:** $(date -u +%Y-%m-%d\ %H:%M:%S\ UTC)

## Run Overview

$(jq -r '
  "- **Character:** " + (.run.character // "Unknown") +
  "\n- **Ascension:** " + (.run.ascension | tostring) +
  "\n- **Current Floor:** " + (.run.floor | tostring) +
  "\n- **Current Act:** " + (.run.act | tostring) +
  "\n- **Run Active:** " + (if .run.active then "Yes" else "No" end)
' "$STATE_FILE")

## Player State

$(jq -r '
  "- **HP:** " + (.player.hp.current | tostring) + " / " + (.player.hp.max | tostring) +
  "\n- **Gold:** " + (.player.gold | tostring) +
  "\n- **Potions:** " + (.player.potions.slot1 // "Empty") + ", " + (.player.potions.slot2 // "Empty")
' "$STATE_FILE")

## Deck

$(jq -r '"- **Size:** " + (.deck.size | tostring) + " cards"' "$STATE_FILE")

### Cards

$(jq -r '.deck.cards | join(", ")' "$STATE_FILE")

## Relics

$(jq -r '.relics.owned | join(", ")' "$STATE_FILE")

## History

$(jq -r '.history.floors[] | "- Floor " + (.floor | tostring) + ": " + .type + " - " + .outcome' "$STATE_FILE")

---
*Generated by spire - https://github.com/bensmith/spire*
EOF

  echo "Exported run state to: $output_file"
}

# ============================================================================
# Parallel Processing Helper Functions (v2.2.0+)
# ============================================================================

# Check if parallel processing is enabled and not disabled by circuit breaker
# Returns: 0 (enabled) or 1 (disabled)
check_parallel_support() {
  local session_id="${1:-$(get_current_session_id)}"
  local state_file="$STATE_DIR/sessions/$session_id/state.json"

  # Check if state file exists
  if [[ ! -f "$state_file" ]]; then
    # No state yet, assume enabled for first use
    return 0
  fi

  # Check if parallel processing is explicitly disabled
  local disabled
  disabled=$(jq -r '.metadata.parallelProcessing.disabled // false' "$state_file" 2>/dev/null)

  if [[ "$disabled" == "true" ]]; then
    return 1
  fi

  return 0
}

# Record parallel processing usage
# Args: session_id (optional)
record_parallel_usage() {
  local session_id="${1:-$(get_current_session_id)}"
  local state_file="$STATE_DIR/sessions/$session_id/state.json"

  if [[ -f "$state_file" ]]; then
    local now
    now=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    update_state "
      .metadata.parallelProcessing.enabled = true |
      .metadata.parallelProcessing.lastUsed = \"$now\"
    " "$session_id"
  fi
}

# Record parallel processing failure (for circuit breaker)
# Args: failure_reason (optional)
record_parallel_failure() {
  local failure_reason="${1:-Unknown error}"
  local session_id=$(get_current_session_id)
  local state_file="$STATE_DIR/sessions/$session_id/state.json"

  if [[ -f "$state_file" ]]; then
    # Increment failure counter
    update_state '
      .metadata.parallelProcessing.failures += 1 |
      .metadata.parallelProcessing.lastFailure = $failure_reason
    ' "$session_id"

    # Check if we should disable parallel processing (3+ failures)
    local failures
    failures=$(get_state_value '.metadata.parallelProcessing.failures // 0' "$session_id")

    if [[ "$failures" -ge 3 ]]; then
      update_state '.metadata.parallelProcessing.disabled = true' "$session_id"
      echo "⚠️ Parallel processing disabled after $failures consecutive failures."
      echo "  Last failure: $failure_reason"
      echo "  To re-enable: update_state '.metadata.parallelProcessing.disabled = false'"
    fi
  fi
}

# Record fallback to sequential mode
# Args: fallback_reason (optional)
record_fallback_usage() {
  local fallback_reason="${1:-Agent unavailable}"
  local session_id=$(get_current_session_id)
  local state_file="$STATE_DIR/sessions/$session_id/state.json"

  if [[ -f "$state_file" ]]; then
    update_state '
      .metadata.parallelProcessing.fallbackCount += 1 |
      .metadata.parallelProcessing.lastFallback = $fallback_reason
    ' "$session_id"
  fi
}

# Aggregate multiple screenshot analysis results
# Args: result_json1 result_json2 ... (multiple JSON objects)
# Returns: Merged JSON with combined extracted_data and universal_data
aggregate_screenshots() {
  local results=("$@")
  local merged='{"screenshots": [], "universal_data": {}}'
  local universal_merged='{}'

  # Collect all results
  for result in "${results[@]}"; do
    # Extract screen type and extracted data
    local screen_type=$(echo "$result" | jq -r '.screen_type // "unknown"')
    local extracted_data=$(echo "$result" | jq '.extracted_data // {}')
    local universal_data=$(echo "$result" | jq '.universal_data // {}')

    # Add to screenshots array
    merged=$(echo "$merged" | jq --arg st "$screen_type" --argjson ed "$extracted_data" \
      '.screenshots += [{"screen_type": $st, "extracted_data": $ed}]')

    # Merge universal data (prioritize non-null values)
    universal_merged=$(echo "$universal_merged" | jq --argjson ud "$universal_data" '
      .hp_current = ($ud.hp_current // .hp_current) |
      .hp_max = ($ud.hp_max // .hp_max) |
      .gold = ($ud.gold // .gold) |
      .potions = ($ud.potions // .potions) |
      .relics_visible = (.relics_visible + ($ud.relics_visible // [])) | unique
    ')
  done

  # Add universal data to merged result
  merged=$(echo "$merged" | jq --argjson ud "$universal_merged" '.universal_data = $ud')

  echo "$merged"
}

# Check if background agents are running
# Args: session_id (optional)
# Returns: 0 (agents running) or 1 (no agents)
check_agents_running() {
  local session_id="${1:-$(get_current_session_id)}"
  local state_file="$STATE_DIR/sessions/$session_id/state.json"

  if [[ ! -f "$state_file" ]]; then
    return 1
  fi

  local status_monitor
  local card_advisor

  status_monitor=$(jq -r '.metadata.agents.statusMonitor.running // false' "$state_file" 2>/dev/null)
  card_advisor=$(jq -r '.metadata.agents.cardAdvisor.running // false' "$state_file" 2>/dev/null)

  if [[ "$status_monitor" == "true" ]] || [[ "$card_advisor" == "true" ]]; then
    return 0
  fi

  return 1
}

# Mark agent as running or stopped
# Args: agent_name (status_monitor|card_advisor), state (true|false)
set_agent_status() {
  local agent_name="$1"
  local agent_state="$2"
  local session_id=$(get_current_session_id)
  local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

  case "$agent_name" in
    status_monitor)
      update_state "
        .metadata.agents.statusMonitor.running = $agent_state |
        .metadata.agents.statusMonitor.lastUpdate = \"$timestamp\"
      " "$session_id"
      ;;
    card_advisor)
      update_state "
        .metadata.agents.cardAdvisor.running = $agent_state |
        .metadata.agents.cardAdvisor.lastUpdate = \"$timestamp\"
      " "$session_id"
      ;;
    *)
      echo "Unknown agent: $agent_name"
      return 1
      ;;
  esac
}

# Reset circuit breaker (re-enable parallel processing)
# Args: session_id (optional)
reset_parallel_circuit_breaker() {
  local session_id="${1:-$(get_current_session_id)}"

  update_state '
    .metadata.parallelProcessing.disabled = false |
    .metadata.parallelProcessing.failures = 0 |
    .metadata.parallelProcessing.lastFallback = null |
    .metadata.parallelProcessing.lastFailure = null
  ' "$session_id"

  echo "✓ Parallel processing circuit breaker reset."
  echo "  Failures cleared, parallel processing re-enabled."
}

# Show parallel processing statistics
# Args: session_id (optional)
show_parallel_stats() {
  local session_id="${1:-$(get_current_session_id)}"
  local state_file="$STATE_DIR/sessions/$session_id/state.json"

  if [[ ! -f "$state_file" ]]; then
    echo "No state file found for session: $session_id"
    return 1
  fi

  echo "=== Parallel Processing Statistics ==="
  echo ""
  echo "Status:"
  jq -r '
    "  Enabled: " + (.metadata.parallelProcessing.enabled // "true" | tostring) +
    "\n  Disabled (circuit breaker): " + (.metadata.parallelProcessing.disabled // "false" | tostring) +
    "\n  Failures: " + (.metadata.parallelProcessing.failures // 0 | tostring) +
    "\n  Fallbacks: " + (.metadata.parallelProcessing.fallbackCount // 0 | tostring)
  ' "$state_file" 2>/dev/null || echo "  (no data)"

  echo ""
  echo "Last Usage:"
  jq -r '
    "  Last used: " + (.metadata.parallelProcessing.lastUsed // "Never") +
    "\n  Last failure: " + (.metadata.parallelProcessing.lastFailure // "None") +
    "\n  Last fallback: " + (.metadata.parallelProcessing.lastFallback // "None")
  ' "$state_file" 2>/dev/null || echo "  (no data)"

  echo ""
  echo "Background Agents:"
  jq -r '
    "  Status Monitor: " + (.metadata.agents.statusMonitor.running // "false" | tostring) +
    "\n  Card Advisor: " + (.metadata.agents.cardAdvisor.running // "false" | tostring)
  ' "$state_file" 2>/dev/null || echo "  (no data)"
}

# ============================================================================
# Catchup workflow functions
# ============================================================================
start_catchup() {
  local workflow_dir="$STATE_DIR/catchup-workflows"
  local workflow_id=$(date +%Y%m%d-%H%M%S)
  local workflow_file="$workflow_dir/$workflow_id.json"

  mkdir -p "$workflow_dir"

  echo '{
    "workflow_id": "'$workflow_id'",
    "current_step": 1,
    "total_steps": 3,
    "steps": [
      {"name": "deck_view", "description": "Deck View - Shows current deck composition", "completed": false},
      {"name": "map_view", "description": "Map View - Shows current floor and path", "completed": false},
      {"name": "current_screen", "description": "Current Screen - Shows current context", "completed": false}
    ],
    "state": {}
  }' > "$workflow_file"

  echo "Starting catchup workflow (ID: $workflow_id)"
  echo "Please provide screenshots in the following order:"
  echo ""
  local steps=("deck_view" "map_view" "current_screen")
  for ((i=0; i<${#steps[@]}; i++)); do
    local step_name="${steps[i]}"
    local step_desc=$(jq -r ".steps[$i].description" "$workflow_file")
    echo "$((i+1)). $step_name - $step_desc"
  done
  echo ""
  echo "Use: /spire <screenshot_path> to provide the next screenshot"
  echo "Use: /spire catchup status to check progress"
  echo "Use: /spire catchup cancel to abort"
}

complete_catchup_step() {
  local workflow_file="$1"
  local step_index="$2"
  local screenshot_data="$3"

  jq --argjson step_index "$step_index" \
     --argjson screenshot_data "$screenshot_data" \
     '.steps[($step_index | tonumber)].completed = true |
      .state.steps[($step_index | tonumber)].data = $screenshot_data' \
     "$workflow_file" > "${workflow_file}.tmp" && mv "${workflow_file}.tmp" "$workflow_file"

  local current_step=$(jq '.current_step' "$workflow_file")
  local total_steps=$(jq '.total_steps' "$workflow_file")

  if [[ "$current_step" -lt "$total_steps" ]]; then
    local next_step=$((current_step + 1))
    jq '.current_step = $next_step' "$workflow_file" > "${workflow_file}.tmp" && mv "${workflow_file}.tmp" "$workflow_file"
    echo "Step $current_step completed. Please provide screenshot for step $next_step:"
    echo "  $(jq -r ".steps[($next_step - 1)].description" "$workflow_file")"
  else
    echo "✅ All catchup steps completed!"
    echo "Finalizing state..."
    # Apply all screenshot data to state
    finalize_catchup "$workflow_file"
    rm "$workflow_file"
  fi
}

finalize_catchup() {
  local workflow_file="$1"
  local session_id=$(get_current_session_id)

  # Apply deck view data
  local deck_data=$(jq -r '.state.steps[0].data' "$workflow_file")
  if [[ "$deck_data" != "null" ]]; then
    update_state ".deck.cards = $deck_data.cards | .deck.size = ($deck_data.cards | length)" "$session_id"
  fi

  # Apply map view data
  local map_data=$(jq -r '.state.steps[1].data' "$workflow_file")
  if [[ "$map_data" != "null" ]]; then
    update_state ".run.floor = $map_data.floor | .run.act = $map_data.act | .map.path = $map_data.path" "$session_id"
  fi

  # Apply current screen data
  local current_data=$(jq -r '.state.steps[2].data' "$workflow_file")
  if [[ "$current_data" != "null" ]]; then
    local screen_type=$(echo "$current_data" | jq -r '.type')
    case "$screen_type" in
      "combat")
        update_state ".combat = $current_data" "$session_id"
        ;;
      "event")
        update_state ".event = $current_data" "$session_id"
        ;;
      "shop")
        update_state ".shop = $current_data" "$session_id"
        ;;
      "rest")
        update_state ".rest = $current_data" "$session_id"
        ;;
      *)
        update_state ".run.screen = \"$screen_type\"" "$session_id"
        ;;
    esac
  fi

  echo "✅ Catchup complete! Run state updated."
}

get_catchup_status() {
  local workflow_file="$1"
  if [[ ! -f "$workflow_file" ]]; then
    echo "No active catchup workflow."
    return 1
  fi

  local workflow_id=$(jq -r '.workflow_id' "$workflow_file")
  local current_step=$(jq -r '.current_step' "$workflow_file")
  local total_steps=$(jq -r '.total_steps' "$workflow_file")

  echo "Catchup Workflow: $workflow_id"
  echo "Progress: $current_step/$total_steps"
  echo ""

  for ((i=0; i<total_steps; i++)); do
    local step_name=$(jq -r ".steps[$i].name" "$workflow_file")
    local step_desc=$(jq -r ".steps[$i].description" "$workflow_file")
    local completed=$(jq -r ".steps[$i].completed" "$workflow_file")

    if [[ "$completed" == "true" ]]; then
      echo "✓ $step_name - $step_desc"
    else
      echo "❌ $step_name - $step_desc"
    fi
  done
}

cancel_catchup() {
  local workflow_file="$1"
  if [[ ! -f "$workflow_file" ]]; then
    echo "No active catchup workflow to cancel."
    return 1
  fi

  local workflow_id=$(jq -r '.workflow_id' "$workflow_file")
  rm "$workflow_file"
  echo "Catchup workflow $workflow_id cancelled."
}

# Main script execution - allow calling functions directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  case "${1:-}" in
    load) load_state ;;
    save) save_state "${2:-}" ;;
    get) get_state_value "${2:-.}" ;;
    update) update_state "${2:-}" ;;
    clear) clear_transient ;;
    reset) reset_state ;;
    validate) validate_state ;;
    show) show_state ;;
    list) list_backups ;;
    restore) restore_backup "${2:-}" ;;
    export) export_to_markdown "${2:-}" ;;
    sessions) list_sessions "${2:-}" ;;
    switch) switch_session "${2:-}" ;;
    cleanup) cleanup_sessions "${2:-}" ;;
    delete) delete_session "${2:-}" ;;
    parallel)
      case "${2:-}" in
        check) check_parallel_support "${3:-}" && echo "✓ Parallel processing enabled" || echo "✗ Parallel processing disabled" ;;
        stats) show_parallel_stats "${3:-}" ;;
        reset) reset_parallel_circuit_breaker "${3:-}" ;;
        *) echo "Usage: $0 parallel {check|stats|reset}" ;;
      esac
      ;;
    catchup)
      case "${2:-}" in
        start) start_catchup ;;
        status) get_catchup_status "$STATE_DIR/catchup-workflows/$(ls -t "$STATE_DIR/catchup-workflows" | head -1)" ;;
        cancel) cancel_catchup "$STATE_DIR/catchup-workflows/$(ls -t "$STATE_DIR/catchup-workflows" | head -1)" ;;
        *) echo "Usage: $0 catchup {start|status|cancel}" ;;
      esac
      ;;
    *)
      echo "Usage: $0 {load|save|get|update|clear|reset|validate|show|list|restore|export|sessions|switch|cleanup|delete|parallel|catchup}"
      echo ""
      echo "State management functions for spire"
      echo ""
      echo "Commands:"
      echo "  load                    - Load and display current state"
      echo "  save '<json>'           - Save new state (must be valid JSON)"
      echo "  get <jq_expr>           - Get specific value (e.g., '.run.character')"
      echo "  update '<jq_filter>'    - Update state using jq filter"
      echo "  clear                   - Clear transient state (combat, rewards, etc.)"
      echo "  reset                   - Reset all state to empty"
      echo "  validate                - Validate state file JSON"
      echo "  show                    - Show state summary"
      echo "  list                    - List available backups"
      echo "  restore <backup_file>   - Restore from backup"
      echo "  export [output_file]    - Export to markdown"
      echo "  sessions [days]         - List all sessions (optional: filter by age)"
      echo "  switch <session_id>     - Display specific session state"
      echo "  cleanup [days]          - Remove old sessions (default: 30)"
      echo "  delete <session_id>     - Permanently delete session"
      echo "  parallel {check|stats|reset} - Parallel processing management"
      echo "  catchup {start|status|cancel} - Catchup workflow management"
      exit 1
      ;;
  esac
fi
