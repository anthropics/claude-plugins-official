# YPM Detailed Guide (English)

> Complete usage guide for YPM (Your Project Manager)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Setup](#setup)
- [Usage](#usage)
- [Customization](#customization)
- [FAQ](#faq)
- [Future Enhancements](#future-enhancements)

---

## Overview

YPM is a tool that automatically collects and organizes the status of multiple projects within a specified directory and displays them in a unified view.

**Who is this tool for?**
- Engineers and creators working on multiple projects simultaneously
- People with side projects alongside their main work
- Managers overseeing multiple team projects

### Problems It Solves

- ✅ Too many projects to track which ones are active
- ✅ Difficult to remember the status of side projects
- ✅ Time-consuming to check what needs to be done next
- ✅ Hard to visualize progress and priorities

---

## Features

- **Automatic Collection**: Gathers information from Git history and documentation
- **Centralized Management**: All projects managed in a single file
- **Claude Code Integration**: Easy updates using Claude Code
- **Progress Visualization**: Displays progress metrics for each project
- **Next Task Identification**: Shows what to do next for each project
- **Flexible Configuration**: Customize monitoring targets via `config.yml`

---

## Prerequisites

- **Claude Code**: Required for running YPM
  - [Get Claude Code](https://claude.ai/download)
- **Git**: Used for collecting project information
- **Python 3.8+**: For project scanning (included in the plugin)

---

## Installation

YPM is installed as a Claude Code plugin, making it accessible from **any directory**.

### Step 1: Install the Plugin

```bash
# In Claude Code, run:
/install signalcompose/YPM
```

### Step 2: Initial Setup

```bash
# Run the setup wizard (from any directory)
/ypm:setup
```

The setup wizard will interactively collect:
1. Path to the project directories to monitor
2. Project detection patterns
3. Classification threshold days for active/inactive status

Upon completion, `~/.ypm/config.yml` will be automatically generated.

### Step 3: First Scan

```bash
# Scan your projects
/ypm:update
```

This will generate `~/.ypm/PROJECT_STATUS.md` with all project information collected.

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

## Usage

### 1. Check Project Status

```bash
# View the status file directly
cat ~/.ypm/PROJECT_STATUS.md

# Or use the command
/ypm:active
```

View the status of all projects at a glance.

### 2. Update Status

```bash
# From any directory in Claude Code
/ypm:update
```

This will automatically:
1. Scan directories specified in `~/.ypm/config.yml`
2. Retrieve Git information for each project
3. Read documentation (CLAUDE.md, README.md, docs/INDEX.md)
4. Update `~/.ypm/PROJECT_STATUS.md`

### 3. Check Next Tasks

```bash
/ypm:next
```

Displays next tasks for each project in priority order.

---

## Available Commands

YPM provides the following commands. All commands are prefixed with `ypm:`.

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

### Project Management Commands

#### `/ypm:start`
Displays a welcome message and list of frequently used commands. Useful when starting a session.

#### `/ypm:help`
Displays detailed help for all commands. You can view command descriptions, YPM principles, and common use cases.

#### `/ypm:update`
Scans all projects and updates `~/.ypm/PROJECT_STATUS.md`.

**Actions performed**:
1. Scans monitoring target directories specified in `~/.ypm/config.yml`
2. Retrieves Git information for each project (branch, last commit, changed files)
3. Reads `CLAUDE.md`, `README.md`, `docs/INDEX.md` from each project
4. Collects progress information (Phase, implementation progress, testing, documentation)
5. Updates `~/.ypm/PROJECT_STATUS.md`

**Note**: Other projects' files are read-only (modification forbidden)

#### `/ypm:next`
Displays "next tasks" for each project in priority order.

**Display content**:
- Project name
- Current Phase
- Next task
- Last update date

**Priority order**:
1. Active projects (updated within the last week)
2. Projects with high implementation progress
3. Phase order

#### `/ypm:active`
Displays only active projects updated within the last week.

**Display content**:
- Project name, overview, branch
- Last update date, Phase, implementation progress
- Next task

Displayed in descending order of update date (newest first).

#### `/ypm:open [project] [editor] [options]`
Opens a project in your preferred editor with automatic environment variable cleanup.

**Basic Usage**:
- `/ypm:open` - Show project list (excluding ignored projects, worktrees auto-excluded)
- `/ypm:open oshireq` - Open "oshireq" project with default editor
- `/ypm:open oshireq cursor` - Open "oshireq" project with Cursor editor

**Supported Editors**:
- `code` - VS Code
- `cursor` - Cursor
- `zed` - Zed
- `terminal` - Terminal.app

**Editor Settings**:
- `/ypm:open --editor` - Show current default editor
- `/ypm:open --editor cursor` - Set default editor to Cursor
- `/ypm:open --editor zed` - Set default editor to Zed

**Ignore Management**:
- `/ypm:open all` - Show all projects including ignored ones
- `/ypm:open ignore-list` - Show currently ignored projects
- `/ypm:open add-ignore` - Add a project to ignore list
- `/ypm:open remove-ignore` - Remove a project from ignore list

**Features**:
- **Environment Variable Cleanup**: Automatically clears `NODENV_VERSION`, `NODENV_DIR`, `RBENV_VERSION`, `PYENV_VERSION` before launching editor, ensuring each project's version files (`.node-version`, etc.) are properly loaded
- **Automatic Worktree Exclusion**: Git worktree directories (e.g., `MaxMCP-main`, `InstrVo-develop`) are automatically excluded from selection
- **Flexible Editor Selection**: Switch between code editors based on project needs or personal preference

**Configuration**:
Default editor is set in `~/.ypm/config.yml`:
```yaml
editor:
  default: code  # Options: code, cursor, zed, terminal
```

See [ypm-open-spec.md](development/ypm-open-spec.md) for detailed specifications.

### New Project Setup Command

#### `/ypm:new`
Launches an interactive wizard to help set up new projects.

Sets up projects step-by-step through 8 phases:
1. **Project Planning**: Requirements definition, technology selection
2. **Directory Creation**: Local directory creation and Git initialization
3. **Documentation Setup**: Development environment based on DDD/TDD/DRY principles
4. **GitHub Integration**: Remote repository creation and initial push
5. **Git Workflow Setup**: Branch strategy and rule establishment
6. **Environment Configuration**: `.gitignore`, `.claude/settings.json`
7. **Documentation Management Rules**: Synchronization between implementation and documentation
8. **Final Confirmation**: Ready to start development

**After setup completion**:
- Move to the new project directory
- Start development in a dedicated Claude Code session for that project
- YPM will automatically add it to monitoring targets on the next `/ypm:update`

See [project-bootstrap-prompt.md](../project-bootstrap-prompt.md) for details.

### Git Workflow Command

#### `/ypm:setup-gitflow`
Set up Git Flow workflow for the current project with branch protection and security settings.

**What it does**:
- Creates `main` (default) and `develop` branches
- Configures branch protection (no direct push to main/develop)
- Disables squash/rebase merge (merge commit only)
- Sets up security settings based on project type (CODEOWNERS, Secret Scanning)

**Project Types**:
1. **Personal Project** - Minimal settings, solo development
2. **Small OSS** - CODEOWNERS, branch protection recommended
3. **Large OSS** - All security settings enabled

**Usage**:
```bash
/ypm:setup-gitflow
```

The command will interactively ask about project type and development style to configure appropriate settings.

### Security & Export Commands

#### `/ypm:export-community`
Export private repository to public community version.
- Interactive setup on first run
- Automatic export on subsequent runs
- TruffleHog security scan integration

#### `/ypm:trufflehog-scan`
Run TruffleHog security scan on all managed projects.
- Requires TruffleHog to be installed (`brew install trufflehog`)
- Scans entire Git history for secrets

---

## Project Bootstrap Assistant

YPM includes a comprehensive assistant feature for launching new projects.

### How to Use

Two methods are available:

**Method 1: Use Custom Command (Recommended)**

Execute in Claude Code:
```
/ypm:new
```

**Method 2: Use Prompt Manually**

1. Copy the contents of `project-bootstrap-prompt.md`
2. Paste into Claude Code
3. Follow the interactive wizard through 8 phases

### Features

- **Comprehensive Support from Requirements to Setup**
  - Project planning interviews
  - Requirements and specification documents
  - Proper directory structure

- **Introduction of Development Best Practices**
  - DDD (Domain-Driven Design)
  - TDD (Test-Driven Development)
  - DRY (Don't Repeat Yourself) principle

- **Git Workflow Configuration**
  - Git Flow support
  - Git Worktree support (optional)
  - Branch protection rules

- **Documentation Management Rules**
  - Synchronization between implementation and documentation
  - Onboarding support
  - PR templates and checklists

### Introduced Development Principles

#### DDD (Domain-Driven Design)
- Layer structure definition (Domain, Application, Infrastructure, Presentation)
- Directory structure guidelines

#### TDD (Test-Driven Development)
- Red → Green → Refactor cycle adherence
- Culture of writing tests before implementation
- Test coverage goal setting

#### DRY (Don't Repeat Yourself)
- Avoid code duplication
- Extract common logic
- Reusable component design

### Generated Documentation

The following documentation is created during project setup:

- `README.md` - Project overview, setup instructions
- `docs/requirements.md` - Requirements specification
- `docs/specifications.md` - System specifications
- `docs/architecture.md` - Architecture design
- `docs/development-guide.md` - Development guidelines
- `docs/onboarding.md` - Onboarding guide for new members
- `.claude/settings.json` - Claude Code permissions
- `.gitignore` - Git exclusion settings

---

## File Structure

### Plugin Files (installed via `/install`)

```
~/.claude/plugins/ypm/          # Plugin installation directory
├── commands/                   # Slash commands
│   ├── start.md
│   ├── help.md
│   ├── setup.md
│   ├── update.md
│   ├── next.md
│   ├── active.md
│   ├── open.md
│   ├── new.md
│   ├── setup-gitflow.md
│   ├── export-community.md
│   └── trufflehog-scan.md
├── scripts/
│   └── scan_projects.py        # Project scanning script
└── ...
```

### User Data (created by `/ypm:setup`)

```
~/.ypm/
├── config.yml                  # Your monitoring settings
└── PROJECT_STATUS.md           # Generated project status
```

---

## Project Categories

### 🔥 Active Projects
Projects updated within the last week. Currently in progress.

### 🎨 Planning Stage
Projects in Phase 0 or documentation phase. Pre-implementation.

### 🚧 In Development
Implementation in progress but no updates in over a week.

### 💤 Inactive
No updates for over 1 month. Temporarily paused.

### 📦 Non-Git
Not a Git repository. Not tracked for progress.

---

## Progress Calculation Criteria

YPM estimates project progress based on the following criteria:

| Progress | Phase | Status |
|----------|-------|--------|
| 0-20% | Phase 0 | Design/Planning |
| 20-30% | Phase 1 | Development Environment Setup |
| 30-60% | Phase 2-3 | Basic Feature Implementation |
| 60-80% | Phase 4-5 | Testing/Improvement |
| 80-100% | Phase 6+ | Production/Feature Expansion |

**Note**: These are estimated values. Manually adjust if they don't match reality.

---

## Customization

Edit `~/.ypm/config.yml` to customize YPM behavior.

### Language Settings

YPM supports multiple languages. Set your preferred language in `~/.ypm/config.yml`:

```yaml
settings:
  language: en   # Options: en (English), ja (Japanese)
```

- **English (`en`)**: Default language, output displayed as-is
- **Japanese (`ja`)**: Claude will dynamically translate all output to Japanese

The language setting is applied during `/ypm:setup` when you select your preferred language, or you can change it manually in the config file.

### Adding Monitoring Targets

Add to `directories` in `~/.ypm/config.yml`:

```yaml
monitor:
  directories:
    - ~/Projects
    - ~/Work      # Add
    - ~/Documents/code  # Add
```

### Changing Project Detection Patterns

For different directory structures:

```yaml
monitor:
  patterns:
    - "proj_*/*"          # 2-level structure
    - "projects/*"        # 1-level structure
    - "my-apps/*/src"     # 3-level structure
```

### Changing Default Editor

Set your preferred editor in `~/.ypm/config.yml`:

```yaml
editor:
  default: cursor    # Change from code to cursor
  # Options: code (VS Code), cursor (Cursor), zed (Zed), terminal (Terminal.app)
```

Or use the command:
```
/ypm:open --editor cursor
```

### Changing Classification Criteria

Modify active/inactive threshold days:

```yaml
classification:
  active_days: 14    # Change to 2 weeks for active
  inactive_days: 60  # Change to 2 months for inactive
```

---

## Update Frequency

- **Recommended**: Once a week
- **Minimum**: Once a month

Regular updates help you stay on top of project status.

---

## FAQ

### Q: How do I add a new project?

**A**: Create a project under the directory specified in `~/.ypm/config.yml`, and it will be automatically detected on the next `/ypm:update`.

### Q: How do I exclude a project?

**A**: Add to `exclude` in `~/.ypm/config.yml`:

```yaml
monitor:
  exclude:
    - proj_YPM/YPM
    - old_projects/*   # Pattern to exclude
```

### Q: Progress percentages are inaccurate

**A**: Manually edit `~/.ypm/PROJECT_STATUS.md` to adjust them.

### Q: Next tasks are not displayed

**A**: Add development plans to the project's `CLAUDE.md` or `docs/`. YPM will read and display them.

### Q: Can I use this on another machine?

**A**: Yes. Install YPM using `/install signalcompose/YPM`, then run `/ypm:setup` to configure your environment. You can also copy your `~/.ypm/config.yml` to the new machine.

---

## Future Enhancements

YPM is currently at **Phase 1 completion**. The Claude Code-driven approach has proven effective in production use.

Potential future enhancements:

- [ ] Project creation support tool
- [ ] Dashboard UI (web-based)
- [ ] Slack notification integration
- [ ] Automatic priority calculation
- [ ] Gantt chart generation
- [ ] Inter-project dependency visualization

**Note**: Automated update scripts (cron support) are currently deprioritized, as AI-based contextual understanding and flexible task extraction are superior.

---

## Troubleshooting

### Q: Project not detected

**A**: Check the following:
1. Is it a Git repository? (Does `.git/` directory exist?)
2. Does the directory structure match the configured pattern in `~/.ypm/config.yml`?
3. Is it included in the exclusion list?

### Q: "config.yml not found" error

**A**: Run `/ypm:setup` to create the initial configuration file at `~/.ypm/config.yml`.

---

## Contributing

Contributions to YPM are welcome!

### Bug Reports & Feature Requests

- Report via [GitHub Issues](https://github.com/signalcompose/YPM/issues)

### Pull Requests

1. Fork this repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Create a pull request

### Development Guidelines

See `CONTRIBUTING.md` (to be created) for details.

---

## License

This project is licensed under the [MIT License](../LICENSE).

---

## Author

**Hiroshi Yamato / dropcontrol**

- Website: [hiroshiyamato.com](https://hiroshiyamato.com/) | [yamato.dev](https://yamato.dev/)
- X: [@yamato](https://x.com/yamato)
- GitHub: [dropcontrol](https://github.com/dropcontrol)

Powered by Claude Code

---

## Related Documentation

- **[README.md](../README.md)** - Project overview (English)
- **[CLAUDE.md](../CLAUDE.md)** - Claude Code instructions
- **[docs/INDEX.md](INDEX.md)** - Documentation index

> **Note**: Japanese documentation (`guide-ja.md`) is deprecated. Use `settings.language: ja` in config for Japanese output.

---

**Manage your projects, simplified.** 🚀
