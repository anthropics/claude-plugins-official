#!/bin/bash
# Stop the PAI Discord Gateway Daemon

PID_FILE="/tmp/pai-discord-daemon.pid"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        sleep 1
        if kill -0 "$PID" 2>/dev/null; then
            kill -9 "$PID"
        fi
        echo -e "${GREEN}OK Discord daemon stopped (PID $PID)${NC}"
    else
        echo -e "${RED}! Daemon not running (stale PID $PID)${NC}"
    fi
    rm -f "$PID_FILE"
else
    echo -e "${RED}! No PID file found${NC}"
fi
