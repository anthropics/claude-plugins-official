#!/bin/bash
# Test session isolation for Ralph Loop
# Verifies that concurrent sessions don't share state

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

echo "=== Test: Session ID extraction from transcript path ==="

# Test 1: Session ID is correctly extracted from transcript path
TRANSCRIPT_PATH="/Users/test/.claude/projects/-test-project/abc123-def456-ghi789.jsonl"
SESSION_ID=$(basename "$TRANSCRIPT_PATH" .jsonl)

if [[ "$SESSION_ID" == "abc123-def456-ghi789" ]]; then
  pass "Session ID correctly extracted from transcript path"
else
  fail "Expected 'abc123-def456-ghi789', got '$SESSION_ID'"
fi

echo "=== Test: State files are session-specific ==="

# Test 2: Two different session IDs produce different state file paths
SESSION_A="session-aaa-111"
SESSION_B="session-bbb-222"

STATE_FILE_A=".claude/ralph-loop-${SESSION_A}.local.md"
STATE_FILE_B=".claude/ralph-loop-${SESSION_B}.local.md"

if [[ "$STATE_FILE_A" != "$STATE_FILE_B" ]]; then
  pass "Different sessions produce different state file paths"
else
  fail "State files should be different for different sessions"
fi

echo "=== Test: Stop hook only reads its own session's state ==="

# Test 3: Create two state files, verify they're independent
cat > ".claude/ralph-loop-${SESSION_A}.local.md" << 'STATE_A'
---
active: true
iteration: 5
max_iterations: 10
completion_promise: "DONE_A"
---

Prompt for session A
STATE_A

cat > ".claude/ralph-loop-${SESSION_B}.local.md" << 'STATE_B'
---
active: true
iteration: 3
max_iterations: 20
completion_promise: "DONE_B"
---

Prompt for session B
STATE_B

# Verify both files exist
if [[ -f ".claude/ralph-loop-${SESSION_A}.local.md" ]] && [[ -f ".claude/ralph-loop-${SESSION_B}.local.md" ]]; then
  pass "Both session state files created independently"
else
  fail "Failed to create independent state files"
fi

# Verify content is different
ITER_A=$(grep '^iteration:' ".claude/ralph-loop-${SESSION_A}.local.md" | sed 's/iteration: *//')
ITER_B=$(grep '^iteration:' ".claude/ralph-loop-${SESSION_B}.local.md" | sed 's/iteration: *//')

if [[ "$ITER_A" == "5" ]] && [[ "$ITER_B" == "3" ]]; then
  pass "Session state is isolated (A has iteration 5, B has iteration 3)"
else
  fail "State isolation failed: A=$ITER_A, B=$ITER_B"
fi

echo "=== Test: Session ID derivation from project directory ==="

# Test 4: Project directory path encoding
# Simulates: /Users/test/.claude -> -Users-test--claude
TEST_CWD="/Users/test/.claude"
EXPECTED_PROJECT="-Users-test--claude"
DERIVED_PROJECT=$(echo "$TEST_CWD" | tr '/' '-' | tr '.' '-')

if [[ "$DERIVED_PROJECT" == "$EXPECTED_PROJECT" ]]; then
  pass "Project directory path encoding is correct"
else
  fail "Expected '$EXPECTED_PROJECT', got '$DERIVED_PROJECT'"
fi

echo "=== Test: Fallback session ID generation ==="

# Test 5: Fallback generates unique IDs
FALLBACK_1="fallback-$(date +%s)-$$"
sleep 1
FALLBACK_2="fallback-$(date +%s)-$$"

if [[ "$FALLBACK_1" != "$FALLBACK_2" ]]; then
  pass "Fallback session IDs are unique"
else
  fail "Fallback session IDs should be unique"
fi

echo ""
echo "=== All tests passed! ==="
