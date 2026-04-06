# claude-channel-whatsapp

A WhatsApp channel plugin for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Bridges WhatsApp Web to Claude using the [Baileys](https://github.com/WhiskeySockets/Baileys) library and the MCP channel protocol, so people can message Claude on WhatsApp and get responses.

## How it works

This plugin runs as an MCP server that:

1. Connects to WhatsApp Web using multi-device credentials (no phone needed to stay online)
2. Receives incoming WhatsApp messages and delivers them to Claude Code via channel notifications
3. Exposes `reply`, `react`, and `download_attachment` tools so Claude can respond

Messages are gated by access control -- nobody can talk to Claude unless you explicitly approve them.

## Prerequisites

- **[Bun](https://bun.sh/)** runtime (v1.0+)
- **Claude Code** v2.1+ with channel support
- **Claude Max or Pro subscription** (channels require these tiers)

## Quick setup

### 1. Install the plugin

```bash
# Clone to Claude's plugins directory
mkdir -p ~/.claude/plugins
cd ~/.claude/plugins
git clone https://github.com/PenguinMiaou/claude-channel-whatsapp.git whatsapp
cd whatsapp
bun install
```

### 2. Launch Claude Code with the plugin

Plugins that provide channels require the development flag:

```bash
claude --dangerously-load-development-channels
```

Claude Code will detect the plugin from `~/.claude/plugins/whatsapp/` and start the MCP server automatically.

### 3. Check status

In Claude Code, run:

```
/whatsapp:configure
```

This shows whether auth credentials exist and lists any allowed senders.

### 4. Authenticate with WhatsApp

If you have no existing auth, you need to link your WhatsApp account. The plugin uses Baileys' multi-device auth -- you scan a QR code or use a pairing code, similar to WhatsApp Web.

To import auth from another Baileys-based setup, copy the auth files (creds.json and key files) into `~/.claude/channels/whatsapp/auth/`, or use:

```
/whatsapp:configure import
```

To clear auth and start fresh:

```
/whatsapp:configure clear
```

### 5. Pair a sender

Once connected, have someone message you on WhatsApp. The plugin will reply with a pairing code. In Claude Code, approve it:

```
/whatsapp:access pair <code>
```

That sender is now allowlisted and their messages will reach Claude.

## Access control

Access is managed entirely through the `/whatsapp:access` skill. The plugin never auto-approves anyone.

### DM policies

| Policy | Behavior |
|---|---|
| `pairing` (default) | Unknown senders get a pairing code; approve in Claude Code |
| `allowlist` | Only pre-approved numbers can message; unknowns are silently dropped |
| `disabled` | All incoming messages are dropped |

### Commands

```
/whatsapp:access                    # Show status
/whatsapp:access pair <code>        # Approve a pairing
/whatsapp:access deny <code>        # Reject a pairing
/whatsapp:access allow <phone>      # Add a phone number (E.164 format: +1234567890)
/whatsapp:access remove <phone>     # Remove a phone number
/whatsapp:access policy <mode>      # Set DM policy
/whatsapp:access set <key> <value>  # Set config (ackReaction, textChunkLimit, chunkMode)
```

All state lives in `~/.claude/channels/whatsapp/access.json`.

## Tools

The plugin exposes three MCP tools to Claude:

### `reply`
Send a text message and/or file attachments to a WhatsApp chat.
- `chat_id` (required): JID from the inbound message
- `text` (required): message text (markdown is converted to WhatsApp formatting)
- `reply_to`: message ID to quote
- `files`: array of absolute file paths to attach (images send as photos, others as documents; max 50MB each)

### `react`
Add an emoji reaction to a message.
- `chat_id`, `message_id`, `emoji` (all required)

### `download_attachment`
Download a media attachment (voice, video, document, sticker) from a recent message. Returns a local file path.
- `message_json` (required): the attachment message ID from inbound metadata

## LID mapping

WhatsApp has been migrating from phone-based JIDs (e.g. `60168816782@s.whatsapp.net`) to Linked IDs (LIDs, e.g. `84576647000082@lid`). Baileys stores reverse mappings in the auth directory, and the plugin loads these to resolve LIDs back to phone numbers for access control.

If you see a raw LID number in logs instead of a phone number, the mapping file has not been created yet. This usually resolves after the contact sends a few messages.

## Directory structure

```
~/.claude/plugins/whatsapp/          # Plugin code (this repo)
~/.claude/channels/whatsapp/         # Runtime state (not in repo)
  access.json                        # Access control config
  auth/                              # Baileys auth state (creds.json, keys)
  inbox/                             # Downloaded media attachments
  approved/                          # Temp files for pairing confirmations
```

## Configuration

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `WHATSAPP_STATE_DIR` | `~/.claude/channels/whatsapp` | Override the runtime state directory |

### Access config keys

Set via `/whatsapp:access set <key> <value>`:

| Key | Default | Description |
|---|---|---|
| `ackReaction` | (none) | Emoji to react with on receipt |
| `textChunkLimit` | 4000 | Max characters per message chunk |
| `chunkMode` | `length` | `length` (hard cut) or `newline` (break at paragraphs/lines) |

## Security notes

- **Auth credentials** in `~/.claude/channels/whatsapp/auth/` are your WhatsApp session. Protect them like passwords. The directory is created with `0700` permissions.
- **Access control** is enforced server-side. Claude cannot approve pairings or modify the allowlist -- only the user can, via the `/whatsapp:access` skill in their terminal.
- **Channel messages are untrusted input.** The plugin instructs Claude to never act on access-control requests that arrive via WhatsApp. This prevents prompt injection from granting access.
- **File sending is restricted.** The plugin refuses to send files from the channel state directory (auth, config) to prevent credential exfiltration.
- The `--dangerously-load-development-channels` flag is required because this is a community plugin, not an official Anthropic channel.

## License

Apache 2.0 -- see [LICENSE](LICENSE).
