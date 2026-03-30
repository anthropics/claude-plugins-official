# iMessage Plugin — Troubleshooting

## Permission reply sends duplicate ✅ acks

**Symptom:** Replying `yes [request_id]` to a permission prompt results in two ✅ messages sent back instead of one.

**Cause:** iCloud sync can write the same inbound message as two rows in `chat.db` with different GUIDs but the same content. Both rows pass the permission-reply regex, firing two acks.

**Fix (merged):** `server.ts` now maintains a `seenPermissions` map keyed on `${chat_guid}\x00${request_id}` with a 30-second TTL. The second row hits the dedup check and returns early before the ack fires.

```ts
const PERM_DEDUP_WINDOW_MS = 30000
const seenPermissions = new Map<string, number>()
// …inside the permission-reply intercept:
const permKey = `${r.chat_guid}\x00${requestId}`
const now = Date.now()
for (const [k, t] of seenPermissions) if (now - t > PERM_DEDUP_WINDOW_MS) seenPermissions.delete(k)
if (seenPermissions.has(permKey)) return
seenPermissions.set(permKey, now)
```

Tracked in anthropics/claude-plugins-official#1165.

---

## Server exits immediately with `authorization denied`

macOS TCC is blocking access to `chat.db`. Grant **Full Disk Access** to your terminal app: **System Settings → Privacy & Security → Full Disk Access**.

---

## Messages arrive but no reply comes back

The first outbound reply triggers an **Automation** permission prompt in macOS ("Terminal wants to control Messages"). If you dismissed it, re-grant via **System Settings → Privacy & Security → Automation** → enable Messages for your terminal.

---

## Old messages are replayed on restart

The watermark initializes to `MAX(ROWID)` at boot so history isn't replayed. If you're seeing old messages, the watermark file may have been deleted. Check `~/.claude/channels/imessage/` — the state directory can be overridden with `IMESSAGE_STATE_DIR`.

---

## Plugin server doesn't restart after being killed

Killing the `bun server.ts` process (e.g. to hot-reload a patch) does not restart it automatically. The parent `claude --channels plugin:imessage@claude-plugins-official` process must be restarted to bring the server back up.

---

## Self-chat address not detected

The server builds the `SELF` set from `message.account` for `is_from_me = 1` rows. If your Apple ID hasn't sent any messages yet in `chat.db`, `SELF` will be empty and self-chat won't be recognized. Send yourself at least one iMessage first, then restart the server.
