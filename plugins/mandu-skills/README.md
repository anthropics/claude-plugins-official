# Mandu Skills

Development skills for [Mandu](https://github.com/konamgil/mandu) — the agent-native Bun + React fullstack framework.

## What's Included

9 skills covering the complete Mandu development lifecycle:

| Skill | Description |
|-------|-------------|
| `mandu-create-feature` | Scaffold pages, APIs, and Islands via MCP tool pipeline |
| `mandu-create-api` | Generate REST APIs with Zod contracts and ATE tests |
| `mandu-debug` | Diagnose build failures, white screens, Island issues, API errors |
| `mandu-explain` | Explain 18 Mandu concepts (Island, Filling, Guard, Contract, etc.) |
| `mandu-guard-guide` | Architecture guidance for 6 presets (FSD, Clean, Hexagonal, etc.) |
| `mandu-deploy` | Production deployment (Docker, CI/CD, nginx) — manual only |
| `mandu-slot` | Filling API reference (ctx methods, lifecycle hooks) |
| `mandu-fs-routes` | File-system routing rules and conventions |
| `mandu-hydration` | Island hydration strategies and import rules |

## Requirements

- [Mandu](https://github.com/konamgil/mandu) project
- Mandu MCP server (`@mandujs/mcp`)

## MCP Server Setup

This plugin works best with the Mandu MCP server. Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "mandu": {
      "command": "bunx",
      "args": ["@mandujs/mcp"]
    }
  }
}
```

## Also Available on npm

```bash
bun add -d @mandujs/skills
```

## License

MPL-2.0
