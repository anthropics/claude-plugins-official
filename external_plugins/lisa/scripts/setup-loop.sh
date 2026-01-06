#!/bin/bash

# Lisa Loop Setup Script
# Creates state file for in-session Lisa loop

set -euo pipefail

# Parse arguments
PROMPT_PARTS=()
MAX_ITERATIONS=0
COMPLETION_PROMISE="null"

# Parse options and positional arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      cat << 'HELP_EOF'
Lisa Loop - Interactive self-referential development loop

USAGE:
  /lisa-loop [PROMPT...] [OPTIONS]

ARGUMENTS:
  PROMPT...    Initial prompt to start the loop (can be multiple words without quotes)

OPTIONS:
  --max-iterations <n>           Maximum iterations before auto-stop (default: unlimited)
  --completion-promise '<text>'  Promise phrase (USE QUOTES for multi-word)
  -h, --help                     Show this help message

DESCRIPTION:
  Starts a Lisa loop in your CURRENT session. The stop hook prevents
  exit and feeds your output back as input until completion or iteration limit.

  To signal completion, you must output: <promise>YOUR_PHRASE</promise>

  AUTO-DETECTION: If no --completion-promise flag is provided, the script will
  automatically extract <promise>...</promise> from the prompt content. If the
  prompt is a file path, the file will be read to find the promise.

  Use this for:
  - Interactive iteration where you want to see progress
  - Tasks requiring self-correction and refinement
  - Learning how Lisa works

EXAMPLES:
  /lisa-loop Build a todo API --completion-promise 'DONE' --max-iterations 20
  /lisa-loop --max-iterations 10 Fix the auth bug
  /lisa-loop Refactor cache layer  (runs forever)
  /lisa-loop --completion-promise 'TASK COMPLETE' Create a REST API

STOPPING:
  Only by reaching --max-iterations or detecting --completion-promise
  No manual stop - Lisa runs infinitely by default!

MONITORING:
  # View current iteration:
  grep '^iteration:' .claude/lisa-loop.local.md

  # View full state:
  head -10 .claude/lisa-loop.local.md
HELP_EOF
      exit 0
      ;;
    --max-iterations)
      if [[ -z "${2:-}" ]]; then
        echo "❌ Error: --max-iterations requires a number argument" >&2
        echo "" >&2
        echo "   Valid examples:" >&2
        echo "     --max-iterations 10" >&2
        echo "     --max-iterations 50" >&2
        echo "     --max-iterations 0  (unlimited)" >&2
        echo "" >&2
        echo "   You provided: --max-iterations (with no number)" >&2
        exit 1
      fi
      if ! [[ "$2" =~ ^[0-9]+$ ]]; then
        echo "❌ Error: --max-iterations must be a positive integer or 0, got: $2" >&2
        echo "" >&2
        echo "   Valid examples:" >&2
        echo "     --max-iterations 10" >&2
        echo "     --max-iterations 50" >&2
        echo "     --max-iterations 0  (unlimited)" >&2
        echo "" >&2
        echo "   Invalid: decimals (10.5), negative numbers (-5), text" >&2
        exit 1
      fi
      MAX_ITERATIONS="$2"
      shift 2
      ;;
    --completion-promise)
      if [[ -z "${2:-}" ]]; then
        echo "❌ Error: --completion-promise requires a text argument" >&2
        echo "" >&2
        echo "   Valid examples:" >&2
        echo "     --completion-promise 'DONE'" >&2
        echo "     --completion-promise 'TASK COMPLETE'" >&2
        echo "     --completion-promise 'All tests passing'" >&2
        echo "" >&2
        echo "   You provided: --completion-promise (with no text)" >&2
        echo "" >&2
        echo "   Note: Multi-word promises must be quoted!" >&2
        exit 1
      fi
      COMPLETION_PROMISE="$2"
      shift 2
      ;;
    *)
      # Non-option argument - collect all as prompt parts
      PROMPT_PARTS+=("$1")
      shift
      ;;
  esac
done

# Join all prompt parts with spaces
PROMPT="${PROMPT_PARTS[*]}"

# Check if a loop is already active
if [[ -f ".claude/lisa-loop.local.md" ]]; then
  CURRENT_ITERATION=$(grep '^iteration:' .claude/lisa-loop.local.md 2>/dev/null | sed 's/iteration: *//' || echo "?")
  echo "⚠️  Warning: A Lisa loop is already active (iteration $CURRENT_ITERATION)" >&2
  echo "" >&2
  echo "   Options:" >&2
  echo "     /cancel-lisa     - Cancel existing loop first" >&2
  echo "     /lisa-status     - Check current loop state" >&2
  echo "" >&2
  echo "   Starting a new loop will REPLACE the existing one." >&2
  echo "" >&2
fi

# Validate prompt is non-empty
if [[ -z "$PROMPT" ]]; then
  echo "❌ Error: No prompt provided" >&2
  echo "" >&2
  echo "   Lisa needs a task description to work on." >&2
  echo "" >&2
  echo "   Examples:" >&2
  echo "     /lisa-loop Build a REST API for todos" >&2
  echo "     /lisa-loop Fix the auth bug --max-iterations 20" >&2
  echo "     /lisa-loop --completion-promise 'DONE' Refactor code" >&2
  echo "" >&2
  echo "   For all options: /lisa-loop --help" >&2
  exit 1
