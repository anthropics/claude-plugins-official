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

## Per-session channel routing (opt-in)

By default every Claude Code session shares the bot's DM conversation. With routing enabled, each session gets its own text channel in a private server: rename a session "Library SSR" (`/rename`) and it answers in `#library-ssr`. No matching channel means the session answers in a fallback channel (default `#general`), where it offers to create the missing channel with one click.

Enable it by creating `~/.claude/channels/discord/channels.json`:

```json
{
  "guildId": "your-server-id",
  "fallback": "general",
  "dmMode": "off",
  "map": {}
}
```

Without this file, nothing changes — the plugin behaves exactly as before.

How a server instance finds its session: a `SessionStart` hook records the session id and transcript path keyed by the Claude process PID; the instance walks its parent-PID chain to that file and reads the session's title from the transcript. Bindings re-resolve every 30 seconds, so renames move the session to its new channel. Binding priority: `DISCORD_CHANNEL` env var, then session title, then a `map` entry for the project directory, then the project folder name, then `fallback`. Bindings are logged to `~/.claude/channels/discord/bind-log.txt`.

With routing active: messages in a session's channel need no @mention and reach only that session; DMs are not delivered as chat (`dmMode: "on"` restores them); permission prompts post in the session's channel with Allow/Deny/See more buttons instead of DMs.

| `channels.json` key | Meaning |
| --- | --- |
| `guildId` | The private server's id. Presence of the file enables routing. |
| `fallback` | Channel for sessions with no matching channel (default `general`). |
| `dmMode` | `off` (default): DMs are not delivered while routing. `on`: keep DM delivery. |
| `map` | Optional per-directory overrides: `{ "/path/to/project": "channel-name" }`. |

## Tools exposed to the assistant

| Tool | Purpose |
| --- | --- |
| `reply` | Send to a channel. Takes `chat_id` + `text`, optionally `reply_to` (message ID) for native threading and `files` (absolute paths) for attachments — max 10 files, 25MB each. Auto-chunks; files attach to the first chunk. Returns the sent message ID(s). |
| `react` | Add an emoji reaction to any message by ID. Unicode emoji work directly; custom emoji need `<:name:id>` form. |
| `edit_message` | Edit a message the bot previously sent. Useful for "working…" → result progress updates. Only works on the bot's own messages. |
| `fetch_messages` | Pull recent history from a channel (oldest-first). Capped at 100 per call. Each line includes the message ID so the model can `reply_to` it; messages with attachments are marked `+Natt`. Discord's search API isn't exposed to bots, so this is the only lookback. |
| `download_attachment` | Download all attachments from a specific message by ID to `~/.claude/channels/discord/inbox/`. Returns file paths + metadata. Use when `fetch_messages` shows a message has attachments. |
| `bind_channel` | Routing only. Bind the session to a guild text channel by name or id; `create: true` creates it first (needs the Manage Channels permission). |
| `ask_user` | Routing only. Ask multiple-choice questions with clickable UI: colored buttons for one simple question, a modal form with dropdowns and a free-text field for multi-question or multi-select. Answers come back as normal inbound messages. |

Inbound messages trigger a typing indicator automatically — Discord shows
"botname is typing…" while the assistant works on a response.

## Attachments

Attachments are **not** auto-downloaded. The `<channel>` notification lists
each attachment's name, type, and size — the assistant calls
`download_attachment(chat_id, message_id)` when it actually wants the file.
Downloads land in `~/.claude/channels/discord/inbox/`.

Same path for attachments on historical messages found via `fetch_messages`
(messages with attachments are marked `+Natt`).
