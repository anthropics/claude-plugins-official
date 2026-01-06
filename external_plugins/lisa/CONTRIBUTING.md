# Contributing to Lisa

First off, thanks for taking the time to contribute!

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates.

When creating a bug report, include:

- **Clear title** describing the issue
- **Steps to reproduce** the behavior
- **Expected behavior** vs what actually happened
- **Claude Code version** (`claude --version`)
- **OS and version**
- **Relevant logs** from `.claude/lisa-loop.log` if applicable

### Suggesting Features

Feature suggestions are welcome! Please:

- Check if the feature was already suggested
- Describe the use case clearly
- Explain how it aligns with Lisa's philosophy (observable, safe, intelligent loops)

### Pull Requests

1. Fork the repo and create your branch from `main`
2. Make your changes
3. Test your changes locally with `claude --plugin-dir .`
4. Update documentation if needed
5. Submit a PR with a clear description

## Development Setup

```bash
# Clone your fork
git clone git@github.com:YOUR_USERNAME/lisa-plugin.git
cd lisa-plugin

# Test locally
claude --plugin-dir .

# Try a command
/lisa --help
```

## Code Style

- Shell scripts: Use `shellcheck` for linting
- Markdown: Keep lines under 100 characters when practical
- Commit messages: Use conventional commits (`feat:`, `fix:`, `docs:`, etc.)

## Plugin Structure

```
lisa-plugin/
├── .claude-plugin/
│   ├── plugin.json           # Plugin manifest
│   └── marketplace.json      # Marketplace catalog
├── commands/                 # Slash commands (Markdown)
├── hooks/                    # Event hooks
├── scripts/                  # Shell scripts
├── skills/                   # Agent skills
└── examples/                 # Example prompts
```

## Testing Changes

### Manual Testing

```bash
# Start Claude with your local plugin
claude --plugin-dir /path/to/lisa-plugin

# Test commands
/lisa-status
/lisa --help
/lisa "Test prompt" --max-iterations 3
```

### Verify Hook Behavior

```bash
# Check hook syntax
bash -n hooks/stop-hook.sh

# Check script syntax
bash -n scripts/setup-loop.sh
```

## Philosophy

Lisa is an evolution of the Ralph Wiggum technique. When contributing, keep these principles:

1. **Preserve Ralph's soul** - Simple, iterative, persistent
2. **Add observability** - Log what matters
3. **Ensure safety** - Max iterations, clean exits
4. **Keep it simple** - Complexity in files, not prompts

## Questions?

Open an issue with the `question` label.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
