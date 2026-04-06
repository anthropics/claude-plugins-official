---
name: configure
description: Set up the WhatsApp channel — check connection status, manage auth. Use when the user asks to configure WhatsApp, check channel status, or troubleshoot connection.
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Bash(ls *)
  - Bash(mkdir *)
  - Bash(cp *)
  - Bash(rm *)
---

# /whatsapp:configure — WhatsApp Channel Setup

Unlike Telegram which uses a bot token, WhatsApp uses device-linked auth
via @whiskeysockets/baileys. Auth state lives in
`~/.claude/channels/whatsapp/auth/`.

Arguments passed: `$ARGUMENTS`

---

## Dispatch on arguments

### No args — status and guidance

1. **Auth** — check if `~/.claude/channels/whatsapp/auth/creds.json` exists.
   If yes, show "authenticated" with brief info. If no, show "not authenticated".

2. **Access** — read `~/.claude/channels/whatsapp/access.json` (missing =
   defaults). Show:
   - DM policy and what it means
   - Allowed senders: count and phone numbers
   - Pending pairings

3. **What next** — concrete guidance:
   - No auth → explain they need to set up auth (import from another
     Baileys setup or link a new device)
   - Auth exists, nobody allowed → tell them to message from WhatsApp, then
     pair with `/whatsapp:access pair <code>`
   - Auth + people allowed → "Ready."

Push toward lockdown (allowlist mode) once users are paired.

### `import`

Import auth from another Baileys-based WhatsApp setup:
1. Ask the user for the source directory path containing creds.json
2. Copy all files to `~/.claude/channels/whatsapp/auth/`
3. Confirm

### `clear`

Remove auth state to force re-authentication:
1. Remove all files in `~/.claude/channels/whatsapp/auth/`
2. Confirm — note that re-auth will require linking the device again

---

## Implementation notes

- Auth is managed by baileys' `useMultiFileAuthState` — don't manually
  edit creds.json.
- Connection issues: check `~/.claude/channels/whatsapp/auth/creds.json` exists
  and has valid content.
