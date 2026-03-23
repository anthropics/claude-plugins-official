#!/bin/bash
# Start the PAI Discord Courier session in tmux

SESSION_NAME="pai-courier"

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "Courier session already running: tmux attach -t $SESSION_NAME"
    exit 0
fi

tmux new-session -d -s "$SESSION_NAME" \
  "claude --channels plugin:discord@claude-plugins-official"

echo "Courier session started in tmux: $SESSION_NAME"
echo "  Attach: tmux attach -t $SESSION_NAME"
