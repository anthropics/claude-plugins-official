# Changelog

All notable changes to the Lisa plugin.

## [1.3.2] - 2026-01-06

### Changed

- **Command naming**: Renamed `/lisa:lisa` to `/lisa:loop` for clarity
  - All commands now follow consistent `lisa:action` pattern:
    - `/lisa:loop` - Start iterative loop that auto-restarts until completion promise is detected
    - `/lisa:cancel` - Cancel active Lisa loop
    - `/lisa:clean` - Remove stale loop files, logs, and orphaned PROMPT.md files
    - `/lisa:status` - Check current loop iteration, max limit, and completion promise
    - `/lisa:prep` - Create PROMPT.md, IMPLEMENTATION_PLAN.md, and specs/ scaffolding
    - `/lisa:help` - Explain Lisa technique and available commands

- **README updates**: Updated all command references to use new `lisa:action` format

### Fixed

- **Installation documentation**: Corrected marketplace install commands:
  ```bash
  claude plugin marketplace add Arakiss/lisa
  claude plugin install lisa@lisa-marketplace
  ```

## [1.3.0] - 2026-01-06

### Added

- **Iteration logging**: Each Lisa iteration is now logged to `.claude/lisa-loop.log` with:
  - Timestamps for each iteration start/end
  - Duration of each iteration in seconds
  - Progress detection (completed/total items from IMPLEMENTATION_PLAN.md)
  - Error logging for debugging
  - Summary stats on completion (total time, total iterations)

- **Progress detection**: If an `IMPLEMENTATION_PLAN*.md` exists, Lisa now:
  - Counts completed `[x]` and pending `[ ]` items
  - Shows progress in system message: `Progress: 15/48`
  - Logs progress to file

- **Iteration timing**: State file now tracks `last_iteration_at` timestamp for duration calculation

### Improved

- **`/lisa-clean` command**: Now also cleans `.claude/lisa-loop.log`
  - New `--keep-logs` flag to preserve logs for analysis

- **Completion messages**: Now show total iterations and log file location

## [1.2.0] - 2026-01-06

### Improved

- **`/lisa-clean` command**: Now detects and offers to delete orphaned prompt files:
  - Scans for untracked `PROMPT*.md` and `IMPLEMENTATION_PLAN*.md` in project root
  - Shows file preview before deletion
  - New `--all` flag to delete all orphaned files without prompting
  - Documents why prompt files become orphaned (crashes, force-quit, completed tasks)

### Fixed

- **Orphaned file accumulation**: Previously, `PROMPT.md` and `IMPLEMENTATION_PLAN.md` files were never cleaned up after loop completion. Users had to manually delete them. Now `/lisa-clean` handles this.

## [1.1.0] - 2026-01-05

### Added

- **Auto-detection of completion promises**: The setup script now automatically extracts `<promise>...</promise>` tags from prompt files. No need to pass `--completion-promise` separately when your prompt file contains the tag.

- **New `/lisa-status` command**: Check the current state of a running Lisa loop without canceling it. Shows iteration count, max iterations, promise, and start time.

- **New `/lisa-prep` command**: Guided preparation workflow that creates structured files for Lisa loops (specs/, IMPLEMENTATION_PLAN.md, PROMPT.md).

- **Example PROMPT files**: Added `examples/` folder with sample prompts for different scenarios:
  - `PROMPT-api.md` - Building a REST API
  - `PROMPT-bugfix.md` - Fixing failing tests
  - `PROMPT-refactor.md` - Codebase refactoring
  - `PROMPT-minimal.md` - Minimal template

- **Safety warnings**:
  - Warns if no completion promise AND no max-iterations are set (3-second delay to abort)
  - Warns if prompt looks like a file path but file doesn't exist
  - Warns if a loop is already active when starting a new one

- **Better file detection**: Shows "📄 Reading prompt from file: X" when using file-based prompts

### Changed

- **README.md**: Completely rewritten with:
  - Visual diagram of how Lisa works
  - Documentation of auto-detect feature
  - All new commands documented
  - Troubleshooting section
  - Best practices section
  - Updated file structure

- **lisa-guide skill**: Updated documentation to reflect auto-detection feature

### Fixed

- **Infinite loop bug**: Previously, if `--completion-promise` flag was not provided, the promise defaulted to `null` and the stop hook would skip promise detection entirely, causing infinite loops even when prompts contained `<promise>` tags. Now the script auto-detects promises from prompt content.

## [1.0.0] - 2025-12-17

Initial fork from anthropics/claude-plugins-official.

### Features from original

- `/lisa-loop` command to start iterative loops
- `/cancel-lisa` command to stop loops
- `/help` command for documentation
- Stop hook for loop continuation
- YAML frontmatter state file
- Max iterations support
- Completion promise support (manual flag only)
