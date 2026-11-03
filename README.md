# Claude Code Plugins Directory

> [!WARNING]
> **This marketplace is deprecated.** Plugins are now listed and served through the [Claude plugin directory](https://claude.ai/plugins), which you can also browse at [claude.com/marketplace](https://claude.com/marketplace).
>
> - **Submit or update a plugin:** use [claude.ai/directory/manage](https://claude.ai/directory/manage). Pull requests that add or update marketplace entries here are no longer reviewed.
> - **Install a plugin:** use the directory. The entries in this repository's `marketplace.json` remain in place, but entries that point to other repositories stay at the versions they were last pinned to.
> - **Source code:** some plugins in the directory are still built from the source in this repository, so it stays available.

A curated directory of high-quality plugins for Claude Code.

> **⚠️ Important:** Make sure you trust a plugin before installing, updating, or using it. Anthropic does not control what MCP servers, files, or other software are included in plugins and cannot verify that they will work as intended or that they won't change. See each plugin's homepage for more information.

## Structure

- **`/plugins`** - Internal plugins developed and maintained by Anthropic
- **`/external_plugins`** - Third-party plugins from partners and the community

## Installation

Install plugins from the [Claude plugin directory](https://claude.ai/plugins). This marketplace is deprecated, and installs from it (`/plugin install {plugin-name}@claude-plugins-official`) don't pick up new versions of plugins that live in other repositories.

## Contributing

### Internal Plugins

Internal plugins are developed by Anthropic team members. See `/plugins/example-plugin` for a reference implementation.

### External Plugins

Third-party plugins are no longer added to this repository. To list a plugin, submit it at [claude.ai/directory/manage](https://claude.ai/directory/manage). Plugins must meet quality and security standards for approval.

## Plugin Structure

Each plugin follows a standard structure:

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json      # Plugin metadata (required)
├── .mcp.json            # MCP server configuration (optional)
├── commands/            # Slash commands (optional)
├── agents/              # Agent definitions (optional)
├── skills/              # Skill definitions (optional)
└── README.md            # Documentation
```

## Plugin names are immutable

The `name` field in a marketplace entry is an **immutable slug**. Once a plugin has been published, its `name` must not change — users have it installed under that slug, and renaming it breaks their install with a `plugin-not-found` error.

- To change how a plugin is labeled in the UI, set or update `displayName` instead.
- If a rename is genuinely unavoidable, add an entry to the top-level `renames` map in `.claude-plugin/marketplace.json` so existing installs auto-migrate:

```json
"renames": {
  "old-name": "new-name"
}
```

The Claude Code plugin loader reads this map and transparently rewrites the old slug to the new one on the user's next sync.

## Skill-bundle plugins

When a plugin's source repository ships skills (`SKILL.md` files) without a `.claude-plugin/plugin.json` manifest, the marketplace entry can declare the skills directly using `strict: false` and an explicit `skills` array.

```json
{
  "name": "example-bundle",
  "description": "Brief description of the bundled skills.",
  "author": { "name": "Author Name" },
  "category": "development",
  "source": {
    "source": "git-subdir",
    "url": "https://github.com/example-org/sdk.git",
    "path": "packages/agent-skills",
    "ref": "main",
    "sha": "<commit sha>"
  },
  "strict": false,
  "skills": [
    "./skill-a",
    "./skill-b",
    "./skill-c"
  ],
  "homepage": "https://github.com/example-org/sdk"
}
```

Each path in `skills` is relative to `source.path` and points at a directory containing a `SKILL.md`. Paths can reach deeper than a single level — for example, `["./libA/skill-1", "./libB/skill-2"]` exposes a curated subset across multiple library subdirectories. Each skill is registered as `<plugin-name>:<skill-name>` in Claude Code.

For the underlying schema, see [Strict mode](https://code.claude.com/docs/en/plugin-marketplaces) in the marketplace documentation.

## License

Please see each linked plugin for the relevant LICENSE file.

## Documentation

For more information on developing Claude Code plugins, see the [official documentation](https://code.claude.com/docs/en/plugins).
