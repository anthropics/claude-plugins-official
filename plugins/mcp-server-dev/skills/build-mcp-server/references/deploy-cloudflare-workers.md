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

This pulls a minimal template with the right deps (`agents`, `zod`) and a working `wrangler.jsonc`.

---

## `src/index.ts`

Replace the template's calculator example with your tools. Use `registerTool()` (same API as the Express scaffold — the `McpServer` instance is identical):

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { McpAgent } from "agents/mcp";
import { z } from "zod";

export class MyMCP extends McpAgent {
  server = new McpServer(
    { name: "my-service", version: "0.1.0" },
    { instructions: "Prefer search_items before get_item — IDs aren't guessable." },
  );

  async init() {
    this.server.registerTool(
      "search_items",
      {
        description: "Search items by keyword. Returns up to `limit` matches.",
        inputSchema: {
          query: z.string().describe("Search keywords"),
          limit: z.number().int().min(1).max(50).default(10),
        },
        annotations: { readOnlyHint: true },
      },
      async ({ query, limit }) => {
        const results = await upstreamApi.search(query, limit);
        return { content: [{ type: "text", text: JSON.stringify(results, null, 2) }] };
      },
    );
  }
}

export default {
  fetch(request: Request, env: Env, ctx: ExecutionContext) {
    const url = new URL(request.url);
    if (url.pathname === "/mcp") {
      return MyMCP.serve("/mcp").fetch(request, env, ctx);
    }
    return new Response("Not found", { status: 404 });
  },
};
```

`McpAgent` is Cloudflare's wrapper — it handles the streamable-HTTP transport, session routing, and Durable Object plumbing. Your code only touches `this.server`, which is the same `McpServer` class from the SDK. Everything in `tool-design.md` and `server-capabilities.md` applies unchanged.

---

## `wrangler.jsonc`

The template ships this. The Durable Objects block is **boilerplate** — `McpAgent` uses DO for session state. You don't interact with it directly.

```jsonc
{
  "name": "my-mcp-server",
  "main": "src/index.ts",
  "compatibility_date": "2025-03-10",
  "compatibility_flags": ["nodejs_compat"],
  "migrations": [{ "new_sqlite_classes": ["MyMCP"], "tag": "v1" }],
  "durable_objects": {
    "bindings": [{ "class_name": "MyMCP", "name": "MCP_OBJECT" }]
  }
}
```

If you rename the `MyMCP` class, update both `new_sqlite_classes` and `class_name` to match.

---

## Run and deploy

```bash
npx wrangler dev     # → http://localhost:8787/mcp
npx wrangler deploy  # → https://my-mcp-server.<account>.workers.dev/mcp
```

`wrangler deploy` prints the live URL. That's the URL users paste into Claude.

Secrets (upstream API keys): `npx wrangler secret put UPSTREAM_API_KEY`, then read `env.UPSTREAM_API_KEY` inside `init()`.

---

## OAuth

Cloudflare ships `@cloudflare/workers-oauth-provider` — a drop-in that handles the authorization server side (CIMD/DCR endpoints, token issuance, consent UI). It wraps your `McpAgent` and gates `/mcp` behind a token check. See `auth.md` for the protocol details; the CF template `cloudflare/ai/demos/remote-mcp-github-oauth` shows the wiring.
