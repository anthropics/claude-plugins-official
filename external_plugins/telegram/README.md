# Telegram

Connect a Telegram bot to your Claude Code with an MCP server.

The MCP server logs into Telegram as a bot and provides tools to Claude to reply, react, or edit messages. When you message the bot, the server forwards the message to your Claude Code session.

## Prerequisites

- [Bun](https://bun.sh) — the MCP server runs on Bun. Install with `curl -fsSL https://bun.sh/install | bash`.

## Quick Setup
> Default pairing flow for a single-user DM bot. See [ACCESS.md](./ACCESS.md) for groups and multi-user setups.

**1. Create a bot with BotFather.**

Open a chat with [@BotFather](https://t.me/BotFather) on Telegram and send `/newbot`. BotFather asks for two things:

- **Name** — the display name shown in chat headers (anything, can contain spaces)
- **Username** — a unique handle ending in `bot` (e.g. `my_assistant_bot`). This becomes your bot's link: `t.me/my_assistant_bot`.

BotFather replies with a token that looks like `123456789:AAHfiqksKZ8...` — that's the whole token, copy it including the leading number and colon.

**2. Install the plugin.**

These are Claude Code commands — run `claude` to start a session first.

Install the plugin:
```
/plugin install telegram@claude-plugins-official
```

**3. Give the server the token.**

```
/telegram:configure 123456789:AAHfiqksKZ8...
```

Writes `TELEGRAM_BOT_TOKEN=...` to `~/.claude/channels/telegram/.env`. You can also write that file by hand, or set the variable in your shell environment — shell takes precedence. For per-project bots, see the [Per-project bots](#per-project-bots) section below.

**4. Relaunch with the channel flag.**

The server won't connect without this — exit your session and start a new one:

```sh
claude --channels plugin:telegram@claude-plugins-official
```

**5. Pair.**

With Claude Code running from the previous step, DM your bot on Telegram — it replies with a 6-character pairing code. If the bot doesn't respond, make sure your session is running with `--channels`. In your Claude Code session:

```
/telegram:access pair <code>
```

Your next DM reaches the assistant.

> Unlike Discord, there's no server invite step — Telegram bots accept DMs immediately. Pairing handles the user-ID lookup so you never touch numeric IDs.

**6. Lock it down.**

Pairing is for capturing IDs. Once you're in, switch to `allowlist` so strangers don't get pairing-code replies. Ask Claude to do it, or `/telegram:access policy allowlist` directly.

## Access control

See **[ACCESS.md](./ACCESS.md)** for DM policies, groups, mention detection, delivery config, skill commands, and the `access.json` schema.

Quick reference: IDs are **numeric user IDs** (get yours from [@userinfobot](https://t.me/userinfobot)). Default policy is `pairing`. `ackReaction` only accepts Telegram's fixed emoji whitelist.

## Per-project bots

By default, all Claude Code sessions share one bot token and one access config (the "global" setup described above). Per-project mode gives each project its own Telegram bot, access policy, and message inbox — so messages to `@alpha_dev_bot` only arrive in the Alpha project session, never in Beta's.

### How it works

The MCP server reads the `TELEGRAM_PROJECT_ID` environment variable at startup. When set, it resolves all state to a project-scoped subdirectory instead of the global one:

| | Global (default) | Per-project |
| --- | --- | --- |
| State dir | `~/.claude/channels/telegram/` | `~/.claude/channels/telegram/projects/<id>/` |
| Bot token | Shared across all sessions | One token per project |
| Access policy | Shared `access.json` | Independent per-project `access.json` |
| Inbox | Shared | Separate per project |

Each project-scoped state directory contains the same files as the global one:

```
~/.claude/channels/telegram/projects/<id>/
├── .env              # TELEGRAM_BOT_TOKEN for this project's bot
├── access.json       # per-project access policy
├── inbox/            # downloaded photos
└── approved/         # pairing approval signals
```

### Setting `TELEGRAM_PROJECT_ID`

The project ID is passed to the MCP server via the `env` block in `.claude/settings.local.json` in your project root. The `/telegram:configure --project` command writes this automatically, but the resulting structure is:

```json
{
  "env": {
    "TELEGRAM_PROJECT_ID": "myproject"
  }
}
```

Claude Code's `env` is a flat `Record<string, string>` — all values must be strings, no nesting. These environment variables are passed to all MCP server processes at startup.

**Important:** The `env` block does **not** support nested structures like `env.mcpServers.telegram`. The project ID must be a direct key in the `env` object.

### Project ID rules

- Allowed characters: letters, digits, hyphens, underscores (`[a-zA-Z0-9_-]`)
- Maximum length: 64 characters
- Used as a directory name — path separators (`/`, `\`, `..`) are rejected
- Validated both by the configure skill and by `server.ts` at startup (fail-fast on invalid IDs)

### Setup walkthrough

**1. Create a bot per project** with [@BotFather](https://t.me/BotFather). Give each a descriptive username (e.g. `@myproject_dev_bot`). Note the exact username BotFather gives you — it may differ from what you requested.

**2. Configure each project.** In the project's Claude Code session:

```
/telegram:configure --project myproject 123456789:AAH...
```

This does four things:
1. Creates `~/.claude/channels/telegram/projects/myproject/`
2. Saves the bot token to `projects/myproject/.env` (mode `0600`)
3. Writes `TELEGRAM_PROJECT_ID=myproject` to the project's `.claude/settings.local.json`
4. Copies `allowFrom` from the global `access.json` as the initial per-project access list (if the global config exists)

**3. Restart** the Claude Code session. The MCP server reads `TELEGRAM_PROJECT_ID` from the environment at startup — it does not hot-reload. You can verify the server connected to the right bot by checking for `telegram channel: polling as @myproject_dev_bot` in the startup output.

**4. Pair** by DMing the project's bot. If your user ID was already in the global allowlist, it carries over automatically and you can skip pairing. Otherwise, the bot replies with a pairing code — approve with `/telegram:access pair <code>` as usual.

**5. Run multiple sessions** — each project directory launches its own bot:

```sh
# Terminal 1: Alpha project connects to @alpha_dev_bot
cd ~/projects/alpha && claude --channels plugin:telegram@claude-plugins-official

# Terminal 2: Beta project connects to @beta_dev_bot
cd ~/projects/beta && claude --channels plugin:telegram@claude-plugins-official

# Terminal 3: No project ID — connects to the global bot
cd ~/projects/other && claude --channels plugin:telegram@claude-plugins-official
```

DM `@alpha_dev_bot` to reach Terminal 1, `@beta_dev_bot` to reach Terminal 2. Messages never cross between sessions.

### Access inheritance

When a per-project `access.json` is created for the first time (either by the configure skill or by the server's startup bootstrap), it inherits the `allowFrom` list from the global `~/.claude/channels/telegram/access.json`. After creation, the per-project config is fully independent — changes to the global config do not propagate, and vice versa.

### Verifying your setup

Check which mode a project is using:

```
/telegram:configure
```

This shows the active mode (global or per-project), the resolved state directory, token status, and access summary.

To inspect the state directly:

```bash
# Check the project's settings
cat ~/projects/myproject/.claude/settings.local.json | grep TELEGRAM_PROJECT_ID

# Check the per-project state directory
ls ~/.claude/channels/telegram/projects/myproject/
cat ~/.claude/channels/telegram/projects/myproject/access.json
```

### Removing per-project configuration

```
/telegram:configure clear
```

In per-project mode, this removes the token from the per-project `.env` and removes `TELEGRAM_PROJECT_ID` from `.claude/settings.local.json`. After restarting, the session falls back to the global bot.

See [ACCESS.md](./ACCESS.md) for the full per-project access control reference.

## Tools exposed to the assistant

| Tool | Purpose |
| --- | --- |
| `reply` | Send to a chat. Takes `chat_id` + `text`, optionally `reply_to` (message ID) for native threading and `files` (absolute paths) for attachments. Images (`.jpg`/`.png`/`.gif`/`.webp`) send as photos with inline preview; other types send as documents. Max 50MB each. Auto-chunks text; files send as separate messages after the text. Returns the sent message ID(s). |
| `react` | Add an emoji reaction to a message by ID. **Only Telegram's fixed whitelist** is accepted (👍 👎 ❤ 🔥 👀 etc). |
| `edit_message` | Edit a message the bot previously sent. Useful for "working…" → result progress updates. Only works on the bot's own messages. |

Inbound messages trigger a typing indicator automatically — Telegram shows
"botname is typing…" while the assistant works on a response.

## Photos

Inbound photos are downloaded to `~/.claude/channels/telegram/inbox/` (or the project-scoped inbox in per-project mode) and the
local path is included in the `<channel>` notification so the assistant can
`Read` it. Telegram compresses photos — if you need the original file, send it
as a document instead (long-press → Send as File).

## No history or search

Telegram's Bot API exposes **neither** message history nor search. The bot
only sees messages as they arrive — no `fetch_messages` tool exists. If the
assistant needs earlier context, it will ask you to paste or summarize.

This also means there's no `download_attachment` tool for historical messages
— photos are downloaded eagerly on arrival since there's no way to fetch them
later.
