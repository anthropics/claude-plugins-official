#!/bin/bash
# PreToolUse hook: Lists uncommitted changes and nudges Claude

changes=$(git status --porcelain 2>/dev/null)

if [ -z "$changes" ]; then
    exit 0
fi

echo "=== PACT Audit ==="
echo ""
echo "Files changed this session:"
echo "$changes" | while read -r line; do
    file="${line:3}"
    echo "  • $file"
done
echo ""
echo "Consider:"
echo "  • Any cleanup or docs updates needed?"
echo "  • Ready to commit?"
echo ""
