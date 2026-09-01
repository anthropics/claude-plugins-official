# Telegram

Connect a Telegram bot to your Claude Code with an MCP server.

The MCP server logs into Telegram as a bot and provides tools to Claude to reply, react, or edit messages. When you message the bot, the server forwards the message to your Claude Code session.

Replies are formatted as Bot API 10.1 **rich messages** — ordinary Markdown, no escaping, 32768 chars per message — and long answers can **stream** into the chat as they're written. See [Formatting](#formatting) and [Streaming drafts](#streaming-drafts).

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
| `reply` | Send to a chat. Takes `chat_id` + `text`, optionally `format`, `buttons` (see [Buttons](#buttons)), `reply_to` (message ID) for native threading and `files` (absolute paths) for attachments. Images (`.jpg`/`.png`/`.gif`/`.webp`) send as photos with inline preview; other types send as documents. Max 50MB each. Auto-chunks text; files send as separate messages after the text. Returns the sent message ID(s). |
| `draft` | Stream a partial answer while the assistant is still working. Private chats only. See [Streaming drafts](#streaming-drafts). |
| `react` | Add an emoji reaction to a message by ID. **Only Telegram's fixed whitelist** is accepted (👍 👎 ❤ 🔥 👀 etc). |
| `edit_message` | Edit a message the bot previously sent. Only works on the bot's own messages. |

Inbound messages trigger a typing indicator automatically — Telegram shows
"botname is typing…" while the assistant works on a response.

## Formatting

`reply`, `edit_message` and `draft` take a `format` argument:

| `format` | Cap | Escaping | Notes |
| --- | --- | --- | --- |
| `rich` *(default)* | 32768 | none | Bot API 10.1 rich message |
| `markdownv2` | 4096 | every special char | legacy `parse_mode` |
| `text` | 4096 | n/a | sent verbatim |

`rich` accepts ordinary Markdown and needs no escaping at all — that matters
because an assistant writes Markdown natively, and MarkdownV2's rule that every
`.`, `-`, `(` and `!` must be backslash-escaped is the main source of mangled
replies. Supported: `#`–`######` headings, `-`/`1.` lists, `- [ ]` task lists,
tables, ```` ``` ```` fenced code with syntax highlighting, `>` block quotes
(including collapsible ones), `---` rules, `**bold**`, `*italic*`,
`~~strikethrough~~`, `` `code` ``, `==marked==`, `||spoiler||`, footnotes and
`$LaTeX$` formulas.

Long, skimmable-past content goes in a collapsible block — Markdown is still
parsed inside it, and on a phone a 300-line log costs one line instead of a
screenful of scrolling:

```markdown
<details><summary>Build log (142 lines)</summary>

```text
…
```

</details>
```

The 32768-char cap means most answers arrive as a single message instead of
three or four fragments. Longer ones are split on paragraph boundaries; a code
block that has to be cut is closed and reopened — language tag included — so
neither half renders as loose backticks.

If Telegram rejects the Markdown (HTTP 400), the message is resent as plain
text rather than dropped, and the tool result says so.

## Buttons

`reply` takes a `buttons` array (max 12) rendered as a tappable keyboard under
the message — the main way to save typing on a phone:

```jsonc
"buttons": [
  { "text": "Continue" },                              // action button
  { "text": "Show diff", "action": "show me the diff" },// custom text sent back
  { "text": "Copy", "copy": "npm run build" },          // copies to clipboard
  { "text": "Docs", "url": "https://core.telegram.org" }
]
```

Tapping an action button delivers its `action` (defaulting to the label) as a
new inbound message, so the assistant just continues the conversation. The
keyboard is removed on the first tap: tokens are single-use and bound to the
chat they were issued for, so a press can't be replayed or fired from
elsewhere. Only allowlisted senders are accepted, same as chat.

Labels of 16 characters or less pair up two per row; longer ones take a row of
their own.

## Topics

Telegram can run a private chat as a forum, which turns one endless stream into
separate threads — a large readability win on a phone.

Two things happen automatically:

- **Replies go back to the thread the message came from.** This needs no setup
  beyond creating topics yourself in the Telegram UI.
- **Each project gets its own topic**, named after the session's working
  directory (`CLAUDE_PROJECT_DIR`). Created on first use and remembered in
  `~/.claude/channels/telegram/topics.json`, so a restart reuses it rather than
  piling up duplicates.

Per-project topics need topic mode enabled for the bot — message
[@BotFather](https://t.me/BotFather), pick your bot, and turn on topics in
private chats. Without it `getMe` reports no topic support and the feature is a
no-op; nothing is created and nothing fails. Set `"projectTopics": false` in
`access.json` to keep threading-by-inbound but stop creating project topics.

> One bot token still allows only one polling session at a time, so topics
> organize history per project — they don't let two sessions run at once.

## Streaming drafts

`draft` calls `sendRichMessageDraft`, so a long answer appears progressively
instead of arriving after a silence:

- Called with no `text` (or `thinking: true`) it shows an animated
  **"Thinking…"** placeholder — use it the moment a long task starts.
- Called again with partial text, Telegram **animates the delta**. Successive
  calls to the same chat reuse one draft id automatically.
- `can_stop` (default `true`) puts a **stop** button under the draft. Pressing
  it arrives as a normal inbound message, so the assistant can cut the answer
  short — it does not abort the underlying turn.

> Drafts are ephemeral previews. They disappear after ~30 seconds and are never
> saved to the chat, so the assistant must still send the finished answer with
> `reply` — which also clears the draft.

This is not token-by-token streaming: an MCP tool is called once with text that
already exists, so the granularity is however often the assistant chooses to
call `draft`. What it buys is a live placeholder and progress instead of a dead
chat window during a long task.

Set `"streaming": false` in `access.json` to disable the tool.

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
