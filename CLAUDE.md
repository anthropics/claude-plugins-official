# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Validation

This repo uses [Bun](https://bun.sh) to run the frontmatter validation script. Install dependencies first:

```bash
cd .github/scripts && bun install yaml
```

Validate all frontmatter files in the repo:

```bash
bun .github/scripts/validate-frontmatter.ts
```

Validate specific files:

```bash
bun .github/scripts/validate-frontmatter.ts plugins/my-plugin/skills/my-skill/SKILL.md
```

Validate from a specific directory:

```bash
bun .github/scripts/validate-frontmatter.ts plugins/my-plugin
```

The CI workflow (`validate-frontmatter.yml`) runs validation only on changed files in pull requests. Exit code 1 means validation errors; exit code 2 means a fatal script error.

## Plugin Structure

Each plugin lives under `plugins/` (Anthropic-maintained) or `external_plugins/` (third-party). Every plugin requires:

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json       # Required: name, description, author
├── .mcp.json             # Optional: MCP server configuration
├── agents/               # Optional: agent .md files
├── skills/               # Optional: one subdirectory per skill, each with SKILL.md
│   └── skill-name/
│       └── SKILL.md
├── commands/             # Optional: slash command .md files (legacy format)
└── README.md
```

## Frontmatter Requirements

Frontmatter is validated per file type by `.github/scripts/validate-frontmatter.ts`:

- **Skills** (`skills/*/SKILL.md`): requires `description` or `when_to_use`
- **Agents** (`agents/*.md`): requires `name` and `description`
- **Commands** (`commands/*.md`): requires `description`

File type is detected by path pattern. Importantly, `agents/` or `commands/` directories nested *inside* a skill's content directory (e.g. `skills/foo/agents/`) are treated as skill content, not as plugin-level agent definitions.

YAML special characters (`{}[]` etc.) in frontmatter values should be quoted. The validator auto-quotes unquoted values containing these characters, but it's cleaner to quote them in source.

## Architecture Notes

- `plugins/example-plugin` is the canonical reference implementation for all extension types (commands, agents, skills, hooks, MCP servers).
- `plugins/plugin-dev` contains the toolkit for developing new plugins.
- Skills are the primary extension mechanism; `commands/` is considered legacy.
- External plugins are submitted via the plugin directory submission form and must pass quality/security review before inclusion.
