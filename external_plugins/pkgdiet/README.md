# PkgDiet Plugin for Claude Code

A local-first dependency policy gate and security guardrail to stop AI coding agents from installing risky npm packages.

## Features

- **PreToolUse Execution Guard**: Intercepts `npm`, `pnpm`, `yarn`, and `bun` install commands before Claude Code executes them. Blocks unpinned, ambiguous, or policy-violating packages.
- **Model Context Protocol (MCP)**: Native tools for inspecting packages:
  - `check_dependency`
  - `check_dependencies`
  - `suggest_alternative`
  - `get_policy`
- **Slash Commands**:
  - `/pkgdiet:check <package>` - Check package health and security.
  - `/pkgdiet:audit` - Audit workspace `package.json` and lockfiles.

## Installation

```bash
/plugin install pkgdiet@claude-plugins-official
```

Or directly from GitHub:

```bash
/plugin install github:om-tajne/pkgdiet
```
