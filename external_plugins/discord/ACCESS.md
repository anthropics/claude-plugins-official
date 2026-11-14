# Discord — Access & Delivery

Discord only allows DMs between accounts that share a server. Who can DM your bot depends on where it's installed: one private server means only that server's members can reach it; a public community means every member there can open a DM.

The **Public Bot** toggle in the Developer Portal (Bot tab, on by default) controls who can add the bot to new servers. Turn it off and only your own account can install it. This is your first gate, and it's enforced by Discord rather than by this process.

For DMs that do get through, the default policy is **pairing**. An unknown sender gets a 6-character code in reply and their message is dropped. You run `/discord:access pair <code>` from your assistant session to approve them. Once approved, their messages pass through.

All state lives in `~/.claude/channels/discord/access.json`. The `/discord:access` skill commands edit this file; the server re-reads it on every inbound message, so changes take effect without a restart. Set `DISCORD_ACCESS_MODE=static` to pin config to what was on disk at boot (pairing is unavailable in static mode since it requires runtime writes).

## At a glance

| | |
| --- | --- |
| Default policy | `pairing` |
| Sender ID | User snowflake (numeric, e.g. `184695080709324800`) |
| Group key | Channel snowflake — not guild ID (server-wide entries go in `guilds`) |
| Config file | `~/.claude/channels/discord/access.json` |

## DM policies

`dmPolicy` controls how DMs from senders not on the allowlist are handled.

| Policy | Behavior |
| --- | --- |
| `pairing` (default) | Reply with a pairing code, drop the message. Approve with `/discord:access pair <code>`. |
| `allowlist` | Drop silently. No reply. Use this once everyone who needs access is already on the list, or if pairing replies would attract spam. |
| `disabled` | Drop everything, including allowlisted users and guild channels. |

```
/discord:access policy allowlist
```

## User IDs

Discord identifies users by **snowflakes**: permanent numeric IDs like `184695080709324800`. Usernames are mutable; snowflakes aren't. The allowlist stores snowflakes.

Pairing captures the ID automatically. To add someone manually, enable **User Settings → Advanced → Developer Mode** in Discord, then right-click any user and choose **Copy User ID**. Your own ID is available by right-clicking your avatar in the lower-left.

```
/discord:access allow 184695080709324800
/discord:access remove 184695080709324800
```

## Guild channels

