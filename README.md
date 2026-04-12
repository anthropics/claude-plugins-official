# axisrow's Claude Code Plugins

Personal marketplace for Claude Code plugins.

## Plugins

- **github** -- GitHub workflows via the `gh` CLI. Skills-based (no MCP server). See [`external_plugins/github/README.md`](external_plugins/github/README.md) for details.

## Installation

Add to `~/.claude/settings.json` under `extraKnownMarketplaces`:

```json
"axisrow-plugins": {
  "source": {
    "source": "github",
    "repo": "axisrow/claude-plugins-official"
  }
}
```

Then install via Claude Code: `/plugin install github@axisrow-plugins`
