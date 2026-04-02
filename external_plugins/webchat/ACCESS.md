# Webchat Access Control

The webchat channel has two layers of authentication:

1. **API key** — every HTTP/WS request must include the key. This authenticates the _app_.
2. **Per-user access control** — within authenticated requests, individual `user_id`s are gated by the DM policy. This controls _which users_ reach Claude.

## DM policies

| Policy | Behavior |
|--------|----------|
| `pairing` (default) | Unknown `user_id` gets a 6-char code. Approved in terminal via `/webchat:access pair <code>`. Code expires in 1 hour. Max 3 pending. |
| `allowlist` | Only `user_id`s in `allowFrom` are accepted. Others get HTTP 403. |
| `open` | Any authenticated request passes — no per-user gating. Use this when your app handles its own user auth. |
| `disabled` | Everything dropped. |

### When to use `open`

If your chat app already authenticates users and you trust all of them to talk to Claude, set `dmPolicy` to `open`. The API key becomes the sole trust boundary. This is the simplest setup for single-developer or internal apps.

```bash
/webchat:access policy open
```

### When to use `pairing`

If multiple untrusted users might send messages through your app and you want to approve each one individually, keep the default `pairing` policy. Each new `user_id` triggers a pairing flow.

## Pairing flow

1. Chat app sends `POST /api/messages` with an unknown `user_id`
2. Server returns `202` with a pairing code:
   ```json
   { "pairing": true, "code": "a1b2c3", "message": "Pairing required — run in Claude Code: /webchat:access pair a1b2c3" }
   ```
3. Your app shows this message to the user
4. The Claude Code operator runs `/webchat:access pair a1b2c3` in their terminal
5. Server sends a "Paired!" confirmation via the outbound channel
6. Subsequent messages from that `user_id` are delivered to Claude

## Group support

A "group" is a `chat_id` with multiple users. Your app signals this with `"group": true` in the message payload.

```bash
# Enable a group chat
/webchat:access group add room-123

# Require @mention (your app sets mentions_bot: true)
/webchat:access group add room-123 --mention

# Restrict to specific users in the group
/webchat:access group add room-123 --allow user1,user2
```

Groups are keyed by `chat_id`. Per-group options:
- `requireMention` — only process messages where `mentions_bot: true` (default: true)
- `allowFrom` — restrict to specific `user_id`s (empty = any group member)

## Webhook delivery

Configure a webhook URL to receive Claude's responses as push notifications:

```bash
/webchat:access set webhook_url https://myapp.com/claude-webhook
/webchat:access set webhook_secret my-hmac-secret
```

Each outbound event is POSTed as JSON. If `webhook_secret` is set, requests include:
- `X-Webhook-Signature`: HMAC-SHA256 hex digest of the request body

## Config file

State lives in `~/.claude/channels/webchat/access.json`:

```json
{
  "dmPolicy": "pairing",
  "allowFrom": ["alice", "bob"],
  "groups": {
    "room-123": {
      "requireMention": true,
      "allowFrom": []
    }
  },
  "pending": {},
  "webhook": {
    "url": "https://myapp.com/webhook",
    "secret": "hmac-secret"
  },
  "replyToMode": "first",
  "textChunkLimit": 10000,
  "chunkMode": "newline"
}
```

### Delivery config

| Key | Values | Default | Description |
|-----|--------|---------|-------------|
| `replyToMode` | `off`, `first`, `all` | `first` | Which chunks get a `reply_to` reference |
| `textChunkLimit` | 1–10000 | 10000 | Max chars per outbound message before splitting |
| `chunkMode` | `length`, `newline` | `length` | Split strategy: hard cut vs paragraph boundaries |

## Skill commands

| Command | Description |
|---------|-------------|
| `/webchat:access` | Show current access state |
| `/webchat:access pair <code>` | Approve a pairing code |
| `/webchat:access deny <code>` | Reject a pending code |
| `/webchat:access allow <user_id>` | Add to allowlist |
| `/webchat:access remove <user_id>` | Remove from allowlist |
| `/webchat:access policy <mode>` | Set DM policy (pairing/allowlist/open/disabled) |
| `/webchat:access group add <chat_id>` [options] | Enable a group chat |
| `/webchat:access group rm <chat_id>` | Disable a group chat |
| `/webchat:access set <key> <value>` | Configure delivery/webhook settings |
