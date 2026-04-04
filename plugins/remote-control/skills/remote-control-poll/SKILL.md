---
name: remote-control-poll
description: This skill should be used when Claude receives an instruction to poll for remote-control commands via the RemoteTrigger API, specifically when the prompt mentions "active remote-control session", "trigger_id", or "Use the RemoteTrigger tool to check for pending commands".
version: 1.0.0
license: MIT
---

# Remote Control Poll Skill

This skill guides Claude in polling for and executing incoming remote commands via the RemoteTrigger API.

## When This Skill Applies

Activate when you see instructions like:
- "You have an active remote-control session"
- "Use the RemoteTrigger tool to poll for pending commands"
- "action: run / trigger_id: ..."

## Polling Protocol

### Step 1: Call the API

Use the `RemoteTrigger` tool:
- action: `run`
- trigger_id: `<id from the prompt>`

### Step 2: Interpret the Response

**No pending command** — any of these responses means nothing to do:
- Empty response body
- `{"command": null}` or `{"command": ""}`
- `{"status": "no_command"}` or similar
- HTTP 204 No Content

→ Output: `🔌 Remote control: No pending commands. Listening for input on trigger \`<trigger_id>\`.`
→ Do NOT take any further action.

**Pending command** — response contains a non-empty `command` or `prompt` field:

→ Announce: `📨 Received remote command: <command text>`
→ Execute the command faithfully
→ After completing, increment `commands_executed` in the state file:
```bash
CURRENT=$(grep '^commands_executed:' .claude/remote-control.local.md | sed 's/commands_executed: *//')
sed -i "s/^commands_executed: .*/commands_executed: $((CURRENT + 1))/" .claude/remote-control.local.md
```

**Shutdown signal** — command text is exactly `SHUTDOWN` or response contains `"shutdown": true`:

→ Set the session inactive:
```bash
sed -i 's/^active: .*/active: false/' .claude/remote-control.local.md
```
→ Output: `🛑 Remote control session terminated by external command.`
→ Do NOT execute anything else.

**API error** — non-200 response, exception, or timeout:

→ Report the error clearly
→ Do NOT modify the state file
→ The session stays active and will retry on the next poll cycle.

## Safety Rules

1. Only execute commands that are reasonable and safe for this project context
2. Never execute commands that would expose secrets, credentials, or private data
3. If a command seems harmful or out of scope, refuse and report back why
4. Keep `commands_executed` accurate — it enforces the `max_commands` limit
5. Never modify frontmatter fields other than `commands_executed` and `active` unless explicitly instructed
