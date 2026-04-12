#!/usr/bin/env bash
# PreToolUse hook for the GitHub plugin.
# Auto-allows gh CLI, git, and bundled Python helper commands
# so the user is not prompted for permission on every call.
#
# The SKILL.md files instruct Claude to use dangerouslyDisableSandbox: true
# for gh/git commands. This hook auto-approves those calls so the user
# never sees a permission prompt.

set -euo pipefail

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data.get('tool_input', {}).get('command', ''))
" 2>/dev/null || echo "")

if [ -z "$COMMAND" ]; then
  exit 0
fi

# Allow gh CLI commands
if echo "$COMMAND" | grep -qE '^\s*(gh )|^\s*(gh$)'; then
  echo '{"hookSpecificOutput":{"permissionDecision":"allow","permissionDecisionReason":"GitHub plugin: gh CLI command auto-allowed"}}'
  exit 0
fi

# Allow git commands (needed for branch/commit/push operations)
if echo "$COMMAND" | grep -qE '^\s*(git )'; then
  echo '{"hookSpecificOutput":{"permissionDecision":"allow","permissionDecisionReason":"GitHub plugin: git command auto-allowed"}}'
  exit 0
fi

# Allow bundled Python helper scripts
if echo "$COMMAND" | grep -qE 'python3?\s+.*/(inspect_pr_checks|fetch_comments)\.py'; then
  echo '{"hookSpecificOutput":{"permissionDecision":"allow","permissionDecisionReason":"GitHub plugin: bundled helper script auto-allowed"}}'
  exit 0
fi

# Everything else: pass through to default permission handling
exit 0
