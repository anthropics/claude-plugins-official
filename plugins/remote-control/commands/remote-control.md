---
description: "Start a remote-control session — creates a RemoteTrigger so external systems can send commands to this Claude Code session"
argument-hint: "[--name NAME] [--max-commands N]"
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/setup-remote-control.sh:*)", "RemoteTrigger", "Read", "Write", "Bash"]
hide-from-slash-command-tool: "true"
---

# Remote Control Setup

Run the setup script to initialize state, then create the RemoteTrigger:

```!
"${CLAUDE_PLUGIN_ROOT}/scripts/setup-remote-control.sh" $ARGUMENTS
```

Now create the actual RemoteTrigger using the RemoteTrigger tool:

1. Call `RemoteTrigger` with:
   - action: `create`
   - body: `{"name": "<trigger_name from script output>", "description": "Remote control trigger for this Claude Code session"}`

2. From the API response, extract the `id` field (this is the `trigger_id`).

3. Update the state file `.claude/remote-control.local.md` — replace the `PENDING` placeholder on the `trigger_id:` line with the real trigger ID returned by the API:
   ```bash
   sed -i "s/^trigger_id: PENDING/trigger_id: <REAL_TRIGGER_ID>/" .claude/remote-control.local.md
   ```

4. Display a summary to the user:
   ```
   ✅ Remote control session active!

   Trigger ID:   <trigger_id>
   Trigger Name: <trigger_name>
   Max commands: <max_commands or "unlimited">

   External systems can now send commands to this session using:
     RemoteTrigger action=run trigger_id=<trigger_id> body={"command": "your task here"}

   Special commands:
     "SHUTDOWN" — gracefully ends the remote-control session

   To stop: /remote-control-stop
   To check status: /remote-control-status
   To monitor state: cat .claude/remote-control.local.md
   ```

The stop hook is now active. After each response, Claude will automatically poll for pending commands from this trigger.
