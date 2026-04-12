# GitHub plugin for Claude Code

Skills-based GitHub workflows for Claude Code, driven by the `gh` CLI.

## What it does

This plugin bundles four model-invoked skills that guide Claude through
common GitHub workflows without requiring any remote MCP server or static
Personal Access Token:

- **`github`** — umbrella triage skill for repository, pull request, and
  issue work. Routes to a more specific skill when the task becomes narrower.
- **`yeet`** — full publish flow: branch setup, staging, commit, push, and
  opening a draft pull request.
- **`gh-fix-ci`** — debug failing GitHub Actions checks on a PR. Ships with
  a bundled Python helper that fetches check status, run metadata, and log
  snippets.
- **`gh-address-comments`** — inspect unresolved review threads on a PR
  (including inline review locations and resolution state) and implement
  selected fixes. Ships with a GraphQL helper that reads thread-aware review
  data via `gh api graphql`.

## Prerequisites

The plugin assumes the GitHub CLI (`gh`) is installed and authenticated on
the local machine. It does **not** require any environment variables or
tokens stored in Claude Code settings.

```sh
# One-time setup, not plugin-specific:
brew install gh          # or equivalent for your platform
gh auth login            # interactive OAuth device flow
gh auth status           # verify
```

The skills expect `gh` to have at least `repo`, `read:org`, and `workflow`
scopes. `gh auth login` will ask for the right scopes by default.

Python 3 is required for the two bundled helper scripts
(`skills/gh-fix-ci/scripts/inspect_pr_checks.py` and
`skills/gh-address-comments/scripts/fetch_comments.py`).

## Why this plugin does not ship an MCP server

The official `github` plugin in
[anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official)
ships a `.mcp.json` pointing at the remote GitHub Copilot MCP endpoint
(`https://api.githubcopilot.com/mcp/`). That endpoint does **not** support
OAuth 2.0 Dynamic Client Registration (RFC 7591), which Claude Code's
plugin auth path currently requires. Installing the official plugin fails
with:

```
Invalid MCP server config for "github": Missing environment variables:
GITHUB_PERSONAL_ACCESS_TOKEN
```

and any attempt to authenticate through the plugin UI returns:

```
SDK auth failed: Incompatible auth server: does not support dynamic client
registration
```

For comparison, OpenAI's
[`github@openai-curated` plugin for Codex](https://github.com/openai/plugins)
solves the same problem with a hybrid approach: a pre-registered OAuth app
on their Apps & Connectors backend (no DCR needed) plus a `gh` CLI
fallback in every skill. That plugin works out of the box today.

Claude Code has no equivalent connector registry, so this plugin takes
the `gh` CLI path exclusively — a skills bundle that reaches GitHub
through the already-authenticated `gh` CLI, which uses real OAuth via
`gh auth login` and stores credentials in the OS keyring.

Tracked upstream:

- Plugin-level: [anthropics/claude-plugins-official#283](https://github.com/anthropics/claude-plugins-official/issues/283)
- Claude Code core: [anthropics/claude-code#3433](https://github.com/anthropics/claude-code/issues/3433)

When Claude Code gains pre-registered OAuth client support for MCP, a
structured MCP server can be added back alongside the skills without
breaking anything.

## Sandbox compatibility

The plugin works in Claude Code's sandbox mode without any user configuration:

1. **Skill instructions** tell Claude to set `dangerouslyDisableSandbox: true`
   on every `gh`, `git`, and helper-script Bash call. This bypasses the
   sandbox network proxy that would otherwise block TLS connections to
   `api.github.com`.

2. **PreToolUse hook** (`hooks/hooks.json` + `hooks/allow-gh.sh`)
   auto-approves these calls with `permissionDecision: "allow"`, so the
   user is never prompted for permission.

No changes to project or global `settings.json` are needed.

## Attribution

The skills and helper scripts in this plugin were adapted from OpenAI's
[`openai/plugins` `github@openai-curated` plugin for Codex](https://github.com/openai/plugins),
which is licensed under the Apache License, Version 2.0. References to
OpenAI's proprietary Apps & Connectors registry and the "GitHub app from
this plugin" workflow were rewritten to use the `gh` CLI, since Claude
Code has no connector-registry equivalent today.

See the `NOTICE` and `LICENSE` files at the root of this plugin directory
for full attribution and license terms.
