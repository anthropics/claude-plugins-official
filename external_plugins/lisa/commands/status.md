---
description: "Check current loop iteration, max limit, and completion promise"
hide-from-slash-command-tool: "true"
---

# Lisa Status

Check the current state of a Lisa loop.

To check Lisa loop status:

1. Check if `.claude/lisa-loop.local.md` exists using Bash: `test -f .claude/lisa-loop.local.md && echo "ACTIVE" || echo "NO_LOOP"`

2. **If NO_LOOP**: Say "No active Lisa loop."

3. **If ACTIVE**:
   - Read `.claude/lisa-loop.local.md` to get the full state
   - Parse the YAML frontmatter to extract:
     - `iteration`: current iteration number
     - `max_iterations`: limit (0 = unlimited)
     - `completion_promise`: the promise text (or null)
     - `started_at`: when the loop started
   - Display a formatted status report:

   ```
   🔄 Lisa Loop Status
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Iteration:    {iteration}
   Max:          {max_iterations or "unlimited"}
   Promise:      {completion_promise or "none"}
   Started:      {started_at}
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Prompt:
   {prompt content after the YAML frontmatter}
   ```

4. If user asks for more detail, also show the raw file content.
