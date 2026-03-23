---
name: configure
description: Set up the Telegram channel — save the bot token and review access policy. Use when the user pastes a Telegram bot token, asks to configure Telegram, asks "how do I set this up" or "who can reach me," or wants to check channel status.
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Bash(ls *)
  - Bash(mkdir *)
  - Bash(chmod *)
---

# /telegram:configure — Telegram Channel Setup

Writes the bot token to the appropriate state directory and orients the
user on access policy. The server reads both files at boot.

Arguments passed: `$ARGUMENTS`

---

## State directory resolution

Before any operation, determine which mode is active:

1. Read `.claude/settings.local.json` in the current project root (if it exists)
2. Check for `TELEGRAM_PROJECT_ID` in the `env` object (flat `Record<string, string>`)
3. If found: state dir is `~/.claude/channels/telegram/projects/<id>/`
4. If not found: state dir is `~/.claude/channels/telegram/` (global)

Use this resolved state dir for ALL file operations below.

## Project ID validation

When `--project <name>` is used, validate the name:
- Allowed: `[a-zA-Z0-9_-]` only
- Max length: 64 characters
- Reject with a clear error if invalid

### `--project <name> <token>` — per-project setup

1. Validate `<name>` against project ID constraints. Reject if invalid.
2. Set state dir to `~/.claude/channels/telegram/projects/<name>/`.
3. `mkdir -p <state_dir>`
4. Read existing `<state_dir>/.env` if present; update/add `TELEGRAM_BOT_TOKEN=` line.
   Write back, no quotes around the value.
5. `chmod 600 <state_dir>/.env`
6. Read `.claude/settings.local.json` (create if missing). Add `TELEGRAM_PROJECT_ID` to the
   flat `env` object. Write back with 2-space indent. The resulting `env` block must be:
   ```json
   {
     "env": {
       "TELEGRAM_PROJECT_ID": "<name>"
     }
   }
   ```
   Merge into any existing keys — don't overwrite the whole file. Claude Code's `env` is a
   flat `Record<string, string>` — all values must be strings, no nesting. These env vars are
   passed to all MCP server processes at startup.
7. If global `~/.claude/channels/telegram/access.json` exists and has `allowFrom` entries,
   AND `<state_dir>/access.json` does NOT exist:
   copy it as the initial per-project access.json.
8. Confirm: show project name, state dir, token status, inherited users count.
9. Remind: "Restart your Claude Code session (or run `/reload-plugins`) for the
   MCP server to pick up the new project configuration."

### `--project <name>` (no token) — project status

Show status for the named project: token set/not-set, access summary, state dir path.

### `--global <token>` — global setup

Same as the existing bare-token behavior. Saves to `~/.claude/channels/telegram/.env`.

### `--global` (no token) — global status

Show global status: token, access, state dir.

### No args — status and guidance

Determine which mode is active via state directory resolution above. Then read the
appropriate state files and give the user a complete picture:

1. **Mode** — check `.claude/settings.local.json` for `TELEGRAM_PROJECT_ID`:
   - If found: note that per-project mode is active, show the project name, and
     that the state dir is `~/.claude/channels/telegram/projects/<name>/`.
   - If not found: note global mode is active (`~/.claude/channels/telegram/`),
     and mention that `--project <name> <token>` can set up a per-project bot.

2. **Token** — check `<state_dir>/.env` for `TELEGRAM_BOT_TOKEN`. Show set/not-set;
   if set, show first 10 chars masked (`123456789:...`).

3. **Access** — read `<state_dir>/access.json` (missing file = defaults:
   `dmPolicy: "pairing"`, empty allowlist). Show:
   - DM policy and what it means in one line
   - Allowed senders: count, and list display names or IDs
   - Pending pairings: count, with codes and display names if any

4. **What next** — end with a concrete next step based on state:
   - No token → *"Run `/telegram:configure <token>` with the token from
     BotFather."*
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

### `<token>` — save it

1. Treat `$ARGUMENTS` as the token (trim whitespace). BotFather tokens look
   like `123456789:AAH...` — numeric prefix, colon, long string.
2. Resolve state dir via state directory resolution above.
3. `mkdir -p <state_dir>`
4. Read existing `<state_dir>/.env` if present; update/add the `TELEGRAM_BOT_TOKEN=` line,
   preserve other keys. Write back, no quotes around the value.
5. `chmod 600 <state_dir>/.env` — the token is a credential.
6. Confirm, then show the no-args status so the user sees where they stand.

### `clear` — remove the token

Resolve state dir via state directory resolution above.

- **Per-project mode** (TELEGRAM_PROJECT_ID present in `.claude/settings.local.json`):
  Delete the `TELEGRAM_BOT_TOKEN=` line from `<state_dir>/.env` (or the file if that's
  the only line). Also remove the `TELEGRAM_PROJECT_ID` key from the
  `env` object in `.claude/settings.local.json`. If the `env` object is
  empty after removal, clean it up.
- **Global mode**: Delete the `TELEGRAM_BOT_TOKEN=` line from
  `~/.claude/channels/telegram/.env` (or the file if that's the only line).

---

## Implementation notes

- The channels dir might not exist if the server hasn't run yet. Missing file
  = not configured, not an error.
- The server reads `.env` once at boot. Token changes need a session restart
  or `/reload-plugins`. Say so after saving.
- `access.json` is re-read on every inbound message — policy changes via
  `/telegram:access` take effect immediately, no restart.
