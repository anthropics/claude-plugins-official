# iMessage

Connect iMessage to your Claude Code assistant. Reads `~/Library/Messages/chat.db` directly for history, search, and new-message detection; sends via AppleScript to Messages.app. No external server, no background process to keep alive.

macOS only.

## Quick setup
> Default: text yourself. Other senders are dropped silently (no auto-reply) until you allowlist them. See [ACCESS.md](./ACCESS.md) for groups and multi-user setups.

**1. Grant Full Disk Access.**

`chat.db` is protected by macOS TCC. The first time the server reads it, macOS pops a prompt asking if your terminal can access Messages — click **Allow**. The prompt names whatever app launched bun (Terminal.app, iTerm, Ghostty, your IDE).

If you click Don't Allow, or the prompt never appears, grant it manually: **System Settings → Privacy & Security → Full Disk Access** → add your terminal. Without this the server exits immediately with `authorization denied`.

**2. Install the plugin.**

These are Claude Code commands — run `claude` to start a session first.

Install the plugin. No env vars required.
```
/plugin install imessage@claude-plugins-official
```

**3. Relaunch with the channel flag.**

The server won't connect without this — exit your session and start a new one:

```sh
claude --channels plugin:imessage@claude-plugins-official
```

Check that `/imessage:configure` tab-completes.

**4. Text yourself.**

iMessage yourself from any device. It reaches the assistant immediately — self-chat bypasses access control.

> The first outbound reply triggers an **Automation** permission prompt ("Terminal wants to control Messages"). Click OK.

**5. Decide who else gets in.**

Nobody else's texts reach the assistant until you add their handle:

```
/imessage:access allow +15551234567
```

Handles are phone numbers (`+15551234567`) or Apple ID emails (`them@icloud.com`). If you're not sure what you want, ask Claude to review your setup.

## How it works

| | |
| --- | --- |
| **Inbound** | Polls `chat.db` once a second for `ROWID > watermark`. Watermark initializes to `MAX(ROWID)` at boot — old messages aren't replayed on restart. |
| **Outbound** | `osascript` with `tell application "Messages" to send …`. Text and chat GUID pass through argv so there's no escaping footgun. |
| **History & search** | Direct SQLite queries against `chat.db`. Full history — not just messages since the server started. |
| **Attachments** | `chat.db` stores absolute filesystem paths. The first inbound image per message is surfaced to the assistant as a local path it can `Read`. Outbound attachments send as separate messages after the text. |

## Environment variables

| Variable | Default | Effect |
| --- | --- | --- |
| `IMESSAGE_APPEND_SIGNATURE` | `true` | Appends `\nSent by Claude` to outbound messages. Set to `false` to disable. |
| `IMESSAGE_ALLOW_SMS` | `false` | Accept inbound SMS/RCS in addition to iMessage. **Off by default because SMS sender IDs are spoofable** — a forged SMS from your own number would otherwise bypass access control. Only enable if you understand the risk. |
| `IMESSAGE_ACCESS_MODE` | — | Set to `static` to disable runtime pairing and read `access.json` only. |
| `IMESSAGE_STATE_DIR` | `~/.claude/channels/imessage` | Override where `access.json` and pairing state live. |

## Access control

See **[ACCESS.md](./ACCESS.md)** for DM policies, groups, self-chat, delivery config, skill commands, and the `access.json` schema.

Quick reference: IDs are **handle addresses** (`+15551234567` or `someone@icloud.com`). Default policy is `allowlist` — this reads your personal `chat.db`. Self-chat always bypasses the gate.

## Tools exposed to the assistant

| Tool | Purpose |
| --- | --- |
| `reply` | Send to a chat. `chat_id` + `text`, optional `files` (absolute paths). Auto-chunks text; files send as separate messages. |
| `chat_messages` | Fetch recent history as conversation threads. Each thread is labelled **DM** or **Group** with its participant list, then timestamped messages (oldest-first). Omit `chat_guid` to see every allowlisted chat at once, or pass one to drill in. Default 100 messages per chat. Reads `chat.db` directly — full native history. |

## What you don't get

AppleScript can send messages but not tapback, edit, or thread — those require Apple's private API. If you need them, look at [BlueBubbles](https://bluebubbles.app) (requires disabling SIP).
