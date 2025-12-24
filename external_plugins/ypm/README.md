# YPM (Your Project Manager)

> Multi-project progress tracking system powered by Claude Code

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

---

## What is YPM?

YPM is a project management tool that automatically tracks the status of multiple projects in a specified directory.

**Key Features**:
- Automatic information collection from Git history and documentation
- Centralized management of all projects in a single file (`PROJECT_STATUS.md`)
- Progress visualization with multiple metrics (Phase, Implementation, Testing, Documentation)
- Next task identification for each project
- Flexible configuration via `config.yml`

---

## Quick Start

YPM is installed as a Claude Code plugin, making it accessible from **any directory**.

### Step 1: Install the Plugin

```bash
# In Claude Code, first add the marketplace:
/plugin marketplace add signalcompose/ypm

# Then install the plugin:
/plugin install ypm
```

### Step 2: Initial Setup

```bash
# Run the setup wizard (from any directory)
/ypm:setup
```

This creates `~/.ypm/` with your configuration:
- `~/.ypm/config.yml` - Your monitoring settings
- `~/.ypm/PROJECT_STATUS.md` - Generated project status

### Step 3: Start Using

```bash
# Scan your projects
/ypm:update

# View next tasks
/ypm:next

# Show active projects
/ypm:active
```

---

## Available Commands

All commands are prefixed with `ypm:`:

| Command | Description |
|---------|-------------|
| `/ypm:setup` | Initial setup wizard |
| `/ypm:start` | Show welcome and quick commands |
| `/ypm:help` | Show detailed help |
| `/ypm:update` | Update project status |
| `/ypm:next` | Show next tasks |
| `/ypm:active` | Show active projects only |
| `/ypm:open` | Open project in editor |
| `/ypm:new` | Launch project setup wizard |
| `/ypm:setup-gitflow` | Set up Git Flow workflow |
| `/ypm:export-community` | Export to community version |
| `/ypm:trufflehog-scan` | Run TruffleHog security scan |

### Optional: Prefix-Free Commands

During setup, you can optionally create symlinks to `~/.claude/commands/` for prefix-free access:

```bash
# With symlinks, you can use:
/update    # instead of /ypm:update
/next      # instead of /ypm:next
```

### Data Location

YPM stores all user data in `~/.ypm/`:

```
~/.ypm/
  ├── config.yml           # Your monitoring settings
  └── PROJECT_STATUS.md    # Generated project status
```

This separation ensures:
- Plugin updates don't affect your configuration
- Easy backup (just backup `~/.ypm/`)
- Works across all your projects

---

## Documentation

- **[Detailed Guide (English)](docs/guide-en.md)** - Complete usage guide
- **[詳細ガイド（日本語）](docs/guide-ja.md)** - 日本語の詳細ガイド
- **[Security Policy](SECURITY.md)** - Security considerations and best practices

---

## How It Works

1. **Scans** directories specified in `config.yml`
2. **Collects** Git information (branch, commits, changes)
3. **Reads** project documentation (CLAUDE.md, README.md, docs/)
4. **Generates** `PROJECT_STATUS.md` with categorized project status

---

## Project Categories

- **🔥 Active**: Updated within 1 week
- **🎨 Planning**: In design phase (Phase 0)
- **🚧 In Development**: Implementation in progress
- **💤 Inactive**: No updates for over 1 month
- **📦 Non-Git**: Not a Git repository

---

## Requirements

- **Claude Code**: Required for running YPM
  - [Get Claude Code](https://claude.ai/download)
- **Git**: For project information collection
- **Python 3.8+**: For project scanning (included in the plugin)

---

## Language Support

YPM supports multiple languages through dynamic translation:

- **English (default)**: All output displayed as-is
- **Japanese**: Set `settings.language: ja` in `~/.ypm/config.yml`

Claude automatically translates command output based on your language preference. Static documentation remains in English to ensure consistency across the global community.

```yaml
# In ~/.ypm/config.yml
settings:
  language: ja   # Options: en (default), ja
```

---

## Project Bootstrap Assistant

YPM includes a comprehensive project setup assistant for launching new projects.

**What it does**:
- Guides you through project planning and requirements definition
- Creates proper directory structure with documentation
- Sets up Git workflow (Git Flow, Worktree support)
- Configures development environment (.gitignore, .claude/settings.json)
- Establishes documentation management rules (DDD, TDD, DRY principles)

**How to use**:

Simply run `/ypm:new` in Claude Code, or manually use the prompt:

1. Copy the contents of `project-bootstrap-prompt.md`
2. Paste into Claude Code
3. Follow the interactive wizard through 8 phases

See [project-bootstrap-prompt.md](project-bootstrap-prompt.md) for details.

---

## Configuration

Edit `~/.ypm/config.yml` to customize monitoring (created by `/ypm:setup`):

```yaml
monitor:
  directories:
    - /path/to/your/projects    # Directories to monitor

  patterns:
    - "proj_*/*"                # Project detection patterns
    - "my-apps/*"

  exclude:
    - old_projects/*            # Exclude patterns

editor:
  default: code                 # Default editor (code/cursor/zed)

classification:
  active_days: 7                # Consider active if updated within N days
  inactive_days: 30             # Consider inactive if no updates for N days
```

---

## Development Setup

For contributors or those who want to run YPM from source:

```bash
# Clone the repository
git clone https://github.com/signalcompose/YPM.git
cd YPM

# Install dependencies
pip3 install -r requirements.txt

# Run onboarding wizard (creates config.yml in current directory)
python3 scripts/onboarding.py
```

Then open Claude Code in the YPM directory and use the commands directly.

---

## Contributing

Contributions to YPM are welcome!

- **Repository**: [signalcompose/YPM](https://github.com/signalcompose/YPM)
- **Bug reports & feature requests**: [GitHub Issues](https://github.com/signalcompose/YPM/issues)
- **Pull requests**: Please follow the Git Flow in `CLAUDE.md`

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Author

**Hiroshi Yamato / dropcontrol**

- Website: [hiroshiyamato.com](https://hiroshiyamato.com/) | [yamato.dev](https://yamato.dev/)
- X: [@yamato](https://x.com/yamato)
- GitHub: [dropcontrol](https://github.com/dropcontrol)

Powered by Claude Code

---

**Manage your projects, simplified.** 🚀