Guild channels are off by default. Opt each one in individually, keyed on the **channel** snowflake (not the guild), or a whole server at once (see [Whole server](#whole-server)). Threads inherit their parent channel's opt-in; no separate entry needed. Find channel IDs the same way as user IDs: Developer Mode, right-click the channel, Copy Channel ID.

```
/discord:access group add 846209781206941736
```

With the default `requireMention: true`, the bot responds only when @mentioned or replied to. Pass `--no-mention` to process every message in the channel, or `--allow id1,id2` to restrict which members can trigger it.

```
/discord:access group add 846209781206941736 --no-mention
/discord:access group add 846209781206941736 --allow 184695080709324800,221773638772129792
/discord:access group rm 846209781206941736
```

To change an existing channel without retyping its settings, use `group set`. Only the flags you pass change. `--allow ""` clears the list, `--mention` turns mention-only back on.

```
/discord:access group set 846209781206941736 --sticky 15
/discord:access group set 846209781206941736 --allow ""
```

### Whole server

`guild add <guildId>` opts in every channel and thread of a server at once, including channels created later. It takes the same flags as `group add` (`--no-mention`, `--allow`, `--sticky`), and `guild set` / `guild rm` work like their `group` versions. Copy the **server** ID with Developer Mode by right-clicking the server icon.

A `groups` entry always wins over the server-wide one, so you can give one channel different settings. The bot still only sees channels its Discord role can read, so Discord permissions are the way to keep it out of a channel entirely.

```
/discord:access guild add 1120375923481059328 --allow 184695080709324800 --sticky 30
/discord:access guild rm 1120375923481059328
```

Without `--allow`, every member of the server can reach the assistant in every channel the bot can read. Prefer `--allow` on servers you don't fully control.

### Sticky mention window

`--sticky <minutes>` (0 to 1440, default 0 = off) keeps the bot listening in a channel for a while after someone talks to it. A mention or a reply to the bot opens a window of that many minutes. Messages during the window reach the assistant without a mention, marked `sticky="true"` so it can stay quiet when people are talking to each other. Each new mention or reply restarts the window, and so does the bot replying in that channel, so an active conversation doesn't close mid-thread (a bot reply never opens a window by itself). `--allow` still applies, so only listed members can open or use the window.

The window is tracked where the mention happened: a mention inside a thread opens the window for that thread only, not the parent channel or other threads.

```
/discord:access group add 846209781206941736 --sticky 30
```

Notes:
- The window is kept in memory. Restarting the session closes all windows, so the next message needs a mention again.
- Every message in an open window starts an assistant turn, so a busy channel uses more tokens. Keep the minutes low, or use `--allow` to limit who can trigger it.
- `--sticky` does nothing with `--no-mention`, since every message already passes.

## Mention detection

In channels with `requireMention: true`, any of the following triggers the bot:

- A structured `@botname` mention (typed via Discord's autocomplete)
- A reply to one of the bot's recent messages
- A match against any regex in `mentionPatterns`

Example regex setup for a nickname trigger:

```
/discord:access set mentionPatterns '["^hey claude\\b", "\\bassistant\\b"]'
```

## Delivery

Configure outbound behavior with `/discord:access set <key> <value>`.

**`ackReaction`** reacts to inbound messages on receipt as a "seen" acknowledgment. Unicode emoji work directly; custom server emoji require the full `<:name:id>` form. The emoji ID is at the end of the URL when you right-click the emoji and copy its link. Empty string disables.

```
/discord:access set ackReaction 🔨
/discord:access set ackReaction ""
```

**`replyToMode`** controls threading on chunked replies. When a long response is split, `first` (default) threads only the first chunk under the inbound message; `all` threads every chunk; `off` sends all chunks standalone.

**`textChunkLimit`** sets the split threshold. Discord rejects messages over 2000 characters, which is the hard ceiling.

**`chunkMode`** chooses the split strategy: `length` cuts exactly at the limit; `newline` prefers paragraph boundaries.

## Skill reference

| Command | Effect |
| --- | --- |
| `/discord:access` | Print current state: policy, allowlist, pending pairings, enabled channels. |
| `/discord:access pair a4f91c` | Approve pairing code `a4f91c`. Adds the sender to `allowFrom` and sends a confirmation on Discord. |
| `/discord:access deny a4f91c` | Discard a pending code. The sender is not notified. |
| `/discord:access allow 184695080709324800` | Add a user snowflake directly. |
| `/discord:access remove 184695080709324800` | Remove from the allowlist. |
| `/discord:access policy allowlist` | Set `dmPolicy`. Values: `pairing`, `allowlist`, `disabled`. |
| `/discord:access group add 846209781206941736` | Enable a guild channel. Flags: `--no-mention`, `--allow id1,id2`, `--sticky <minutes>`. |
| `/discord:access group set 846209781206941736 --sticky 15` | Change only the given settings of an enabled channel. Flags: `--mention`, `--no-mention`, `--allow id1,id2` (`""` clears), `--sticky <minutes>`. |
| `/discord:access group rm 846209781206941736` | Disable a guild channel. |
| `/discord:access guild add 1120375923481059328` | Enable every channel in a server. Same flags as `group add`; `guild set` / `guild rm` also exist. Per-channel entries win. |
| `/discord:access set ackReaction 🔨` | Set a config key: `ackReaction`, `replyToMode`, `textChunkLimit`, `chunkMode`, `mentionPatterns`. |

## Config file

`~/.claude/channels/discord/access.json`. Absent file is equivalent to `pairing` policy with empty lists, so the first DM triggers pairing.

```jsonc
{
  // Handling for DMs from senders not in allowFrom.
  "dmPolicy": "pairing",

  // User snowflakes allowed to DM.
  "allowFrom": ["184695080709324800"],

  // Guild channels the bot is active in. Empty object = DM-only.
  "groups": {
    "846209781206941736": {
      // true: respond only to @mentions and replies.
      "requireMention": true,
      // Restrict triggers to these senders. Empty = any member (subject to requireMention).
      "allowFrom": [],
      // Minutes the bot keeps listening after a mention. 0 = off.
      "stickyMinutes": 0
    }
  },

  // Server-wide opt-in, keyed on guild ID. Same fields as a groups entry.
  // Covers every channel without its own groups entry.
  "guilds": {},

  // Case-insensitive regexes that count as a mention.
  "mentionPatterns": ["^hey claude\\b"],

  // Reaction on receipt. Empty string disables.
  "ackReaction": "👀",

  // Threading on chunked replies: first | all | off
  "replyToMode": "first",

  // Split threshold. Discord rejects > 2000.
  "textChunkLimit": 2000,

  // length = cut at limit. newline = prefer paragraph boundaries.
  "chunkMode": "newline"
}
```
