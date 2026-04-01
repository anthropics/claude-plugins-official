# slack-channel-plugin

Slack channel plugin for [Claude Code](https://claude.ai/code) — real-time messaging via Socket Mode with per-conversation thread routing.

## What it does

- Connects to Slack via Socket Mode and pushes messages into your Claude Code session in real time
- Threads you create via the `reply` tool are automatically tracked — replies come back to the right session
- Multiple Claude Code sessions get isolated routing (each session only sees replies to its own threads)
- Persists thread ownership across `--resume`

## Quick Start

### 1. Install the plugin

```bash
# From a marketplace (once published):
claude plugin install slack-channel@<marketplace>

# Or load directly during development:
claude --plugin-dir /path/to/slack-channel-plugin
```

### 2. Create a Slack App

Go to https://api.slack.com/apps → Create New App → From manifest:

```yaml
display_information:
  name: Claude Code
settings:
  socket_mode_enabled: true
oauth_config:
  scopes:
    bot:
      - channels:history
      - channels:read
      - chat:write
      - groups:history
      - groups:read
      - reactions:read
      - reactions:write
      - users:read
features:
  bot_user:
    display_name: Claude Code
    always_online: true
event_subscriptions:
  bot_events:
    - message.channels
    - message.groups
```

Install to your workspace, then get:
- **Bot Token**: OAuth & Permissions → Bot User OAuth Token (`xoxb-...`)
- **App Token**: Basic Information → App-Level Tokens → Generate with `connections:write` scope (`xapp-...`)

### 3. Configure credentials

In Claude Code, run:
```
/slack-channel:configure <bot-token> <app-token>
```

Or manually create `~/.claude/channels/slack-channel/.env`:
```
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
SLACK_CHANNEL_ID=C...  # optional: filter to one channel
```

### 4. Enable channels

Start Claude Code with the channels flag:
```bash
claude --dangerously-load-development-channels server:slack-channel
```

## Tools

| Tool | Description |
|------|-------------|
| `reply` | Send a message to a channel or thread |
| `add_reaction` | Add an emoji reaction |
| `list_channels` | List available channels |
| `read_history` | Read channel message history |
| `get_thread` | Get thread replies |

## Architecture

- **Single Socket Mode connection** — leader election via lock file prevents duplicate event delivery
- **Event bus** — leader writes Slack events to a shared JSONL file; all instances tail it
- **Per-conversation routing** — threads tracked by Claude Code conversation ID (stable across `--resume`)
- **SessionStart hook** — writes conversation ID so the MCP server can associate threads with sessions
- **Custom notifications** — `notifications/claude/channel` sent via raw `_write_stream` (bypasses MCP SDK's typed validation)

## License

Apache 2.0
