# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is **arizonabay's fork** of the official Anthropic Claude Code Plugins Directory. This fork serves as an internal plugin repository for arizonabay, allowing customization to match our preferences and workflows. We sync regularly with the upstream repo to stay updated with Anthropic's changes.

All issues, PRs, and development work here are for modifying and extending our fork - not for contributing upstream.

## Repository Structure

```
/plugins           # Internal plugins (originally Anthropic-developed, plus our additions)
/external_plugins  # Third-party plugins from partners
```

Each plugin follows this standard structure:
```
plugin-name/
├── .claude-plugin/
│   └── plugin.json      # Plugin metadata (required)
├── .mcp.json            # MCP server configuration (optional)
├── commands/            # Slash commands as .md files (optional)
├── agents/              # Agent definitions as .md files (optional)
├── skills/              # Skills with SKILL.md files (optional)
├── hooks/               # Event hooks with hooks.json (optional)
└── README.md
```

## Plugin Component Patterns

### plugin.json (required)
```json
{
  "name": "plugin-name",
  "description": "Plugin description",
  "author": { "name": "Author", "email": "email@example.com" }
}
```

### Commands (commands/*.md)
Slash commands with YAML frontmatter:
```yaml
---
description: Short description for /help
argument-hint: <arg1> [optional-arg]
allowed-tools: [Read, Glob, Grep, Bash]
---
```
Use `$ARGUMENTS` to access user input. Use `!` backtick syntax for dynamic context (e.g., `!`git status``).

### Agents (agents/*.md)
Autonomous subagents with frontmatter:
```yaml
---
name: agent-name
description: When to invoke this agent (include trigger conditions)
tools: Glob, Grep, Read, Bash
model: sonnet
color: green
---
```

### Skills (skills/*/SKILL.md)
Model-invoked capabilities with frontmatter:
```yaml
---
name: skill-name
description: Trigger conditions - describe when Claude should use this skill
version: 1.0.0
---
```

### Hooks (hooks/hooks.json)
Event-driven automation using `${CLAUDE_PLUGIN_ROOT}` for portable paths:
```json
{
  "hooks": {
    "PreToolUse": [{ "hooks": [{ "type": "command", "command": "...", "timeout": 10 }] }]
  }
}
```
Supported events: PreToolUse, PostToolUse, Stop, SubagentStop, SessionStart, SessionEnd, UserPromptSubmit, PreCompact, Notification.

### MCP Servers (.mcp.json)
Model Context Protocol configuration:
```json
{
  "server-name": { "type": "http", "url": "https://mcp.example.com/api" }
}
```
Types: stdio (local), SSE (hosted/OAuth), HTTP (REST), WebSocket (real-time).

## Development

### Testing a Plugin Locally
```bash
cc --plugin-dir /path/to/plugin-name
```

### Debugging
```bash
claude --debug
```

### Reference Implementation
See `plugins/example-plugin/` for a complete reference demonstrating all component types.

### Plugin Development Toolkit
The `plugins/plugin-dev/` plugin provides seven specialized skills for plugin development: hook-development, mcp-integration, plugin-structure, plugin-settings, command-development, agent-development, and skill-development.
