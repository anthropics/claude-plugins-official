#!/bin/bash
# ClaudeMem Stop Hook
# Reminds about session saving when there's active work

MANIFEST="$HOME/Vault/_manifest.md"

# Only run if manifest exists
if [ ! -f "$MANIFEST" ]; then
    exit 0
fi

# Check if there's an active project
PROJECT=$(grep "^project:" "$MANIFEST" | head -1 | cut -d: -f2 | tr -d ' ')

if [ "$PROJECT" != "null" ] && [ -n "$PROJECT" ]; then
    # Check if session was saved today
    TODAY=$(date +%Y-%m-%d)
    SESSION_FILE="$HOME/Vault/Sessions/${TODAY}.md"

    if [ ! -f "$SESSION_FILE" ]; then
        # No session saved today, output reminder (goes to Claude's context)
        echo ""
        echo "[ClaudeMem] Active project: $PROJECT. Consider /claudemem save before ending."
    fi
fi

exit 0
