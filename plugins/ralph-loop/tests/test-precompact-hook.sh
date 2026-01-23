#!/bin/bash
# Test pre-compact hook for Ralph Loop
# Verifies that compaction clears Ralph state

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

pass() { echo -e "${GREEN}PASS${NC}: $1"; }
fail() { echo -e "${RED}FAIL${NC}: $1"; exit 1; }

# Create temp directory for test
TEST_DIR=$(mktemp -d)
trap "rm -rf $TEST_DIR" EXIT

cd "$TEST_DIR"
mkdir -p .claude

echo "=== Test: PreCompact clears session-specific state file ==="

# Create a session-specific state file
SESSION_ID="test-session-123"
STATE_FILE=".claude/ralph-loop-${SESSION_ID}.local.md"

cat > "$STATE_FILE" << 'STATE'
---
active: true
iteration: 5
max_iterations: 10
completion_promise: "DONE"
---

Test prompt
STATE

# Create mock hook input
HOOK_INPUT="{\"transcript_path\": \"/test/projects/test/${SESSION_ID}.jsonl\"}"

# Run the pre-compact hook
OUTPUT=$(echo "$HOOK_INPUT" | "$PLUGIN_DIR/hooks/pre-compact.sh" 2>&1)

if [[ ! -f "$STATE_FILE" ]]; then
  pass "PreCompact hook cleared session-specific state file"
else
  fail "State file should have been removed"
fi

if echo "$OUTPUT" | grep -q "Iteration: 5"; then
  pass "PreCompact hook reported correct iteration"
else
  fail "PreCompact hook should report the iteration number"
fi

echo "=== Test: PreCompact clears legacy state file ==="

# Create a legacy state file
LEGACY_FILE=".claude/ralph-loop.local.md"

cat > "$LEGACY_FILE" << 'STATE'
---
active: true
iteration: 3
max_iterations: 20
completion_promise: "COMPLETE"
---

Legacy test prompt
STATE

# Run the pre-compact hook with empty transcript path
HOOK_INPUT="{}"
OUTPUT=$(echo "$HOOK_INPUT" | "$PLUGIN_DIR/hooks/pre-compact.sh" 2>&1)

if [[ ! -f "$LEGACY_FILE" ]]; then
  pass "PreCompact hook cleared legacy state file"
else
  fail "Legacy state file should have been removed"
fi

echo "=== Test: PreCompact succeeds with no state file ==="

# Ensure no state files exist
rm -f .claude/ralph-loop*.local.md

# Run the pre-compact hook - should succeed silently
HOOK_INPUT="{\"transcript_path\": \"/test/projects/test/session-456.jsonl\"}"
OUTPUT=$(echo "$HOOK_INPUT" | "$PLUGIN_DIR/hooks/pre-compact.sh" 2>&1)
EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 ]]; then
  pass "PreCompact hook succeeds with no state file (exit code 0)"
else
  fail "PreCompact hook should always exit 0 to allow compaction"
fi

echo ""
echo "=== All tests passed! ==="
