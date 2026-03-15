# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Primary Project

The main project is the **Claude Code Plugins Directory** at `.claude/plugins/marketplaces/claude-plugins-official/` — Anthropic's official plugin marketplace for Claude Code.

## Validation

The CI pipeline validates frontmatter in agent/skill/command `.md` files using Bun:

```bash
# Install dependencies
cd .claude/plugins/marketplaces/claude-plugins-official/.github/scripts && bun install yaml

# Validate all frontmatter files
bun .github/scripts/validate-frontmatter.ts

# Validate specific files
bun .github/scripts/validate-frontmatter.ts path/to/file.md
```

Validation runs automatically on PRs that touch `**/agents/*.md`, `**/skills/*/SKILL.md`, or `**/commands/*.md`.

## Plugin Architecture

Each plugin lives under `plugins/` (Anthropic-maintained) or `external_plugins/` (third-party) and follows this structure:

```
plugin-name/
├── .claude-plugin/plugin.json   # name, description, author (required)
├── .mcp.json                    # MCP server config (optional)
├── commands/                    # User-invoked slash commands (*.md)
├── agents/                      # Agent definitions (*.md)
├── skills/skill-name/SKILL.md   # Model-invoked skill definitions
└── README.md
```

## Frontmatter Requirements

**Commands** (`commands/*.md`): require `description` field.

**Skills** (`skills/*/SKILL.md`): require `description` or `when_to_use` field. The `description` drives when Claude auto-invokes the skill — write it with specific trigger phrases.

**Agents** (`agents/*.md`): require both `name` and `description` fields.

YAML values containing special characters (`{}[]*&#!|>%@\``) must be quoted.

## Key Distinction Between Extension Types

- **Commands**: user-triggered via `/command-name`
- **Skills**: Claude autonomously invokes based on task context matching the `description`
- **Agents**: Claude spawns these as subprocesses for complex tasks
- **MCP servers**: configured in `.mcp.json`, provide external tool integrations

## Contributing External Plugins

External plugins are submitted via the plugin directory submission form (not PRs to this repo). The `close-external-prs.yml` workflow automatically closes direct PRs from non-Anthropic contributors.
