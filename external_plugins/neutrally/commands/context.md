---
description: Show what Neutrally memory context is currently active for this session.
---

Show the user what memory context Neutrally has injected for this session.

1. Show the contents of the `<neutrally-memory>` block that was injected at session start (if available in context)

2. Call `get_context` from the Neutrally MCP tools to fetch the current live user context:
   ```
   get_context()
   ```

3. Show the current session capture state by reading `~/.neutrally/sessions/` for the current session file:
   ```bash
   ls -la ~/.neutrally/sessions/ 2>/dev/null && cat ~/.neutrally/sessions/*.json 2>/dev/null | head -50
   ```

4. Report:
   - What user context is known (tech stack, projects, interests)
   - How many exchanges are pending (buffered but not yet flushed to API)
   - When the last flush to Neutrally happened
   - The configured capture interval (from `~/.neutrally/plugin-config.json` or default 5 min)

Present this clearly so the user understands what Neutrally knows about them in this session.
