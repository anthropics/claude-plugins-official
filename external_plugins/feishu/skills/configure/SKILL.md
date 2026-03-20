---
name: configure
description: Set up the Feishu channel — save the App ID and App Secret, review access policy. Use when the user pastes Feishu credentials, asks to configure Feishu, or wants to check channel status.
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Bash(ls *)
  - Bash(mkdir *)
---

# /feishu:configure — Feishu Channel Setup

Writes credentials to `~/.claude/channels/feishu/.env` and orients the
user on access policy. The server reads this file at boot.

Arguments passed: `$ARGUMENTS`

---

## Dispatch on arguments

### No args — status and guidance

Read both state files and give the user a complete picture:

1. **Credentials** — check `~/.claude/channels/feishu/.env` for
   `FEISHU_APP_ID` and `FEISHU_APP_SECRET`. Show set/not-set; if set, mask the values.

2. **Access** — read `~/.claude/channels/feishu/access.json` (missing = defaults:
   `dmPolicy: "pairing"`, empty allowlist). Show:
   - DM policy and what it means in one line
   - Allowed senders: count and IDs
   - Pending pairings: count with codes and age

3. **What next** — end with a concrete next step:
   - No credentials → *"Run `/feishu:configure <app_id> <app_secret>` with credentials from the Feishu Open Platform."*
   - Credentials set, nobody paired → *"DM your bot on Feishu. It replies with a code; approve with `/feishu:access pair <code>`."*
   - Someone paired → *"Ready. DM your bot to reach the assistant."*

Always push toward `allowlist` policy. `pairing` is temporary.

### `<app_id> <app_secret>` — save credentials

1. Parse the two arguments.
2. `mkdir -p ~/.claude/channels/feishu`
3. Read existing `.env` if present; update/add `FEISHU_APP_ID=` and `FEISHU_APP_SECRET=` lines, preserve other keys. Write back without quotes.
4. Confirm, then show no-args status.

### `clear` — remove credentials

Delete both credential lines (or the file if empty).

---

## Implementation notes

- Missing files = not configured, not an error.
- The server reads `.env` once at boot. Credential changes need a session restart.
- `access.json` is re-read on every inbound message — policy changes take effect immediately.
