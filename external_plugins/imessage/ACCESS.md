# iMessage — Access & Delivery

This channel reads your Messages database (`~/Library/Messages/chat.db`) directly. Every text to this Mac — from any contact, in any chat — reaches the gate. Access control selects which conversations the assistant should see.

Texting yourself always works. **Self-chat bypasses the gate** with no setup: the server learns your own addresses at boot and lets them through unconditionally. For other senders, the default policy is **`allowlist`**: nothing passes until you add the handle with `/imessage:access allow <address>`.

All state lives in `~/.claude/channels/imessage/access.json`. The `/imessage:access` skill commands edit this file; the server re-reads it on every inbound message, so changes take effect without a restart. Set `IMESSAGE_ACCESS_MODE=static` to pin config to what was on disk at boot.

## At a glance

| | |
| --- | --- |
| Default policy | `allowlist` |
| Self-chat | Bypasses the gate; no config needed |
| Sender ID | Handle address: `+15551234567` or `someone@icloud.com` |
| Group key | Chat GUID: `iMessage;+;chat…` |
| Mention quirk | Regex only; iMessage has no structured @mentions |
| Config file | `~/.claude/channels/imessage/access.json` |

## Self-chat

Open Messages on any device signed into your Apple ID, start a conversation with yourself, and text. It reaches the assistant.

The server identifies your addresses at boot by reading `message.account` and `chat.last_addressed_handle` from `chat.db`. Messages from those addresses skip the gate entirely. To distinguish your input from its own replies — both appear in `chat.db` as from-me — it maintains a 15-second window of recently sent text and matches against it.

## DM policies

`dmPolicy` controls how texts from senders other than you, not on the allowlist, are handled.

| Policy | Behavior |
| --- | --- |
| `allowlist` (default) | Drop silently. Safe default for a personal account. |
| `pairing` | Reply with a pairing code, drop the message. Every contact who texts this Mac will receive one; only use this if very few people have the number. |
| `disabled` | Drop everything except self-chat, which always bypasses. |

```
/imessage:access policy pairing
```

## Handle addresses

iMessage identifies senders by **handle addresses**: either a phone number in `+country` format or the Apple ID email. The form matches what appears at the top of the conversation in Messages.app.

| Contact shown as | Handle address |
| --- | --- |
| Phone number | `+15551234567` (keep the `+`, no spaces or dashes) |
| Email | `someone@icloud.com` |

If the exact form is unclear, check the `chat_messages` tool output or (under `pairing` policy) the pending entry in `access.json`.

```
/imessage:access allow +15551234567
/imessage:access allow friend@icloud.com
/imessage:access remove +15551234567
```

## Groups

Groups are off by default. Opt each one in individually, keyed on the chat GUID.

Chat GUIDs look like `iMessage;+;chat123456789012345678`. They're not exposed in Messages.app; get them from the `chat_id` field in `chat_messages` tool output or from the server's stderr log when it drops a group message.

```
/imessage:access group add "iMessage;+;chat123456789012345678"
```

Quote the GUID; the semicolons are shell metacharacters.

iMessage has **no structured @mentions**. The `@Name` highlight in group chats is presentational styling — nothing in `chat.db` marks it as a mention. With the default `requireMention: true`, the only trigger is a `mentionPatterns` regex match. Set at least one pattern before opting a group in, or no message will ever match.

```
/imessage:access set mentionPatterns '["^claude\\b", "@assistant"]'
```

Pass `--no-mention` to process every message in the group, or `--allow addr1,addr2` to restrict which members can trigger it.

```
/imessage:access group add "iMessage;+;chat123456789012345678" --no-mention
/imessage:access group add "iMessage;+;chat123456789012345678" --allow +15551234567,friend@icloud.com
/imessage:access group rm "iMessage;+;chat123456789012345678"
```

## Delivery

AppleScript can send messages but cannot tapback, edit, or thread-reply; those require private API. Delivery config is correspondingly limited. Set with `/imessage:access set <key> <value>`.

**`textChunkLimit`** sets the split threshold. iMessage has no length cap; chunking is for readability. Defaults to 10000.

**`chunkMode`** chooses the split strategy: `length` cuts exactly at the limit; `newline` prefers paragraph boundaries.

There is no `ackReaction` or `replyToMode` on this channel.

## Skill reference

| Command | Effect |
| --- | --- |
| `/imessage:access` | Print current state: policy, allowlist, pending pairings, enabled groups. |
| `/imessage:access pair a4f91c` | Approve a pending code (relevant only under `pairing` policy). |
| `/imessage:access deny a4f91c` | Discard a pending code. |
| `/imessage:access allow +15551234567` | Add a handle. The primary entry point under the default `allowlist` policy. |
| `/imessage:access remove +15551234567` | Remove from the allowlist. |
| `/imessage:access policy pairing` | Set `dmPolicy`. Values: `pairing`, `allowlist`, `disabled`. |
| `/imessage:access group add "iMessage;+;chat…"` | Enable a group. Quote the GUID. Flags: `--no-mention`, `--allow a,b`. |
| `/imessage:access group rm "iMessage;+;chat…"` | Disable a group. |
| `/imessage:access set textChunkLimit 5000` | Set a config key: `textChunkLimit`, `chunkMode`, `mentionPatterns`. |

## Config file

`~/.claude/channels/imessage/access.json`. Absent file is equivalent to `allowlist` policy with empty lists: only self-chat passes.

```jsonc
{
  // Handling for texts from senders not in allowFrom.
  // Defaults to allowlist since this reads your personal chat.db.
  // Self-chat bypasses regardless.
  "dmPolicy": "allowlist",

  // Handle addresses allowed to reach the assistant.
  "allowFrom": ["+15551234567", "friend@icloud.com"],

  // Group chats the assistant participates in. Empty object = DM-only.
  "groups": {
    "iMessage;+;chat123456789012345678": {
      // true: respond only on mentionPatterns match.
      // iMessage has no structured @mentions; regex is the only trigger.
      "requireMention": true,
      // Restrict triggers to these senders. Empty = any member (subject to requireMention).
      "allowFrom": []
    }
  },

  // Case-insensitive regexes that count as a mention.
  // Required for groups with requireMention, since there are no structured mentions.
  "mentionPatterns": ["^claude\\b", "@assistant"],

  // Split threshold. No length cap; this is about readability.
  "textChunkLimit": 10000,

  // length = cut at limit. newline = prefer paragraph boundaries.
  "chunkMode": "newline"
}
```
