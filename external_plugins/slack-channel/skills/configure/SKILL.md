---
name: configure
description: Configure Slack credentials for the slack-channel plugin
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Bash(ls *)
  - Bash(mkdir *)
---

# Slack Channel Plugin Configuration

You are helping the user configure their Slack credentials for the slack-channel plugin.

## Credentials Location

Credentials are stored at: `~/.claude/channels/slack-channel/.env`

## Handle the user's request

### If no arguments provided — show status:

1. Check if `~/.claude/channels/slack-channel/.env` exists
2. If it does, show which vars are set (mask the values):
   - `SLACK_BOT_TOKEN` — required
   - `SLACK_APP_TOKEN` — required for real-time notifications
   - `SLACK_CHANNEL_ID` — optional, filters to one channel
3. Show connection status if the MCP server is running

### If the user provides tokens — save them:

Write to `~/.claude/channels/slack-channel/.env`:
```
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
SLACK_CHANNEL_ID=C...  # optional
```

### If the user says "clear" — remove credentials:

Delete `~/.claude/channels/slack-channel/.env`.

## Setup Instructions (show if no credentials configured)

To set up the Slack channel plugin:

1. **Create a Slack App** at https://api.slack.com/apps → "Create New App" → "From an app manifest"

2. **Use this manifest** (paste into the YAML tab):
```yaml
display_information:
  name: Claude Code
  description: Claude Code channel plugin
settings:
  socket_mode_enabled: true
  token_rotation_enabled: false
  org_deploy_enabled: false
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
  app_home:
    messages_tab_enabled: true
event_subscriptions:
  bot_events:
    - message.channels
    - message.groups
```

3. **Install to workspace** → OAuth & Permissions → Install

4. **Get tokens**:
   - Bot Token: OAuth & Permissions → Bot User OAuth Token (`xoxb-...`)
   - App Token: Basic Information → App-Level Tokens → Generate (`xapp-...`, needs `connections:write` scope)

5. **Configure**: `/slack-channel:configure <bot-token> <app-token>`

6. **Optional**: Add a channel filter: `/slack-channel:configure channel <channel-id>`

7. **Restart Claude Code** to pick up the new credentials.
