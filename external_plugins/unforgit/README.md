# Unforgit Claude Code Plugin

Persistent repository memory for Claude Code using Unforgit's MCP server, rules, skills, and slash commands.

## Prerequisites

Install Unforgit so the `unforgit-mcp` command is available on your PATH:

```bash
npm install -g unforgit
unforgit init --ide claude
```

The plugin does not store secrets in MCP config. If embeddings or remote sync need credentials, keep them in the repository `.env` file or your normal secret manager.

## Included

- `.mcp.json` registering the `unforgit-mcp` stdio server
- `unforgit-memory` skill with recall/save/curation rules
- Slash commands for recall, remember, health, and curation workflows

## Marketplace install

From a Claude Code session, add the Unforgit marketplace and install the plugin:

```text
/plugin marketplace add MiguelMedeiros/unforgit
/plugin install unforgit
```

If installing from a local checkout during development, install this plugin directory directly if your Claude Code build supports local plugin paths.
