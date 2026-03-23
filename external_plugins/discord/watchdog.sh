#!/bin/bash
# PAI Discord Watchdog — cron every 5 minutes
# Ensures daemon is running and healthy

LOG="/tmp/pai-discord-watchdog.log"

# Check daemon health
if ! curl -sf http://localhost:8890/health > /dev/null 2>&1; then
    echo "$(date -Iseconds) Daemon unhealthy, restarting..." >> "$LOG"

    # Kill stale process if PID file exists
    PID_FILE="/tmp/pai-discord-daemon.pid"
    if [ -f "$PID_FILE" ]; then
        kill "$(cat "$PID_FILE")" 2>/dev/null
        rm -f "$PID_FILE"
    fi

    # Try systemd first, fall back to manual start
    if systemctl --user is-enabled pai-discord.service &>/dev/null; then
        systemctl --user restart pai-discord
    else
        cd "$HOME/.claude/channels/discord"
        nohup bun run daemon.ts > /tmp/pai-discord-daemon.log 2>&1 &
        echo $! > "$PID_FILE"
    fi

    echo "$(date -Iseconds) Daemon restart triggered" >> "$LOG"
fi
