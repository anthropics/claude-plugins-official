---
name: configure
description: Set up the DingTalk channel — save the app credentials and review access policy. Use when the user provides DingTalk credentials, asks to configure DingTalk, asks "how do I set this up" or "who can reach me," or wants to check channel status.
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Bash(ls *)
  - Bash(mkdir *)
---

# /dingtalk:configure — DingTalk Channel Setup

Writes the app credentials to `~/.claude/channels/dingtalk/.env` and orients
the user on access policy. The server reads both files at boot.

Arguments passed: `$ARGUMENTS`

---

## Dispatch on arguments

### No args — status and guidance

Read both state files and give the user a complete picture:

1. **Credentials** — check `~/.claude/channels/dingtalk/.env` for
   `DINGTALK_CLIENT_ID` and `DINGTALK_CLIENT_SECRET`. Show set/not-set;
   if set, show first 6 chars masked.

2. **Access** — read `~/.claude/channels/dingtalk/access.json` (missing file
   = defaults: `dmPolicy: "pairing"`, empty allowlist). Show:
   - DM policy and what it means in one line
   - Allowed senders: count, and list staff IDs
   - Pending pairings: count, with codes if any
   - Groups opted in: count

3. **What next** — end with a concrete next step based on state:
   - No credentials → *"Run `/dingtalk:configure <clientId> <clientSecret>`
     with your app credentials from the DingTalk Developer Platform."*
   - Credentials set, policy is pairing, nobody allowed → *"DM your bot on
     DingTalk. It replies with a code; approve with `/dingtalk:access pair
     <code>`."*
   - Credentials set, someone allowed → *"Ready. DM your bot to reach the
     assistant."*

**Push toward lockdown — always.** `pairing` is temporary. Once the IDs are
captured, switch to `allowlist`.

### `<clientId> <clientSecret>` — save credentials

1. Treat `$ARGUMENTS` as space-separated clientId and clientSecret.
2. `mkdir -p ~/.claude/channels/dingtalk`
3. Read existing `.env` if present; update/add the lines, preserve other keys.
   Write back, no quotes.
4. Optionally: if a third argument is provided, save it as `DINGTALK_ROBOT_CODE`.
5. Confirm, then show the no-args status.

### `clear` — remove credentials

Delete the credential lines (or the file if those are the only lines).

---

## Getting DingTalk credentials

1. Go to [DingTalk Developer Platform](https://open-dev.dingtalk.com/)
2. Create an Enterprise Internal Application (企业内部应用)
3. Under "Robot" (机器人), enable the bot capability
4. Under "Credentials" (凭证与基础信息), find:
   - **AppKey** = Client ID
   - **AppSecret** = Client Secret
5. Under "Bot Configuration" (机器人配置):
   - Set message receiving mode to **Stream Mode** (Stream 模式)
   - No public URL required

## Implementation notes

- The channels dir might not exist if the server hasn't run yet.
- The server reads `.env` once at boot. Credential changes need a session
  restart or `/reload-plugins`.
- `access.json` is re-read on every inbound message — policy changes take
  effect immediately.
