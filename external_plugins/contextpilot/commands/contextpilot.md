---
name: contextpilot
description: Inspect ContextPilot status, index statistics, token savings, and context confidence
---

# ContextPilot Status & Inspection

Run the ContextPilot diagnostic status inspector to see the current project index state, last prompt context injection details, active files, and confidence metrics.

Execute:
```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/contextpilot.mjs" status
```

This output displays:
- Project root path & database status
- Number of indexed files, symbols, imports, and dependency edges
- Last prompt classification, selected candidate files, and token usage
- Context confidence score and current routing health
