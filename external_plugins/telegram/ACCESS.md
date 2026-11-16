# Telegram — Access & Delivery

A Telegram bot is publicly addressable. Anyone who finds its username can DM it, and without a gate those messages would flow straight into your assistant session. The access model described here decides who gets through.

By default, a DM from an unknown sender triggers **pairing**: the bot replies with a 6-character code and drops the message. You run `/telegram:access pair <code>` from your assistant session to approve them. Once approved, their messages pass through.

Access configuration lives in `~/.claude/channels/telegram/access.json`. The `/telegram:access` skill commands edit this file; the server re-reads it on every inbound message, so changes take effect without a restart. Set `TELEGRAM_ACCESS_MODE=static` to pin config to what was on disk at boot (pairing is unavailable in static mode since it requires runtime writes; the inbound journal below is written either way).

Alongside it the server keeps `inbound.jsonl`, a journal of received messages — see **What is kept on disk** — plus `server.log`, `bot.pid`, `inbox/` and `.env`.

## At a glance

| | |
| --- | --- |
| Default policy | `pairing` |
| Sender ID | Numeric user ID (e.g. `412587349`) |
| Group key | Supergroup ID (negative, `-100…` prefix) |
| `ackReaction` quirk | Fixed whitelist only; non-whitelisted emoji silently do nothing |
| Config file | `~/.claude/channels/telegram/access.json` |
| Message journal | `~/.claude/channels/telegram/inbound.jsonl`, last 500 or 7 days |
| Server log | `~/.claude/channels/telegram/server.log`, newest 256 KB |

## DM policies

`dmPolicy` controls how DMs from senders not on the allowlist are handled.

| Policy | Behavior |
| --- | --- |
| `pairing` (default) | Reply with a pairing code, drop the message. Approve with `/telegram:access pair <code>`. |
| `allowlist` | Drop silently. No reply. Useful if the bot's username is guessable and pairing replies would attract spam. |
| `disabled` | Drop everything, including allowlisted users and groups. |

```
/telegram:access policy allowlist
```

## User IDs

Telegram identifies users by **numeric IDs** like `412587349`. Usernames are optional and mutable; numeric IDs are permanent. The allowlist stores numeric IDs.