fi

# Check if prompt looks like a file path but doesn't exist
if [[ "$PROMPT" == *.md ]] && [[ ! -f "$PROMPT" ]]; then
  echo "⚠️  Warning: '$PROMPT' looks like a file path but doesn't exist" >&2
  echo "" >&2
  echo "   Did you mean to create it first? Try:" >&2
  echo "     /lisa-prep" >&2
  echo "" >&2
  echo "   Or provide an inline prompt instead." >&2
  echo "" >&2
fi

# Auto-extract completion promise from prompt if not explicitly provided
if [[ "$COMPLETION_PROMISE" == "null" ]]; then
  SEARCH_CONTENT="$PROMPT"

  # If prompt is a file path, read its content
  if [[ -f "$PROMPT" ]]; then
    SEARCH_CONTENT=$(cat "$PROMPT" 2>/dev/null || echo "$PROMPT")
    echo "📄 Reading prompt from file: $PROMPT"
  fi

  # Check if content contains <promise>...</promise> tags (portable sed version)
  EXTRACTED_PROMISE=$(echo "$SEARCH_CONTENT" | sed -n 's/.*<promise>\([^<]*\)<\/promise>.*/\1/p' | head -1 || true)
  if [[ -n "$EXTRACTED_PROMISE" ]]; then
    COMPLETION_PROMISE="$EXTRACTED_PROMISE"
    echo "📋 Auto-detected completion promise from prompt: \"$COMPLETION_PROMISE\""
  fi
fi

# Warn if no safety net is configured
if [[ "$COMPLETION_PROMISE" == "null" ]] && [[ "$MAX_ITERATIONS" -eq 0 ]]; then
  echo "" >&2
  echo "🚨 DANGER: No safety limits configured!" >&2
  echo "" >&2
  echo "   This loop will run FOREVER because:" >&2
  echo "   - No completion promise detected in prompt" >&2
  echo "   - No --max-iterations limit set" >&2
  echo "" >&2
  echo "   Recommended: Add one of these:" >&2
  echo "   - Include <promise>DONE</promise> in your prompt" >&2
  echo "   - Add --max-iterations 50" >&2
  echo "" >&2
  echo "   Continuing anyway in 3 seconds... (Ctrl+C to abort)" >&2
  sleep 3
fi

# Create state file for stop hook (markdown with YAML frontmatter)
mkdir -p .claude

# Quote completion promise for YAML if it contains special chars or is not null
if [[ -n "$COMPLETION_PROMISE" ]] && [[ "$COMPLETION_PROMISE" != "null" ]]; then
  COMPLETION_PROMISE_YAML="\"$COMPLETION_PROMISE\""
else
  COMPLETION_PROMISE_YAML="null"
fi

cat > .claude/lisa-loop.local.md <<EOF
---
active: true
iteration: 1
max_iterations: $MAX_ITERATIONS
completion_promise: $COMPLETION_PROMISE_YAML
started_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
---

$PROMPT
EOF

# Output setup message
cat <<EOF
🔄 Lisa loop activated in this session!

Iteration: 1
Max iterations: $(if [[ $MAX_ITERATIONS -gt 0 ]]; then echo $MAX_ITERATIONS; else echo "unlimited"; fi)
Completion promise: $(if [[ "$COMPLETION_PROMISE" != "null" ]]; then echo "${COMPLETION_PROMISE//\"/} (ONLY output when TRUE - do not lie!)"; else echo "none (runs forever)"; fi)

The stop hook is now active. When you try to exit, the SAME PROMPT will be
fed back to you. You'll see your previous work in files, creating a
self-referential loop where you iteratively improve on the same task.

To monitor: head -10 .claude/lisa-loop.local.md

⚠️  WARNING: This loop cannot be stopped manually! It will run infinitely
    unless you set --max-iterations or --completion-promise.

🔄
EOF

# Output the initial prompt if provided
if [[ -n "$PROMPT" ]]; then
  echo ""
  echo "$PROMPT"
fi

# Display completion promise requirements if set
if [[ "$COMPLETION_PROMISE" != "null" ]]; then
  echo ""
  echo "═══════════════════════════════════════════════════════════"
  echo "CRITICAL - Lisa Loop Completion Promise"
  echo "═══════════════════════════════════════════════════════════"
  echo ""
  echo "To complete this loop, output this EXACT text:"
  echo "  <promise>$COMPLETION_PROMISE</promise>"
  echo ""
  echo "STRICT REQUIREMENTS (DO NOT VIOLATE):"
  echo "  ✓ Use <promise> XML tags EXACTLY as shown above"
  echo "  ✓ The statement MUST be completely and unequivocally TRUE"
  echo "  ✓ Do NOT output false statements to exit the loop"
  echo "  ✓ Do NOT lie even if you think you should exit"
  echo ""
  echo "IMPORTANT - Do not circumvent the loop:"
  echo "  Even if you believe you're stuck, the task is impossible,"
  echo "  or you've been running too long - you MUST NOT output a"
  echo "  false promise statement. The loop is designed to continue"
  echo "  until the promise is GENUINELY TRUE. Trust the process."
  echo ""
  echo "  If the loop should stop, the promise statement will become"
  echo "  true naturally. Do not force it by lying."
  echo "═══════════════════════════════════════════════════════════"
fi
