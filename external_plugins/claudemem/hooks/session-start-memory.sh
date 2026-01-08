#!/bin/bash
# ClaudeMem SessionStart Hook
# Loads workspace context at the beginning of each session

MANIFEST="$HOME/Vault/_manifest.md"

# Check if manifest exists
if [ ! -f "$MANIFEST" ]; then
    echo "[ClaudeMem] No workspace manifest found. Run /claudemem to initialize."
    exit 0
fi

# Parse manifest for key info
echo "=== CLAUDEMEM: WORKSPACE STATE ==="
echo ""

# Extract active context using grep/awk
PROJECT=$(grep "^project:" "$MANIFEST" | head -1 | cut -d: -f2 | tr -d ' ')
EPIC=$(grep "^epic:" "$MANIFEST" | head -1 | cut -d: -f2 | tr -d ' ')
TASK=$(grep "^task:" "$MANIFEST" | head -1 | cut -d: -f2 | tr -d ' ')

if [ "$PROJECT" != "null" ] && [ -n "$PROJECT" ]; then
    echo "ACTIVE PROJECT: $PROJECT"

    # Try to get project name from index file
    INDEX_FILE="$HOME/Vault/Projects/$PROJECT/_index.md"
    if [ -f "$INDEX_FILE" ]; then
        NAME=$(grep "^name:" "$INDEX_FILE" | head -1 | cut -d: -f2 | xargs)
        BRIEF=$(grep "^brief:" "$INDEX_FILE" | head -1 | cut -d: -f2- | xargs)
        echo "  Name: $NAME"
        [ -n "$BRIEF" ] && echo "  Brief: $BRIEF"
    fi

    if [ "$EPIC" != "null" ] && [ -n "$EPIC" ]; then
        echo "ACTIVE EPIC: $EPIC"
    fi

    if [ "$TASK" != "null" ] && [ -n "$TASK" ]; then
        echo "ACTIVE TASK: $TASK"
    fi

    echo ""
    echo "Use /claudemem status for full details."
else
    echo "NO ACTIVE PROJECT"
    echo ""

    # Count projects
    PROJECT_COUNT=$(find "$HOME/Vault/Projects" -maxdepth 1 -type d 2>/dev/null | wc -l)
    PROJECT_COUNT=$((PROJECT_COUNT - 1))  # Subtract 1 for the Projects dir itself

    if [ "$PROJECT_COUNT" -gt 0 ]; then
        echo "Available projects: $PROJECT_COUNT"
        echo "Use /claudemem status to see them."
    else
        echo "No projects yet."
        echo "Use /claudemem plan to create one from conversation."
    fi
fi

echo ""
echo "==================================="

exit 0
