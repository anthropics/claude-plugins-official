# Slack plugin — open decisions

Judgement calls made while VoX is away. Review and override at will.

## Manifest scope choices

- Chose `chat:write.public` so the bot can post to channels it isn't a member of (matches discord's "any allowlisted channel" feel). Drop if you'd rather force `/invite` everywhere.
- Included `users:read.email` for `get_user_info` parity. Sensitive — drop if you don't want claude to see workspace emails.
- `commands` scope added in 0.1.16 to ship `/status`. Other slash-command parity with discord (`/dunk`, `/dedunk`) still pending.
- `/status` command name is configurable via `SLACK_STATUS_COMMAND` (0.1.17) so multiple bots can share a workspace without colliding and operators can sidestep slack's built-in `/status` (which sets a user-presence message and shadows ours). Default is `/status` for fresh installs. When overridden, the slack app manifest's `slash_commands` block must be updated to match + the app reinstalled.

## Token storage

- `server.ts` reads `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` from process env first (so a systemd `EnvironmentFile=…/.bot.env` works), falling back to `$STATE_DIR/.env` (where `/slack:configure` writes them). State-dir `.env` is chmod 0600 + parsed with quote-stripping so `KEY="value"` lines work correctly.

## API/SDK choices

- `@slack/bolt` v4 with Socket Mode. Bolt's `client.files.uploadV2` wraps the 3-step `getUploadURLExternal` → POST → `completeUploadExternal` flow. Removes ~50 LOC of plumbing.
- `@slack/web-api` is a transitive dep of bolt — listed explicitly in package.json for IDE clarity but not directly imported.

## Pairing flow

- Same shape as discord: `pairing` default; first DM from unknown sender → 8-hex code; VoX runs `/slack:access pair <code>` to approve. Slack workspaces are smaller blast-radius than discord (no random internet DMs), so pairing is mostly cargo-culted from discord. Can default to `allowlist` if the bot is only used in one workspace and you'd rather skip the pairing dance.

## Scope omissions vs discord plugin

- **No `send_embed`/`edit_embed`** — VoX directive: skip embed parity for now. Slack has no native color-bar; legacy `attachments` field still works but is "not actively developed".
- **No `typing` tool** — VoX directive: omit. Slack bots can't send typing indicators (Slack-side limitation, not API design choice). Existing skills that rely on typing-then-reply will need a slack-aware fork or graceful fallback.
- **No `claude/channel/permission` relay** — discord plugin sends button-driven permission prompts to allowlisted DMs. Skipped for v0.1; can port from discord if needed.
- **Partial slash commands** — `/status` shipped in 0.1.16 (Haiku-summary equivalent of discord's). `/dunk`, `/dedunk` still pending.

## Channel notification format

Inbound `<channel>` tag includes `source="slack"`, `team_id`, `chat_id`, `message_id` (slack `ts`), `user`, `user_id`, `ts` (ISO8601), `channel_type` (channel|group|im|mpim), and `thread_ts` when in a thread. `message_id` is the slack `ts` — same string used in `chat.update`, `reactions.add`, etc.

## Reaction shortcode enforcement

- `react` tool rejects unicode emoji with a clear error message (slack's API would 400 anyway, but the error is opaque). Forces shortcode form.

## Image downscaling

- Same Anthropic-vision-friendly downscale (1600px long edge, 5MB cap, animated images skip) as discord plugin. `sharp` dep carried over.

## File upload limits

- Capped at 50MB per file (slack's tier-1 limit is much higher, but this matches discord's spirit of "don't fill the inbox"). Adjust upward if you need bigger uploads.

## Deferred from the 4-agent review rounds

Substantive findings that fix would have meaningfully changed scope or
required bigger refactors. Documented here so they're not lost:

- **Extract a shared `channel-core` module across discord + slack** —
  `withAccessLock`, `pruneExpired`, `recentSentTs`/`noteSent`,
  `BOOT_ACCESS`, `readAccessFile`, atomic JSON write, dunk subsystem,
  username cache LRU — all are line-for-line clones between the two
  plugins. Significant refactor, deferred until a third channel-bridge
  plugin (telegram?) makes the duplication a real cost.
- **Move from FIFO eviction to a real LRU** in usernameCache — current
  drop-the-first-key-on-overflow lies about being LRU (it's FIFO). Names
  read frequently still get evicted on insertion order.
- **Cache `loadAccess` in-memory + watch mtime** — `access.json` is
  parsed from disk on every gate(), assertChannelAllowed(), and
  chunkOutbound(). For high-volume channels this is a measurable cost.
  Holding for now since it changes the locking model.
- **Cache DM-channel→user-id mapping** so `assertChannelAllowed` for
  DMs doesn't hit `conversations.info` on every send. Discord plugin
  has `dmChannelUsers` for this; slack should mirror.
- **Add `gate()` / `applyDunk` / `assertChannelAllowed` unit tests**.
  Requires mocking @slack/bolt's WebClient or extracting these as pure
  functions taking an injected client. Significant test infra build-out.
- **Surface slack rate-limit responses + retry-after** explicitly.
  Currently the catch-all returns a generic "tool failed" without the
  retry hint. Bolt's WebAPIRequestError carries this info.
- **Bot identity refresh** — BOT_USER_ID/HANDLE/TEAM_ID loaded once at
  boot. On bot rename, app reinstall, or workspace migration, in-memory
  identity goes stale until restart. Add a 1h refresh timer + a
  `tokens_revoked`/`app_uninstalled` event handler that triggers reboot.
- **Drop discord-plugin's `replyToMode` from slack access.json schema** —
  slack threading is conceptually different and the option doesn't
  apply. Right now the schema accepts it silently.
- **Distinguish "channel not opted in" vs "bot not invited to channel"**
  in the assertChannelAllowed error. Currently both yield the same
  "not opted in — add via /slack:access" message; if the channel IS in
  groups but the bot isn't a member, the operator gets misdirected.
- **Permalink in inbound channel tag** — slack's `chat.getPermalink`
  is cheap and the model could use it to cite messages back.

## Open follow-ups (not blockers)

- Port discord plugin's permission relay to slack (Block Kit actions buttons can drive the same flow).
- Bolt's reconnect/watchdog story — Bolt handles reconnects internally but a watchdog timer matching the discord plugin's pattern (kill on prolonged disconnect, let systemd restart) might still be valuable. Not added in v0.1.