Pairing captures the ID automatically. To find one manually, have the person message [@userinfobot](https://t.me/userinfobot), which replies with their ID. Forwarding any of their messages to @userinfobot also works.

```
/telegram:access allow 412587349
/telegram:access remove 412587349
```

## Groups

Groups are off by default. Opt each one in individually.

```
/telegram:access group add -1001654782309
```

Supergroup IDs are negative numbers with a `-100` prefix, e.g. `-1001654782309`. They're not shown in the Telegram UI. To find one, either add [@RawDataBot](https://t.me/RawDataBot) to the group temporarily (it dumps a JSON blob including the chat ID), or add your bot and run `/telegram:access` to see recent dropped-from groups.

With the default `requireMention: true`, the bot responds only when @mentioned or replied to. Pass `--no-mention` to process every message, or `--allow id1,id2` to restrict which members can trigger it.

```
/telegram:access group add -1001654782309 --no-mention
/telegram:access group add -1001654782309 --allow 412587349,628194073
/telegram:access group rm -1001654782309
```

**Privacy mode.** Telegram bots default to a server-side privacy mode that filters group messages before they reach your code. [Telegram's list](https://core.telegram.org/bots/features#privacy-mode) of what still gets through is: commands aimed at the bot (`/command@your_bot`), general commands if your bot sent the last message, inline messages sent via the bot, and **replies to the bot's own messages** — plus service messages, and everything in private chats.

**@mentions are not on that list.** So with privacy mode on, replying to one of the bot's messages is the trigger to rely on; a plain `@your_bot hello` may never reach the plugin at all, and `requireMention: true` is the default. If a group looks silent, that is the first thing to check — run with `TELEGRAM_DEBUG=1` (see **When nothing arrives**) to tell "Telegram never delivered it" from "the gate dropped it".

Using `--no-mention`, or relying on @mentions, requires disabling privacy mode: message [@BotFather](https://t.me/BotFather), send `/setprivacy`, pick your bot, choose **Disable**. **The bot must then be removed from the group and re-added** for the change to take effect — Telegram applies it at join time.

## Mention detection

In groups with `requireMention: true`, any of the following triggers the bot:

- **A reply to one of the bot's messages** — the only one Telegram guarantees while privacy mode is on, so prefer it
- A structured `@botusername` mention — needs privacy mode disabled to be reliable
- A match against any regex in `mentionPatterns` — the message has to reach the plugin first, so the same caveat applies

```
/telegram:access set mentionPatterns '["^hey claude\\b", "\\bassistant\\b"]'
```

## Delivery

Configure outbound behavior with `/telegram:access set <key> <value>`.

**`ackReaction`** reacts to inbound messages on receipt. Telegram accepts only a **fixed whitelist** of reaction emoji; anything else is silently ignored. The full Bot API list:

> 👍 👎 ❤ 🔥 🥰 👏 😁 🤔 🤯 😱 🤬 😢 🎉 🤩 🤮 💩 🙏 👌 🕊 🤡 🥱 🥴 😍 🐳 ❤‍🔥 🌚 🌭 💯 🤣 ⚡ 🍌 🏆 💔 🤨 😐 🍓 🍾 💋 🖕 😈 😴 😭 🤓 👻 👨‍💻 👀 🎃 🙈 😇 😨 🤝 ✍ 🤗 🫡 🎅 🎄 ☃ 💅 🤪 🗿 🆒 💘 🙉 🦄 😘 💊 🙊 😎 👾 🤷‍♂ 🤷 🤷‍♀ 😡

```
/telegram:access set ackReaction 👀
/telegram:access set ackReaction ""
```

**`replyToMode`** controls threading on chunked replies. When a long response is split, `first` (default) threads only the first chunk under the inbound message; `all` threads every chunk; `off` sends all chunks standalone.

**`textChunkLimit`** sets the split threshold. Telegram rejects messages over 4096 characters.

**`chunkMode`** chooses the split strategy: `length` cuts exactly at the limit; `newline` prefers paragraph boundaries.

## When nothing arrives

A message the gate turns away is dropped in silence, which looks the same as a bot that is broken.

**The plugin keeps a log at `<state-dir>/server.log`.** Start there. It holds what the server reports — poller handovers, delivery failures, Telegram API errors — oldest entries trimmed once it passes 256 KB. The log is a file because Claude Code stops reading a plugin's stderr once the MCP connection is up, so nothing printed after startup reaches the MCP logs; only startup lines land there.

Set `TELEGRAM_DEBUG=1` in `<state-dir>/.env` and restart the session to add a line for each message the gate drops, with the chat, the sender and the reason — a group that was never enabled, a sender not on the allowlist, a missing mention. Message text is never logged, only ids and the reason.

Resolve `<state-dir>` first; it is not always `~/.claude/channels/telegram`:

```bash
echo "${TELEGRAM_STATE_DIR:-${CLAUDE_CONFIG_DIR:-$HOME/.claude}/channels/telegram}"
```

Two things the log will not show:

- **Bot commands.** `/start`, `/help` and `/status` are answered only in private chats and are discarded in groups before the gate runs, so they produce no line.
- **Messages Telegram never delivered.** If a group message leaves no trace even with the flag on, Telegram filtered it server-side — see **Privacy mode** above, which is the usual reason.

When several sessions have the plugin loaded they share this file, and only the one holding the polling slot writes the inbound lines. That is the log to read, whichever session you are in.

## What is kept on disk

Handing a message to the session can fail without the plugin being told — a session running without `--channels` accepts the push and drops it. So every inbound message is written to `inbound.jsonl` *before* delivery is attempted, and the `recent_inbound` tool reads it back. Without it, a message lost that way leaves no trace anywhere.

What that means for you:

- **Message text is on disk**, including group messages and forwarded third-party content, in a file mode `600` inside a directory mode `700`. The plugin never sends it to Telegram: `reply` refuses any file inside the state directory.
- **It is capped** at the most recent 500 entries or 7 days, whichever comes first. Entries past the cap are never replayed, even before the file is next rewritten.
- **It is shared between sessions.** Every Claude Code session on the machine reads the same file, which is what makes recovery work — the session that lost the message is usually not the one you ask about it. A session in an unrelated project can therefore replay messages that arrived for another.
- Inbound photos are already stored in `inbox/`; this adds the text beside them.

Delete `inbound.jsonl` at any time; it is recreated on the next message.

## Several sessions, one bot token

Telegram allows exactly one long-polling consumer per bot token, so when more than one Claude Code session has the plugin loaded, only one of them polls. The others serve the tools (`reply`, `react`, `edit_message`, `recent_inbound`) normally and wait; whichever is polling records itself in `bot.pid`.

A session that starts while another is already polling waits **`pollerTakeoverSeconds`** (default 120) and then takes the slot, so the session you just started does end up receiving your messages. The session that had it notices on its next check and steps down to serving tools only — nothing signals it and it keeps running. The wait is what keeps short-lived instances, such as the throwaway servers `claude mcp list` spawns to health-check, from disturbing a working session at all.

```
/telegram:access set pollerTakeoverSeconds 0
```

Set it to `0` to pin the slot to the first session that claims it; no later session will take it while that one is alive. A poller that stops responding (crashed session, hung process) is replaced either way, within about half a minute — that one is terminated, since it cannot step down on its own.

While another session holds the slot, permission prompts from this session are not sent to Telegram: the tap would come back to whichever session is polling. Answer those in the terminal.

## Skill reference

| Command | Effect |
| --- | --- |
| `/telegram:access` | Print current state: policy, allowlist, pending pairings, enabled groups. |
| `/telegram:access pair a4f91c` | Approve pairing code `a4f91c`. Adds the sender to `allowFrom` and sends a confirmation on Telegram. |
| `/telegram:access deny a4f91c` | Discard a pending code. The sender is not notified. |
| `/telegram:access allow 412587349` | Add a user ID directly. |
| `/telegram:access remove 412587349` | Remove from the allowlist. |
| `/telegram:access policy allowlist` | Set `dmPolicy`. Values: `pairing`, `allowlist`, `disabled`. |
| `/telegram:access group add -1001654782309` | Enable a group. Flags: `--no-mention` (also requires disabling privacy mode), `--allow id1,id2`. |
| `/telegram:access group rm -1001654782309` | Disable a group. |
| `/telegram:access set ackReaction 👀` | Set a config key: `ackReaction`, `replyToMode`, `textChunkLimit`, `chunkMode`, `mentionPatterns`, `pollerTakeoverSeconds`. |

## Config file

`~/.claude/channels/telegram/access.json`. Absent file is equivalent to `pairing` policy with empty lists, so the first DM triggers pairing.

```jsonc
{
  // Handling for DMs from senders not in allowFrom.
  "dmPolicy": "pairing",

  // Numeric user IDs allowed to DM.
  "allowFrom": ["412587349"],

  // Groups the bot is active in. Empty object = DM-only.
  "groups": {
    "-1001654782309": {
      // true: respond only to @mentions and replies.
      // false also requires disabling privacy mode via BotFather.
      "requireMention": true,
      // Restrict triggers to these senders. Empty = any member (subject to requireMention).
      "allowFrom": []
    }
  },

  // Case-insensitive regexes that count as a mention.
  "mentionPatterns": ["^hey claude\\b"],

  // Emoji from Telegram's fixed whitelist. Empty string disables.
  "ackReaction": "👀",

  // Threading on chunked replies: first | all | off
  "replyToMode": "first",

  // Split threshold. Telegram rejects > 4096.
  "textChunkLimit": 4096,

  // length = cut at limit. newline = prefer paragraph boundaries.
  "chunkMode": "newline",

  // Seconds a new session waits before taking the polling slot from a
  // session that already has it. 0 = never take it.
  "pollerTakeoverSeconds": 120
}
```
