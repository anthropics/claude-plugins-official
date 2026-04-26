---
name: configure
description: Set up the WhatsApp channel — save Cloud API credentials and review access policy. Use when the user pastes a WhatsApp access token, asks to configure WhatsApp, asks "how do I set this up" or "who can reach me," or wants to check channel status.
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Bash(ls *)
  - Bash(mkdir *)
  - Bash(chmod *)
---

# /whatsapp:configure — WhatsApp Channel Setup

Writes WhatsApp Cloud API credentials to `~/.claude/channels/whatsapp/.env`
and orients the user on access policy. The server reads `.env` once at boot.

Arguments passed: `$ARGUMENTS`

---

## Required env vars

The server fails fast if any of these are missing:

| Var | What it is | Where to find it |
|---|---|---|
| `WHATSAPP_ACCESS_TOKEN` | Long-lived System User token with `whatsapp_business_messaging` scope | Meta App Dashboard → System Users → Generate Token |
| `WHATSAPP_PHONE_NUMBER_ID` | The phone number ID (NOT the phone number itself) | Meta App Dashboard → WhatsApp → API Setup |
| `WHATSAPP_WABA_ID` | WhatsApp Business Account ID | Meta App Dashboard → WhatsApp → API Setup |
| `WHATSAPP_VERIFY_TOKEN` | Any random string you choose; you'll paste the same value into Meta's webhook config | Pick a strong random string (e.g. `openssl rand -hex 32`) |
| `WHATSAPP_APP_SECRET` | The Meta App Secret used for HMAC-SHA256 signature verification | Meta App Dashboard → App Settings → Basic → App Secret |

Optional:

| Var | Default | Purpose |
|---|---|---|
| `WHATSAPP_PORT` | `3789` | Local HTTP port for the webhook receiver |
| `WHATSAPP_SELF_PHONE` | (empty) | Your own WABA phone — used to filter outbound echoes |
| `WHATSAPP_PERMISSION_TARGET` | (empty) | Phone allowed to answer Claude's permission prompts |
| `WHATSAPP_PHONE_REGION` | `intl` | Set to `BR` to enable Brazilian DDD9 matching heuristics |
| `WHATSAPP_TIMEZONE` | `UTC` | IANA timezone for `local_time` in notifications |
| `WHATSAPP_STATE_DIR` | `~/.claude/channels/whatsapp` | Override the state directory |

---

## Dispatch on arguments

Parse `$ARGUMENTS` (whitespace-separated). If empty or unrecognized, show status.

### No args — status and guidance

Read state files and give the user a complete picture:

1. **Credentials** — check `~/.claude/channels/whatsapp/.env`. For each
   required key, show set/not-set; if set, mask everything except the first
   6 and last 4 chars.

2. **Access** — read `~/.claude/channels/whatsapp/access.json` (missing file
   = defaults: `dmPolicy: "allowlist"`, empty allowlist). Show:
   - DM policy and what it means in one line
   - Allowed phones: count, list (E.164 without `+`)
   - Pending pairings: count, with codes and senderIds if any (only relevant
     in `pairing` mode)

3. **What next** — end with a concrete next step based on state:
   - Missing required env vars → list them and tell the user
     *"Run `/whatsapp:configure <key>=<value>` for each, or paste your full
     `.env` block."*
   - All env vars set, no allowed phones, policy is `allowlist` (default) →
     *"Configure your webhook URL in the Meta App Dashboard pointing to a
     public tunnel (cloudflared/ngrok) of
     `http://localhost:<WHATSAPP_PORT>/webhook`, then add allowed contacts
     with `/whatsapp:access allow <phone>` (E.164 digits only, no `+`)."*
   - Token set, someone allowed → *"Ready. Send WhatsApp messages to your
     WABA number to reach the assistant."*
   - Policy is `pairing` and pending entries → list them so the operator
     can run `/whatsapp:access pair <code>` for each.

**Recommended: stay on `allowlist`.** Unlike Telegram or Discord (where
the bot identifier is opaque so pairing is the only way to discover IDs),
WhatsApp uses the sender's phone number directly — you already know who
should reach you. `allowlist` mode silently drops strangers at zero cost.
`pairing` only makes sense for self-onboarding flows like customer support,
and each stranger triggers an outbound message that counts against your
quota.

Drive the conversation this way:

1. Read the allowlist. Tell the user who's in it.
2. Ask: *"Is that everyone who should reach you through this WABA?"*
3. **If allowlist is empty (fresh setup)** → *"Add the phones that should
   reach you with `/whatsapp:access allow <phone>` (digits only, no +).
   On WhatsApp the sender ID is the phone number itself — no need to send
   a test message first."*
4. **If policy is `pairing` and the allowlist looks right** → *"Switch to
   `allowlist` so strangers don't trigger paid replies:
   `/whatsapp:access policy allowlist`."* Offer this proactively.
5. **If someone is missing** → *"Just add them: `/whatsapp:access allow
   <phone>`. If you'd rather have them message first to confirm the right
   number, briefly flip with `/whatsapp:access policy pairing` → they
   message → you pair → flip back."*

Don't push pairing as the default. WhatsApp's phone-as-ID model makes
direct allowlist the natural fit.

### `<key>=<value>` — save one credential

1. Treat each whitespace-separated arg matching `KEY=VALUE` as a credential
   to save. Trim whitespace and surrounding quotes from the value.
2. Validate `KEY` is one of the recognized vars (see tables above). Reject
   unknown keys with a list of accepted names.
3. `mkdir -p ~/.claude/channels/whatsapp`
4. Read existing `.env` if present. Update or insert each `KEY=VALUE` line,
   preserving other keys. Write back, no quotes around values.
5. `chmod 600 ~/.claude/channels/whatsapp/.env` — these are credentials.
6. Confirm what was set (mask values), then show the no-args status so the
   user sees where they stand.

### Multi-line paste — bulk save

If `$ARGUMENTS` contains multiple lines or several `KEY=VALUE` pairs, treat
each as a separate save in one pass. Preserves any keys not mentioned.

### `clear` — remove all credentials

Delete `~/.claude/channels/whatsapp/.env` (or all `WHATSAPP_*` lines if
other unrelated keys are in the file).

---

## Implementation notes

- The channels dir might not exist if the server hasn't run yet. Missing
  file = not configured, not an error.
- The server reads `.env` once at boot. Credential changes require a
  session restart or `/reload-plugins`. Say so after saving.
- `access.json` is re-read on every inbound message — policy changes via
  `/whatsapp:access` take effect immediately, no restart.
- Never log full token values. Always mask in output.
- The webhook URL configured in the Meta dashboard must point to a
  publicly reachable HTTPS endpoint (cloudflared, ngrok, or similar
  tunnel). The server itself binds to localhost.
