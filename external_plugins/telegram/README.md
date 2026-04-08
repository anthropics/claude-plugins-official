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
/reload-plugins
```

**3. Give the server the token.**

```
/telegram:configure 123456789:AAHfiqksKZ8...
```

Writes `TELEGRAM_BOT_TOKEN=...` to `~/.claude/channels/telegram/.env`. You can also write that file by hand, or set the variable in your shell environment — shell takes precedence.

> To run multiple bots on one machine (different tokens, separate allowlists), point `TELEGRAM_STATE_DIR` at a different directory per instance.

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

## Tools exposed to the assistant

| Tool | Purpose |
| --- | --- |
| `reply` | Send to a chat. Takes `chat_id` + `text`, optionally `reply_to` (message ID) for native threading and `files` (absolute paths) for attachments. Images (`.jpg`/`.png`/`.gif`/`.webp`) send as photos with inline preview; other types send as documents. Max 50MB each. Auto-chunks text; files send as separate messages after the text. Returns the sent message ID(s). |
| `react` | Add an emoji reaction to a message by ID. **Only Telegram's fixed whitelist** is accepted (👍 👎 ❤ 🔥 👀 etc). |
| `edit_message` | Edit a message the bot previously sent. Useful for "working…" → result progress updates. Only works on the bot's own messages. |

Inbound messages trigger a typing indicator automatically — Telegram shows
"botname is typing…" while the assistant works on a response.

## Photos

Inbound photos are downloaded to `~/.claude/channels/telegram/inbox/` and the
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

## Group chat setup

The Quick Setup above covers DMs. Groups require extra steps — **order matters**.

**1. Disable privacy mode (once per bot).**

Message [@BotFather](https://t.me/BotFather):

```
/setprivacy
```

Select your bot, then choose **Disable**. This lets the bot see all group messages, not just commands and @mentions. You only need to do this once, but verify it's off before proceeding.

**2. Add the bot to the group and promote to admin.**

Add your bot to the target group, then promote it to admin. Admin status is required for the bot to reliably receive and send messages in groups.

> **Critical:** If the bot was added to the group _before_ privacy mode was disabled, remove the bot from the group and re-add it. Privacy mode changes only take effect for groups joined _after_ the change.

**3. Trigger chat ID registration.**

After adding the bot, someone must send a message in the group. The bot registers the `chat_id` on the first message it sees — until then, it doesn't know the group exists.

**4. Enable the group in access config.**

```
/telegram:access group add <chat_id>
```

See [ACCESS.md](./ACCESS.md) for `--no-mention`, `--allow`, and other group flags.

## Troubleshooting

**"Channels are not currently available"**

This is a known Claude Code bug. Workaround: launch with the development channels flag and add a `.mcp.json` entry:

```sh
claude --dangerously-load-development-channels server:telegram
```

Ensure your `.mcp.json` includes the telegram server configuration. See [#36503](https://github.com/anthropics/claude-code/issues/36503) for details.

**409 Conflict errors**

Only one process can poll a bot token at a time. If you see `409 Conflict`, another process is already polling with the same token. Kill old Claude Code sessions or other scripts using the token:

```sh
ps aux | grep telegram
```

**Bot shows "typing" but never replies**

The channel notification was sent to Claude Code, but the model didn't route it to the reply tool. This can happen when the assistant is busy with another task or the channel message was deprioritized. Try sending the message again, or check that `--channels` is active in your session.

**Bot doesn't see group messages**

Privacy mode is still enabled, or the bot was added before privacy mode was disabled. Fix:

1. Verify privacy is off: [@BotFather](https://t.me/BotFather) → `/setprivacy` → select bot → should show "Privacy mode is disabled".
2. Remove the bot from the group.
3. Re-add the bot to the group.
4. Promote to admin.

## Known issues

- [#36503](https://github.com/anthropics/claude-code/issues/36503) — "Channels are not currently available" error
- [#36477](https://github.com/anthropics/claude-code/issues/36477) — Channel plugin setup issues
- [#38259](https://github.com/anthropics/claude-code/issues/38259) — Telegram channel reliability
- [#38098](https://github.com/anthropics/claude-code/issues/38098) — Bot polling conflicts
