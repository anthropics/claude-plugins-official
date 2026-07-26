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

`instructions` are prepended to the message body for that turn. The file is
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
