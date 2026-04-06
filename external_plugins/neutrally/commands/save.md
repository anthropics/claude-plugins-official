---
description: Manually save a decision, convention, or important note to Neutrally memory.
---

Save the user's note to Neutrally memory using the `save_memory` MCP tool.

Ask the user what they want to save if not already clear, then call:

```
save_memory({
  type: "decision" | "preference" | "fact" | "project" | "note",
  title: "<concise title>",
  content: "<the full note or decision>"
})
```

**Choosing the type:**
- `decision` — an architectural or product decision ("use server actions for mutations")
- `preference` — a personal preference or working style ("always use TypeScript strict mode")
- `fact` — a factual piece of project state ("the API uses Bearer token auth via ntrl_ prefix")
- `project` — project-level context ("neutrally is a Next.js 16 app with Supabase and Stripe")
- `note` — anything that doesn't fit the above

After saving, confirm with: "Saved to your Neutrally memory."

The automatic capture hook also saves conversations every 5 minutes — use this command for things you want to save *right now* without waiting for the next capture cycle.
