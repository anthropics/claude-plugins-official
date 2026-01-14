# Changelog

All notable changes to the Pseudo-Code Prompting Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-01-14

### Changed

#### Plugin Structure Refactoring

- **BREAKING**: Restructured plugin to follow official Claude Code plugin patterns
- Moved from `.claude/` folder structure to official auto-discovery layout
- Skills now in `skills/*/` with progressive loading (capabilities.json → SKILL.md → references → templates)
- Agents now in `agents/*.md` with YAML frontmatter
- Commands now in `commands/*.md` with markdown format
- Hooks now registered via `hooks/hooks.json` with bash scripts

#### Hook System Overhaul

- Created `hooks/hooks.json` for proper hook registration
- Updated all hook scripts to use `${CLAUDE_PLUGIN_ROOT}` for portable paths
- Added `set -euo pipefail` for better error handling
- Split hooks by event type: UserPromptSubmit and PostToolUse
- Hooks now use interactive approval mode with `permissionDecision: "ask"`

#### Documentation Updates

- Updated README.md with "Plugin Architecture" section
- Updated `.claude-plugin/README.md` (marketplace documentation)
- Removed outdated `.claude/` folder references
- Added progressive loading architecture documentation
- Updated troubleshooting to reflect new structure

### Removed

- Removed root `SKILL.md` (skills now have individual `skills/*/SKILL.md` files)
- Removed `.claude/agent-registry.json` (Claude Code uses auto-discovery)
- Removed `.claude/settings.json` (hooks now in `hooks/hooks.json`)

## [1.1.0] - 2026-01-13

### Added - Skills

- `prompt-analyzer` - Analyze prompts for ambiguity, complexity, and clarity with scoring
- `prompt-optimizer` - Optimize pseudo-code for completeness and implementation readiness
- `context-compressor` - Compress verbose requirements into concise pseudo-code (60-95% reduction)
- `requirement-validator` - Validate pseudo-code requirements for completeness, security, and correctness

### Added - Agents

- `requirement-validator` - Validates transformed pseudo-code, identifies gaps and security issues
- `prompt-optimizer` - Enhances pseudo-code by adding missing parameters and clarifying ambiguities
- `context-compressor` - Transforms verbose requirements into structured, compact pseudo-code

### Added - Commands

- `/validate-requirements` - Validate pseudo-code for completeness and correctness
- `/optimize-prompt` - Optimize pseudo-code for implementation readiness
- `/compress-context` - Compress verbose requirements into concise pseudo-code format

### Added - Hooks

- `post-transform-validation.sh` - Auto-validate transformed pseudo-code for completeness
- `context-compression-helper.sh` - Suggest context compression for verbose requirements (>100 words)

### Added - Reference Files

- `validation-checklists.md` - Comprehensive checklists for different feature types (API, database, auth, etc.)
- `common-issues.md` - Pattern library for common requirement issues and solutions

### Added - Project Files

- `.gitignore` - Standard ignore patterns for development
- `LICENSE` - MIT License
- `CHANGELOG.md` - Version history and changes
- `CONTRIBUTING.md` - Contribution guidelines

### Enhanced

#### Workflows
- `full-transformation` - Now includes requirement validation step (900 tokens)
- `optimize-and-validate` - New workflow for enhancing existing pseudo-code (700 tokens)
- `compress-transform-validate` - Complete workflow from verbose to validated (1000 tokens)

#### Plugin Metadata
- Updated version to 2.1.0
- Added keywords: validation, optimization, compression, security-validation
- Enhanced description to highlight validation and optimization capabilities

### Changed
- Increased `max_skills_per_task` in discovery to 3 (from 2)
- Updated progressive loading strategy with validation tier

## [1.0.0] - 2026-01-12

### Added

#### Core Features
- Initial release of Pseudo-Code Prompting Plugin
- PROMPTCONVERTER methodology implementation
- Progressive loading system with 4-tier architecture

#### Skills
- `prompt-structurer` - Transform natural language to pseudo-code using PROMPTCONVERTER
- `feature-dev-enhancement` - Apply structured pseudo-code across feature-dev workflow phases

#### Agents
- `prompt-analyzer` - Analyze prompts for ambiguity and complexity
- `prompt-transformer` - Transform natural language to function-like pseudo-code

#### Commands
- `/transform-query` - Transform natural language to pseudo-code

#### Hooks
- `user-prompt-submit.sh` - Detect /feature-dev and /pseudo-prompt commands

#### Documentation
- Comprehensive README.md with usage examples
- MARKETPLACE.md for Claude Code Marketplace
- PROMPTCONVERTER.md methodology guide

### Features
- Semantic skill discovery with confidence thresholds
- Token-efficient progressive loading (100-800 tokens per tier)
- Workflow automation with estimated token usage
- Integration with feature-dev workflow

## Version History

### [1.1.0] - 2026-01-13
- Added validation, optimization, and compression capabilities
- 4 new skills, 3 new agents, 3 new commands, 2 new hooks
- Enhanced workflows and quality gates

### [1.0.0] - 2026-01-12
- Initial release with transformation and analysis
- 2 skills, 2 agents, 1 command, 1 hook
- Progressive loading and semantic discovery

---

For more details, see the [README.md](README.md) and [CONTRIBUTING.md](CONTRIBUTING.md).
