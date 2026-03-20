# Feishu — Access & Delivery

Feishu apps require tenant admin approval to install, providing a baseline of trust. However, any user in the tenant who can see the bot can DM it, so fine-grained access control is still needed.

The default policy is **pairing**. An unknown sender gets a 6-character code in reply and their message is dropped. You run `/feishu:access pair <code>` from your assistant session to approve them. Once approved, their messages pass through.

All state lives in `~/.claude/channels/feishu/access.json`. The `/feishu:access` skill commands edit this file; the server re-reads it on every inbound message, so changes take effect without a restart. Set `FEISHU_ACCESS_MODE=static` to pin config to what was on disk at boot (pairing is unavailable in static mode since it requires runtime writes).

## At a glance

| | |
| --- | --- |
| Default policy | `pairing` |
| Sender ID | Feishu open_id (e.g. `ou_xxxx`) |
| Group key | chat_id (e.g. `oc_yyyy`) |
| Config file | `~/.claude/channels/feishu/access.json` |

## DM policies

`dmPolicy` controls how DMs from senders not on the allowlist are handled.

| Policy | Behavior |
| --- | --- |
| `pairing` (default) | Reply with a pairing code, drop the message. Approve with `/feishu:access pair <code>`. |
| `allowlist` | Drop silently. No reply. Use this once everyone who needs access is already on the list, or if pairing replies would attract noise. |
| `disabled` | Drop everything, including allowlisted users and group chats. |

```
/feishu:access policy allowlist
```

## User IDs

Feishu identifies users by **open_id**: strings like `ou_xxxx` that are scoped to your app. They are stable within an app's context. The allowlist stores open_ids.

Pairing captures the ID automatically. To add someone manually, you need their open_id — this can be found via the Feishu admin console or API.

```
/feishu:access allow ou_xxxx
/feishu:access remove ou_xxxx
```

## Group chats

Group chats are off by default. Opt each one in individually, keyed on the **chat_id** (e.g. `oc_yyyy`). Find chat IDs from the inbound message notifications or via the Feishu API.

```
/feishu:access group add oc_yyyy
```

With the default `requireMention: true`, the bot responds only when @mentioned or replied to. Pass `--no-mention` to process every message in the group, or `--allow id1,id2` to restrict which members can trigger it.

```
/feishu:access group add oc_yyyy --no-mention
/feishu:access group add oc_yyyy --allow ou_xxxx,ou_zzzz
/feishu:access group rm oc_yyyy
```

## Mention detection

In groups with `requireMention: true`, any of the following triggers the bot:

- A structured `@bot` mention (typed via Feishu's autocomplete)
- A reply to one of the bot's recent messages
- A match against any regex in `mentionPatterns`

Example regex setup for a nickname trigger:

```
/feishu:access set mentionPatterns '["小助手", "\\bassistant\\b"]'
```

## Delivery

Configure outbound behavior with `/feishu:access set <key> <value>`.

**`ackReaction`** reacts to inbound messages on receipt as a "seen" acknowledgment. Use Feishu emoji_type strings like `THUMBSUP`, `SMILE`, etc. Empty string disables.

```
/feishu:access set ackReaction THUMBSUP
/feishu:access set ackReaction ""
```

**`replyToMode`** controls threading on chunked replies. When a long response is split, `first` (default) threads only the first chunk under the inbound message; `all` threads every chunk; `off` sends all chunks standalone.

**`textChunkLimit`** sets the split threshold. Default is 4000 characters. Feishu allows much more than Discord (~30k), but shorter chunks are more readable.

**`chunkMode`** chooses the split strategy: `length` cuts exactly at the limit; `newline` prefers paragraph boundaries.

## Skill reference

| Command | Effect |
| --- | --- |
| `/feishu:access` | Print current state: policy, allowlist, pending pairings, enabled groups. |
| `/feishu:access pair a4f91c` | Approve pairing code `a4f91c`. Adds the sender to `allowFrom` and sends a confirmation on Feishu. |
| `/feishu:access deny a4f91c` | Discard a pending code. The sender is not notified. |
| `/feishu:access allow ou_xxxx` | Add an open_id directly. |
| `/feishu:access remove ou_xxxx` | Remove from the allowlist. |
| `/feishu:access policy allowlist` | Set `dmPolicy`. Values: `pairing`, `allowlist`, `disabled`. |
| `/feishu:access group add oc_yyyy` | Enable a group chat. Flags: `--no-mention`, `--allow id1,id2`. |
| `/feishu:access group rm oc_yyyy` | Disable a group chat. |
| `/feishu:access set ackReaction THUMBSUP` | Set a config key: `ackReaction`, `replyToMode`, `textChunkLimit`, `chunkMode`, `mentionPatterns`. |

## Config file

`~/.claude/channels/feishu/access.json`. Absent file is equivalent to `pairing` policy with empty lists, so the first DM triggers pairing.

```jsonc
{
  // Handling for DMs from senders not in allowFrom.
  "dmPolicy": "pairing",

  // Feishu open_ids allowed to DM.
  "allowFrom": ["ou_xxxx"],

  // Group chats the bot is active in. Empty object = DM-only.
  "groups": {
    "oc_yyyy": {
      // true: respond only to @mentions and replies.
      "requireMention": true,
      // Restrict triggers to these senders. Empty = any member (subject to requireMention).
      "allowFrom": []
    }
  },

  // Case-insensitive regexes that count as a mention.
  "mentionPatterns": ["小助手"],

  // Reaction on receipt. Empty string disables. Use Feishu emoji_type strings.
  "ackReaction": "",

  // Threading on chunked replies: first | all | off
  "replyToMode": "first",

  // Split threshold. Default 4000.
  "textChunkLimit": 4000,

  // length = cut at limit. newline = prefer paragraph boundaries.
  "chunkMode": "newline"
}
```
