# Handshake

Multi-agent swarm orchestration for parallel development with Claude Code.

## Overview

Handshake transforms Claude Code from a single assistant into a coordinated development team. Launch multiple Claude agents simultaneously, each working on different parts of your codebase.

| Role | Description |
|------|-------------|
| **Orchestrator** | You — plans work and assigns tasks |
| **Crews** | Groups of 1-4 agents working in parallel |
| **Agents** | Individual Claude instances with specific assignments |

## Features

- **Cross-Platform** — macOS (iTerm), Linux (tmux), Windows (WSL + tmux)
- **Flexible Crew Sizes** — Launch 1-4 agents per crew
- **Model Tiers** — Choose haiku (cheap), sonnet (balanced), or opus (powerful)
- **Task Coordination** — Assign, track, and manage work across agents
- **Daemon Orchestration** — Background service for crew lifecycle management

## Installation

```bash
# Install plugin
claude plugin install handshake@claude-plugins-official

# Install daemon (macOS)
brew tap leepickdev/tap
brew install handshake
brew services start handshake
```

## Quick Start

```bash
# Initialize in your project
handshake-init

# Launch a crew
.handshake/bin/hive-client crew launch haack --spaces 2 --model haiku

# Assign tasks
.handshake/bin/hive-client task kai "Implement user authentication"
.handshake/bin/hive-client task neo "Create API endpoints"
```

Or use the bootstrap skill:
```
/handshake:hive-bootstrap
```

## Skills

| Skill | Description |
|-------|-------------|
| `hive-bootstrap` | Initialize swarm infrastructure with guided setup |
| `hive-orchestrator` | Manage agents as the orchestrator |
| `hive-agent` | Protocol for individual agents in the swarm |
| `api-handshake` | API contract negotiation between agents |

## Requirements

- **macOS**: Python 3.9+, iTerm2 or tmux
- **Linux/WSL**: Python 3.9+, tmux

## Documentation

- [GitHub Repository](https://github.com/leepickdev/handshake)
- [Daemon API Reference](https://github.com/leepickdev/handshake/blob/main/DAEMON_API_ENDPOINTS.md)

## License

MIT
