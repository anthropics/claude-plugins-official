# Open-Crab 🦀

Self-maintaining system toolkit for Claude Code. Set up the ecosystem and it runs itself.

## Commands

| Command | Description | Daily |
|---------|-------------|-------|
| `/daily` | Run all `daily: true` commands, output summary table, log results | - |
| `/disk-clean` | Scan current directory for large files and cleanable caches | No |
| `/security` | System security scan (ports, users, services, sensitive files) | Yes |
| `/evolve` | Self-review all commands, check scan history, fix issues | No |

## How it works

```
/daily ──→ scans commands with `daily: true` ──→ runs them ──→ logs to scan_log.md
              │
/evolve ──→ reviews all commands ──→ reads scan_log.md
              │                         │
              ├─ fixes outdated commands │
              ├─ detects OS compatibility │
              └─ checks recurring errors  │
                                          ▼
                               self-healing loop
```

## Install

```
/install Open-Crab
```

Or clone manually:

```bash
git clone https://github.com/jay2zxy/Open-Crab.git ~/.claude/plugins/Open-Crab
```

## Requirements

- Claude Code CLI
- Works on Windows / macOS / Linux

## Customization

- Add `daily: true` to any command's frontmatter to include it in daily patrol
- Add new commands to `commands/` and `/evolve` will automatically review them
- Scan logs are stored in the plugin directory (`scan_log.md`, gitignored)
