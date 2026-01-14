#!/bin/bash

# Claude Code Hook: ContextCompressionHelper
# Event: Triggered when verbose requirements are detected
# Purpose: Suggest context compression for lengthy specifications
#
# This hook:
# 1. Detects when user provides verbose, multi-sentence requirements
# 2. Suggests using context-compressor skill for better efficiency
# 3. Helps maintain token efficiency in conversations

set -euo pipefail

# Read hook input from stdin (JSON format)
INPUT=$(cat)

# Extract the user prompt using pure bash (no jq dependency)
if [[ "$INPUT" =~ \"prompt\":[[:space:]]*\"([^\"]*)\" ]]; then
  PROMPT="${BASH_REMATCH[1]}"
else
  exit 0
fi

# Check if prompt is empty
if [[ -z "$PROMPT" ]]; then
  exit 0
fi

# Count words in the prompt (rough metric for verbosity)
WORD_COUNT=$(echo "$PROMPT" | wc -w)

# Detect verbose requirements (more than 100 words and contains requirement keywords)
if [[ $WORD_COUNT -gt 100 ]] && [[ "$PROMPT" =~ (implement|create|add|build|need|want|should|must|require) ]]; then
  # Check if it's a feature request or requirement specification
  if [[ "$PROMPT" =~ (feature|endpoint|authentication|database|API|system|function|service) ]]; then
    cat <<EOF

[VERBOSE REQUIREMENT DETECTED - ${WORD_COUNT} words]

Tip: Consider using the context-compressor skill or /compress-context command to transform verbose requirements into concise pseudo-code format. This will:
- Reduce token usage by 60-95%
- Create structured, implementation-ready specifications
- Preserve all critical information
- Improve clarity and maintainability

Example: /compress-context [your verbose requirement]

Proceeding with current request...
EOF
    exit 0
  fi
fi

# Check for explicit compression commands
if [[ "$PROMPT" =~ ^/(compress|compress-context)[[:space:]] ]]; then
  cat <<EOF

[CONTEXT COMPRESSION MODE]

Applying compression techniques to transform verbose requirements into concise pseudo-code:

1. Extract Core Intent: Identify main action and objective
2. Distill Parameters: Convert prose into structured key-value pairs
3. Preserve Constraints: Keep all validation, security, and performance requirements
4. Eliminate Redundancy: Remove explanatory phrases and obvious defaults
5. Maintain Clarity: Ensure compressed form is unambiguous

Use the context-compressor skill to systematically compress the requirement.
EOF
  exit 0
fi

# Pass through unchanged
exit 0
