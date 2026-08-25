# Local patches

Personal fork of `anthropics/claude-plugins-official`, pruned to the telegram
plugin only. Everything that remains is upstream except the commits below.

| Commit subject | What it does |
| --- | --- |
| `marketplace: rename to centralhardware-plugins` | lets this fork be added alongside the upstream marketplace without an id collision |
| `telegram: surface quote-reply context in inbound channel meta` | adds `reply_to_message_id` / `reply_to_user` / `reply_to_text` to the `<channel>` tag so the model knows which message a quote-reply answers |
| `telegram: register extra bot-menu commands from local config` | feeds `{command, description}` entries from `$CLAUDE_CONFIG_DIR/telegram-commands.json` into `setMyCommands`, so hook-implemented commands (`/clr`, `/clr_status`, `/clear`) show up in the Telegram menu |
| `telegram: drop built-in start/help/status from the bot command menu` | the menu now lists only the local commands above; the upstream `/start`, `/help` and `/status` handlers still respond if typed |
| `telegram: keep "typing…" alive until the turn ends` | re-sends `sendChatAction` on an interval (upstream sends it once, so it expires after ~5s), stopping on `reply()`, a 10-minute cap, or the `$CLAUDE_CONFIG_DIR/telegram-turn-done` sentinel written by the local `/clr` and mail quick-action hooks |
| `telegram: fix poller lock, 409 bail-out and delivery; add topics + formats` | see below |
| `telegram: let a topic be marked send-only via ignore` | a topic listed in `telegram-topics.json` with `"ignore": true` (the day-review briefing topic) never starts a turn from inbound messages |
| `telegram: add rich messages to reply` | see below |
| `telegram: answer guest queries from allowlisted callers` | see below |
| `telegram: move per-topic instructions into the channel meta` | a topic's standing rules ride in a `topic_instructions` attribute instead of being prepended to the message body, so the model still gets them while the transcript shows only what the sender typed |
| `telegram: add /cancel to interrupt the running turn` | DM-only, allowlist-gated `/cancel` presses Escape in the session's tmux pane (`tmux send-keys -t $CLAUDE_TMUX_SESSION Escape`, default session `claude`) and stops the typing keep-alive. It lives in the server, not a UserPromptSubmit hook like `/clr`, because Claude Code queues prompts that arrive mid-turn — a relayed `/cancel` would only be read after the turn it was meant to stop had ended |
| `telegram: ignore the topic-creation message as a quote-reply` | in a forum topic every message's `reply_to_message` points at the topic-creation service message; that no longer emits `reply_to_*` meta, so only a real quote-reply to another message is surfaced |

## `telegram: fix poller lock, 409 bail-out and delivery; add topics + formats`

Fixes for upstream bugs that are still open there, plus forum-topic support.

