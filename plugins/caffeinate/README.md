# Caffeinate

A Claude Code plugin that blocks `sleep` commands and reminds Claude to use background tasks instead.

## Purpose

When Claude uses `sleep` commands in Bash, it blocks the session unnecessarily. This plugin intercepts these commands and suggests using proper async patterns like:

- `run_in_background: true` parameter for long-running commands
- Polling for conditions instead of sleeping
- Proper async/background task patterns

## Installation

```bash
# From the plugin directory
claude --plugin-dir /path/to/caffeinate
```

Or copy to your project's `.claude-plugin/` directory.

## What Gets Blocked

| Command | Blocked? | Reason |
|---------|----------|--------|
| `sleep 5` | Yes | Direct sleep command |
| `sleep $TIMEOUT` | Yes | Sleep with variable |
| `echo "test" && sleep 5` | Yes | Sleep after separator, outside quotes |
| `cmd; sleep 10` | Yes | Sleep after semicolon |
| `echo "sleep 8 hours"` | No | Sleep is inside quotes (not a command) |
| `echo "foo && sleep 5"` | No | Entire sleep pattern is in a string |

## How It Works

The plugin uses a `PreToolUse` hook on the `Bash` tool to:

1. Check if commands start with `sleep`
2. Detect `sleep` after command separators (`&&`, `||`, `;`, `|`)
3. Use quote-counting to avoid false positives when `sleep` appears inside strings

## Alternatives to Sleep

Instead of:
```bash
sleep 5 && check_status
```

Use background execution:
```bash
# Run in background with run_in_background: true
long_running_command
```

Or poll for conditions:
```bash
# Poll for a file to exist
while [ ! -f /tmp/ready ]; do :; done
```
