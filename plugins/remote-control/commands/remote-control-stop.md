---
description: "Stop the active remote-control session and clean up the trigger"
allowed-tools: ["Bash", "RemoteTrigger"]
hide-from-slash-command-tool: "true"
---

# Remote Control Stop

Stop the active remote-control session.

```!
cat .claude/remote-control.local.md 2>/dev/null | sed -n '/^---$/,/^---$/{ /^---$/d; p; }' | grep '^trigger_id:' | sed 's/trigger_id: *//' || echo ""
```

Using the trigger ID from the state file above:

1. If the trigger ID is not empty, call `RemoteTrigger` with:
   - action: `update`
   - trigger_id: `<trigger_id>`
   - body: `{"active": false}`

2. Set the session to inactive in the state file:
   ```bash
   sed -i 's/^active: .*/active: false/' .claude/remote-control.local.md
   ```

3. Remove the state file:
   ```bash
   rm -f .claude/remote-control.local.md
   ```

4. Report to the user:
   ```
   🛑 Remote control session stopped.
      Trigger deactivated. This session will exit normally on next stop.
   ```

If the state file does not exist, report: "No active remote-control session found."
