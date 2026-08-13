# Context7

[Context7](https://context7.com) solves a common problem with AI coding assistants: outdated training data and hallucinated APIs. Instead of relying on stale knowledge, Context7 fetches current documentation and code examples directly from source repositories.

This plugin connects Claude Code to Context7's hosted remote MCP server (`https://mcp.context7.com/mcp`) — no local Node.js, npm, or npx required.

## Available Tools

- **`resolve-library-id`** — searches for libraries and returns Context7-compatible identifiers (e.g. `/vercel/next.js`) plus available versions.
- **`query-docs`** — fetches documentation for a specific library, ranked by relevance to your question.

## API Key (optional)

Without an API key the plugin connects anonymously and shares the anonymous rate limits. To use your own plan, create an API key in the [Context7 dashboard](https://context7.com/dashboard) and export it as an environment variable before launching Claude Code:

```bash
# e.g. in ~/.zshrc or ~/.bashrc
export CONTEXT7_API_KEY="your-api-key"
```

The plugin's MCP server configuration picks up `CONTEXT7_API_KEY` automatically. Restart Claude Code after setting it, then verify usage in the [dashboard](https://context7.com/dashboard).

## Usage

The plugin works automatically when you ask about libraries:

- "How do I set up authentication in Next.js 15?"
- "Show me React Server Components examples"
- "What's the Prisma syntax for relations?"

To get documentation for a specific version, include the version in the library ID (e.g. `/vercel/next.js/v15.1.8`). The `resolve-library-id` tool returns available versions, so you can pick the one that matches your project.

---

Maintained by [Upstash](https://upstash.com). Source and full plugin (with skills, agents, and commands): [upstash/context7](https://github.com/upstash/context7).
