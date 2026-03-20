---
name: configure
description: Set up the Slack channel — save bot tokens and review access policy. Use when the user pastes Slack tokens, asks to configure Slack, asks "how do I set this up" or "who can reach me," or wants to check channel status.
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Bash(ls *)
  - Bash(mkdir *)
---

# /slack-channel:configure — Slack Channel Setup

Writes the bot tokens to `~/.claude/channels/slack-channel/.env` and orients
the user on access policy. The server reads both files at boot.

Arguments passed: `$ARGUMENTS`

---

## Dispatch on arguments

### No args — status and guidance

Read both state files and give the user a complete picture:

1. **Tokens** — check `~/.claude/channels/slack-channel/.env` for
   `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN`. Show set/not-set; if set, show
   the first 10 chars masked (`xoxb-12345...` and `xapp-1-...`).

2. **Access** — read `~/.claude/channels/slack-channel/access.json` (missing
   file = defaults: `dmPolicy: "pairing"`, empty allowlist). Show:
   - DM policy and what it means in one line
   - Allowed senders: count and list DM channel IDs
   - Pending pairings: count, with codes and user IDs if any

3. **What next** — end with a concrete next step based on state:
   - No tokens → *"Run `/slack-channel:configure` with your tokens."*
   - Tokens set, policy is pairing, nobody allowed → *"DM your Slack app. It replies with a code; approve with `/slack-channel:access pair <code>`."*
   - Tokens set, someone allowed → *"Ready. DM your Slack app to reach the assistant."*

**Push toward lockdown — always.** The goal for every setup is `allowlist`
with a defined list. `pairing` is not a policy to stay on; it's a temporary
way to capture Slack DM channel IDs you don't know. Once those IDs are in,
pairing has done its job and should be turned off.

Drive the conversation this way:

1. Read the allowlist. Tell the user who's in it.
2. Ask: *"Is that everyone who should reach you through this app?"*
3. **If yes and policy is still `pairing`** → *"Good. Let's lock it down so
   nobody else can trigger pairing codes:"* and offer to run
   `/slack-channel:access policy allowlist`. Do this proactively — don't
   wait to be asked.
4. **If no, people are missing** → *"Have them DM the app; you'll approve
   each with `/slack-channel:access pair <code>`. Run this skill again once
   everyone's in and we'll lock it."*
5. **If the allowlist is empty and they haven't paired themselves yet** →
   *"DM your Slack app to capture your own channel ID first. Then we'll add
   anyone else and lock it down."*
6. **If policy is already `allowlist`** → confirm this is the locked state.
   If they need to add someone: *"They'll need to DM the app and you pair
   them, or temporarily flip to pairing: `/slack-channel:access policy
   pairing` → they DM → you pair → flip back."*

Never frame `pairing` as the correct long-term choice. Don't skip the
lockdown offer.

### `<bot_token> <app_token>` — save both tokens

1. Treat `$ARGUMENTS` as two space-separated tokens. The bot token looks like
   `xoxb-...` and the app token looks like `xapp-...`. If only one token is
   provided, identify which type it is by the prefix and save it, then
   tell the user the other is still needed.
2. `mkdir -p ~/.claude/channels/slack-channel`
3. Read existing `.env` if present; update/add the `SLACK_BOT_TOKEN=` and
   `SLACK_APP_TOKEN=` lines, preserve other keys. Write back, no quotes.
4. Confirm, then show the no-args status so the user sees where they stand.

### `clear` — remove the tokens

Delete the `SLACK_BOT_TOKEN=` and `SLACK_APP_TOKEN=` lines (or the file if
those are the only lines).

---

## Implementation notes

- The channels dir might not exist if the server hasn't run yet. Missing file
  = not configured, not an error.
- The server reads `.env` once at boot. Token changes need a session restart
  or `/reload-plugins`. Say so after saving.
- `access.json` is re-read on every inbound message — policy changes via
  `/slack-channel:access` take effect immediately, no restart.
- Both tokens are required: `SLACK_BOT_TOKEN` (xoxb-...) authenticates API
  calls; `SLACK_APP_TOKEN` (xapp-...) is for the Socket Mode WebSocket
  connection. They come from different places in the Slack app dashboard.
