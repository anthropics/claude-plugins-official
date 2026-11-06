# Deploy to Cloudflare Workers

Fastest path from zero to a live `https://` MCP URL. Free tier, no credit card to start, two commands to deploy.

**Trade-off:** This is a Workers-native scaffold, not a deploy target for the Express scaffold in `remote-http-scaffold.md`. Different runtime. If you need portability across hosts, stick with Express. If you just want it live, start here.

---

## Bootstrap

```bash
npm create cloudflare@latest -- my-mcp-server \
  --template=cloudflare/ai/demos/remote-mcp-authless
cd my-mcp-server
```

This pulls a minimal template with the right deps (`@modelcontextprotocol/server`, `agents`, `zod`) and a working `wrangler.jsonc`.

---

## `src/index.ts`

Replace the template's calculator example with your tools. Use `registerTool()` (same API as the Express scaffold — the `McpServer` class is identical):

```typescript
import { McpServer } from "@modelcontextprotocol/server";
import { createMcpHandler } from "agents/mcp/server";
import { z } from "zod";

// Called once per request. Always build a new McpServer here.
function createServer() {
  const server = new McpServer(
    { name: "my-service", version: "0.1.0" },
    { instructions: "Prefer search_items before get_item — IDs aren't guessable." },
  );

  server.registerTool(
    "search_items",
    {
      description: "Search items by keyword. Returns up to `limit` matches.",
      inputSchema: z.object({
        query: z.string().describe("Search keywords"),
        limit: z.number().int().min(1).max(50).default(10),
      }),
      annotations: { readOnlyHint: true },
    },
    async ({ query, limit }) => {
      const results = await upstreamApi.search(query, limit);
      return { content: [{ type: "text", text: JSON.stringify(results, null, 2) }] };
    },
  );

  return server;
}

const handler = createMcpHandler(createServer); // serves /mcp

export default {
  fetch(request: Request, env: Env, ctx: ExecutionContext) {
    return handler(request, env, ctx);
  },
} satisfies ExportedHandler<Env>;
```

`createMcpHandler` from `agents/mcp/server` is Cloudflare's wrapper around the SDK's stateless handler — it adds the `/mcp` route, CORS, and Host/Origin checks. No sessions and no Durable Objects. Everything in `tool-design.md` and `server-capabilities.md` applies unchanged.

Older versions of this template used `McpAgent` with a Durable Object binding and SDK v1. Don't mix the two: `McpAgent` takes a v1 `McpServer` from `@modelcontextprotocol/sdk`.

---

## `wrangler.jsonc`

The template ships this. Nothing MCP-specific in it.

```jsonc
{
  "name": "my-mcp-server",
  "main": "src/index.ts",
  "compatibility_date": "2026-07-02",
  "compatibility_flags": ["nodejs_compat"]
}
```

---

## Run and deploy

```bash
npx wrangler dev     # → http://localhost:8787/mcp
npx wrangler deploy  # → https://my-mcp-server.<account>.workers.dev/mcp
```

`wrangler deploy` prints the live URL. That's the URL users paste into Claude.

Secrets (upstream API keys): `npx wrangler secret put UPSTREAM_API_KEY`, then `import { env } from "cloudflare:workers"` and read `env.UPSTREAM_API_KEY`.

---

## OAuth

Cloudflare ships `@cloudflare/workers-oauth-provider` — a drop-in that handles the authorization server side (CIMD/DCR endpoints, token issuance, consent UI). It wraps your handler and gates `/mcp` behind a token check; `getMcpAuthContext()` from `agents/mcp/server` gives the factory the signed-in user's props. See `auth.md` for the protocol details; the CF template `cloudflare/ai/demos/remote-mcp-github-oauth` shows the wiring.
