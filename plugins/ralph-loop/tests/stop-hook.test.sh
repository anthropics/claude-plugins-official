#!/bin/bash

# Regression tests for hooks/stop-hook.sh
# Run: bash plugins/ralph-loop/tests/stop-hook.test.sh
#
# Covers:
#   1. A bare completion word WITHOUT <promise> tags must NOT end the loop
#      (anthropics/claude-code#81827)
#   2. A promise containing multiple spaces must still match a tagged promise
#      (whitespace is normalized on BOTH sides) (anthropics/claude-code#81828)
#   3. "iteration:N" (no space after the colon) must still be advanced by the
#      writer, so max_iterations terminates the loop (anthropics/claude-code#81829)
#   4. Control: a normal in-progress message blocks the stop and bumps iteration

set -uo pipefail

HOOK="$(cd "$(dirname "$0")/.." && pwd)/hooks/stop-hook.sh"
FAILURES=0

# run_hook <workdir> <last-assistant-text>
# Prints the hook's stdout; hook exit status is propagated.
run_hook() {
  local workdir=$1 text=$2
  local transcript="$workdir/transcript.jsonl"
  jq -cn --arg t "$text" '{"role":"assistant","message":{"content":[{"type":"text","text":$t}]}}' > "$transcript"
  (cd "$workdir" && jq -cn --arg p "$transcript" '{"session_id":"test-session","transcript_path":$p}' | bash "$HOOK")
}

# write_state <workdir> <iteration-line> <max_iterations> <completion_promise-yaml>
write_state() {
  local workdir=$1 iteration_line=$2 max=$3 promise=$4
  mkdir -p "$workdir/.claude"
  cat > "$workdir/.claude/ralph-loop.local.md" <<EOF
---
active: true
$iteration_line
session_id: test-session
max_iterations: $max
completion_promise: $promise
started_at: "2026-01-01T00:00:00Z"
---

keep working on the task
EOF
}

check() {
  local name=$1 ok=$2
  if [[ "$ok" == "true" ]]; then
    echo "PASS: $name"
  else
    echo "FAIL: $name"
    FAILURES=$((FAILURES + 1))
  fi
}

TMP=$(mktemp -d "${TMPDIR:-/tmp}/ralph-stop-hook-test.XXXXXX") || { echo "mktemp failed" >&2; exit 1; }
trap 'rm -rf "$TMP"' EXIT

# Case 1 (#81827): bare "DONE" with no <promise> tag must NOT complete the loop.
d="$TMP/case1"; mkdir -p "$d"
write_state "$d" "iteration: 1" 0 '"DONE"'
out=$(run_hook "$d" "DONE")
check "untagged bare word does not complete" \
  "$([[ -f "$d/.claude/ralph-loop.local.md" ]] && grep -q '"decision": "block"' <<< "$out" && echo true || echo false)"

# Case 1b: properly tagged <promise>DONE</promise> completes and removes state.
d="$TMP/case1b"; mkdir -p "$d"
write_state "$d" "iteration: 1" 0 '"DONE"'
out=$(run_hook "$d" "All finished. <promise>DONE</promise>")
check "tagged promise completes" \
  "$([[ ! -f "$d/.claude/ralph-loop.local.md" ]] && grep -q "Detected" <<< "$out" && echo true || echo false)"

# Case 2 (#81828): promise with a double space must match its tagged emission.
d="$TMP/case2"; mkdir -p "$d"
write_state "$d" "iteration: 1" 0 '"ALL  DONE"'
out=$(run_hook "$d" "<promise>ALL  DONE</promise>")
check "double-space promise completes" \
  "$([[ ! -f "$d/.claude/ralph-loop.local.md" ]] && grep -q "Detected" <<< "$out" && echo true || echo false)"

# Case 2b: single-space promise still works.
d="$TMP/case2b"; mkdir -p "$d"
write_state "$d" "iteration: 1" 0 '"ALL DONE"'
out=$(run_hook "$d" "<promise>ALL DONE</promise>")
check "single-space promise completes" \
  "$([[ ! -f "$d/.claude/ralph-loop.local.md" ]] && grep -q "Detected" <<< "$out" && echo true || echo false)"

# Case 3 (#81829): "iteration:1" (no space) must still advance, and the loop
# must terminate once max_iterations is reached.
d="$TMP/case3"; mkdir -p "$d"
write_state "$d" "iteration:1" 2 null
out=$(run_hook "$d" "still working on it")
advanced=$(grep -c '^iteration: 2$' "$d/.claude/ralph-loop.local.md" || true)
check "no-space iteration counter advances" \
  "$([[ "$advanced" == "1" ]] && grep -q '"decision": "block"' <<< "$out" && echo true || echo false)"
out=$(run_hook "$d" "still working on it")
check "loop terminates at max_iterations" \
  "$([[ ! -f "$d/.claude/ralph-loop.local.md" ]] && grep -q "Max iterations" <<< "$out" && echo true || echo false)"

# Case 4 (control): in-progress message blocks and bumps iteration.
d="$TMP/case4"; mkdir -p "$d"
write_state "$d" "iteration: 1" 0 '"DONE"'
out=$(run_hook "$d" "still working on it")
check "in-progress message blocks and bumps iteration" \
  "$(grep -q '^iteration: 2$' "$d/.claude/ralph-loop.local.md" && grep -q '"decision": "block"' <<< "$out" && echo true || echo false)"

echo ""
if [[ $FAILURES -gt 0 ]]; then
  echo "$FAILURES test(s) failed"
  exit 1
fi
echo "All tests passed"
