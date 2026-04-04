# remote-control

Send commands to a running Claude Code session from external systems — CI pipelines, scripts, webhooks, or other tools — via the RemoteTrigger API.

## How It Works

1. Run `/remote-control` in your Claude Code session. This creates a **RemoteTrigger** (a persistent API endpoint) and starts listening.
2. From any external system, call the trigger's `/run` endpoint with a command payload.
3. After each response, Claude automatically polls for pending commands using a **Stop hook**. When a command arrives, Claude executes it and loops.
4. Run `/remote-control-stop` (or send `SHUTDOWN`) to end the session.

## Architecture

The plugin uses Claude Code's **Stop hook** pattern (same as `ralph-loop`) to intercept natural session exits and inject a poll prompt. Claude then uses the built-in `RemoteTrigger` tool (which has OAuth automatically) to check the API — the shell hook cannot call it directly.

```
External system
     │
     │  POST /v1/code/triggers/<id>/run  {"command": "..."}
     ▼
RemoteTrigger API
     │
     │  Stop hook fires → injects poll prompt
     ▼
Claude Code session
     │
     │  RemoteTrigger tool: action=run, trigger_id=<id>
     ▼
Command received → executed → loop continues
```

## Commands

| Command | Description |
|---------|-------------|
| `/remote-control` | Start a remote-control session |
| `/remote-control --name <name>` | Start with a custom trigger name |
| `/remote-control --max-commands <n>` | Limit total commands accepted |
| `/remote-control-stop` | Stop the session and deactivate trigger |
| `/remote-control-status` | Show current session status and trigger info |

## State File

The plugin stores session state in `.claude/remote-control.local.md` (project-scoped, not committed):

```yaml
---
active: true
session_id: <claude-code-session-id>
trigger_id: <trigger-id-from-api>
trigger_name: remote-my-project
max_commands: 0
commands_executed: 0
last_poll_at: "2026-04-04T12:00:00Z"
started_at: "2026-04-04T12:00:00Z"
---
```

- `max_commands: 0` means unlimited
- `active: false` is the shutdown signal — the hook allows exit and removes the file

## Sending Commands

From an external system, fire the trigger using the RemoteTrigger API:

```
POST /v1/code/triggers/<trigger_id>/run
Content-Type: application/json

{"command": "run the test suite and report results"}
```

Or using another Claude Code session with the `RemoteTrigger` tool:

```
RemoteTrigger action=run trigger_id=<id> body={"command": "deploy to staging"}
```

### Special Commands

- **`SHUTDOWN`** — gracefully ends the remote-control session (sets `active: false` and exits)

## Session Isolation

If multiple Claude Code sessions are open in the same project, only the session that created the trigger will respond to commands. The state file's `session_id` is matched against the hook's `session_id` to prevent cross-session interference.

## Limitations

- The Stop hook polls on each natural exit, not on a timer. Claude must finish its current task before it checks for the next command.
- The RemoteTrigger API requires an active Claude.ai session (OAuth in-process only).
- State file is project-scoped — one active remote-control session per project at a time.
