# Telegram forwarding hook (optional)

By default the Telegram channel only forwards **inbound** messages — when
someone messages your bot, the message lands in your Claude Code session as
a user prompt. To send Claude's responses **back** to that chat, Claude has
to call the `reply` tool explicitly. That works for short replies, but in
longer turns the user sits in silence for the whole multi-tool sequence and
gets a wall of text only at the end.

The `telegram_forward.py` hook in this directory automates the return path.
With it installed, every time Claude emits an assistant text block the hook
ships that block to the originating Telegram chat — *during* the turn (after
each tool call) and at the *end* of the turn. The user sees Claude's
narration land as it happens, not all at once at the finish line.

## Install via the skill (recommended)

```
/telegram:stream enable
```

This copies `telegram_forward.py` to `~/.claude/hooks/`, wires both
`PostToolUse` and `Stop` events in `~/.claude/settings.json`, and prints the
state. To remove:

```
/telegram:stream disable    # un-wire from settings.json (keep the script)
/telegram:stream uninstall  # un-wire AND delete the script
/telegram:stream            # status only — does nothing
```

## Install manually

If you'd rather wire it yourself:

```sh
mkdir -p ~/.claude/hooks
cp telegram_forward.py ~/.claude/hooks/
```

Then add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      { "hooks": [{ "type": "command",
                    "command": "python3 ~/.claude/hooks/telegram_forward.py" }] }
    ],
    "Stop": [
      { "hooks": [{ "type": "command",
                    "command": "python3 ~/.claude/hooks/telegram_forward.py" }] }
    ]
  }
}
```

If you already have hooks for `PostToolUse` or `Stop`, **append** to the
existing array — don't replace it. The hook is fast and idempotent; running
it alongside others is safe.

## How it works

1. The hook reads the JSONL transcript at `transcript_path` (provided by the
   hook payload).
2. Scans backwards for the most recent user row that contains
   `<channel source="plugin:telegram:telegram" chat_id="...">` — that's where
   the inbound message came in.
3. Reads the per-session high-water mark UUID from
   `~/.claude/hooks/state/telegram_forward_<session>.json`.
4. Collects every assistant text block emitted *after* that UUID (or after
   the user message, if first fire).
5. Posts those blocks to Telegram via the Bot API, chunked at 4000 chars.
6. Writes the new high-water UUID atomically.

PostToolUse fires after each tool result; Stop fires once at end-of-turn.
Both share the same state file so nothing is sent twice.

## Configuration

| Env var                     | Default | Purpose |
| --------------------------- | ------- | ------- |
| `TELEGRAM_FORWARD_PREFIX`   | (empty) | String prepended to each Telegram message — e.g. `[claude]` to distinguish model output in shared chats. |
| `TELEGRAM_FORWARD_CHUNK`    | `4000`  | Soft byte cap per Telegram message. Telegram's hard cap is 4096; default leaves room for a prefix. |

The bot token comes from `~/.claude/channels/telegram/.env` (same file the
MCP server reads). The hook never re-asks for it.

## Debugging

- **Log:** `~/.claude/hooks/state/telegram_forward.log` — every fire writes
  one or two lines: which event fired, what was found, and what was sent.
- **Per-session state:** `~/.claude/hooks/state/telegram_forward_<id>.json` —
  the high-water UUID of the last shipped assistant message.
- **Smoke test:** send a message to your bot, watch the log. You should see
  `FIRED event=PostToolUse ...` lines after each tool call, then a
  `FIRED event=Stop ...` at end-of-turn.
- **Common failure modes:**
  - `no TELEGRAM_BOT_TOKEN in env file` — run `/telegram:configure` first.
  - `no telegram channel tag in any prior user msg` — the turn wasn't
    triggered by Telegram (you typed in the terminal). Hook correctly
    no-ops.
  - Duplicate sends across a turn — most likely a stale state file. Delete
    `~/.claude/hooks/state/telegram_forward_<session>.json` and retry.

## License

Apache-2.0, same as the rest of the plugin.