**Poller lock** (upstream anthropics/claude-plugins-official#4505, #1481, #1691,
#1360). Upstream reads `bot.pid` at startup and SIGTERMs whatever pid it finds,
with no check that the pid is still a poller — so it can kill an unrelated
process after pid reuse, and any second Claude Code session (a cron run, a
terminal session) steals the channel from a healthy one. Now the holder
heartbeats `bot.pid` every 30s and a new instance only takes over when the
holder is gone, is not a `server.ts` process, or has stopped heartbeating for
90s; otherwise it stands by, retries every 30s, and serves outbound tools
without polling. Eviction escalates to `SIGKILL` after 3s for pollers wedged in
a long-poll.

**409 bail-out** (#4348, #1916, #4003). Upstream resets the retry counter inside
`onStart`, which grammY fires after `getMe` and *before* the first `getUpdates`
— so a 409 always arrived with the counter zeroed, the `attempt >= 8` bail-out
was unreachable and the backoff never grew (the retry spin behind the "100% CPU"
reports). The streak now resets on uptime (60s of actual polling) instead. On
bail the process exits (#4259, #2857): upstream just `return`s, leaving a
process that reports healthy while being deaf to every inbound message. The
operator gets a Telegram message in both cases, plus a warning at 5 consecutive
failures.

**Inbound delivery** (#4308, #960). The `mcp.notification` failure path only
wrote to stderr, so a message could be acked with the 👀 reaction and a typing
indicator and then vanish. It now tells the sender the session was unreachable
and the message needs re-sending.

**Formats** (#1032, #1269). `reply`/`edit_message` accept `format: html` and
`markdown` alongside `markdownv2`; any parse failure (400) is re-sent as plain
text instead of the message being lost to one unescaped character.

**Forum topics** (#4349, #1897, #1158). Inbound messages carry `thread_id` (and
`topic`) in the `<channel>` meta; `reply`, attachments and the typing indicator
go back to the originating topic instead of General, either from an explicit
`thread_id` argument or the last topic seen for that chat. Optional per-topic
context lives in `$CLAUDE_CONFIG_DIR/telegram-topics.json`:

```json
{
  "-1001234567890:12": { "name": "coffee",  "instructions": "Log every photo here with log-coffee." },
  "-1001234567890:34": { "name": "finance", "instructions": "Receipts here go to Firefly via log-transaction." },
  "-1001234567890:*":  { "instructions": "Fallback for the rest of the group." },
  "428985392":         { "instructions": "Fallback for a DM." }
}
```

`instructions` ride in the channel meta as `topic_instructions` for that turn
(they used to be prepended to the message body). The file is
re-read per message, so edits apply without restarting the plugin. Requires
`requireMention: false` for the group in `access.json` if the bot should answer
without being @-mentioned.

## Syncing with upstream

```sh
git fetch upstream
git rebase upstream/main      # or: git merge upstream/main
git push --force-with-lease origin main   # only needed after a rebase
claude plugin marketplace update centralhardware-plugins
claude plugin update telegram@centralhardware-plugins
```

Conflicts should be limited to `external_plugins/telegram/server.ts` and
`.claude-plugin/marketplace.json`. Because the prune commit deletes every other
plugin and the rest of the catalog, an upstream sync will also surface newly
added upstream plugins as additions — delete them again (`git rm`) and keep the
manifest's `plugins` array at the single telegram entry.

## `telegram: answer guest queries from allowlisted callers`

Bot API 10.0 (2026-05-08) added **guest mode**: with the switch enabled in
BotFather, a bot can be @mentioned in a chat it never joined, receives a
`guest_message` update, and may place exactly one message there via
`answerGuestQuery`. Upstream ignores the update entirely, so a summons is met
with silence. The plugin now handles it, gated on the existing DM allowlist —
the summoning user (`allowFrom`) must already be paired, otherwise the query is
dropped without a reply (a pairing code would land in a public chat and spend
the one answer). `dmPolicy: disabled` covers guest queries too.

The chat itself is never a send target: it isn't allowlisted, and Telegram
warns a guest chat's id may collide with an unrelated chat the bot does know. A
guest turn is addressed by a synthetic `guest:<query id>` (TTL 1h, capped at 50
live queries), carried in the meta alongside `guest="true"`, `guest_chat_id` and
`guest_chat_title`. `assertAllowedChat` admits that prefix only while the query
is live.

`reply` routes on it: the answer goes out as an `InlineQueryResult` article
whose `input_message_content` is either `message_text` (with the usual
plain-text fallback on a markup rejection) or, for `rich`, a `rich_message`
block document — both shapes verified against the live API. Since Telegram
allows one message per query, a second `reply` edits the first via
`editMessageTextInline` rather than failing, and `edit_message` does the same
(its `message_id` is moot — the answer is an inline message). `react` and
`files` are refused, and neither the ack reaction nor the typing indicator is
attempted: the bot is not a member of that chat. If the inbound notification
can't reach the session, the answer is spent telling the caller so — there is no
other way to speak in that chat.

Requires grammY ≥ 1.45 for the `guest_message` filter query and
`answerGuestQuery` (the dependency floor moved from `^1.21.0`); startup logs a
line when `getMe` reports the bot has guest mode switched off.

## `telegram: add rich messages to reply`

`reply` gained a `rich` parameter: an array of Bot API 10.1 rich blocks, sent via
`sendRichMessage` (grammY has no binding, so it goes over plain `fetch`).

**In practice it renders mangled through this path** — collapsed tables, `_b_`
artifacts, empty list items — so the tool instructions now point interactive
replies at `format: "html"` with `<blockquote expandable>` for folding, and leave
`rich` to the headless senders that call the Bot API directly (`tg_send.py
--rich`). The parameter stays because those senders share this code path for
guest answers and edits.

`text` is now optional (`required: ['chat_id']`): with `rich` it is used only as
the plain-text fallback. If Telegram rejects the payload, the blocks are flattened
(`blocksToPlain`) and sent as text, mirroring the existing markup fallback — a
schema slip costs formatting, not the message.

The accepted block set is narrower than the public docs suggest (probed against the
live API): `paragraph`, `heading` (numeric `size`), `list` (items are `{blocks:[…]}`,
no `type`), `details`, `blockquote`, `table` (`cells`, not `rows`), `pre`, `divider`,
`footer`. `section_heading`, `block_quotation`, `preformatted` and `thinking` are
receive-side names only and are rejected on send.
