# Raven

> Enterprise AI coding discipline platform for Claude Code.
> Built by [Giggso Inc](https://github.com/giggsoinc). MIT License.

*Wit beyond measure — for your codebase.*

## What It Does

Enforces consistent coding standards, stack discipline, and production safety across distributed dev teams — without killing developer productivity.

| During coding | At git commit | At CI/CD |
|---|---|---|
| Agents advise | Pre-commit hook blocks | Pipeline validates |
| Skills guide | CVE check fires | Last safety net |

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/giggsoinc/raven/main/install.sh | bash
cd YourProject && raven-setup
```

## Slash Commands

| Command | What it does |
|---|---|
| `/raven-init` | Initialize Raven for a new project |
| `/raven-scan` | Run CVE + secrets scan |
| `/raven-review` | Architecture and style review |
| `/raven-debug` | Structured debug session |
| `/raven-scaffold` | Scaffold a new component |
| `/raven-approve` | Trigger approval flow |
| `/raven-incident` | Open an incident |

## Components

- **Core Agents** — manifest-checker, style-enforcer, stack-validator, architecture-guard, claude-mem
- **Pre-commit hook** — framework detection, secret scan, CVE three-tier check, style gate
- **MCP server** — 5 tools: manifest read/write, audit log, token tracker, approval flow
- **Skills** — progressive disclosure (~100 tokens at startup)

## Also Install

For production protection (hard-blocks on destructive operations):

```bash
claude plugin install raven-guard@claude-plugins-official
```

## Source

[github.com/giggsoinc/raven](https://github.com/giggsoinc/raven)
