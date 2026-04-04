#!/bin/bash

# Remote Control Setup Script
# Creates a state file stub for the remote-control session.
# Claude (not this script) will call RemoteTrigger to create the actual trigger,
# since the OAuth token is only available in-process.

set -euo pipefail

TRIGGER_NAME=""
MAX_COMMANDS=0

while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      cat << 'HELP_EOF'
Remote Control - Send commands to this session from external systems

USAGE:
  /remote-control [OPTIONS]

OPTIONS:
  --name <name>          Name for the trigger (default: auto-generated from project)
  --max-commands <n>     Maximum commands to accept before auto-stopping (default: unlimited)
  -h, --help             Show this help message

DESCRIPTION:
  Creates a RemoteTrigger and starts listening for incoming commands.
  External systems can send prompts to this running Claude Code session
  using the RemoteTrigger API.

EXAMPLES:
  /remote-control
  /remote-control --name my-project-remote
  /remote-control --name ci-runner --max-commands 10

SENDING COMMANDS (from external system):
  Use RemoteTrigger tool: action=run trigger_id=<id> body={"command": "your task"}
  Or via API: POST /v1/code/triggers/<id>/run

SPECIAL COMMANDS:
  SHUTDOWN   - Gracefully ends the remote-control session

STOPPING:
  /remote-control-stop   - Stop listening and deactivate trigger
  /remote-control-status - Check current session status
HELP_EOF
      exit 0
      ;;
    --name)
      if [[ -z "${2:-}" ]]; then
        echo "❌ Error: --name requires a value" >&2
        exit 1
      fi
      TRIGGER_NAME="$2"
      shift 2
      ;;
    --max-commands)
      if [[ -z "${2:-}" ]]; then
        echo "❌ Error: --max-commands requires a number" >&2
        exit 1
      fi
      if ! [[ "$2" =~ ^[0-9]+$ ]]; then
        echo "❌ Error: --max-commands must be a non-negative integer, got: $2" >&2
        exit 1
      fi
      MAX_COMMANDS="$2"
      shift 2
      ;;
    *)
      echo "❌ Error: Unknown argument: $1" >&2
      echo "   Run /remote-control --help for usage" >&2
      exit 1
      ;;
  esac
done

# Auto-generate trigger name from project directory if not provided
if [[ -z "$TRIGGER_NAME" ]]; then
  TRIGGER_NAME="remote-$(basename "$(pwd)" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/-*$//')"
fi

# Check if a session is already active
if [[ -f ".claude/remote-control.local.md" ]]; then
  EXISTING_ACTIVE=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' ".claude/remote-control.local.md" | grep '^active:' | sed 's/active: *//')
  if [[ "$EXISTING_ACTIVE" == "true" ]]; then
    echo "⚠️  A remote-control session is already active." >&2
    echo "   Run /remote-control-stop first, or /remote-control-status to check it." >&2
    exit 1
  fi
fi

# Create .claude directory if needed
mkdir -p .claude

NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Write state file with PENDING trigger_id — Claude will fill in the real one
cat > .claude/remote-control.local.md << EOF
---
active: true
session_id: ${CLAUDE_CODE_SESSION_ID:-}
trigger_id: PENDING
trigger_name: ${TRIGGER_NAME}
max_commands: ${MAX_COMMANDS}
commands_executed: 0
last_poll_at: "${NOW}"
started_at: "${NOW}"
---
Remote control session active. Polling trigger: ${TRIGGER_NAME}
EOF

# Output instructions for Claude to use when creating the trigger
cat << EOF
✅ State file created.

TRIGGER_NAME=${TRIGGER_NAME}
MAX_COMMANDS=${MAX_COMMANDS}

Next: Create the RemoteTrigger using the RemoteTrigger tool with:
  action: create
  body: {"name": "${TRIGGER_NAME}", "description": "Remote control trigger for this Claude Code session"}

Then update .claude/remote-control.local.md with the returned trigger ID.
EOF
