# Creet

**Skill navigator for Claude Code.** Scans all installed plugins (Skills, MCP tools, LSP servers), recommends the best match for your task in 8 languages, and executes it.

## Usage

```
/c <what you want to do>
```

| You type | What happens |
| --- | --- |
| `/c build a login page` | Recommends your best auth + frontend skills |
| `/c review my PR` | Recommends your code review skill |
| `/c deploy to production` | Recommends your deployment skill |
| `/c` (no args) | Shows full skill inventory |

## How It Works

1. **Scan** - Detects all installed skills, MCP tools, and LSP servers
2. **Recommend** - Matches your request to the best skill(s)
3. **Execute** - Runs the chosen skill immediately
4. **Discover** - If no match, suggests installable plugins from registry

## Features

- Auto-scans all installed plugins at session start
- Detects Skills, MCP tools, and LSP servers
- Zero hardcoded dependencies - works with any plugin combination
- Dynamic keyword matching from scanner-extracted triggers
- Responds in your language (EN, KO, JA, ZH, ES, FR, DE, IT)
- Session memory - remembers your most used skills

## Requirements

- Claude Code v1.0.33+

## Links

- [GitHub Repository](https://github.com/Creeta-creet/creet)
- [Changelog](https://github.com/Creeta-creet/creet/blob/master/CHANGELOG.md)

## License

MIT - [Creeta](https://www.creeta.com)
