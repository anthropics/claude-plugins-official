# Vanikya AI MCP — Claude Code Plugin

Connect [Vanikya](https://vanikya.com) to Claude Code and Claude Desktop. Generate images, videos, vectors, and lottie animations, run SEO analysis, get creative insights, and manage credits — all directly from Claude.

## Installation

```bash
/plugin install vanikya-ai-mcp
```

Then connect Claude to the Vanikya MCP server:

**Claude Code:**
```bash
claude mcp add --transport http vanikya https://prod.vanikya.com/mcp
```

**Claude Desktop** — add to `claude_desktop_config.json`:
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

On first use, a browser window opens for OAuth login with your Vanikya account.

## Skills

Skills activate automatically when you ask Claude about these topics:

| Skill | Triggers when you ask... |
|---|---|
| **Setup** | How to connect, configure, or troubleshoot Vanikya |
| **Imagine** | Generate images, videos, vectors, lottie animations, edit images, enhance prompts |
| **SEO Analysis** | Analyze SEO of a URL, run audits, batch analyze pages |
| **Creative Insights** | Visual/creative analysis of images, branding feedback |
| **Credits** | Check balance, buy credits, view pricing |

## Commands

| Command | What it does |
|---|---|
| `/vanikya-setup` | Step-by-step connection guide |

## Requirements

- A [Vanikya account](https://vanikya.com)
- Claude Code or Claude Desktop
- Node.js (for Claude Desktop only — needed for `npx mcp-remote`)

## MCP Server

Production endpoint: `https://prod.vanikya.com/mcp`

Authentication: OAuth 2.0 via Clerk (browser popup on first connection, cached thereafter)
