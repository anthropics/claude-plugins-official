# Claude Code May Edition

**Personality Persistence + Floating Memory + Cognitive Exoskeleton**

A developer-friendly wrapper for Claude Code that adds persistent user preferences, project-aware context, and optional turbo mode.

## Features

- **Personality Persistence** - Remember user preferences, corrections, and learned behaviors across sessions
- **Floating Memory** - Project-aware context that prioritizes relevant information using float scores
- **MCP Integration** - Pre-configured Model Context Protocol servers for memory and filesystem
- **Turbo Mode** - Optional full autonomous mode with Opus model

## Installation

```bash
# Via Claude Code plugin system
/plugin install claude-code-may-edition@claude-plugins-official

# Or via npm for CLI usage
npm install -g claude-code-may-edition
ccme setup
```

## Quick Start

```bash
# Launch with memory + personality
ccme launch

# Create a personality profile
ccme personality create may
ccme personality trait may "Prefers TypeScript"

# Add project memory
ccme memory init ./myproject
ccme memory add "AuthService" "module" "Handles JWT"

# Full autonomous turbo mode (Opus)
ccme turbo
```

## How It Works

The plugin injects context via CLAUDE.md generation:

1. **Personality** - User preferences stored in `~/.ccme/personalities/`
2. **Memory** - Project entities stored in `~/.ccme/memories/`
3. **Float Score** - `(priority × 0.4) + (access × 0.3) + (recency × 0.3)`
4. **Context** - Auto-generated CLAUDE.md with highest-scoring entities

## Links

- [GitHub Repository](https://github.com/AgewellEPM/claude-code-may-edition)
- [npm Package](https://www.npmjs.com/package/claude-code-may-edition)

## License

MIT - AgewellEPM
