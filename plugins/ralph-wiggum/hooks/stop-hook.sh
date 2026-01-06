#!/bin/bash

# Ralph Wiggum Stop Hook
# Prevents session exit when a ralph-loop is active
# Feeds Claude's output back as input to continue the loop
# Enhanced with rate limit detection and auto-wait

set -euo pipefail

# Read hook input from stdin (advanced stop hook API)
HOOK_INPUT=$(cat)

# Function to check if rate limited and extract reset time from transcript
# Looks for pattern like "resets 6:30am" or "resets 11:45pm"
# Returns: "HH:MM" if rate limited, empty string if not
check_rate_limit_reset_time() {
    local transcript_path="$1"

    if [[ ! -f "$transcript_path" ]]; then
        echo ""
        return
    fi

    # Look for "hit your limit" or "resets" pattern with time
    # Pattern: resets followed by time like "6:30am" or "11:45pm"
    local reset_match=$(grep -oiE "resets[[:space:]]+[0-9]{1,2}:[0-9]{2}[ap]m" "$transcript_path" 2>/dev/null | tail -1)

    if [[ -n "$reset_match" ]]; then
        # Extract time part (e.g., "6:30am")
        local time_str=$(echo "$reset_match" | grep -oiE "[0-9]{1,2}:[0-9]{2}[ap]m")
        echo "$time_str"
    else
        echo ""
    fi
}

# Function to calculate seconds until a given time (e.g., "6:30am")
get_seconds_until_time() {
    local time_str="$1"  # e.g., "6:30am" or "11:45pm"

    if [[ -z "$time_str" ]]; then
        echo "0"
        return
    fi

    # Parse hour, minute, and am/pm
    local hour minute ampm
    if [[ "$time_str" =~ ([0-9]{1,2}):([0-9]{2})([aApP][mM]) ]]; then
        hour=${BASH_REMATCH[1]}
        minute=${BASH_REMATCH[2]}
        ampm=${BASH_REMATCH[3]}
    else
        echo "0"
        return
    fi

    # Convert to 24-hour format
    ampm=$(echo "$ampm" | tr '[:upper:]' '[:lower:]')
    if [[ "$ampm" == "pm" ]] && [[ $hour -ne 12 ]]; then
        hour=$((hour + 12))
    elif [[ "$ampm" == "am" ]] && [[ $hour -eq 12 ]]; then
        hour=0
    fi

    # Get current time components
    local current_hour=$(date +%H | sed 's/^0//')
    local current_minute=$(date +%M | sed 's/^0//')
    local current_second=$(date +%S | sed 's/^0//')

    # Calculate target seconds from midnight
    local target_seconds=$((hour * 3600 + minute * 60))

    # Calculate current seconds from midnight
    local current_seconds=$((current_hour * 3600 + current_minute * 60 + current_second))

    # Calculate difference
    local diff=$((target_seconds - current_seconds))

    # If target is in the past, assume it's tomorrow
    if [[ $diff -le 0 ]]; then
        diff=$((diff + 86400))
    fi

    echo "$diff"
}

# Function to wait for rate limit reset
wait_for_reset() {
    local reset_time="$1"
    local remaining

    if [[ -n "$reset_time" ]]; then
        remaining=$(get_seconds_until_time "$reset_time")
    else
        # Fallback: wait 5 hours if no reset time found
        remaining=18000
    fi

    # Add 60 seconds buffer
    remaining=$((remaining + 60))

    local hours=$((remaining / 3600))
    local minutes=$(((remaining % 3600) / 60))

    echo "⏳ Rate limit hit! Waiting ${hours}h ${minutes}m for reset..." >&2
    if [[ -n "$reset_time" ]]; then
        echo "   Reset time: $reset_time" >&2
    fi
    echo "   Will resume at: $(date -d "+${remaining} seconds" '+%H:%M:%S' 2>/dev/null || date -v+"${remaining}"S '+%H:%M:%S' 2>/dev/null || echo "~${hours}h ${minutes}m from now")" >&2

    sleep "$remaining"

    echo "✅ Rate limit reset. Continuing Ralph loop..." >&2
}

