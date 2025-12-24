---
description: "Show detailed YPM help with all available commands"
---

<!-- Language Handling: Check ~/.ypm/config.yml for settings.language -->
<!-- If language is not "en", translate all output to that language -->

# YPM (Your Project Manager) - Help

## Overview

YPM monitors multiple projects in configured directories and centralizes progress management.

---

## Available Commands

### Project Management

#### `/ypm:start`
Show welcome message and quick commands.

#### `/ypm:update`
Scan all projects and update `PROJECT_STATUS.md`.
- Get Git information for each project
- Read CLAUDE.md, README.md, docs/INDEX.md
- Collect progress info (Phase, Implementation, Testing, Documentation)

#### `/ypm:next`
Display "next tasks" for each project in priority order.
- Active projects (updated within 1 week)
- Projects with high implementation progress
- By Phase order

#### `/ypm:active`
Display only active projects updated within 1 week.
- Project name, overview, branch, last update
- Phase, implementation progress, next task

---

### Project Operations

#### `/ypm:open`
Open project in preferred editor.
- Basic: Select from project list
- `<project>`: Open with default editor
- `<project> <editor>`: Open with specific editor
- `--editor`: View/set default editor
- `all`: Show all including ignored
- `add-ignore`/`remove-ignore`: Manage ignore list

---

### New Project

#### `/ypm:new`
Launch new project setup wizard.
- Project planning (requirements, tech stack)
- Directory creation and Git initialization
- Documentation setup (DDD/TDD/DRY principles)
- GitHub integration
- Git Workflow configuration
- Environment configuration files

See `project-bootstrap-prompt.md` for details.

---

### Export

#### `/ypm:export-community`
Export private repository to public community version.
- Interactive setup on first run
- Automatic export on subsequent runs
- TruffleHog security scan integration

---

### Security

#### `/ypm:trufflehog-scan`
Run TruffleHog security scan on all managed projects.

---

### Help

#### `/ypm:help`
Show this help message.

---

## YPM Principles

### Read-Only
YPM monitors other projects in **read-only** mode. Only YPM's own files can be modified.

### Role Separation
- **YPM**: Project monitoring, progress management, new project setup support
- **Each Project**: Implementation, development, testing (in dedicated Claude Code sessions)

---

## Reference Documents

- **CLAUDE.md** - YPM project instructions
- **project-bootstrap-prompt.md** - New project setup guide
- **config.example.yml** - Configuration file sample

---

## Common Usage

### 1. Session Start
```
/ypm:start
```
Show welcome message to see available options.

### 2. Check Project Status
```
/ypm:update
```
Scan all projects and get latest status.

### 3. Find Next Task
```
/ypm:next
```
Check high-priority tasks.

### 4. Start New Project
```
/ypm:new
```
Interactive project setup.

---

## License

YPM is licensed under the **MIT License**.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

See [LICENSE](https://github.com/signalcompose/YPM/blob/main/LICENSE) for full details.

---

**Manage your projects efficiently with YPM!**
