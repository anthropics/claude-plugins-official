# Claude Code Harness

A development harness for solo developers (VibeCoder) to handle full-cycle development with the **Plan → Work → Review** workflow.

## Features

- **Plan → Work → Review Cycle**: Structured workflow with `/plan-with-agent`, `/work`, `/harness-review`
- **Safety Guardrails**: PreToolUse hooks protect sensitive paths (`.git/`, `.env`, secrets) and block dangerous commands
- **SSOT Memory**: Persistent decisions and patterns in `.claude/memory/`
- **21 Skills**: Auto-activated capabilities for auth, deploy, UI, CI/CD, and more
- **6 Specialized Agents**: Code review, CI/CD fixing, error recovery, project analysis
- **Parallel Execution**: Multiple independent tasks run concurrently
- **i18n Support**: Japanese/English language selection

## Installation

```bash
/plugin install claude-code-harness@claude-plugin-directory
```

Or clone directly:

```bash
git clone https://github.com/Chachamaru127/claude-code-harness.git
claude --plugin-dir /path/to/claude-code-harness
```

## Quick Start

```bash
/harness-init      # Initialize project
/plan-with-agent   # Plan your tasks
/work              # Execute tasks (parallel when possible)
/harness-review    # Review changes
```

## Documentation

- [Full Documentation](https://github.com/Chachamaru127/claude-code-harness)
- [CHANGELOG](https://github.com/Chachamaru127/claude-code-harness/blob/main/CHANGELOG.md)

## License

MIT License - See [LICENSE](https://github.com/Chachamaru127/claude-code-harness/blob/main/LICENSE.md)

## Acknowledgements

- Hierarchical skill structure: Implemented based on feedback from [AI Masao](https://note.com/masa_wunder)
