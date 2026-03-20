# Slack Channel — Access & Delivery

A Slack app is accessible to anyone in the workspace. Without a gate, any DM or channel mention would flow into your assistant session. The access model described here decides who gets through.

By default, a DM from an unknown sender triggers **pairing**: the bot replies with a 6-character code and drops the message. You run `/slack-channel:access pair <code>` from your assistant session to approve them. Once approved, their messages pass through.

All state lives in `~/.claude/channels/slack-channel/access.json`. The `/slack-channel:access` skill commands edit this file; the server re-reads it on every inbound message, so changes take effect without a restart. Set `SLACK_ACCESS_MODE=static` to pin config to what was on disk at boot (pairing is unavailable in static mode since it requires runtime writes).

## At a glance

| | |
| --- | --- |
| Default policy | `pairing` |
| DM identifier | DM channel ID (`D...`) — not user ID |
| User ID | Slack user ID (`U...`) |
| Channel key | Channel ID (`C...` public, `G...` private) |
| Config file | `~/.claude/channels/slack-channel/access.json` |

## DM policies

`dmPolicy` controls how DMs from senders not on the allowlist are handled.

| Policy | Behavior |
| --- | --- |
| `pairing` (default) | Reply with a pairing code, drop the message. Approve with `/slack-channel:access pair <code>`. |
| `allowlist` | Drop silently. No reply. Useful after everyone who needs access has paired. |
| `disabled` | Drop everything, including allowlisted users and channels. |

```
/slack-channel:access policy allowlist
```

## IDs

Slack uses several types of IDs:

- **User IDs** (`U1234567890`) — permanent, identify a person.
- **DM channel IDs** (`D1234567890`) — the conversation between the bot and a user. The allowlist stores these.
- **Channel IDs** (`C1234567890` public, `G1234567890` private group).

Pairing captures the DM channel ID automatically. To find IDs manually, look at the Slack URL when viewing a conversation: `https://app.slack.com/client/T.../C...` or `https://app.slack.com/client/T.../D...`.

```
/slack-channel:access allow D1234567890
/slack-channel:access remove D1234567890
```

## Channels

Channels are off by default. Opt each one in individually.

```
/slack-channel:access channel add C1234567890
```

With the default `requireMention: true`, the bot responds only when @mentioned or replied to in a thread it started. Pass `--no-mention` to process every message, or `--allow U1,U2` to restrict which members can trigger it.

```
/slack-channel:access channel add C1234567890 --no-mention
/slack-channel:access channel add C1234567890 --allow U1234567890,U9876543210
/slack-channel:access channel rm C1234567890
```

**Bot must be invited.** Unlike Telegram (where any user can DM a bot), Slack requires the bot to be a member of a channel before it receives events. Invite it with `/invite @botname` in the channel.

## Mention detection

In channels with `requireMention: true`, any of the following triggers the bot:

- A direct `<@BOTID>` mention in the message text
- A reply in a thread started by the bot
- A match against any regex in `mentionPatterns`

```
/slack-channel:access set mentionPatterns '["^hey claude\\b", "\\bassistant\\b"]'
```

## Delivery

Configure outbound behavior with `/slack-channel:access set <key> <value>`.

**`ackReaction`** reacts to inbound messages on receipt. Pass the emoji name without colons. Slack supports any emoji in the workspace (including custom emoji).

```
/slack-channel:access set ackReaction eyes
/slack-channel:access set ackReaction ""
```

**`replyToMode`** controls threading on chunked replies. When a long response is split, `first` (default) threads only the first chunk under the inbound message; `all` threads every chunk; `off` sends all chunks standalone.

**`textChunkLimit`** sets the split threshold. Default is 4000. Slack has a higher hard limit but messages over ~4000 chars become hard to read.

**`chunkMode`** chooses the split strategy: `length` cuts exactly at the limit; `newline` prefers paragraph boundaries.

## Skill reference

| Command | Effect |
| --- | --- |
| `/slack-channel:access` | Print current state: policy, allowlist, pending pairings, enabled channels. |
| `/slack-channel:access pair a4f91c` | Approve pairing code `a4f91c`. Adds the DM channel to `allowFrom` and sends a confirmation on Slack. |
| `/slack-channel:access deny a4f91c` | Discard a pending code. The sender is not notified. |
| `/slack-channel:access allow D1234567890` | Add a DM channel ID directly. |
| `/slack-channel:access remove D1234567890` | Remove from the allowlist. |
| `/slack-channel:access policy allowlist` | Set `dmPolicy`. Values: `pairing`, `allowlist`, `disabled`. |
| `/slack-channel:access channel add C1234567890` | Enable a channel. Flags: `--no-mention`, `--allow U1,U2`. |
| `/slack-channel:access channel rm C1234567890` | Disable a channel. |
| `/slack-channel:access set ackReaction eyes` | Set a config key: `ackReaction`, `replyToMode`, `textChunkLimit`, `chunkMode`, `mentionPatterns`. |

## Config file

`~/.claude/channels/slack-channel/access.json`. Absent file is equivalent to `pairing` policy with empty lists, so the first DM triggers pairing.

```jsonc
{
  // Handling for DMs from senders not in allowFrom.
  "dmPolicy": "pairing",

  // DM channel IDs (D...) allowed to send.
  "allowFrom": ["D1234567890"],

  // Channels the bot is active in. Empty object = DM-only.
  "channels": {
    "C1234567890": {
      // true: respond only to @mentions and thread replies.
      "requireMention": true,
      // Restrict triggers to these user IDs. Empty = any member (subject to requireMention).
      "allowFrom": []
    }
  },

  // Case-insensitive regexes that count as a mention.
  "mentionPatterns": ["^hey claude\\b"],

  // Emoji name (no colons). Empty string disables.
  "ackReaction": "eyes",

  // Threading on chunked replies: first | all | off
  "replyToMode": "first",

  // Split threshold.
  "textChunkLimit": 4000,

  // length = cut at limit. newline = prefer paragraph boundaries.
  "chunkMode": "newline"
}
```
