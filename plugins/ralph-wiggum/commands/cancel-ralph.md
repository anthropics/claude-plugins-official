---
description: "Cancel active Ralph Wiggum loop"
argument-hint: "[LOOP_NAME]"
allowed-tools: ["Bash"]
hide-from-slash-command-tool: "true"
---

# Cancel Ralph

First, check for active ralph loops by running this command:

```bash
# List all active ralph loops
echo "=== Active Ralph Loops ==="
for f in .claude/ralph-loop-*.local.md; do
  if [[ -f "$f" ]]; then
    NAME=$(grep '^name:' "$f" | sed 's/name: *//' | tr -d '"')
    ITER=$(grep '^iteration:' "$f" | sed 's/iteration: *//')
    PROMISE=$(grep '^completion_promise:' "$f" | sed 's/completion_promise: *//' | tr -d '"')
    echo "  - $NAME (iteration $ITER, promise: $PROMISE)"
    echo "    File: $f"
  fi
done

# Also check for legacy format
if [[ -f .claude/ralph-loop.local.md ]]; then
  ITER=$(grep '^iteration:' .claude/ralph-loop.local.md | sed 's/iteration: *//')
  echo "  - [legacy] (iteration $ITER)"
  echo "    File: .claude/ralph-loop.local.md"
fi

# Count active loops
COUNT=$(ls -1 .claude/ralph-loop*.local.md 2>/dev/null | wc -l | tr -d ' ')
echo ""
echo "Total active loops: $COUNT"
```

Based on the output and the user's request:

## If user specified a loop name (e.g., `/cancel-ralph chart-review`):

Cancel that specific loop:
```bash
LOOP_NAME="<the-name-user-specified>"
rm -f ".claude/ralph-loop-${LOOP_NAME}.local.md"
# Also clean up any TTY links pointing to this loop
grep -l "^${LOOP_NAME}$" .claude/.ralph-tty* 2>/dev/null | xargs rm -f 2>/dev/null || true
echo "Cancelled ralph loop: $LOOP_NAME"
```

## If user wants to cancel ALL loops (e.g., `/cancel-ralph --all`):

```bash
rm -f .claude/ralph-loop*.local.md .claude/.ralph-tty* 2>/dev/null
echo "Cancelled all ralph loops"
```

## If no loops are active:

Say "No active Ralph loops found."

## If loops exist but user didn't specify which one:

List them and ask which one to cancel, or suggest using `--all` to cancel all.
