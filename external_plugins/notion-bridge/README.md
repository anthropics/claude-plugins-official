# Notion Bridge

A native macOS app that exposes the Mac (files, AppleScript, Accessibility, Screen, Messages, Contacts, Spotlight, Chrome, credentials), the Notion workspace (~24 tools — pages, blocks, comments, queries, data sources, file uploads), and a developer workflow surface (LSP, git, gh, code search, file str-replace/apply-patch) as ~160 MCP tools. Streamable-HTTP transport with OAuth 2.1 + RFC 9728 Protected Resource Metadata; stdio still works for local use.

macOS only. Signed, notarized, distributed as a `.app`.

## Plugin shape note (for the marketplace reviewer)

Bridge MCP is **not** an npm/bun/Node MCP server; the marketplace shape it most closely matches is `external_plugins/imessage` (native macOS, reads/writes system data, native Mac runtime). Unlike iMessage's `bun run` server, Bridge MCP is a persistent app the user installs once and leaves running — the plugin's `.mcp.json` registers an HTTP MCP server pointing at the local endpoint the app exposes.

If the marketplace prefers a different shape for pre-installed native apps, please advise — we can ship a Node shim plugin instead. This PR is a spike to surface the shape question, not a final form.

## Setup

**1. Install Bridge MCP.**

Download and install the signed/notarized `.app` from the GitHub releases:

> https://github.com/KUP-IP/Notion-bridge/releases

Drag `Notion Bridge.app` into `/Applications/`. On first launch, macOS prompts for the entitlements it needs (Full Disk Access for Messages history, Accessibility for AX tree queries, etc.). Grant per the in-app onboarding flow.

**2. Configure your Notion API token.**

Notion Bridge needs a Notion API token to talk to your workspace. In **Settings → Credentials** paste a token from https://www.notion.so/my-integrations (or set `NOTION_API_TOKEN` in your environment). Share the relevant Notion pages/databases with that integration.

**3. Install the plugin.**

These are Claude Code commands — run `claude` to start a session first.

```
/plugin install notion-bridge@claude-plugins-official
```

The plugin adds the MCP server registration pointing at Bridge MCP's local streamable-HTTP endpoint (`http://127.0.0.1:9700/mcp`). Make sure Notion Bridge is running (menu-bar icon present); the MCP server is hosted in-app.

**4. (Optional) Enable the streamable-HTTP path.**

Bridge MCP defaults to stdio for local use. If you want OAuth-secured remote access (for Claude.ai mobile or ChatGPT Developer Mode), set `BRIDGE_ENABLE_HTTP=1` in the app's environment and provision a WorkOS AuthKit tenant — see the operator runbook in the Bridge MCP repo.

## What you get

- **macOS native:** `applescript_exec`, the `ax_*` Accessibility tree, `screen_capture` + OCR + recording, `clipboard_*`, `pasteboard_history`, `spotlight_query`, `messages_*` (Messages.app search/send), `contacts_*`, `chrome_*`, `file_*` (read/write/search/move/zip), `credential_*` (Keychain), `bg_process_*`, `system_info`, `notify`, `cgevent_send`, `keyboard_type`, `mouse_click`.
- **Notion workspace (24 tools):** pages (read/create/update/move/markdown), blocks (read/append/update/delete), discussion + comment tools, data sources (create/update/query/delete-trash), database read, file upload, users, token introspect, workspace search, connections list.
- **Developer workflow:** `lsp_*` (definition/hover/references/rename/diagnostics + session_list), `git_*` (status/log/diff/blame/show/create_branch/merge/apply_patch/worktree), `gh_*` (PRs, issues, actions, checks), `code_search`, `file_str_replace`, `file_apply_patch`, `tree_sitter_query`.
- **Background jobs:** `job_create/get/update/delete/duplicate/list/run/history/templates/export/import/pause/resume`.
- **Other:** `snippets_*` (text snippet store with destructive `requiresConfirmation`), `fetch_skill` / `list_routing_skills` / `manage_skill` (workspace skills + filesystem SKILL.md skills incl. 13 bundled Apache-2.0 skills from `anthropics/skills`).

Every tool carries explicit `readOnlyHint` / `destructiveHint` / `requiresConfirmation` / `openWorldHint` annotations — there are no implicit defaults; an audit test fails the build if any tool is unannotated.

## Permission model

- **Carbon hot-keys** (the Commands palette) — no Input Monitoring or Accessibility TCC grant needed.
- **Messages.app history** (`messages_*` read paths) — macOS prompts for Full Disk Access on first read of `~/Library/Messages/chat.db`.
- **Sending iMessage** (`messages_send`) — macOS prompts for Automation access ("Notion Bridge wants to control Messages") on first send.
- **Accessibility tree** (`ax_*`) — macOS prompts for Accessibility access on first call.
- **Notion** — uses the integration token you supply; never asks for OAuth-to-your-workspace permission from end users.

## Versioning + license

- Plugin version: **3.3.1** (tracks Bridge MCP marketing version)
- Bridge MCP license: source-available (see https://github.com/KUP-IP/Notion-bridge/blob/main/LICENSE)
- Bundled SKILL.md skills inside Notion Bridge are Apache-2.0 (upstream: https://github.com/anthropics/skills) — full attribution + LICENSE in the app at `Contents/Resources/NotionBridge_NotionBridgeLib.bundle/skills/`.

## Issues / questions

- Plugin/marketplace issues → file here.
- Bridge MCP issues → https://github.com/KUP-IP/Notion-bridge/issues
