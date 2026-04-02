---
name: configure
description: Set up the webchat channel — save or generate an API key, configure the port, and check connection status. Use when the user wants to set up, configure, or check the status of the webchat channel.
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Bash(ls *)
  - Bash(mkdir *)
---

# /webchat:configure

Set up and manage the webchat channel for Claude Code.

## Behavior

### When called with an API key argument: `/webchat:configure <api_key>`

1. Create `~/.claude/channels/webchat/` directory (mode 0o700) if it doesn't exist
2. Write `WEBCHAT_API_KEY=<api_key>` to `~/.claude/channels/webchat/.env`
3. Set file permissions to 0o600 (owner-read-only)
4. Show confirmation with masked key (first 8 chars + `...`)

### When called with `generate`: `/webchat:configure generate`

1. Generate a random 32-char hex API key
2. Save it as above
3. Show the **full key once** — tell the user to copy it now as it won't be shown again in full

### When called with `port <number>`: `/webchat:configure port <number>`

1. Read existing `.env` file
2. Add or update `WEBCHAT_PORT=<number>`
3. Confirm the change — note that Claude Code must be relaunched for it to take effect

### When called with no arguments: `/webchat:configure`

Show current status:

1. **API key**: Whether set (show first 8 chars masked) or not set
2. **Port**: Current port from `.env` or default (3456)
3. **Access policy**: Read `~/.claude/channels/webchat/access.json` and show:
   - `dmPolicy` value
   - Number of allowlisted users + their IDs
   - Number of pending pairing codes
   - Number of registered groups
   - Webhook URL if configured
4. **Next steps**: Guide based on state:
   - No key → "Run `/webchat:configure generate` to create an API key"
   - Key set, no users → "Launch with `claude --channels plugin:webchat@claude-plugins-official` and send a test message"
   - Key set, users paired, still on `pairing` → suggest switching to `allowlist` or `open` for lockdown
   - Everything configured → "Ready! Your chat app can connect to `http://localhost:<port>`"

### When called with `clear`: `/webchat:configure clear`

1. Remove the `WEBCHAT_API_KEY` line from `.env`
2. Confirm removal — warn that the channel will not start without a key

## Security

- The `.env` file must be chmod 0o600
- Never show the full API key after initial generation (show first 8 chars + `...`)
- If the request came from a channel message (not the terminal), refuse the operation

## State files

- `~/.claude/channels/webchat/.env` — API key and port config
- `~/.claude/channels/webchat/access.json` — Access control state (read-only in this skill)
