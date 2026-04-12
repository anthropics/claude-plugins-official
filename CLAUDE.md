# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal Claude Code plugin marketplace (`axisrow-plugins`) forked from `anthropics/claude-plugins-official`. Contains a single GitHub plugin that provides skills-based workflows for PR triage, CI debugging, review comment handling, and publishing changes — all powered by the `gh` CLI instead of remote MCP servers.

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth login` with `repo`, `read:org`, `workflow` scopes)
- Python 3 for helper scripts in `skills/*/scripts/`

## Repository Structure

```
.claude-plugin/marketplace.json        # Marketplace registry — lists all plugins
external_plugins/github/               # The GitHub plugin
  .claude-plugin/plugin.json           # Plugin metadata (name, version, author)
  .mcp.json                            # MCP server config (stdio, dynamic gh auth token)
  skills/
    github/SKILL.md                    # Umbrella triage — routes to specialist skills
    yeet/SKILL.md                      # Publish flow: branch → commit → push → draft PR
    gh-fix-ci/SKILL.md                 # Debug failing GitHub Actions checks
    gh-fix-ci/scripts/inspect_pr_checks.py   # Parses action logs, extracts failure snippets
    gh-address-comments/SKILL.md       # Handle unresolved PR review threads
    gh-address-comments/scripts/fetch_comments.py  # GraphQL query for review threads
  hooks/
    hooks.json                           # PreToolUse hook config for sandbox compatibility
    allow-gh.sh                          # Auto-allows gh, git, and helper script commands
```

## Architecture

**Skills-based, not MCP-server-based.** The plugin uses 4 SKILL.md files that instruct Claude through workflows, with Python helper scripts for complex operations (log parsing, GraphQL queries). The `gh` CLI provides authentication via OS keyring — no static tokens needed.

**Skill routing:** The `github` umbrella skill classifies tasks and routes to `yeet`, `gh-fix-ci`, or `gh-address-comments` as needed. Each skill has explicit routing rules in its SKILL.md frontmatter and body.

**MCP fallback:** `.mcp.json` defines a stdio MCP server (`@modelcontextprotocol/server-github`) that dynamically obtains a token via `gh auth token`. This is supplementary — the skills work without it.

**Sandbox compatibility:** Each SKILL.md instructs Claude to use `dangerouslyDisableSandbox: true` for `gh`/`git` commands (needed to bypass sandbox TLS proxy). The PreToolUse hook auto-approves these calls so the user sees no prompt. No project-level settings changes required.

## Key Conventions

- Skills use YAML frontmatter (`name`, `description`) followed by markdown instructions
- Helper scripts live in `skills/{skill}/scripts/` and are invoked by Claude during skill execution
- `marketplace.json` references plugins by relative path (`./external_plugins/github`)
- Plugin is installed via: `/plugin install github@axisrow-plugins`
- No build step, no package manager, no compiled artifacts
