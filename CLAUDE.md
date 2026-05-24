# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the official Claude Code plugin marketplace — a curated directory of plugins maintained by Anthropic. The two top-level directories are:

- `plugins/` — Internal Anthropic-maintained plugins
- `external_plugins/` — Third-party partner/community plugins

The central plugin registry is `.claude-plugin/marketplace.json`. It must stay alphabetically sorted by plugin `name`.

## Validation Commands

All validation scripts require [Bun](https://bun.sh) and are run from the repo root:

```bash
# Validate YAML frontmatter in agent/skill/command .md files (specific files)
bun .github/scripts/validate-frontmatter.ts path/to/file.md

# Validate .claude-plugin/marketplace.json structure and sort order
bun .github/scripts/validate-marketplace.ts .claude-plugin/marketplace.json
bun .github/scripts/check-marketplace-sorted.ts

# Auto-fix marketplace.json sort order
bun .github/scripts/check-marketplace-sorted.ts --fix

# Install the yaml dependency needed by validate-frontmatter.ts
cd .github/scripts && bun install yaml
```

CI runs `validate-frontmatter.ts` on every PR that touches agent/skill/command `.md` files, and `validate-marketplace.ts` + `check-marketplace-sorted.ts` on every PR that touches `.claude-plugin/marketplace.json`.

## Plugin Structure

Every plugin follows this layout (only create directories for components the plugin actually uses):

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json       # Required: name (kebab-case), plus optional metadata
├── commands/             # Slash commands: <name>.md files
├── agents/               # Subagent definitions: <name>.md files
├── skills/               # Skills: each in its own subdirectory
│   └── skill-name/
│       └── SKILL.md
├── hooks/
│   └── hooks.json        # Hook event configuration
├── .mcp.json             # MCP server definitions
└── README.md
```

Component directories (`commands/`, `agents/`, `skills/`, `hooks/`) must be at the plugin root, not inside `.claude-plugin/`.

## Component Formats

### Skills (preferred) — `skills/<name>/SKILL.md`

```yaml
---
name: skill-name
description: Trigger phrases and conditions — this is how Claude decides when to load the skill
version: 1.0.0
---
```

Model-invoked automatically based on task context matching the description.

### User-invoked slash commands — also `skills/<name>/SKILL.md`

```yaml
---
name: command-name
description: Short description shown in /help
argument-hint: <required-arg> [optional-arg]
allowed-tools: [Read, Glob, Grep]
---
```

The `argument-hint` field distinguishes user-invoked commands from model-invoked skills. The legacy `commands/<name>.md` layout is identical in behavior — prefer `skills/` for new plugins.

### Agents — `agents/<name>.md`

```yaml
---
name: agent-name           # kebab-case, 3–50 chars
description: |             # Must include <example> blocks for reliable triggering
  Use this agent when...
  <example>...</example>
model: inherit             # inherit | sonnet | opus | haiku
color: yellow              # blue | cyan | green | yellow | magenta | red
tools: ["Read", "Grep"]
---
```

### Hooks — `hooks/hooks.json`

Two types: `"type": "prompt"` (LLM-driven, recommended for context-aware decisions) and `"type": "command"` (bash, for deterministic checks). Available events: `PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`, `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `PreCompact`, `Notification`.

## Portable Paths

Use `${CLAUDE_PLUGIN_ROOT}` for all intra-plugin path references in hooks and MCP server configs — never hardcode absolute paths or use `~/` or relative `./` paths.

## marketplace.json

When adding a new plugin entry to `.claude-plugin/marketplace.json`, each entry requires:

```json
{
  "name": "plugin-name",
  "description": "...",
  "source": { ... }
}
```

The `plugins` array must remain alphabetically sorted by `name` (case-insensitive). Run `bun .github/scripts/check-marketplace-sorted.ts --fix` after inserting entries.

External plugins pinned to a git SHA are bumped automatically weekly by the `bump-plugin-shas` workflow via `discover_bumps.py`.
