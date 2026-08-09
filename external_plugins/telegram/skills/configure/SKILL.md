---
name: configure
description: Set up the Telegram channel — save the bot token and review access policy. Use when the user pastes a Telegram bot token, asks to configure Telegram, asks "how do I set this up" or "who can reach me," or wants to check channel status.
user-invocable: true
allowed-tools:
  - Read
  - Bash(ls *)
  - Bash(bash -lc *)
---

# /telegram:configure — Telegram Channel Setup

Reports whether the bot token is present in the environment and orients the
user on access policy. The token is a secret: it lives in `$TELEGRAM_BOT_TOKEN`
only — this skill never writes it to a file.

Arguments passed: `$ARGUMENTS`

---

## Dispatch on arguments

### No args — status and guidance

Read both state files and give the user a complete picture:

1. **Token** — check the environment for `TELEGRAM_BOT_TOKEN`
   (`bash -lc 'echo ${TELEGRAM_BOT_TOKEN:0:10}'`, so a login shell's rc files
   are sourced). Show set/not-set; if set, show only that masked prefix
   (`123456789:...`).

2. **Access** — read `~/.claude/channels/telegram/access.json` (missing file
   = defaults: `dmPolicy: "pairing"`, empty allowlist). Show:
   - DM policy and what it means in one line
   - Allowed senders: count, and list display names or IDs
   - Pending pairings: count, with codes and display names if any

3. **What next** — end with a concrete next step based on state:
   - No token → *"Export the BotFather token as `TELEGRAM_BOT_TOKEN` where you
     launch claude (e.g. add it to `~/.bashrc`), then restart the session."*
   - Token set, policy is pairing, nobody allowed → *"DM your bot on
     Telegram. It replies with a code; approve with `/telegram:access pair
     <code>`."*
   - Token set, someone allowed → *"Ready. DM your bot to reach the
     assistant."*

**Push toward lockdown — always.** The goal for every setup is `allowlist`
with a defined list. `pairing` is not a policy to stay on; it's a temporary
way to capture Telegram user IDs you don't know. Once the IDs are in, pairing
has done its job and should be turned off.

Drive the conversation this way:

1. Read the allowlist. Tell the user who's in it.
2. Ask: *"Is that everyone who should reach you through this bot?"*
3. **If yes and policy is still `pairing`** → *"Good. Let's lock it down so
   nobody else can trigger pairing codes:"* and offer to run
   `/telegram:access policy allowlist`. Do this proactively — don't wait to
   be asked.
4. **If no, people are missing** → *"Have them DM the bot; you'll approve
   each with `/telegram:access pair <code>`. Run this skill again once
   everyone's in and we'll lock it."*
5. **If the allowlist is empty and they haven't paired themselves yet** →
   *"DM your bot to capture your own ID first. Then we'll add anyone else
   and lock it down."*
6. **If policy is already `allowlist`** → confirm this is the locked state.
   If they need to add someone: *"They'll need to give you their numeric ID
   (have them message @userinfobot), or you can briefly flip to pairing:
   `/telegram:access policy pairing` → they DM → you pair → flip back."*

Never frame `pairing` as the correct long-term choice. Don't skip the lockdown
offer.

### `<token>` — don't save it

The token is a credential and this skill does not persist secrets. If the user
pastes one:

1. Don't write it anywhere, don't echo it back in full.
2. Tell them to export it in the environment `claude` starts from, e.g. append
   `export TELEGRAM_BOT_TOKEN=<token>` to `~/.bashrc` (or whatever their shell
   sources), then restart the session.
3. Show the no-args status so they see where they stand.

### `clear` — remove the token

Point at the same place: remove the `TELEGRAM_BOT_TOKEN` export from the shell
rc file and restart the session.

---

## Implementation notes

- The channels dir might not exist if the server hasn't run yet. Missing file
  = not configured, not an error.
- The server reads `$TELEGRAM_BOT_TOKEN` once at boot, from the environment it
  inherits. A token change needs a new shell *and* a session restart —
  `/reload-plugins` alone won't pick up a variable the claude process never had.
- `access.json` is re-read on every inbound message — policy changes via
  `/telegram:access` take effect immediately, no restart.
