#!/bin/bash
set -euo pipefail

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [ -z "$COMMAND" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# --- Always blocked (dangerous regardless of location) ---
ALWAYS_BLOCKED=(
  "git push.*--force"
  "git push.*-f\b"
  "git reset --hard"
  "git checkout \."
  "git clean.*-f"
  "drop_table"
  "drop table"
  "truncate table"
  "rails db:drop"
  "rails db:reset"
  "rake db:drop"
  "rake db:reset"
  "mkfs\."
  "dd if="
  "\bformat\b.*disk"
)

for pattern in "${ALWAYS_BLOCKED[@]}"; do
  if echo "$COMMAND" | grep -qiE "$pattern"; then
    echo "BLOCKED: '$COMMAND' matches dangerous pattern '$pattern'. This command is always blocked. Ask user for explicit permission." >&2
    exit 2
  fi
done

# --- File deletion: allowed inside project, blocked outside ---
if echo "$COMMAND" | grep -qE '\brm\b'; then
  # Extract paths from rm command (skip flags)
  PATHS=$(echo "$COMMAND" | grep -oE '\brm\s+.*' | sed 's/^rm\s*//' | tr ' ' '\n' | grep -v '^-')

  for TARGET in $PATHS; do
    # Resolve to absolute path
    if [[ "$TARGET" != /* ]]; then
      TARGET="$PROJECT_DIR/$TARGET"
    fi
    RESOLVED=$(realpath -m "$TARGET" 2>/dev/null || echo "$TARGET")

    if [[ "$RESOLVED" != "$PROJECT_DIR"* ]]; then
      echo "BLOCKED: 'rm' targets '$RESOLVED' which is OUTSIDE project directory '$PROJECT_DIR'. File deletion is only allowed within the project. Ask user for explicit permission." >&2
      exit 2
    fi

    # Block deleting the project root itself
    if [[ "$RESOLVED" == "$PROJECT_DIR" ]]; then
      echo "BLOCKED: Cannot delete the project root directory itself." >&2
      exit 2
    fi
  done
fi

# --- Moving/copying files outside project ---
if echo "$COMMAND" | grep -qE '\bmv\b'; then
  # Get the last argument (destination) of mv
  DEST=$(echo "$COMMAND" | grep -oE '\bmv\s+.*' | awk '{print $NF}')
  if [ -n "$DEST" ]; then
    if [[ "$DEST" != /* ]]; then
      DEST="$PROJECT_DIR/$DEST"
    fi
    RESOLVED=$(realpath -m "$DEST" 2>/dev/null || echo "$DEST")

    if [[ "$RESOLVED" != "$PROJECT_DIR"* ]]; then
      echo "BLOCKED: 'mv' destination '$RESOLVED' is OUTSIDE project directory '$PROJECT_DIR'. Ask user for explicit permission." >&2
      exit 2
    fi
  fi
fi

# --- Writing to files outside project via redirection ---
if echo "$COMMAND" | grep -qE '>\s*/'; then
  REDIR_TARGET=$(echo "$COMMAND" | grep -oE '>\s*/[^ ]+' | sed 's/^>\s*//')
  if [ -n "$REDIR_TARGET" ]; then
    RESOLVED=$(realpath -m "$REDIR_TARGET" 2>/dev/null || echo "$REDIR_TARGET")

    if [[ "$RESOLVED" != "$PROJECT_DIR"* ]]; then
      echo "BLOCKED: Redirect target '$RESOLVED' is OUTSIDE project directory '$PROJECT_DIR'. Ask user for explicit permission." >&2
      exit 2
    fi
  fi
fi

# --- Chmod/chown outside project ---
for CMD_NAME in chmod chown; do
  if echo "$COMMAND" | grep -qE "\b${CMD_NAME}\b"; then
    PATHS=$(echo "$COMMAND" | grep -oE "\b${CMD_NAME}\s+.*" | sed "s/^${CMD_NAME}\s*//" | tr ' ' '\n' | grep -v '^-' | grep -v '^[0-9]')
    for TARGET in $PATHS; do
      if [[ "$TARGET" != /* ]]; then
        TARGET="$PROJECT_DIR/$TARGET"
      fi
      RESOLVED=$(realpath -m "$TARGET" 2>/dev/null || echo "$TARGET")

      if [[ "$RESOLVED" != "$PROJECT_DIR"* ]]; then
        echo "BLOCKED: '${CMD_NAME}' targets '$RESOLVED' which is OUTSIDE project directory. Ask user for explicit permission." >&2
        exit 2
      fi
    done
  fi
done

exit 0
