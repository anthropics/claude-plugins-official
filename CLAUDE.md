# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the **Claude Code Plugins Official Marketplace** (`claude-plugins-official`) -- a curated directory of plugins for Claude Code, maintained by Anthropic. It contains both internal (Anthropic-developed) plugins and external (third-party) plugins.

The repo is content-driven: plugins are defined via Markdown files with YAML frontmatter, JSON manifests, and MCP configurations. There is no traditional build step or application runtime.

## Commands

### Validate frontmatter (CI check)
```bash
cd .github/scripts && bun install yaml
bun .github/scripts/validate-frontmatter.ts                    # scan all files
bun .github/scripts/validate-frontmatter.ts file1.md file2.md  # validate specific files
```

This runs automatically on PRs that modify files in `**/agents/*.md`, `**/skills/*/SKILL.md`, or `**/commands/*.md`.

### Install a plugin (for testing)
```
/plugin install {plugin-name}@claude-plugin-directory
```

## Architecture

### Directory Layout

- `plugins/` -- Internal plugins developed by Anthropic
- `external_plugins/` -- Third-party plugins from partners and community
- `.claude-plugin/marketplace.json` -- Central registry listing all plugins with metadata, categories, and LSP server configs
- `.github/scripts/validate-frontmatter.ts` -- Bun/TypeScript validation script for CI
- `plugins/example-plugin/` -- Reference implementation showing all extension types

### Plugin Structure

Every plugin follows this layout:
```
plugin-name/
├── .claude-plugin/
│   └── plugin.json        # Plugin metadata (required: name, description, author)
├── .mcp.json              # MCP server config (optional)
├── commands/              # Slash commands as .md files (optional)
├── agents/                # Agent definitions as .md files (optional)
├── skills/                # Skill definitions in subdirs (optional)
│   └── skill-name/
│       └── SKILL.md
└── README.md
```

### Plugin Component Types

**Commands** (`commands/*.md`) -- User-invoked via `/command-name`. Required frontmatter: `description`. Optional: `argument-hint`, `allowed-tools`, `model`. Use `$ARGUMENTS` in body to reference user input.

**Skills** (`skills/*/SKILL.md`) -- Model-invoked capabilities that Claude activates based on task context. Required frontmatter: `description` (or `when_to_use`). The description field defines trigger conditions with specific phrases and keywords.

**Agents** (`agents/*.md`) -- Autonomous agents for multi-phase workflows. Required frontmatter: `name`, `description`.

**MCP Servers** (`.mcp.json`) -- External tool integration via Model Context Protocol. Supports types: `http`, `stdio`, `sse`.

### Marketplace Registry

`.claude-plugin/marketplace.json` is the central index. Each plugin entry includes `name`, `description`, `source` (path or URL), `category`, and optionally `lspServers` for language server plugins. LSP plugins define `command`, `args`, and `extensionToLanguage` mappings.

### External Contributions

External PRs are automatically closed by the `close-external-prs.yml` workflow. Third-party plugins must be submitted through the plugin directory submission form. Only Anthropic team members can merge PRs.

## Frontmatter Validation Rules

The CI validator checks:
- **Agents**: Must have `name` (string) and `description` (string)
- **Skills**: Must have `description` or `when_to_use`
- **Commands**: Must have `description` (string)

YAML values containing special characters (`{}[]&#!|>%@\``) are auto-quoted during validation. Files without valid frontmatter (delimited by `---`) fail validation.
