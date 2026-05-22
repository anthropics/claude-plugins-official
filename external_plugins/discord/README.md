# Discord

Connect a Discord bot to your Claude Code with an MCP server.

When the bot receives a message, the MCP server forwards it to Claude and provides tools to reply, react, and edit messages.

## Prerequisites

- [Bun](https://bun.sh) — the MCP server runs on Bun. Install with `curl -fsSL https://bun.sh/install | bash`.

## Quick Setup
> Default pairing flow for a single-user DM bot. See [ACCESS.md](./ACCESS.md) for groups and multi-user setups.

**1. Create a Discord application and bot.**

Go to the [Discord Developer Portal](https://discord.com/developers/applications) and click **New Application**. Give it a name.

Navigate to **Bot** in the sidebar. Give your bot a username.

Scroll down to **Privileged Gateway Intents** and enable **Message Content Intent** — without this the bot receives messages with empty content.

**2. Generate a bot token.**

Still on the **Bot** page, scroll up to **Token** and press **Reset Token**. Copy the token — it's only shown once. Hold onto it for step 5.

**3. Invite the bot to a server.**

Discord won't let you DM a bot unless you share a server with it.

Navigate to **OAuth2** → **URL Generator**. Select the `bot` scope. Under **Bot Permissions**, enable:

- View Channels
- Send Messages
- Send Messages in Threads
- Read Message History
- Attach Files
- Add Reactions

Integration type: **Guild Install**. Copy the **Generated URL**, open it, and add the bot to any server you're in.

> For DM-only use you technically need zero permissions — but enabling them now saves a trip back when you want guild channels later.

**4. Install the plugin.**

These are Claude Code commands — run `claude` to start a session first.

Install the plugin:
```
/plugin install discord@claude-plugins-official
/reload-plugins
```

**5. Give the server the token.**

```
/discord:configure MTIz...
```

Writes `DISCORD_BOT_TOKEN=...` to `~/.claude/channels/discord/.env`. You can also write that file by hand, or set the variable in your shell environment — shell takes precedence.

> To run multiple bots on one machine (different tokens, separate allowlists), point `DISCORD_STATE_DIR` at a different directory per instance.

**6. Relaunch with the channel flag.**

The server won't connect without this — exit your session and start a new one:

```sh
claude --channels plugin:discord@claude-plugins-official
```

**7. Pair.**

With Claude Code running from the previous step, DM your bot on Discord — it replies with a pairing code. If the bot doesn't respond, make sure your session is running with `--channels`. In your Claude Code session:

```
/discord:access pair <code>
```

Your next DM reaches the assistant.

**8. Lock it down.**

Pairing is for capturing IDs. Once you're in, switch to `allowlist` so strangers don't get pairing-code replies. Ask Claude to do it, or `/discord:access policy allowlist` directly.

## Access control

See **[ACCESS.md](./ACCESS.md)** for DM policies, guild channels, mention detection, delivery config, skill commands, and the `access.json` schema.

Quick reference: IDs are Discord **snowflakes** (numeric — enable Developer Mode, right-click → Copy ID). Default policy is `pairing`. Guild channels are opt-in per channel ID.

## Tools exposed to the assistant

| Tool | Purpose |
| --- | --- |
| `reply` | Send to a channel. Takes `chat_id` + `text`, optionally `reply_to` (message ID) for native threading and `files` (absolute paths) for attachments — max 10 files, 25MB each. Auto-chunks; files attach to the first chunk. Returns the sent message ID(s). |
| `react` | Add an emoji reaction to a message. Takes `chat_id`, `message_id`, `emoji`. Unicode emoji work directly; custom emoji need `<:name:id>` form. |
| `edit_message` | Edit a message the bot previously sent. Takes `chat_id`, `message_id`, `text`. Useful for interim progress updates; edits don't trigger push notifications, so send a new `reply` when a long task completes. |
| `pin_message` | Pin a message in a channel. Takes `chat_id`, `message_id`. Requires Manage Messages permission. |
| `send_voice_message` | Send a Discord voice message (with waveform UI) from an Ogg/Opus audio file. Takes `chat_id`, `file` (absolute path to `.ogg` Opus), optional `reply_to`. |
| `typing` | Show "bot is typing…" in a channel until a message is sent. Takes `chat_id`. The assistant calls this when it decides an inbound message needs a response, before doing the work. |
| `fetch_messages` | Pull recent history from a channel (oldest-first). Capped at 100 per call. Each line includes the message ID so the model can `reply_to` it; messages with attachments are marked `+Natt`. Discord's search API isn't exposed to bots, so this is the only lookback. |
| `download_attachment` | Download all attachments from a specific message by ID to `~/.claude/channels/discord/inbox/`. Optional `dest_dir` copies files to a target directory. Returns file paths + metadata. Use when `fetch_messages` shows a message has attachments. |

The `typing` tool lets the assistant show a typing indicator manually —
the bot does not auto-type on every inbound message (that made it look
like it was always responding, even when it wasn't).

## Attachments

Attachments are **not** auto-downloaded. The `<channel>` notification lists
each attachment's name, type, and size — the assistant calls
`download_attachment(chat_id, message_id)` when it actually wants the file.
Downloads land in `~/.claude/channels/discord/inbox/`.

Same path for attachments on historical messages found via `fetch_messages`
(messages with attachments are marked `+Natt`).

## Opt-in gate (`VOX_PLUGINS_ENABLED`)

The plugin is inert unless `VOX_PLUGINS_ENABLED=1` is set in the environment. Without it the MCP server still answers `initialize` and `tools/list` (so Claude Code's plugin registry stays happy), but exposes **zero tools**: no `.env` load, no discord.js gateway connection, no state writes, nothing. The process sits idle until shut down.

**Why this exists.** Claude Code auto-starts every registered plugin MCP server in every session. Without the gate, running a fresh `claude` session on the same machine as the bot's long-lived systemd service would spin up a **second** discord.js gateway connection using the same `DISCORD_BOT_TOKEN` — producing duplicate bot responses, racing writes to `access.json` / `dm_users.json`, and generally corrupting state. `VOX_PLUGINS_ENABLED` ensures only the one session you actually want to run the bot (typically your systemd unit) touches Discord; every other session sees a silent no-op plugin.

**How to opt in.** Set the env var in whatever launches your "live" session — most commonly a systemd unit:

```ini
[Service]
Environment=VOX_PLUGINS_ENABLED=1
```

Any other `claude` session on the box stays inert automatically.

## Permission prompts

Tool calls that trigger `permission_request` notifications get a Discord
DM with Allow / Deny / See more buttons, sent to everyone in the
allowlist. If no one answers within 30 s the request is auto-denied.

Set `DISCORD_AUTO_ALLOW_PERMISSIONS=1` to skip the DM entirely and
auto-approve every request. Intended for deployments where the gating
lives in the model's own rules (CLAUDE.md, persona instructions) rather
than the OS prompt layer. Default off. Every auto-allow writes
`permission_request <id> auto-allowed (DISCORD_AUTO_ALLOW_PERMISSIONS=1)
tool=<name>` to stderr for audit.

## Changelog

### 0.2.18
- Harden gateway lifecycle: exit on `shardDisconnect` / `invalidated` / terminal `error`, log-only for `shardError`, plus a 30s-interval watchdog that exits after 3 consecutive non-READY `client.ws.status` checks (resets on inbound messages) so systemd restarts a silently dead socket.
