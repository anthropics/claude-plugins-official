# Webchat Channel for Claude Code

HTTP/WebSocket bridge that lets **any chat application** talk to Claude Code.
Your app authenticates with an API key and sends/receives messages via REST or WebSocket — no platform SDK required.

## Prerequisites

- [Bun](https://bun.sh) runtime installed
- Claude Code with channel support

## Quick start

```bash
# 1. Install the plugin
/plugin install webchat@claude-plugins-official

# 2. Configure — generates an API key and saves it
/webchat:configure

# 3. Relaunch Claude Code with the channel
claude --channels plugin:webchat@claude-plugins-official

# 4. Send a message from your app
curl -X POST http://localhost:3456/api/messages \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice", "text": "Hello Claude!"}'

# 5. Poll for Claude's response
curl http://localhost:3456/api/messages/alice \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## API Reference

All endpoints (except `/api/health`) require `Authorization: Bearer <api_key>`.

### Send a message

```
POST /api/messages
```

```json
{
  "chat_id": "room-123",
  "message_id": "msg-456",
  "user_id": "alice",
  "username": "Alice",
  "text": "Hello Claude!",
  "group": false,
  "mentions_bot": false,
  "attachments": [
    { "name": "photo.png", "url": "https://example.com/photo.png", "type": "image/png" }
  ]
}
```

Required fields: `user_id`, `text`. If `chat_id` is omitted, defaults to `user_id` (DM).

**Responses:**
- `200` — Message delivered to Claude
- `202` — Pairing required (returns a code)
- `403` — User not allowed
- `401` — Invalid API key

### Poll for responses

```
GET /api/messages/:chat_id
```

Returns and clears queued outbound events:

```json
{
  "messages": [
    {
      "id": "a1b2c3d4",
      "type": "reply",
      "chat_id": "room-123",
      "text": "Hello! How can I help?",
      "reply_to": "msg-456",
      "files": ["1717000000-abcd1234.png"],
      "timestamp": "2026-04-02T12:00:00.000Z"
    }
  ]
}
```

File names in `files` can be downloaded via `GET /api/files/:name`.

### Download file attachments

```
GET /api/files/:name
```

Serves files that Claude attached to replies.

### Respond to permission requests

```
POST /api/permissions/:code
```

```json
{ "allow": true }
```

### Health check

```
GET /api/health
```

No auth required. Returns `{ "status": "ok", "port": 3456 }`.

## WebSocket

Connect to `ws://localhost:3456/ws?token=YOUR_API_KEY&chat_id=room-123`.

Use `chat_id=*` to receive events for all chats.

**Send (inbound):**
```json
{
  "type": "message",
  "chat_id": "room-123",
  "user_id": "alice",
  "username": "Alice",
  "text": "Hello!"
}
```

**Receive (outbound):**
```json
{
  "id": "a1b2c3d4",
  "type": "reply",
  "chat_id": "room-123",
  "text": "Hello! How can I help?",
  "timestamp": "2026-04-02T12:00:00.000Z"
}
```

**Permission responses via WS:**
```json
{
  "type": "permission_response",
  "request_id": "abcde",
  "allow": true
}
```

## Webhook delivery

Register a webhook to receive push notifications for Claude's responses:

```bash
/webchat:access set webhook_url https://myapp.com/webhook
/webchat:access set webhook_secret my-hmac-secret  # optional
```

Each outbound event is POSTed as JSON. If a secret is set, the request includes
an `X-Webhook-Signature` header with the HMAC-SHA256 hex digest.

## Access control

See [ACCESS.md](ACCESS.md) for the full access control model, including pairing,
allowlists, group support, and the `open` policy for apps that handle their own auth.

## Tools

| Tool | Description |
|------|-------------|
| `reply` | Send text + optional file attachments to a chat |
| `react` | Send an emoji reaction event |
| `edit_message` | Edit a previously sent message |
| `fetch_messages` | View recent outbound messages for a chat |

## Local development guide

Step-by-step setup to connect a local chat app to the webchat plugin.

### 1. Generate an API key

```bash
mkdir -p ~/.claude/channels/webchat
API_KEY=$(openssl rand -hex 16)
echo "WEBCHAT_API_KEY=$API_KEY" > ~/.claude/channels/webchat/.env
chmod 600 ~/.claude/channels/webchat/.env
echo "Your API key: $API_KEY"
```

### 2. Skip per-user gating (easiest for local dev)

Set the policy to `open` so you don't need to pair every user:

```bash
cat > ~/.claude/channels/webchat/access.json << 'EOF'
{
  "dmPolicy": "open",
  "allowFrom": [],
  "groups": {},
  "pending": {}
}
EOF
```

### 3. Launch Claude Code with the channel

```bash
claude --channels plugin:webchat@claude-plugins-official
```

You should see: `webchat channel: HTTP server listening on http://localhost:3456`

### 4. Connect your chat app

#### Option A: REST polling (simplest)

```javascript
const API_KEY = 'your-key-from-step-1';
const PLUGIN = 'http://localhost:3456';

// Send a user message to Claude
async function sendToClaude(userId, text) {
  const res = await fetch(`${PLUGIN}/api/messages`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ user_id: userId, text }),
  });
  return res.json();
}

// Poll for Claude's responses
async function pollResponses(chatId) {
  const res = await fetch(`${PLUGIN}/api/messages/${chatId}`, {
    headers: { 'Authorization': `Bearer ${API_KEY}` },
  });
  const { messages } = await res.json();
  return messages; // [{ id, type, text, reply_to, files, timestamp }]
}
```

#### Option B: WebSocket (real-time)

```javascript
const ws = new WebSocket('ws://localhost:3456/ws?token=YOUR_KEY&chat_id=*');

// Receive Claude's responses
ws.onmessage = (event) => {
  const evt = JSON.parse(event.data);
  // evt = { id, type: "reply", chat_id, text, timestamp }
  displayInChat(evt);
};

// Send a user message
ws.send(JSON.stringify({
  type: 'message',
  user_id: 'alice',
  chat_id: 'alice',
  text: 'Hello Claude!',
}));
```

#### Option C: Webhook (push to your app)

Configure the plugin to POST Claude's responses to your app:

```bash
cat > ~/.claude/channels/webchat/access.json << 'EOF'
{
  "dmPolicy": "open",
  "allowFrom": [],
  "groups": {},
  "pending": {},
  "webhook": {
    "url": "http://localhost:6863/webhook"
  }
}
EOF
```

Add a POST handler at `/webhook` in your app — every Claude reply is pushed there as JSON.

### 5. Smoke test from terminal

```bash
API_KEY="your-key"

# Send a message
curl -s -X POST http://localhost:3456/api/messages \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","text":"What is 2+2?"}'

# Wait a few seconds, then poll for Claude's response
curl -s http://localhost:3456/api/messages/test \
  -H "Authorization: Bearer $API_KEY" | python3 -m json.tool
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WEBCHAT_API_KEY` | — | Required. API key for authenticating chat app requests |
| `WEBCHAT_PORT` | `3456` | HTTP server port |
| `WEBCHAT_STATE_DIR` | `~/.claude/channels/webchat` | State directory |
| `WEBCHAT_ACCESS_MODE` | — | Set to `static` to snapshot config at boot |
