#!/bin/bash

# Ralph Wiggum Stop Hook
# Prevents session exit when a lisa-loop is active
# Feeds Claude's output back as input to continue the loop

set -euo pipefail

# === LOGGING FUNCTIONS ===
LOG_FILE=".claude/lisa-loop.log"

log_entry() {
  local level="$1"
  local message="$2"
  local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

log_iteration_start() {
  local iteration="$1"
  log_entry "INFO" "=== Iteration $iteration started ==="
}

log_iteration_end() {
  local iteration="$1"
  local duration="$2"
  local status="$3"
  log_entry "INFO" "Iteration $iteration completed in ${duration}s - Status: $status"
}

log_progress() {
  local completed="$1"
  local total="$2"
  local percent=$((completed * 100 / total))
  log_entry "PROGRESS" "Items: $completed/$total ($percent%)"
}

# === PROGRESS DETECTION ===
detect_progress() {
  # Look for IMPLEMENTATION_PLAN*.md and count completed items
  local plan_file=""
  for f in IMPLEMENTATION_PLAN*.md IMPLEMENTATION-PLAN*.md; do
    if [[ -f "$f" ]]; then
      plan_file="$f"
      break
    fi
  done

  if [[ -n "$plan_file" ]]; then
    # Count [x] (completed) and [ ] (pending) items
    local completed=$(grep -c '\[x\]\|\[X\]\|✅\|COMPLETADO\|DONE\|completed' "$plan_file" 2>/dev/null || echo "0")
    local pending=$(grep -c '\[ \]\|⬜\|PENDIENTE\|pending\|TODO' "$plan_file" 2>/dev/null || echo "0")
    local total=$((completed + pending))

    if [[ $total -gt 0 ]]; then
      echo "$completed/$total"
      return 0
    fi
  fi
  echo ""
}

# === MAIN HOOK LOGIC ===

# Read hook input from stdin (advanced stop hook API)
HOOK_INPUT=$(cat)

# Check if lisa-loop is active
RALPH_STATE_FILE=".claude/lisa-loop.local.md"

if [[ ! -f "$RALPH_STATE_FILE" ]]; then
  # No active loop - allow exit
  exit 0
fi

# Ensure log directory exists
mkdir -p .claude

# Parse markdown frontmatter (YAML between ---) and extract values
FRONTMATTER=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$RALPH_STATE_FILE")
ITERATION=$(echo "$FRONTMATTER" | grep '^iteration:' | sed 's/iteration: *//')
MAX_ITERATIONS=$(echo "$FRONTMATTER" | grep '^max_iterations:' | sed 's/max_iterations: *//')
STARTED_AT=$(echo "$FRONTMATTER" | grep '^started_at:' | sed 's/started_at: *//' | tr -d '"')
LAST_ITERATION_AT=$(echo "$FRONTMATTER" | grep '^last_iteration_at:' | sed 's/last_iteration_at: *//' | tr -d '"')
# Extract completion_promise and strip surrounding quotes if present
COMPLETION_PROMISE=$(echo "$FRONTMATTER" | grep '^completion_promise:' | sed 's/completion_promise: *//' | sed 's/^"\(.*\)"$/\1/')

# Calculate iteration duration if we have last_iteration_at
ITERATION_DURATION="?"
if [[ -n "$LAST_ITERATION_AT" ]]; then
  LAST_TS=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$LAST_ITERATION_AT" +%s 2>/dev/null || echo "0")
  NOW_TS=$(date +%s)
  if [[ $LAST_TS -gt 0 ]]; then
    ITERATION_DURATION=$((NOW_TS - LAST_TS))
  fi
fi

# Validate numeric fields before arithmetic operations
if [[ ! "$ITERATION" =~ ^[0-9]+$ ]]; then
  log_entry "ERROR" "State file corrupted - invalid iteration: $ITERATION"
  echo "⚠️  Lisa loop: State file corrupted" >&2
  echo "   File: $RALPH_STATE_FILE" >&2
  echo "   Problem: 'iteration' field is not a valid number (got: '$ITERATION')" >&2
  echo "" >&2
  echo "   This usually means the state file was manually edited or corrupted." >&2
  echo "   Lisa loop is stopping. Run /lisa-loop again to start fresh." >&2
  rm "$RALPH_STATE_FILE"
  exit 0
fi

if [[ ! "$MAX_ITERATIONS" =~ ^[0-9]+$ ]]; then
  log_entry "ERROR" "State file corrupted - invalid max_iterations: $MAX_ITERATIONS"
  echo "⚠️  Lisa loop: State file corrupted" >&2
  echo "   File: $RALPH_STATE_FILE" >&2
  echo "   Problem: 'max_iterations' field is not a valid number (got: '$MAX_ITERATIONS')" >&2
  echo "" >&2
  echo "   This usually means the state file was manually edited or corrupted." >&2
  echo "   Lisa loop is stopping. Run /lisa-loop again to start fresh." >&2
  rm "$RALPH_STATE_FILE"
  exit 0
fi

# Check if max iterations reached
if [[ $MAX_ITERATIONS -gt 0 ]] && [[ $ITERATION -ge $MAX_ITERATIONS ]]; then
  log_entry "INFO" "Max iterations ($MAX_ITERATIONS) reached - loop stopping"
  log_iteration_end "$ITERATION" "$ITERATION_DURATION" "MAX_ITERATIONS"

  # Calculate total duration
  if [[ -n "$STARTED_AT" ]]; then
    START_TS=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$STARTED_AT" +%s 2>/dev/null || echo "0")
    NOW_TS=$(date +%s)
    TOTAL_DURATION=$((NOW_TS - START_TS))
    TOTAL_MINUTES=$((TOTAL_DURATION / 60))
    log_entry "SUMMARY" "Total time: ${TOTAL_MINUTES}m, Iterations: $ITERATION"
  fi

  echo "🛑 Lisa loop: Max iterations ($MAX_ITERATIONS) reached."
  echo "   Total iterations: $ITERATION"
  echo "   Log: $LOG_FILE"
  rm "$RALPH_STATE_FILE"
  exit 0
fi

# Get transcript path from hook input
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path')

if [[ ! -f "$TRANSCRIPT_PATH" ]]; then
  log_entry "ERROR" "Transcript file not found: $TRANSCRIPT_PATH"
  echo "⚠️  Lisa loop: Transcript file not found" >&2
  echo "   Expected: $TRANSCRIPT_PATH" >&2
  echo "   This is unusual and may indicate a Claude Code internal issue." >&2
  echo "   Lisa loop is stopping." >&2
  rm "$RALPH_STATE_FILE"
  exit 0
fi

# Read last assistant message from transcript (JSONL format - one JSON per line)
# First check if there are any assistant messages
if ! grep -q '"role":"assistant"' "$TRANSCRIPT_PATH"; then
  log_entry "ERROR" "No assistant messages in transcript"
  echo "⚠️  Lisa loop: No assistant messages found in transcript" >&2
  echo "   Transcript: $TRANSCRIPT_PATH" >&2
  echo "   This is unusual and may indicate a transcript format issue" >&2
  echo "   Lisa loop is stopping." >&2
  rm "$RALPH_STATE_FILE"
  exit 0
fi

# Extract last assistant message with explicit error handling
LAST_LINE=$(grep '"role":"assistant"' "$TRANSCRIPT_PATH" | tail -1)
if [[ -z "$LAST_LINE" ]]; then
  log_entry "ERROR" "Failed to extract last assistant message"
  echo "⚠️  Lisa loop: Failed to extract last assistant message" >&2
  echo "   Lisa loop is stopping." >&2
  rm "$RALPH_STATE_FILE"
  exit 0
fi

# Parse JSON with error handling
LAST_OUTPUT=$(echo "$LAST_LINE" | jq -r '
  .message.content |
  map(select(.type == "text")) |
  map(.text) |
  join("\n")
' 2>&1)

# Check if jq succeeded
if [[ $? -ne 0 ]]; then
  log_entry "ERROR" "Failed to parse JSON: $LAST_OUTPUT"
  echo "⚠️  Lisa loop: Failed to parse assistant message JSON" >&2
  echo "   Error: $LAST_OUTPUT" >&2
  echo "   This may indicate a transcript format issue" >&2
  echo "   Lisa loop is stopping." >&2
  rm "$RALPH_STATE_FILE"
  exit 0
fi

if [[ -z "$LAST_OUTPUT" ]]; then
  log_entry "ERROR" "Empty assistant message"
  echo "⚠️  Lisa loop: Assistant message contained no text content" >&2
  echo "   Lisa loop is stopping." >&2
  rm "$RALPH_STATE_FILE"
  exit 0
fi

# Log this iteration
log_iteration_end "$ITERATION" "$ITERATION_DURATION" "CONTINUE"

# Check for completion promise (only if set)
if [[ "$COMPLETION_PROMISE" != "null" ]] && [[ -n "$COMPLETION_PROMISE" ]]; then
  # Extract text from <promise> tags using Perl for multiline support
  # -0777 slurps entire input, s flag makes . match newlines
  # .*? is non-greedy (takes FIRST tag), whitespace normalized
  PROMISE_TEXT=$(echo "$LAST_OUTPUT" | perl -0777 -pe 's/.*?<promise>(.*?)<\/promise>.*/$1/s; s/^\s+|\s+$//g; s/\s+/ /g' 2>/dev/null || echo "")

  # Use = for literal string comparison (not pattern matching)
  # == in [[ ]] does glob pattern matching which breaks with *, ?, [ characters
  if [[ -n "$PROMISE_TEXT" ]] && [[ "$PROMISE_TEXT" = "$COMPLETION_PROMISE" ]]; then
    log_entry "SUCCESS" "Completion promise detected: $COMPLETION_PROMISE"

    # Calculate total duration
    if [[ -n "$STARTED_AT" ]]; then
      START_TS=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$STARTED_AT" +%s 2>/dev/null || echo "0")
      NOW_TS=$(date +%s)
      TOTAL_DURATION=$((NOW_TS - START_TS))
      TOTAL_MINUTES=$((TOTAL_DURATION / 60))
      log_entry "SUMMARY" "Total time: ${TOTAL_MINUTES}m, Iterations: $ITERATION"
    fi

    echo "✅ Lisa loop: Detected <promise>$COMPLETION_PROMISE</promise>"
    echo "   Total iterations: $ITERATION"
    echo "   Log: $LOG_FILE"
    rm "$RALPH_STATE_FILE"
    exit 0
  fi
fi

# Not complete - continue loop with SAME PROMPT
NEXT_ITERATION=$((ITERATION + 1))

# Log next iteration start
log_iteration_start "$NEXT_ITERATION"

# Detect progress if IMPLEMENTATION_PLAN exists
PROGRESS=$(detect_progress)
if [[ -n "$PROGRESS" ]]; then
  IFS='/' read -r COMPLETED TOTAL <<< "$PROGRESS"
  log_progress "$COMPLETED" "$TOTAL"
fi

# Extract prompt (everything after the closing ---)
# Skip first --- line, skip until second --- line, then print everything after
# Use i>=2 instead of i==2 to handle --- in prompt content
PROMPT_TEXT=$(awk '/^---$/{i++; next} i>=2' "$RALPH_STATE_FILE")

if [[ -z "$PROMPT_TEXT" ]]; then
  log_entry "ERROR" "No prompt text found in state file"
  echo "⚠️  Lisa loop: State file corrupted or incomplete" >&2
  echo "   File: $RALPH_STATE_FILE" >&2
  echo "   Problem: No prompt text found" >&2
  echo "" >&2
  echo "   This usually means:" >&2
  echo "     • State file was manually edited" >&2
  echo "     • File was corrupted during writing" >&2
  echo "" >&2
  echo "   Lisa loop is stopping. Run /lisa-loop again to start fresh." >&2
  rm "$RALPH_STATE_FILE"
  exit 0
fi

# Update state file with new iteration and timestamp
NOW_ISO=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
TEMP_FILE="${RALPH_STATE_FILE}.tmp.$$"

# Update both iteration and last_iteration_at
sed -e "s/^iteration: .*/iteration: $NEXT_ITERATION/" \
    -e "s/^last_iteration_at: .*/last_iteration_at: \"$NOW_ISO\"/" \
    "$RALPH_STATE_FILE" > "$TEMP_FILE"

# Add last_iteration_at if it doesn't exist
if ! grep -q '^last_iteration_at:' "$TEMP_FILE"; then
  sed -i.bak "/^started_at:/a\\
last_iteration_at: \"$NOW_ISO\"
" "$TEMP_FILE" 2>/dev/null || \
  sed "/^started_at:/a\\
last_iteration_at: \"$NOW_ISO\"
" "$TEMP_FILE" > "${TEMP_FILE}.new" && mv "${TEMP_FILE}.new" "$TEMP_FILE"
  rm -f "${TEMP_FILE}.bak"
fi

mv "$TEMP_FILE" "$RALPH_STATE_FILE"

# Build system message with iteration count, progress, and completion promise info
PROGRESS_MSG=""
if [[ -n "$PROGRESS" ]]; then
  PROGRESS_MSG=" | Progress: $PROGRESS"
fi

if [[ "$COMPLETION_PROMISE" != "null" ]] && [[ -n "$COMPLETION_PROMISE" ]]; then
  SYSTEM_MSG="🔄 Lisa iteration $NEXT_ITERATION$PROGRESS_MSG | To stop: output <promise>$COMPLETION_PROMISE</promise> (ONLY when TRUE!)"
else
  SYSTEM_MSG="🔄 Lisa iteration $NEXT_ITERATION$PROGRESS_MSG | No completion promise - loop runs infinitely"
fi

# Output JSON to block the stop and feed prompt back
# The "reason" field contains the prompt that will be sent back to Claude
jq -n \
  --arg prompt "$PROMPT_TEXT" \
  --arg msg "$SYSTEM_MSG" \
  '{
    "decision": "block",
    "reason": $prompt,
    "systemMessage": $msg
  }'

# Exit 0 for successful hook execution
exit 0
