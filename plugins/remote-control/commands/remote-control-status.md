---
description: "Show status of the active remote-control session and trigger details"
allowed-tools: ["Bash", "RemoteTrigger"]
hide-from-slash-command-tool: "true"
---

# Remote Control Status

Show the current remote-control session status.

```!
if [[ -f .claude/remote-control.local.md ]]; then
  echo "STATE_FILE_EXISTS=true"
  cat .claude/remote-control.local.md
else
  echo "STATE_FILE_EXISTS=false"
fi
```

Based on the output above:

**If STATE_FILE_EXISTS=false:**
- Report: "No active remote-control session. Run `/remote-control` to start one."
- Stop here.

**If STATE_FILE_EXISTS=true:**

1. Parse the state file to extract: `active`, `trigger_id`, `trigger_name`, `max_commands`, `commands_executed`, `last_poll_at`, `started_at`.

2. Call `RemoteTrigger` with:
   - action: `get`
   - trigger_id: `<trigger_id from state file>`

3. Display a status summary combining local state and API data:
   ```
   🔌 Remote Control Session Status

   Local State:
     Active:            <active>
     Trigger ID:        <trigger_id>
     Trigger Name:      <trigger_name>
     Commands executed: <commands_executed> / <max_commands or "unlimited">
     Started at:        <started_at>
     Last polled:       <last_poll_at>

   API Status:
     <relevant fields from RemoteTrigger get response>

   To send a command from an external system:
     RemoteTrigger action=run trigger_id=<trigger_id> body={"command": "your task"}

   To stop: /remote-control-stop
   ```