# Check if ralph-loop is active
RALPH_STATE_FILE=".claude/ralph-loop.local.md"

if [[ ! -f "$RALPH_STATE_FILE" ]]; then
  # No active loop - allow exit
  exit 0
fi

# Parse markdown frontmatter (YAML between ---) and extract values
FRONTMATTER=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$RALPH_STATE_FILE")
ITERATION=$(echo "$FRONTMATTER" | grep '^iteration:' | sed 's/iteration: *//')
MAX_ITERATIONS=$(echo "$FRONTMATTER" | grep '^max_iterations:' | sed 's/max_iterations: *//')
# Extract completion_promise and strip surrounding quotes if present
COMPLETION_PROMISE=$(echo "$FRONTMATTER" | grep '^completion_promise:' | sed 's/completion_promise: *//' | sed 's/^"\(.*\)"$/\1/')

# Validate numeric fields before arithmetic operations
if [[ ! "$ITERATION" =~ ^[0-9]+$ ]]; then
  echo "⚠️  Ralph loop: State file corrupted" >&2
  echo "   File: $RALPH_STATE_FILE" >&2
  echo "   Problem: 'iteration' field is not a valid number (got: '$ITERATION')" >&2
  echo "" >&2
  echo "   This usually means the state file was manually edited or corrupted." >&2
  echo "   Ralph loop is stopping. Run /ralph-loop again to start fresh." >&2
  rm "$RALPH_STATE_FILE"
  exit 0
fi

if [[ ! "$MAX_ITERATIONS" =~ ^[0-9]+$ ]]; then
  echo "⚠️  Ralph loop: State file corrupted" >&2
  echo "   File: $RALPH_STATE_FILE" >&2
  echo "   Problem: 'max_iterations' field is not a valid number (got: '$MAX_ITERATIONS')" >&2
  echo "" >&2
  echo "   This usually means the state file was manually edited or corrupted." >&2
  echo "   Ralph loop is stopping. Run /ralph-loop again to start fresh." >&2
  rm "$RALPH_STATE_FILE"
  exit 0
fi

# Check if max iterations reached
if [[ $MAX_ITERATIONS -gt 0 ]] && [[ $ITERATION -ge $MAX_ITERATIONS ]]; then
  echo "🛑 Ralph loop: Max iterations ($MAX_ITERATIONS) reached."
  rm "$RALPH_STATE_FILE"
  exit 0
fi

# Get transcript path from hook input
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path')

if [[ ! -f "$TRANSCRIPT_PATH" ]]; then
  echo "⚠️  Ralph loop: Transcript file not found" >&2
  echo "   Expected: $TRANSCRIPT_PATH" >&2
  echo "   This is unusual and may indicate a Claude Code internal issue." >&2
  echo "   Ralph loop is stopping." >&2
  rm "$RALPH_STATE_FILE"
  exit 0
fi

# Check for rate limit and wait if needed
RESET_TIME=$(check_rate_limit_reset_time "$TRANSCRIPT_PATH")
if [[ -n "$RESET_TIME" ]]; then
  echo "🚨 Ralph loop: Rate limit detected!" >&2
  wait_for_reset "$RESET_TIME"
  # After waiting, continue with the loop (don't check transcript for output)
fi

# Read last assistant message from transcript (JSONL format - one JSON per line)
# First check if there are any assistant messages
if ! grep -q '"role":"assistant"' "$TRANSCRIPT_PATH"; then
  echo "⚠️  Ralph loop: No assistant messages found in transcript" >&2
  echo "   Transcript: $TRANSCRIPT_PATH" >&2
  echo "   This is unusual and may indicate a transcript format issue" >&2
  echo "   Ralph loop is stopping." >&2
  rm "$RALPH_STATE_FILE"
  exit 0
fi

