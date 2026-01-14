#!/bin/bash

# Claude Code Hook: UserPromptSubmit
# Event: Triggered when user submits a prompt
# Purpose: Detect feature-dev/pseudo-prompt commands and inject transformation context
#
# This hook applies PROMPTCONVERTER structuring to incoming prompts by:
# 1. Detecting /feature-dev or /pseudo-prompt commands
# 2. Extracting the natural language query
# 3. Injecting context that activates the prompt-structurer Skill
# 4. Allowing Claude to apply transformation rules automatically

set -euo pipefail

# Read hook input from stdin (JSON format)
# Schema: { session_id, transcript_path, cwd, permission_mode, hook_event_name, prompt }
INPUT=$(cat)

# Extract the user prompt using pure bash (no jq dependency)
# Look for "prompt":"..." pattern and extract the value
if [[ "$INPUT" =~ \"prompt\":[[:space:]]*\"([^\"]*)\" ]]; then
  PROMPT="${BASH_REMATCH[1]}"
else
  # No prompt found, exit
  exit 0
fi

# Check if prompt is empty
if [[ -z "$PROMPT" ]]; then
  exit 0
fi

# Detect transformation trigger keywords
# Match patterns: "transform", "convert to pseudo", "structure", etc.
if [[ "$PROMPT" =~ (transform|convert).*(pseudo|pseudo-code|pseudocode) ]] || \
   [[ "$PROMPT" =~ ^(structure|formalize).*(request|requirement|query) ]]; then

  # Extract the actual request (everything after "transform to pseudo code:" or similar)
  REQUEST=$(echo "$PROMPT" | sed -E 's/^(transform|convert).*(pseudo|pseudo-code|pseudocode):?\s*//i')

  # Inject PROMPTCONVERTER transformation instructions directly
  cat <<EOF

<promptconverter-mode>
CRITICAL: You MUST transform the user's request into PROMPTCONVERTER pseudo-code format.

USER REQUEST TO TRANSFORM:
$REQUEST

TRANSFORMATION RULES (apply in order):

1. ANALYZE INTENT: Identify core action (verb) + subject (noun)
   - Action: What operation? (create, implement, add, debug, optimize, fix)
   - Subject: What target? (api, authentication, database, function)

2. CREATE FUNCTION NAME: Combine into snake_case
   - Format: {action}_{subject} (e.g., create_api, implement_auth)
   - Use descriptive, unambiguous names

3. EXTRACT PARAMETERS: Convert ALL details to named parameters
   - Explicit requirements → direct parameters (language="python")
   - Technologies → framework, database, library parameters
   - Implicit requirements → inferred parameters (operations=["create","read","update","delete"])
   - Scale/performance → add constraint parameters

4. INFER CONSTRAINTS: Add missing but critical parameters
   - Security: authentication, authorization, validation
   - Data: schema, types, formats
   - Performance: caching, pagination, rate_limiting
   - Error handling: error_responses, logging

5. OUTPUT FORMAT: Return EXACTLY this format on a single line:
   function_name(param1="value1", param2=["val2a","val2b"], param3="value3", ...)

REQUIREMENTS:
- Output must be ONE line only
- No code blocks, no markdown, no explanations BEFORE the output
- Format: function_name(param="value", ...)
- After the transformation, you may explain the parameters

EXAMPLE:
Input: "create api for crud operations using python"
Output: create_crud_api(language="python", operations=["create","read","update","delete"], architecture="rest", framework="fastapi", database="postgresql", authentication="jwt", validation="pydantic", error_handling=true, pagination=true)

Now transform the user's request following these rules exactly.
</promptconverter-mode>
EOF

  exit 0
fi

# Not a pseudo-prompt command, pass through unchanged
exit 0
