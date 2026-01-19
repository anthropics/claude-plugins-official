# /ccme - Claude Code May Edition Status

Show the current CCME configuration and status.

## Usage

```
/ccme
/ccme status
/ccme doctor
```

## Instructions

When the user runs `/ccme`, check and report:

1. **Config Directory**: Check if `~/.ccme/` exists
2. **Personalities**: List available personality profiles from `~/.ccme/personalities/`
3. **Memory**: Show number of tracked projects from `~/.ccme/memories/`
4. **MCP Config**: Verify `~/.ccme/mcp.json` exists
5. **Consent Status**: Check if bypass/turbo mode is enabled

Display results in a clean formatted summary. If any component is missing, suggest running `ccme setup` or `npm install -g claude-code-may-edition`.
