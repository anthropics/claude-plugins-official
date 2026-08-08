---
name: "contextpilot:index"
description: Manually trigger full or incremental project re-indexing
---

# ContextPilot Manual Indexing

Triggers a fast AST parse and dependency graph rebuild for the current repository.

Execute:
```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/contextpilot.mjs" index
```

Options:
- `--force`: Rebuilds the entire SQLite project index from scratch, ignoring cached hashes.
- `--verbose`: Prints detailed parsing and symbol extraction logs per file.
