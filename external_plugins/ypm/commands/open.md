---
description: "Open a project in your preferred editor"
---

<!-- Language Handling: Check ~/.ypm/config.yml for settings.language -->
<!-- If language is not "en", translate all output to that language -->

# YPM - Open Project in Editor

Open a YPM-managed project in specified editor.

**Prerequisites**:
- Run `/ypm:setup` first if `~/.ypm/config.yml` doesn't exist
- Run `/ypm:update` first if `~/.ypm/PROJECT_STATUS.md` doesn't exist

## Subcommands

- **(no args)**: Select from list (excluding ignored, open with default editor)
- `<project> [editor]`: Open project with specified editor
- `all`: Select from all projects including ignored
- `ignore-list`: Show ignored projects list
- `add-ignore`: Add project to ignore list
- `remove-ignore`: Remove from ignore list
- `--editor [name]`: View/set default editor

## Usage Examples

```
/ypm:open                    # Normal mode (default editor)
/ypm:open myproject          # Open myproject with default editor
/ypm:open myproject cursor   # Open myproject with Cursor
/ypm:open myproject terminal # Open myproject in Terminal.app
/ypm:open all                # Show all mode
/ypm:open --editor           # Show current default editor
/ypm:open --editor cursor    # Set default to Cursor
/ypm:open ignore-list        # Show ignore list
/ypm:open add-ignore         # Add to ignore
/ypm:open remove-ignore      # Remove from ignore
```

**Supported Editors**: `code` (VS Code), `cursor` (Cursor), `zed` (Zed), `terminal` (Terminal.app)

---

## Execution Steps

### Common STEP: Check Arguments

Check arguments and branch to corresponding mode:
- No args -> **Mode 1: Normal mode**
- `<project> [editor]` -> **Mode 1: Normal mode** (direct project specification)
- `all` -> **Mode 2: Show all mode**
- `ignore-list` -> **Mode 3: Ignore list**
- `add-ignore` -> **Mode 4: Add ignore**
- `remove-ignore` -> **Mode 5: Remove ignore**
- `--editor [name]` -> **Mode 6: Editor settings**

---

## Mode 1: Normal Mode (no args or project name specified)

### STEP 1: Check config.yml and Editor CLI

#### 1-1. Get default editor from ~/.ypm/config.yml

```bash
# Read ~/.ypm/config.yml
# Get editor.default value (e.g., code, cursor, zed)
```

#### 1-2. Override editor if 2nd argument exists

- If 2nd argument (`cursor`, `code`, `zed`, etc.) specified, use that editor
- If no 2nd argument, use config.yml default

#### 1-3. Check Editor CLI

**For editors other than Terminal.app**:

```bash
which <editor-name>
```

**If result is empty**:
```
Editor CLI not found.

Please install the CLI for your editor.

[VS Code (code)]
1. Open VS Code
2. Command Palette (Cmd+Shift+P)
3. Run "Shell Command: Install 'code' command in PATH"

[Cursor (cursor)]
1. Open Cursor
2. Command Palette (Cmd+Shift+P)
3. Run "Shell Command: Install 'cursor' command in PATH"

[Zed (zed)]
1. Open Zed
2. Command Palette (Cmd+Shift+P)
3. Run "zed: Install CLI"

Please run this command again after installation.
```
-> **Abort process**

**For Terminal.app**:
- No CLI check needed (macOS built-in)
- Proceed to next STEP

### STEP 2: Read ~/.ypm/PROJECT_STATUS.md and ~/.ypm/config.yml

```bash
# Read ~/.ypm/PROJECT_STATUS.md with Read tool
# Read ~/.ypm/config.yml with Read tool
```

**If ~/.ypm/PROJECT_STATUS.md doesn't exist**:
```
~/.ypm/PROJECT_STATUS.md not found.

Please run /ypm:update first to scan projects.
```
-> **Abort process**

### STEP 3: Extract and Filter Project List

#### 3-1. Extract from PROJECT_STATUS.md

1. **Active projects** (`## Active Projects` section)
2. **Developing projects** (`## In Development` section)
3. **Inactive projects** (`## Inactive` section)

**Extraction rules**:
- Get project name from `### ProjectName` lines
- Get brief description from `- **Overview**: ...`
- Get progress from `- **Implementation**: XX%`
- Extract project path from `- **Documentation**: [...]`

#### 3-2. Exclude Git worktrees

Exclude projects matching **any** of these conditions:
- Project name ends with `-main`
- Project name ends with `-develop`
- Overview contains "worktree"

#### 3-3. Exclude ignore_in_open (normal mode only)

Exclude projects in `~/.ypm/config.yml`'s `monitor.ignore_in_open` list.

### STEP 4: Display Numbered List

```
## Available Projects (12 items)

### Active (updated within 1 week)
1. ProjectA - Description (95%)
2. ProjectB - Description (100%)
...

### In Development (updated within 1 month)
12. ProjectX - Description (0%)
...

* Hidden: 2 items (show all: /ypm:open all)

Enter number or project name:
```

### STEP 5: Process User Input

**Input patterns**:

#### 5-1. Number input (e.g., `3`)
- Select corresponding project -> STEP 6

#### 5-2. Project name input (e.g., `proj`)
- Case-insensitive partial match search
- **1 match**: Select that project -> STEP 6
- **Multiple matches**: Show numbered candidates, wait for selection
- **0 matches**: Error message, abort

### STEP 6: Open in Editor

#### 6-1. For editors other than Terminal.app

**Important**: Launch editor with cleared environment variables.

```bash
env -u NODENV_VERSION -u NODENV_DIR -u RBENV_VERSION -u PYENV_VERSION <editor> /path/to/project
```

#### 6-2. For Terminal.app

```bash
osascript -e 'tell application "Terminal" to do script "cd '"$PROJECT_PATH"' && exec $SHELL"'
```

#### 6-3. Success Message

```
Opened "ProjectName" in <Editor Name>.

Project path: /path/to/project
Editor: <Editor Display Name> (<editor>)

* Environment variables (NODENV_VERSION, etc.) were cleared.
Project-specific configuration files (.node-version, etc.) will be loaded correctly.
```

---

## Mode 2: Show All Mode (`/ypm:open all`)

Same as Mode 1, but **does not exclude ignore_in_open**.

---

## Mode 3-6: Ignore Management and Editor Settings

See specification document for details:
- **[docs/development/ypm-open-spec.md](../../docs/development/ypm-open-spec.md)**

---

## Important Notes

### 1. Git Worktree Exclusion
Git worktrees are **automatically excluded in all modes**.

### 2. ignore vs exclude
- **exclude**: Completely excluded from scan (not shown in PROJECT_STATUS.md)
- **ignore_in_open**: Scanned but hidden in ypm-open default (visible with `all`)

### 3. Saving ~/.ypm/config.yml
When adding/removing ignore or changing editor settings, **always save** `~/.ypm/config.yml` using Write tool.

---

**Always display success/failure message after running this command.**
