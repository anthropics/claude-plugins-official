#!/bin/bash
# Start the Discord Gateway Daemon

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PID_FILE="/tmp/discord-daemon.pid"
LOG_FILE="/tmp/discord-daemon.log"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}> Starting Discord Daemon...${NC}"

# Check if already running
if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo -e "${YELLOW}! Daemon is already running (PID $(cat "$PID_FILE"))${NC}"
    echo "  To restart, use: ./stop-daemon.sh && ./start-daemon.sh"
    exit 0
fi

# Install dependencies if needed
if [ ! -d "$SCRIPT_DIR/node_modules" ]; then
    echo -e "${YELLOW}> Installing dependencies...${NC}"
    cd "$SCRIPT_DIR" && bun install --no-summary
fi

# Start daemon with nohup
cd "$SCRIPT_DIR"
nohup bun run daemon.ts > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

# Wait for health endpoint
sleep 3

if curl -s -f http://localhost:8890/health > /dev/null 2>&1; then
    echo -e "${GREEN}OK Discord daemon started (PID $(cat "$PID_FILE"))${NC}"
    echo "  Health: http://localhost:8890/health"
    echo "  Logs:   tail -f $LOG_FILE"
else
    echo -e "${RED}X Failed to start Discord daemon${NC}"
    echo "  Check logs: cat $LOG_FILE"
    exit 1
fi
