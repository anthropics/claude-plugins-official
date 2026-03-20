---
name: configure
description: Set up the Feishu channel — save app credentials and review access policy. Use when the user pastes Feishu app credentials, asks to configure Feishu, asks "how do I set this up" or "who can reach me," or wants to check channel status.
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Bash(ls *)
  - Bash(mkdir *)
---

# /feishu:configure — Feishu Channel Setup

Writes the app credentials to `~/.claude/channels/feishu/.env` and orients the
user on access policy. The server reads the env file at boot.

Arguments passed: `$ARGUMENTS`

---

## Dispatch on arguments

### No args — status and guidance

Read both state files and give the user a complete picture:

1. **Credentials** — check `~/.claude/channels/feishu/.env` for
   `FEISHU_APP_ID` and `FEISHU_APP_SECRET`. Show set/not-set; if set, show
   first 6 chars masked. Also show `FEISHU_DOMAIN` if set (飞书 or Lark).

2. **Access** — read `~/.claude/channels/feishu/access.json` (missing file
   = defaults: `dmPolicy: "pairing"`, empty allowlist). Show:
   - DM policy and what it means in one line
   - Allowed senders: count, and list open_ids
   - Pending pairings: count, with codes and sender IDs if any
   - Group chats opted in: count

3. **What next** — end with a concrete next step based on state:
   - No credentials → *"Run `/feishu:configure <app_id> <app_secret>` with
     your credentials from [飞书开放平台](https://open.feishu.cn) →
     凭证与基础信息."*
   - Credentials set, policy is pairing, nobody allowed → *"在飞书中给你的
     机器人发一条私聊消息。它会回复一个配对码，然后运行
     `/feishu:access pair <code>` 来批准."*
   - Credentials set, someone allowed → *"Ready. DM your bot on Feishu to
     reach the assistant."*

**Push toward lockdown — always.** The goal for every setup is `allowlist`
with a defined list. `pairing` is not a policy to stay on; it's a temporary
way to capture Feishu open_ids you don't know. Once the IDs are in,
pairing has done its job and should be turned off.

Drive the conversation this way:

1. Read the allowlist. Tell the user who's in it.
2. Ask: *"这些是所有需要通过此机器人联系你的人吗？"*
3. **If yes and policy is still `pairing`** → *"好的，让我们锁定它，这样
   就没有其他人可以触发配对码:"* and offer to run
   `/feishu:access policy allowlist`. Do this proactively — don't wait to
   be asked.
4. **If no, people are missing** → *"让他们给机器人发私聊消息，你用
   `/feishu:access pair <code>` 批准每一个。全部添加后再运行本命令锁定."*
   Or, if they can get open_ids directly: guide them to use
   `/feishu:access allow <open_id>`.
5. **If the allowlist is empty and they haven't paired themselves yet** →
   *"先在飞书中给你的机器人发条消息，捕获你自己的 ID。然后我们再添加其他人
   并锁定."*
6. **If policy is already `allowlist`** → confirm this is the locked state.
   If they need to add someone, `/feishu:access allow <open_id>` is the
   clean path — no need to reopen pairing.

Feishu already gates reach (app needs tenant admin approval), but that's not
a substitute for locking the allowlist. Never frame `pairing` as the correct
long-term choice. Don't skip the lockdown offer.

### `<app_id> <app_secret>` — save credentials

1. Parse `$ARGUMENTS` as two space-separated values: app_id and app_secret.
   Feishu app IDs look like `cli_xxxx`. App secrets are alphanumeric strings.
   Both are found on 飞书开放平台 → 应用 → 凭证与基础信息.
2. `mkdir -p ~/.claude/channels/feishu`
3. Read existing `.env` if present; update/add the `FEISHU_APP_ID=` and
   `FEISHU_APP_SECRET=` lines, preserve other keys (like `FEISHU_DOMAIN`).
   Write back, no quotes around values.
4. Confirm, then show the no-args status so the user sees where they stand.

### `<app_id> <app_secret> --lark` — save credentials for Lark international

Same as above, but also set `FEISHU_DOMAIN=https://open.larksuite.com` in the
`.env` file.

### `clear` — remove credentials

Delete the `FEISHU_APP_ID=` and `FEISHU_APP_SECRET=` lines (or the file if
those are the only lines).

---

## Implementation notes

- The channels dir might not exist if the server hasn't run yet. Missing file
  = not configured, not an error.
- The server reads `.env` once at boot. Credential changes need a session
  restart or `/reload-plugins`. Say so after saving.
- `access.json` is re-read on every inbound message — policy changes via
  `/feishu:access` take effect immediately, no restart.
