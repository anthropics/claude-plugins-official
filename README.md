# Claude Code Plugins Directory

A curated collection of plugins for Claude Code.

⚠️ **Note:** Only install plugins you trust. Anthropic does not control third‑party MCP servers, files, or software included in plugins. Functionality and security are the responsibility of each plugin author. Refer to the plugin’s homepage for details.

---

## Structure
- `/plugins` – Official plugins maintained by Anthropic  
- `/external_plugins` – Community and partner plugins  

---

## Installation
Plugins can be installed directly via Claude Code:

```
/plugin install {plugin-name}@claude-plugins-official
```

Or browse and install from **/plugin > Discover**.

---

## Contributing
- **Internal Plugins**: Developed by Anthropic. See `/plugins/example-plugin` for a reference.  
- **External Plugins**: Community submissions must meet quality and security standards. Submit via the plugin directory form.

---

## Plugin Layout
Each plugin follows this standard structure:

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json      # Metadata (required)
├── .mcp.json            # MCP server config (optional)
├── commands/            # Slash commands (optional)
├── agents/              # Agent definitions (optional)
├── skills/              # Skill definitions (optional)
└── README.md            # Documentation
```

---

## License
Refer to each plugin’s LICENSE file for terms.

---

## Documentation
For development guidance, see the official Claude Code plugin documentation.
