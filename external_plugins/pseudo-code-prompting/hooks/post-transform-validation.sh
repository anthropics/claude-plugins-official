#!/bin/bash

# Claude Code Hook: PostTransformValidation
# Event: Triggered after prompt transformation
# Purpose: Automatically validate transformed pseudo-code for completeness
#
# This hook:
# 1. Detects when pseudo-code transformation has occurred
# 2. Triggers requirement validation automatically
# 3. Provides feedback on missing parameters or ambiguities
# 4. Suggests improvements before implementation

set -euo pipefail

# Read hook input from stdin (JSON format)
INPUT=$(cat)

# Extract the user prompt using pure bash (no jq dependency)
if [[ "$INPUT" =~ \"prompt\":[[:space:]]*\"([^\"]*)\" ]]; then
  PROMPT="${BASH_REMATCH[1]}"
else
  exit 0
fi

# Check if this is a response that contains transformed pseudo-code
# Look for the "Transformed:" marker that indicates PROMPTCONVERTER output
if [[ "$PROMPT" =~ Transformed:[[:space:]]*([a-z_]+\() ]]; then
  cat <<EOF

[AUTO-VALIDATION TRIGGERED]

A pseudo-code transformation was detected. Running automatic validation to ensure completeness...

Please validate the transformed pseudo-code against these criteria:
✓ Security: Check for auth, validation, and access control requirements
✓ Data: Verify data types, formats, and validation rules are specified
✓ Errors: Ensure error handling strategies are defined
✓ Performance: Check for timeouts, caching, and scaling considerations
✓ Edge Cases: Identify potential failure scenarios

Use the requirement-validator skill to perform comprehensive validation.

If critical issues are found, suggest improvements using the prompt-optimizer skill.
EOF
  exit 0
fi

# Check for validation or optimize commands
if [[ "$PROMPT" =~ ^/(validate|optimize)[[:space:]] ]]; then
  cat <<EOF

[VALIDATION/OPTIMIZATION MODE]

Analyzing pseudo-code for completeness and implementation readiness.

Apply systematic validation:
1. Check all security requirements (auth, permissions, validation)
2. Verify data handling specifications
3. Ensure error handling is comprehensive
4. Validate performance constraints
5. Identify edge cases

Provide specific, actionable recommendations for improvements.
EOF
  exit 0
fi

# Pass through unchanged
exit 0
