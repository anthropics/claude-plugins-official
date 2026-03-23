# Fixing Discord's Multi-Session Gateway Conflict in Claude Code

**TL;DR:** The Claude Code Discord plugin spawns one gateway connection per session. Discord enforces one connection per bot token. If you run multiple sessions, messages silently vanish. We fixed it by splitting the plugin into a shared daemon and a lightweight bridged server, connected by a filesystem queue.

---

## The Problem

The [Claude Code Discord plugin](https://github.com/anthropics/claude-code-plugins) is well-designed for its intended use case: a single Claude Code session with a Discord bot. Each session spawns an MCP server that opens its own discord.js gateway connection, handles inbound messages, and sends replies. Clean architecture, works great.

Until you run more than one session.

Discord's gateway enforces **one active WebSocket connection per bot token**. When a second session connects with the same token, Discord doesn't error out -- it silently migrates the connection. The previous session's gateway goes dead without notification. Messages arrive at whichever session connected last. Start eight sessions? Seven of them have dead Discord connections and don't know it.

The failure mode is invisible:
- No error messages in any log
- No connection refused
- Messages simply stop arriving at sessions that were connected first
- The "winning" session changes every time a new session starts
- Replies from dead sessions may or may not send (race condition on the gateway)

If you've ever had a Discord bot go silent mid-conversation and couldn't figure out why, this is probably it.

## The Fix: Daemon + Bridged Server

The solution is architectural: separate the gateway connection (which must be a singleton) from the MCP interface (which must be per-session).

### Architecture

```
                         ┌─────────────────────────┐
                         │     Discord Gateway      │
                         │    (WebSocket, 1 per bot) │
                         └────────────┬────────────┘
                                      │
                         ┌────────────▼────────────┐
                         │     daemon.ts            │
                         │   (systemd service)      │
                         │   - Owns gateway         │
                         │   - Access control       │
                         │   - Health: :8890        │
                         └────┬───────────────┬────┘
                              │ write         │ read
                    ┌─────────▼───┐     ┌─────▼─────────┐
                    │  inbound/   │     │  outbound/     │
                    │  (JSON queue)│     │  (JSON queue)  │
                    └─────────┬───┘     └─────┬─────────┘
                              │ read          │ write
                         ┌────▼───────────────▼────┐
                         │   server-bridged.ts      │
                         │   (MCP server, per-session)│
                         │   - Same tools as before │
                         │   - Same notifications   │
                         │   - No gateway connection │
                         └─────────────────────────┘
                                      │
                              ┌───────▼───────┐
                              │  Claude Code   │
                              │  (any session) │
                              └───────────────┘
```

### Component 1: The Daemon (`daemon.ts`)

A standalone Bun process managed by systemd. It is the **sole owner** of the Discord gateway connection.

**What it does:**
- Connects to Discord via discord.js (same intents, partials, and client config as the original plugin)
- Runs the full access control gate: DM pairing, allowlists, group policies, mention detection
- Writes inbound messages as JSON files to `~/.claude/channels/discord/inbound/`
- Polls `~/.claude/channels/discord/outbound/` every second for commands (reply, react, edit, fetch)
- Executes outbound commands via discord.js, writes results back as `.result.json` files
- Exposes a health endpoint on port 8890

**What it doesn't do:**
- No MCP server
- No stdio transport
- No awareness of Claude Code sessions

The daemon is intentionally simple. It's a queue worker with a Discord connection.

**Inbound message format** (written by daemon, consumed by bridged server):

```json
{
  "type": "message",
  "chat_id": "1234567890",
  "message_id": "9876543210",
  "user": "alice",
  "user_id": "111222333444555666",
  "content": "hey, how's the build going?",
  "ts": "2026-03-22T15:30:00.000Z",
  "attachments": []
}
```

**Outbound command format** (written by bridged server, executed by daemon):

```json
{
  "type": "reply",
  "chat_id": "1234567890",
  "text": "Build is at 80%, tests passing. ETA 10 minutes.",
  "reply_to": "9876543210",
  "request_id": "a1b2c3d4e5f6g7h8"
}
```

The daemon writes a corresponding `.result.json` after executing:

```json
{
  "request_id": "a1b2c3d4e5f6g7h8",
  "success": true,
  "result": "sent (id: 1122334455)",
  "error": null
}
```

### Component 2: The Bridged Server (`server-bridged.ts`)

A drop-in replacement for the original `server.ts`. From Claude Code's perspective, nothing changed -- same MCP tools, same notification format, same tool schemas.

**What changed internally:**
- No discord.js import, no `Client`, no gateway connection
- Inbound: polls `inbound/` every 2 seconds, fires `mcp.notification()` for each message, deletes the file
- Outbound: when tools are called, writes a command JSON to `outbound/`, polls for the `.result.json` response (15s timeout)
- All five tools preserved: `reply`, `react`, `edit_message`, `download_attachment`, `fetch_messages`

The bridged server is ~340 lines vs the original's ~707. Most of the reduction comes from removing the discord.js client, gateway event handlers, and duplicated access control logic.

### The Queue Protocol

Communication between daemon and bridged server uses **atomic file writes**:

1. Writer creates a temp file (`.filename.tmp`)
2. Writer calls `rename()` to atomically move it to the final path
3. Reader sees complete files only -- no partial reads

This is a deliberate choice over Unix sockets, HTTP, or shared memory. The filesystem queue means:
- **Crash recovery is free.** If the daemon restarts, queued messages survive on disk.
- **No coordination protocol.** No handshakes, no connection state, no reconnection logic.
- **Debuggable.** `ls inbound/` shows you exactly what's pending. `cat` any file to inspect it.
- **Latency is ~50-200ms.** Acceptable for a chat interface.

### Systemd Service

The daemon runs as a systemd user service:

```ini
[Unit]
Description=PAI Discord Gateway Daemon
After=network-online.target

[Service]
Type=simple
ExecStart=/home/user/.bun/bin/bun run /home/user/.claude/channels/discord/daemon.ts
Restart=always
RestartSec=5
Environment=HOME=/home/user

[Install]
WantedBy=default.target
```

This gives you:
- Auto-restart on crash (5s delay)
- Survives SSH disconnections
- Survives session crashes
- Starts on boot (if enabled)
- Standard `systemctl --user start/stop/status pai-discord` management

---

## The Courier Pattern

With the daemon handling the gateway, any session can communicate with Discord via the bridged server. But there's a design constraint: the bridged server **deletes inbound files after consuming them**. First reader wins. If two sessions run the bridged plugin, one gets the message, the other doesn't.

For multi-session setups, we use a dedicated session called the **Courier** -- a single Claude Code session whose job is Discord communication.

### What the Courier Does

1. **Receives all Discord messages** via the bridged MCP server
2. **Responds to direct questions** ("what are you working on?", "how's the build?")
3. **Monitors other sessions** by reading `work.json` and PRD files to report progress
4. **Stays alive** in a tmux session, surviving SSH drops

### Context Isolation

The Courier session can use `/clear` to reset its context without losing the Discord connection. The bridged server is an MCP plugin -- it persists across `/clear` commands. This means you can:

- Handle a long Discord conversation
- `/clear` to free context
- Continue handling new messages with a fresh context window

### Watchdog

A simple cron job (every 5 minutes) checks both the daemon and the Courier:

```bash
#!/bin/bash
# Check daemon health
if ! curl -sf http://localhost:8890/health > /dev/null 2>&1; then
  systemctl --user restart pai-discord
fi

# Check Courier tmux session
if ! tmux has-session -t pai-courier 2>/dev/null; then
  tmux new-session -d -s pai-courier \
    "claude --channels plugin:discord@claude-plugins-official"
fi
```

---

## Setup Guide

### Prerequisites

- Claude Code with the Discord plugin installed (`claude plugins install discord@claude-plugins-official`)
- A Discord bot token (from the [Discord Developer Portal](https://discord.com/developers/applications))
- Bun runtime
- systemd (Linux) or launchd (macOS, with adapted plist)

### Step 1: Create the Files

Place `daemon.ts` and `server-bridged.ts` in `~/.claude/channels/discord/`. The source is in this repository.

### Step 2: Configure the Bot Token

```bash
# Create the env file
echo "DISCORD_BOT_TOKEN=your-token-here" > ~/.claude/channels/discord/.env
chmod 600 ~/.claude/channels/discord/.env
```

### Step 3: Point the Plugin at the Bridged Server

Edit the plugin's `.mcp.json` to use `server-bridged.ts` instead of `server.ts`:

```json
{
  "mcpServers": {
    "discord": {
      "command": "bun",
      "args": ["run", "/home/user/.claude/channels/discord/server-bridged.ts"]
    }
  }
}
```

Or update your `settings.json`:

```json
{
  "mcpServers": {
    "discord": {
      "command": "bun",
      "args": ["run", "/home/user/.claude/channels/discord/server-bridged.ts"]
    }
  }
}
```

### Step 4: Install the Systemd Service

```bash
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/pai-discord.service << 'EOF'
[Unit]
Description=PAI Discord Gateway Daemon
After=network-online.target

[Service]
Type=simple
ExecStart=%h/.bun/bin/bun run %h/.claude/channels/discord/daemon.ts
Restart=always
RestartSec=5
Environment=HOME=%h

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable pai-discord
systemctl --user start pai-discord
```

### Step 5: Verify

```bash
# Check daemon is running
systemctl --user status pai-discord

# Check health endpoint
curl http://localhost:8890/health
# Should return: {"status":"ok","gateway":true,"bot":"YourBot#1234",...}

# Send a test DM to your bot -- a file should appear in:
ls ~/.claude/channels/discord/inbound/
```

### Step 6: Launch the Courier (Optional)

```bash
tmux new-session -d -s pai-courier \
  "claude --channels plugin:discord@claude-plugins-official"
```

### Step 7: Kill Orphaned Processes

If you previously ran the original plugin across multiple sessions:

```bash
# Find and kill old server.ts processes (not daemon, not bridged)
ps aux | grep 'server.ts' | grep discord | grep -v daemon | grep -v bridged | grep -v grep
# Kill any PIDs found
```

---

## Testing

The repository includes a stress test harness (`stress-test.ts`) that validates the queue machinery without requiring Discord API calls.

### What It Tests

**9 test scenarios, 14 assertions:**

| Test | What It Validates |
|------|-------------------|
| Health | Daemon is running, gateway connected |
| Burst | 10 rapid-fire messages queue and deliver correctly |
| Large Message | 3000-character messages survive the queue intact |
| Queue Ordering | FIFO ordering preserved (timestamp-based filenames) |
| Atomic Write | No partial reads under concurrent writes |
| Outbound Timeout | Daemon returns errors for invalid commands |
| Daemon Restart | Queue files survive systemd restart |
| Courier Crash | Messages accumulate during Courier downtime |
| Process Isolation | No rogue gateway processes from old plugin |

### Running the Tests

```bash
# Run all tests
bun run ~/.claude/channels/discord/stress-test.ts

# Run a specific test
bun run ~/.claude/channels/discord/stress-test.ts burst
bun run ~/.claude/channels/discord/stress-test.ts isolation
```

### Example Output

```
╔══════════════════════════════════════════════╗
║   PAI Discord Courier -- Stress Test Harness  ║
╚══════════════════════════════════════════════╝

━━━ TEST: Daemon Health ━━━
  ✓ daemon healthy -- gateway: true, bot: PAI#1234, uptime: 3600s

━━━ TEST: Burst -- 10 rapid-fire messages ━━━
  ✓ all 10 messages queued (3ms)
  ✓ all 10 consumed by bridged server
  ✓ all 10 logged in bridged.log

━━━ TEST: Process Isolation -- no rogue Discord processes ━━━
  ✓ no rogue Discord server.ts processes
  ✓ 1 bridged server instance(s) -- correct

━━━ RESULTS ━━━
  14 passed  0 failed  0 skipped

PASS
```

---

## Tradeoffs

| Decision | Tradeoff | Why It's OK |
|----------|----------|-------------|
| Filesystem queue | ~50-200ms latency vs direct MCP | Acceptable for chat. Gains crash recovery for free. |
| Single Courier | One context window for all Discord | `/clear` resets it. Phase 2 (HTTP MCP) solves this properly. |
| Polling (not `fs.watch`) | Slightly higher latency | `fs.watch` is unreliable across platforms. Polling at 1-2s is good enough. |
| Daemon needs discord.js | Additional dependency | Symlink to the plugin's existing `node_modules`. No new install. |

## Future: Phase 2 (HTTP MCP)

The filesystem queue is the pragmatic MVP. The ideal-state architecture is an HTTP MCP server:

- Daemon adds `StreamableHTTPServerTransport` on port 8889
- `settings.json` points to `http://localhost:8889/mcp`
- All sessions get Discord tools natively (no dedicated Courier)
- Notification routing: sessions register as "Discord handler" via a tool call
- Eliminates the filesystem queue entirely

This requires solving notification fan-out (which session should receive a given Discord message?) -- a harder problem that the Courier pattern sidesteps.

---

## Credits

- The [Claude Code Discord plugin team](https://github.com/anthropics/claude-code-plugins) for the original plugin design. The MCP tool interface, access control system, and notification format are all theirs -- well-built and thoughtfully designed. This fix preserves their interface entirely.
- The gateway conflict is a Discord platform constraint, not a plugin bug. The plugin was designed for single-session use and does that job well.
