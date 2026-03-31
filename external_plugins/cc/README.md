# cc

[cc](https://github.com/anipotts/cc) gives Claude Code multi-session awareness. It uses hooks to track active sessions, warn about file conflicts, and share context -- so parallel sessions work together instead of stepping on each other.

## Install

```bash
claude plugin add anipotts/cc
```

## What it does

When you run multiple Claude Code sessions in the same project, cc keeps each session informed about what the others are doing. Sessions register themselves on start, broadcast file edits via hooks, and receive warnings when two sessions touch the same file.

### Example: session roster

```
/cc

Active sessions (2):
  #1  refactor-auth    12 min   editing: src/auth/provider.ts, src/auth/tokens.ts
  #2  add-search-api    3 min   editing: src/api/search.ts

No file conflicts detected.
```

## How it works

cc is **hooks-based, not MCP**. It installs `PreToolUse` and `PostToolUse` hooks that fire on file edits, maintaining a lightweight session registry on disk. No background server, no network calls, no MCP configuration required.

## Documentation

For full documentation, configuration options, and architecture details, visit [github.com/anipotts/cc](https://github.com/anipotts/cc).
