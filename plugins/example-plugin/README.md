# Example Plugin

A comprehensive example plugin demonstrating Claude Code extension options.

## Structure

```
example-plugin/
├── .claude-plugin/
│   └── plugin.json            # Plugin metadata
├── .mcp.json                  # MCP server configuration
├── skills/
│   ├── example-skill/
│   │   └── SKILL.md           # Model-invoked skill (contextual guidance)
│   └── example-command/
│       └── SKILL.md           # User-invoked skill (slash command)
└── commands/
    └── example-command.md     # Legacy slash command format (see note below)
```

## Extension Options

### Skills (`skills/`)

Skills are the preferred format for both model-invoked capabilities and user-invoked slash commands. Create a `SKILL.md` in a subdirectory:

**Model-invoked skill** (activated by task context):

```yaml
---
name: skill-name
description: Trigger conditions for this skill
version: 1.0.0
---
```

**User-invoked skill** (slash command — `/skill-name`):

```yaml
---
name: skill-name
description: Short description for /help
argument-hint: <arg1> [optional-arg]
allowed-tools: [Read, Glob, Grep]
---
```

### Commands (`commands/`) — legacy

> **Note:** The `commands/*.md` layout is a legacy format. It is loaded identically to `skills/<name>/SKILL.md` — the only difference is file layout. For new plugins, prefer the `skills/` directory format. This plugin keeps `commands/example-command.md` as a reference for the legacy layout.

### MCP Servers (`.mcp.json`)

Configure external tool integration via Model Context Protocol:

```json
{
  "server-name": {
    "type": "http",
    "url": "https://mcp.example.com/api"
  }
}
```

## Usage

- `/example-command [args]` - Run the example slash command
- The example skill activates based on task context
- The example MCP activates based on task context
