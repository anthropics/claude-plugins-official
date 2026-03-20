# Slack Channel

Connect a Slack app to your Claude Code with an MCP server.

The MCP server connects to Slack via Socket Mode (WebSocket) and provides tools to Claude to reply, react, or edit messages. When you message the bot, the server forwards the message to your Claude Code session.

## Prerequisites

- [Bun](https://bun.sh) — the MCP server runs on Bun. Install with `curl -fsSL https://bun.sh/install | bash`.

## Quick Setup
> Default pairing flow for a single-user DM bot. See [ACCESS.md](./ACCESS.md) for channels and multi-user setups.

**1. Create a Slack App.**

Go to [api.slack.com/apps](https://api.slack.com/apps) and click **Create New App** → **From scratch**. Pick a name and workspace.

**2. Enable Socket Mode.**

In your app's dashboard, go to **Settings → Socket Mode** and toggle it on. You'll be prompted to generate an **App-Level Token** — name it anything (e.g. `claude-socket`) and add the `connections:write` scope. Copy the token — it looks like `xapp-1-...`.

**3. Subscribe to events.**

Go to **Features → Event Subscriptions** and toggle on. Under **Subscribe to bot events**, add:
- `message.im` — DMs to the bot
- `message.channels` — messages in public channels (optional, for channel mode)
- `message.groups` — messages in private channels (optional)

**4. Set bot scopes.**

Go to **Features → OAuth & Permissions**. Under **Bot Token Scopes**, add:
- `chat:write` — send messages
- `reactions:write` — add emoji reactions
- `files:read` — download attached files
- `files:write` — upload file attachments
- `im:history` — receive DM messages
- `channels:history` — receive channel messages (if using channels)
- `groups:history` — receive private channel messages (if using channels)

**5. Install to workspace.**

Go to **Settings → Install App** and click **Install to Workspace**. Authorize the permissions. Copy the **Bot User OAuth Token** — it looks like `xoxb-...`.

**6. Install the plugin.**

These are Claude Code commands — run `claude` to start a session first.

Install the plugin:
```
/plugin install slack-channel@claude-plugins-official
```

**7. Give the server the tokens.**

```
/slack-channel:configure xoxb-your-bot-token xapp-your-app-token
```

Writes `SLACK_BOT_TOKEN=...` and `SLACK_APP_TOKEN=...` to `~/.claude/channels/slack-channel/.env`. You can also write that file by hand, or set the variables in your shell environment — shell takes precedence.

**8. Relaunch with the channel flag.**

The server won't connect without this — exit your session and start a new one:

```sh
claude --channels plugin:slack-channel@claude-plugins-official
```

**9. Pair.**

With Claude Code running from the previous step, DM your bot on Slack — it replies with a 6-character pairing code. If the bot doesn't respond, make sure your session is running with `--channels`. In your Claude Code session:

```
/slack-channel:access pair <code>
```

Your next DM reaches the assistant.

**10. Lock it down.**

Pairing is for capturing IDs. Once you're in, switch to `allowlist` so strangers don't get pairing-code replies. Ask Claude to do it, or `/slack-channel:access policy allowlist` directly.

## Access control

See **[ACCESS.md](./ACCESS.md)** for DM policies, channels, mention detection, delivery config, skill commands, and the `access.json` schema.

Quick reference: DM allowlists use **DM channel IDs** (`D...`), not user IDs. Pairing captures these automatically. Default policy is `pairing`.

## Tools exposed to the assistant

| Tool | Purpose |
| --- | --- |
| `reply` | Send to a chat. Takes `chat_id` + `text`, optionally `reply_to` (message ts) for native threading and `files` (absolute paths) for attachments. Each file uploads via Slack's file API. Auto-chunks text at ~4000 chars; files send as separate uploads after the text. Returns the sent message ts(s). |
| `react` | Add an emoji reaction to a message by ts. Pass the emoji name **without colons** (e.g. `thumbsup`, `eyes`, `tada`). Custom workspace emoji are supported. |
| `edit_message` | Edit a message the bot previously sent. Useful for "working…" → result progress updates. Only works on the bot's own messages. |

## Files

Inbound files are downloaded to `~/.claude/channels/slack-channel/inbox/` and the local path is included in the `<channel>` notification so the assistant can `Read` it. Slack serves files behind auth; the server downloads them eagerly on arrival since private download URLs may expire.

Outbound files are uploaded via `files.uploadV2` — pass absolute paths in the `files` array of the `reply` tool.

## No history or search

This plugin provides **no** message history or search. The bot only sees messages as they arrive — no `fetch_messages` tool exists. If the assistant needs earlier context, it will ask you to paste or summarize.

This also means there's no `download_attachment` tool for historical messages — files are downloaded eagerly on arrival since there's no guaranteed way to fetch them later.
