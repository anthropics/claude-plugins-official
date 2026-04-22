#!/usr/bin/env bash
# Regression tests for ralph-loop stop-hook session isolation.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$SCRIPT_DIR/../hooks/stop-hook.sh"

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

FAILED=0
PASSED=0

pass() { echo "  ✓ $1"; PASSED=$((PASSED + 1)); }
fail() { echo "  ✗ $1" >&2; FAILED=$((FAILED + 1)); }

write_state_file() {
  local dir=$1
  local session_id_value=$2
  mkdir -p "$dir/.claude"
  cat > "$dir/.claude/ralph-loop.local.md" <<EOF
---
active: true
iteration: 1
session_id: $session_id_value
max_iterations: 10
completion_promise: null
started_at: "2026-04-22T00:00:00Z"
---

do the thing
EOF
}

write_transcript() {
  local path=$1
  cat > "$path" <<'EOF'
{"role":"assistant","message":{"content":[{"type":"text","text":"iteration output"}]}}
EOF
}

run_hook() {
  local wd=$1
  local hook_session=$2
  local transcript="$wd/transcript.jsonl"
  write_transcript "$transcript"
  local hook_input
  hook_input=$(jq -n \
    --arg sid "$hook_session" \
    --arg tp "$transcript" \
    '{session_id: $sid, transcript_path: $tp}')
  ( cd "$wd" && echo "$hook_input" | bash "$HOOK" ) 2>/dev/null
}

echo "Test 1: Different explicit session_id is correctly isolated"
{
  wd="$TMPDIR/t1"; mkdir -p "$wd"
  write_state_file "$wd" "session-A"
  out=$(run_hook "$wd" "session-B")
  if [[ -z "$out" ]]; then
    pass "session-B did not intercept session-A's loop (no block output)"
  else
    fail "session-B intercepted session-A's loop: $(printf '%s' "$out" | head -c 160)"
  fi
  if [[ -f "$wd/.claude/ralph-loop.local.md" ]]; then
    pass "session-A's state file preserved"
  else
    fail "session-A's state file was wrongly removed"
  fi
}

echo "Test 2: Empty session_id must NOT fall through to other sessions"
{
  wd="$TMPDIR/t2"; mkdir -p "$wd"
  # Empty session_id reproduces the unset CLAUDE_CODE_SESSION_ID path that
  # used to trigger the cross-session leak via "legacy fallthrough".
  write_state_file "$wd" ""
  out=$(run_hook "$wd" "session-B")
  state_still_there=false
  [[ -f "$wd/.claude/ralph-loop.local.md" ]] && state_still_there=true

  if [[ -n "$out" ]]; then
    fail "empty session_id caused block output (cross-session leak): $(printf '%s' "$out" | head -c 200)"
  else
    pass "no block output emitted"
  fi
  if $state_still_there; then
    fail "state file with empty session_id was not cleaned up as corrupted"
  else
    pass "state file cleaned up"
  fi
}

echo "Test 3: No state file — hook is a no-op"
{
  wd="$TMPDIR/t3"; mkdir -p "$wd/.claude"
  out=$(run_hook "$wd" "session-B")
  if [[ -z "$out" ]]; then
    pass "no output when state file absent"
  else
    fail "unexpected output when no state file: $(printf '%s' "$out" | head -c 160)"
  fi
}

echo "Test 4: pending state is atomically claimed by first Stop hook"
{
  wd="$TMPDIR/t4"; mkdir -p "$wd/.claude"
  write_state_file "$wd" "pending"

  out=$(run_hook "$wd" "session-A")

  if echo "$out" | jq -e '.decision == "block"' >/dev/null 2>&1; then
    pass "block decision emitted for claiming session"
  else
    fail "expected block decision, got: $(printf '%s' "$out" | head -c 200)"
  fi

  claimed_sid=$(grep '^session_id:' "$wd/.claude/ralph-loop.local.md" | sed 's/session_id: *//')
  if [[ "$claimed_sid" == "session-A" ]]; then
    pass "session_id field updated to claiming session"
  else
    fail "session_id not updated, got: '$claimed_sid'"
  fi

  claimed_iter=$(grep '^iteration:' "$wd/.claude/ralph-loop.local.md" | sed 's/iteration: *//')
  # stop-hook.sh progresses iteration 1 → 2 at the bottom of the script.
  # Claim itself does not touch iteration.
  if [[ "$claimed_iter" == "2" ]]; then
    pass "iteration advanced from 1 to 2 after claim + progression"
  else
    fail "unexpected iteration after claim, got: '$claimed_iter'"
  fi
}

echo "Test 5: after claim, other sessions stay isolated"
{
  wd="$TMPDIR/t5"; mkdir -p "$wd/.claude"
  write_state_file "$wd" "pending"
  run_hook "$wd" "session-A" >/dev/null

  out=$(run_hook "$wd" "session-B")
  if [[ -z "$out" ]]; then
    pass "session-B does not intercept session-A's claimed loop"
  else
    fail "session-B intercepted after claim: $(printf '%s' "$out" | head -c 200)"
  fi
}

echo ""
echo "Results: $PASSED passed, $FAILED failed"
if (( FAILED > 0 )); then
  exit 1
fi
exit 0
