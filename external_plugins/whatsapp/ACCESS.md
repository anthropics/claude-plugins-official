# WhatsApp — Access & Delivery

A WhatsApp Business number is publicly addressable. Anyone with the number can send a message, and without a gate those would flow straight into your assistant session. The access model described here decides who gets through.

By default, the channel uses **`allowlist`** mode: messages from senders not in `allowFrom` are silently dropped — no reply, no notification. You add phones explicitly with `/whatsapp:access allow <phone>` from your assistant session. This is cheaper and safer than the alternative (pairing) because every reply WhatsApp sends inside the 24h customer-service window counts against your messaging quota.

If you want a self-onboarding flow (e.g. customer support), flip to **`pairing`**: a DM from an unknown sender gets back a 6-character code, and you run `/whatsapp:access pair <code>` to approve them. Pairing costs one outbound message per stranger, so it's an opt-in choice.

All state lives in `~/.claude/channels/whatsapp/access.json`. The `/whatsapp:access` skill commands edit this file; the server re-reads it on every inbound message, so changes take effect without a restart.

## At a glance

| | |
| --- | --- |
| Default policy | `allowlist` |
| Sender ID | E.164 phone without `+` (e.g. `15551234567`) |
| Group key | WhatsApp group ID (e.g. `120363041234567890@g.us`) |
| Inbound transport | Webhook POST from Meta to your server |
| Outbound transport | WhatsApp Cloud API (Graph API) |
| Config file | `~/.claude/channels/whatsapp/access.json` |

## DM policies

`dmPolicy` controls how messages from senders not on the allowlist are handled.

| Policy | Behavior |
| --- | --- |
| `allowlist` (default) | Drop silently. No reply. Cheapest option — costs zero outbound messages. Recommended for personal/private use where you know who's allowed in advance. |
| `pairing` | Reply with a 6-char pairing code, drop the message. Approve with `/whatsapp:access pair <code>`. Self-onboarding flow useful for customer support. Each stranger costs one outbound message. |
| `disabled` | Drop everything, including allowlisted users and groups. |

### `allowProspects` flag (escape hatch)

Setting `allowProspects: true` in `access.json` lets **any** unknown sender through as a `prospect` (bypassing both `allowlist` drop and `pairing` codes). The notification reaches the assistant tagged with `relationship: "prospect"` so it can choose how to handle them.

```jsonc
{
  "dmPolicy": "allowlist",
  "allowFrom": ["15551234567"],
  "allowProspects": true
}
```

Use cases:
- **Inbound sales/lead capture**: every WhatsApp message lands as a lead in your assistant session, no pre-approval needed.
- **Customer support hotline**: combined with a Claude prompt that triages incoming requests.

**Caveat:** opens the door to spam if your number is publicly listed. Combine with a `mentionPatterns` filter or rate-limit the assistant's outbound replies.

Default is `false`. Toggle via:

```
/whatsapp:access set allowProspects true
```

```
/whatsapp:access policy allowlist
```

## Phone numbers

WhatsApp identifies senders by their E.164 phone number. The server normalizes inbound numbers to digits-only (no `+`, no spaces). The allowlist stores the same format.

Pairing captures the phone automatically. To add someone manually:

```
/whatsapp:access allow 15551234567
/whatsapp:access remove 15551234567
```

Set `WHATSAPP_PHONE_REGION=BR` to enable Brazilian DDD9 matching — numbers with and without the optional 9th digit (e.g. `5511987654321` vs `551187654321`) match each other. Without this flag, comparison is exact-string.

## Groups

Groups are off by default. Opt each one in individually.

```
/whatsapp:access group add 120363041234567890@g.us
```

WhatsApp group IDs end in `@g.us`. To find one, send a test message to the group from your WABA, then look at the `from` field in the inbound webhook payload (or check `~/.claude/channels/whatsapp/messages.db`).

With the default `requireMention: true`, the server forwards a message only when it matches one of your `mentionPatterns` or quotes a previous bot message. Pass `--no-mention` to forward every group message, or `--allow phone1,phone2` to restrict which members can trigger it.

```
/whatsapp:access group add 120363041234567890@g.us --no-mention
/whatsapp:access group add 120363041234567890@g.us --allow 15551234567,15559876543
/whatsapp:access group rm 120363041234567890@g.us
```

## Mention detection

In groups with `requireMention: true`, any of the following triggers the bot:

- A reply to one of the bot's previous messages
- A match against any case-insensitive regex in `mentionPatterns`

```
/whatsapp:access set mentionPatterns '["^hey claude\\b", "\\bassistant\\b"]'
```

## Delivery

Configure outbound behavior with `/whatsapp:access set <key> <value>`.

**`textChunkLimit`** sets the split threshold for long replies. WhatsApp's text body limit is **4096 characters**; default is 4000 to leave headroom.

**`chunkMode`** chooses the split strategy: `length` cuts exactly at the limit; `newline` prefers paragraph boundaries.

```
/whatsapp:access set textChunkLimit 3500
/whatsapp:access set chunkMode newline
```

## Skill reference

| Command | Effect |
| --- | --- |
| `/whatsapp:access` | Print current state: policy, allowlist, pending pairings, enabled groups. |
| `/whatsapp:access pair a4f91c` | Approve pairing code `a4f91c`. Adds the sender to `allowFrom` and sends a confirmation. |
| `/whatsapp:access deny a4f91c` | Discard a pending code. The sender is not notified. |
| `/whatsapp:access allow 15551234567` | Add a phone directly (digits only, no `+`). |
| `/whatsapp:access remove 15551234567` | Remove from the allowlist. |
| `/whatsapp:access policy allowlist` | Set `dmPolicy`. Values: `pairing`, `allowlist`, `disabled`. |
| `/whatsapp:access group add 120363...@g.us` | Enable a group. Flags: `--no-mention`, `--allow phone1,phone2`. |
| `/whatsapp:access group rm 120363...@g.us` | Disable a group. |
| `/whatsapp:access set allowProspects true` | Toggle the prospect-passthrough flag. |
| `/whatsapp:access set textChunkLimit 3500` | Set a config key: `textChunkLimit`, `chunkMode`, `mentionPatterns`, `allowProspects`. |

## Config file

`~/.claude/channels/whatsapp/access.json`. Absent file is equivalent to `pairing` policy with empty lists, so the first DM triggers pairing.

```jsonc
{
  // Handling for DMs from senders not in allowFrom.
  "dmPolicy": "allowlist",

  // E.164 phones (digits only, no +) allowed to DM.
  "allowFrom": ["15551234567"],

  // When true, unknown senders pass through tagged as `prospect`
  // (bypasses `allowlist` drop and `pairing` codes). Default false.
  "allowProspects": false,

  // Groups the server is active in. Empty object = DM-only.
  "groups": {
    "120363041234567890@g.us": {
      // true: respond only to mentions/replies (regex match against mentionPatterns).
      "requireMention": true,
      // Restrict triggers to these senders. Empty = any member (subject to requireMention).
      "allowFrom": []
    }
  },

  // Case-insensitive regexes that count as a mention in groups.
  "mentionPatterns": ["^hey claude\\b"],

  // Pending pairing requests, keyed by 6-char code.
  "pending": {},

  // Split threshold. WhatsApp rejects > 4096.
  "textChunkLimit": 4000,

  // length = cut at limit. newline = prefer paragraph boundaries.
  "chunkMode": "newline"
}
```
