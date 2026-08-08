---
name: "contextpilot:explain"
description: Explain why each file and context item was selected for a prompt
---

# ContextPilot Explainability

Explain why specific files and symbols were routed for your query or prompt.

Execute:
```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/contextpilot.mjs" explain "$ARGUMENTS"
```

This breaks down:
- Candidate relevance scores and individual weights
- Semantic keyword matches, symbol matches, and path matches
- Dependency graph hops (callers, callees, imports)
- Related test association reasons
- Token budget allocation breakdown
