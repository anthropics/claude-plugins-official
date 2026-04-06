---
description: Connect Neutrally persistent memory to Claude Code. Run this once to authenticate and start getting cross-session memory.
---

Run the Neutrally setup command to authenticate and configure Claude Code:

```bash
npx neutrally setup
```

This will:
1. Open your browser to the Neutrally auth page
2. Ask you to log in or create an account at neutrally.app
3. Store your credentials at `~/.neutrally/credentials.json`
4. Configure Claude Code to use persistent memory

After running this command, confirm success by checking:

```bash
npx neutrally status
```

You should see "Logged in as: [your email]" and "Claude Code: configured".

If Claude Code is shown as "not configured" after setup, this means the CLI updated `~/.claude.json` but not `~/.claude/settings.json`. In that case, the plugin hooks will still work because they read credentials directly from `~/.neutrally/credentials.json` — no additional action is needed.

To customise your capture interval (default: every 5 minutes), create or edit `~/.neutrally/plugin-config.json`:

```json
{
  "captureIntervalMinutes": 3
}
```

Valid range: 1–60 minutes.

Once connected, Neutrally will:
- Inject your project context at every session start
- Capture conversations and decisions every 5 minutes
- Restore context after /compact
- Sync with neutrally.app so your memory is available everywhere
