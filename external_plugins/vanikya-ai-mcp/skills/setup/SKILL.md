---
name: vanikya-setup
description: Use this skill when the user asks how to connect Vanikya to Claude, configure the Vanikya MCP server, install the Vanikya plugin, set up authentication, or troubleshoot connection issues with Vanikya tools not working.
version: 1.0.0
---

# Vanikya MCP Setup

Help the user connect Claude to the Vanikya MCP server at `https://prod.vanikya.com/mcp`.

## Claude Code (recommended)

Run in terminal:

```bash
claude mcp add --transport http vanikya https://prod.vanikya.com/mcp
```

Restart Claude Code. On first use, a browser window opens for OAuth login with the user's Vanikya account.

## Claude Desktop

Add to the Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "vanikya": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://prod.vanikya.com/mcp"]
    }
  }
}
```

Restart Claude Desktop. A browser OAuth window opens on first use.

> **Note:** `npx` requires Node.js. If not installed, direct the user to https://nodejs.org.

## Authentication

Vanikya uses OAuth via Clerk. On first connection:
1. A browser window opens automatically
2. User logs in with their Vanikya account
3. User approves the OAuth permissions
4. Claude receives a cached token — no re-login needed for future sessions

## Verify Connection

```bash
claude mcp list
```

Should show `vanikya` listed with the HTTP transport URL (`https://prod.vanikya.com/mcp`).

Once confirmed, try asking Claude to generate an image, run an SEO analysis, or check your credit balance.

## Troubleshooting

| Problem | Fix |
|---|---|
| Tools not appearing | Restart Claude after adding the MCP server |
| Auth error / 401 Unauthorized | Token expired — run `claude mcp remove vanikya` then re-add |
| Connection refused / timeout | Check internet connection; server is at `https://prod.vanikya.com/mcp` |
| `npx` not found (Claude Desktop) | Install Node.js from https://nodejs.org |
| Wrong account | Log out of Vanikya in browser, then remove and re-add the MCP server |
