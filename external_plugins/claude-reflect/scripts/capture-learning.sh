#!/bin/bash
# V3: Detects correction patterns, positive patterns, OR explicit markers
# Features: confidence scoring, positive pattern capture, decay metadata
# Used by UserPromptSubmit hook

QUEUE_FILE="$HOME/.claude/learnings-queue.json"

# Read JSON from stdin
INPUT="$(cat -)"
[ -z "$INPUT" ] && exit 0

# Extract prompt from JSON - handle different possible field names
PROMPT="$(echo "$INPUT" | jq -r '.prompt // .message // .text // empty' 2>/dev/null)"
[ -z "$PROMPT" ] && exit 0

# Get current project path
PROJECT="$(pwd)"

# Initialize queue if doesn't exist
[ ! -f "$QUEUE_FILE" ] && echo "[]" > "$QUEUE_FILE"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
MATCHED_PATTERNS=""
TYPE=""
CONFIDENCE=0.0
SENTIMENT="correction"  # "correction" or "positive"
DECAY_DAYS=90  # Default decay period

# Check for explicit "remember:"
if echo "$PROMPT" | grep -qi "remember:"; then
  TYPE="explicit"
  MATCHED_PATTERNS="remember:"
  CONFIDENCE=0.90
  DECAY_DAYS=120

# Check for POSITIVE patterns (new in v3)
elif echo "$PROMPT" | grep -qiE "perfect!|exactly right|that's exactly|that's what I wanted|great approach|keep doing this|love it|excellent|nailed it"; then
  TYPE="positive"
  SENTIMENT="positive"
  CONFIDENCE=0.70
  DECAY_DAYS=90

  if echo "$PROMPT" | grep -qiE "perfect!|exactly right|that's exactly"; then
    MATCHED_PATTERNS="$MATCHED_PATTERNS perfect"
  fi
  if echo "$PROMPT" | grep -qiE "that's what I wanted|great approach"; then
    MATCHED_PATTERNS="$MATCHED_PATTERNS great-approach"
  fi
  if echo "$PROMPT" | grep -qiE "keep doing this|love it|excellent|nailed it"; then
    MATCHED_PATTERNS="$MATCHED_PATTERNS keep-doing"
  fi

else
  # Check for correction patterns (conservative set to minimize false positives)
  # These patterns strongly indicate a user correction
  # Confidence: 0.80 for strong patterns, 0.60 for medium patterns

  PATTERN_COUNT=0

  # Pattern: "no, use X" / "no use X" (strong)
  if echo "$PROMPT" | grep -qiE "no[,. ]+use"; then
    TYPE="auto"
    MATCHED_PATTERNS="$MATCHED_PATTERNS no,use"
    PATTERN_COUNT=$((PATTERN_COUNT + 1))
  fi

  # Pattern: "don't use" (strong)
  if echo "$PROMPT" | grep -qiE "don't use|do not use"; then
    TYPE="auto"
    MATCHED_PATTERNS="$MATCHED_PATTERNS don't-use"
    PATTERN_COUNT=$((PATTERN_COUNT + 1))
  fi

  # Pattern: "stop using" / "never use" (strong)
  if echo "$PROMPT" | grep -qiE "stop using|never use"; then
    TYPE="auto"
    MATCHED_PATTERNS="$MATCHED_PATTERNS stop/never-use"
    PATTERN_COUNT=$((PATTERN_COUNT + 1))
  fi

  # Pattern: "that's wrong" / "that's incorrect" (strong)
  if echo "$PROMPT" | grep -qiE "that's (wrong|incorrect)|that is (wrong|incorrect)"; then
    TYPE="auto"
    MATCHED_PATTERNS="$MATCHED_PATTERNS that's-wrong"
    PATTERN_COUNT=$((PATTERN_COUNT + 1))
  fi

  # Pattern: "not right" / "not correct" (medium)
  if echo "$PROMPT" | grep -qiE "not right|not correct"; then
    TYPE="auto"
    MATCHED_PATTERNS="$MATCHED_PATTERNS not-right"
    PATTERN_COUNT=$((PATTERN_COUNT + 1))
  fi

  # Pattern: "actually," (medium - context dependent)
  if echo "$PROMPT" | grep -qiE "^actually[,. ]|[.!?] actually[,. ]"; then
    TYPE="auto"
    MATCHED_PATTERNS="$MATCHED_PATTERNS actually"
    PATTERN_COUNT=$((PATTERN_COUNT + 1))
  fi

  # Pattern: "I meant" / "I said" (strong)
  if echo "$PROMPT" | grep -qiE "I meant|I said"; then
    TYPE="auto"
    MATCHED_PATTERNS="$MATCHED_PATTERNS I-meant/said"
    PATTERN_COUNT=$((PATTERN_COUNT + 1))
  fi

  # Pattern: "I told you" / "I already told" (strong - repeated correction)
  if echo "$PROMPT" | grep -qiE "I told you|I already told"; then
    TYPE="auto"
    MATCHED_PATTERNS="$MATCHED_PATTERNS I-told-you"
    PATTERN_COUNT=$((PATTERN_COUNT + 1))
    CONFIDENCE=0.85  # Higher confidence for repeated corrections
  fi

  # Pattern: "you should use" / "you need to use" (medium)
  if echo "$PROMPT" | grep -qiE "you (should|need to|must) use"; then
    TYPE="auto"
    MATCHED_PATTERNS="$MATCHED_PATTERNS you-should-use"
    PATTERN_COUNT=$((PATTERN_COUNT + 1))
  fi

  # Pattern: "use X not Y" / "not X, use Y" (strong)
  if echo "$PROMPT" | grep -qiE "use .+ not|not .+, use"; then
    TYPE="auto"
    MATCHED_PATTERNS="$MATCHED_PATTERNS use-X-not-Y"
    PATTERN_COUNT=$((PATTERN_COUNT + 1))
  fi

  # Set confidence based on pattern count (if not already set)
  if [ "$TYPE" = "auto" ] && [ "$CONFIDENCE" = "0.0" ]; then
    if [ "$PATTERN_COUNT" -ge 3 ]; then
      CONFIDENCE=0.85
      DECAY_DAYS=120
    elif [ "$PATTERN_COUNT" -ge 2 ]; then
      CONFIDENCE=0.75
      DECAY_DAYS=90
    else
      CONFIDENCE=0.60
      DECAY_DAYS=60
    fi
  fi
fi

# If we found something, queue it
if [ -n "$TYPE" ]; then
  # Trim leading space from matched patterns
  MATCHED_PATTERNS=$(echo "$MATCHED_PATTERNS" | sed 's/^ *//')

  jq --arg type "$TYPE" \
     --arg msg "$PROMPT" \
     --arg ts "$TIMESTAMP" \
     --arg proj "$PROJECT" \
     --arg patterns "$MATCHED_PATTERNS" \
     --arg confidence "$CONFIDENCE" \
     --arg sentiment "$SENTIMENT" \
     --arg decay "$DECAY_DAYS" \
    '. += [{"type": $type, "message": $msg, "timestamp": $ts, "project": $proj, "patterns": $patterns, "confidence": ($confidence | tonumber), "sentiment": $sentiment, "decay_days": ($decay | tonumber)}]' \
    "$QUEUE_FILE" > "$QUEUE_FILE.tmp" 2>/dev/null && mv "$QUEUE_FILE.tmp" "$QUEUE_FILE"
fi

exit 0