# Extract last assistant message with explicit error handling
LAST_LINE=$(grep '"role":"assistant"' "$TRANSCRIPT_PATH" | tail -1)
if [[ -z "$LAST_LINE" ]]; then
  echo "⚠️  Ralph loop: Failed to extract last assistant message" >&2
  echo "   Ralph loop is stopping." >&2
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
  echo "⚠️  Ralph loop: Failed to parse assistant message JSON" >&2
  echo "   Error: $LAST_OUTPUT" >&2
  echo "   This may indicate a transcript format issue" >&2
  echo "   Ralph loop is stopping." >&2
  rm "$RALPH_STATE_FILE"
  exit 0
fi

if [[ -z "$LAST_OUTPUT" ]]; then
  echo "⚠️  Ralph loop: Assistant message contained no text content" >&2
  echo "   Ralph loop is stopping." >&2
  rm "$RALPH_STATE_FILE"
  exit 0
fi

# Check for completion promise (only if set)
if [[ "$COMPLETION_PROMISE" != "null" ]] && [[ -n "$COMPLETION_PROMISE" ]]; then
  # Extract text from <promise> tags using Perl for multiline support
  # -0777 slurps entire input, s flag makes . match newlines
  # .*? is non-greedy (takes FIRST tag), whitespace normalized
  PROMISE_TEXT=$(echo "$LAST_OUTPUT" | perl -0777 -pe 's/.*?<promise>(.*?)<\/promise>.*/$1/s; s/^\s+|\s+$//g; s/\s+/ /g' 2>/dev/null || echo "")

  # Use = for literal string comparison (not pattern matching)
  # == in [[ ]] does glob pattern matching which breaks with *, ?, [ characters
  if [[ -n "$PROMISE_TEXT" ]] && [[ "$PROMISE_TEXT" = "$COMPLETION_PROMISE" ]]; then
    echo "✅ Ralph loop: Detected <promise>$COMPLETION_PROMISE</promise>"
    rm "$RALPH_STATE_FILE"
    exit 0
  fi
fi

# Not complete - continue loop with SAME PROMPT
NEXT_ITERATION=$((ITERATION + 1))

# Extract prompt (everything after the closing ---)
# Skip first --- line, skip until second --- line, then print everything after
# Use i>=2 instead of i==2 to handle --- in prompt content
PROMPT_TEXT=$(awk '/^---$/{i++; next} i>=2' "$RALPH_STATE_FILE")

if [[ -z "$PROMPT_TEXT" ]]; then
  echo "⚠️  Ralph loop: State file corrupted or incomplete" >&2
  echo "   File: $RALPH_STATE_FILE" >&2
  echo "   Problem: No prompt text found" >&2
  echo "" >&2
  echo "   This usually means:" >&2
  echo "     • State file was manually edited" >&2
  echo "     • File was corrupted during writing" >&2
  echo "" >&2
  echo "   Ralph loop is stopping. Run /ralph-loop again to start fresh." >&2
  rm "$RALPH_STATE_FILE"
  exit 0
fi

# Update iteration in frontmatter (portable across macOS and Linux)
# Create temp file, then atomically replace
TEMP_FILE="${RALPH_STATE_FILE}.tmp.$$"
sed "s/^iteration: .*/iteration: $NEXT_ITERATION/" "$RALPH_STATE_FILE" > "$TEMP_FILE"
mv "$TEMP_FILE" "$RALPH_STATE_FILE"

# Build system message with iteration count and completion promise info
if [[ "$COMPLETION_PROMISE" != "null" ]] && [[ -n "$COMPLETION_PROMISE" ]]; then
  SYSTEM_MSG="🔄 Ralph iteration $NEXT_ITERATION | To stop: output <promise>$COMPLETION_PROMISE</promise> (ONLY when statement is TRUE - do not lie to exit!)"
else
  SYSTEM_MSG="🔄 Ralph iteration $NEXT_ITERATION | No completion promise set - loop runs infinitely"
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
