# Remote Streamable-HTTP MCP Server — Scaffold

Minimal working servers in both recommended frameworks. Start here, then add tools.

---

## TypeScript SDK v2 (`@modelcontextprotocol/server`)

```bash
npm init -y
npm pkg set type=module
npm install @modelcontextprotocol/server @modelcontextprotocol/express @modelcontextprotocol/node zod express
npm install -D typescript @types/express @types/node tsx
```

**`src/server.ts`**

```typescript
import { createMcpExpressApp } from "@modelcontextprotocol/express";
import { toNodeHandler } from "@modelcontextprotocol/node";
import { McpServer, createMcpHandler } from "@modelcontextprotocol/server";
import * as z from "zod/v4";

// Called once per HTTP request. Always build a new McpServer here:
// a shared instance fails as soon as two requests overlap.
function createServer(): McpServer {
  const server = new McpServer(
    { name: "my-service", version: "0.1.0" },
    { instructions: "Prefer search_items before calling get_item directly — IDs aren't guessable." },
  );

  // Pattern A: one tool per action
  server.registerTool(
    "search_items",
    {
      description: "Search items by keyword. Returns up to `limit` matches ranked by relevance.",
      inputSchema: z.object({
        query: z.string().describe("Search keywords"),
        limit: z.number().int().min(1).max(50).default(10),
      }),
      annotations: { readOnlyHint: true },
    },
    async ({ query, limit }, ctx) => {
      // ctx.mcpReq.signal is an AbortSignal — check it in long loops for cancellation
      const results = await upstreamApi.search(query, limit);
      return {
        content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
      };
    },
  );

  server.registerTool(
    "get_item",
    {
      description: "Fetch a single item by its ID.",
      inputSchema: z.object({ id: z.string() }),
      annotations: { readOnlyHint: true },
    },
    async ({ id }) => {
      const item = await upstreamApi.get(id);
      return { content: [{ type: "text", text: JSON.stringify(item) }] };
    },
  );

  return server;
}

// Local dev: accepts only localhost Host/Origin headers (DNS-rebinding protection).
// Deployed: createMcpExpressApp({ host: "0.0.0.0", allowedHosts: ["mcp.example.com"] })
const app = createMcpExpressApp();

// Streamable HTTP, stateless
const handler = toNodeHandler(createMcpHandler(createServer));
app.all("/mcp", (req, res) => void handler(req, res, req.body));

app.listen(Number(process.env.PORT ?? 3000));
```

**Stateless by design:** `createMcpHandler` builds a fresh server per request and keeps no sessions, so it scales horizontally as-is. It serves clients on the 2026-07-28 protocol revision and older 2025-era clients from the same factory. Create API clients, pools and caches once at module scope and close over them. If tools need to share state across calls, key it on the authenticated user or an ID the tool returns — see the SDK's [sessions, state and scaling](https://ts.sdk.modelcontextprotocol.io/v2/serving/sessions-state-scaling) page.

**Schemas are `z.object(...)`**, not raw `{ key: z.string() }` shapes, and Zod must be `^4.2.0`.

---

## FastMCP 3.x (Python)

```bash
pip install fastmcp
```

**`server.py`**

```python
from fastmcp import FastMCP

mcp = FastMCP(
    name="my-service",
    instructions="Prefer search_items before calling get_item directly — IDs aren't guessable.",
)

@mcp.tool(annotations={"readOnlyHint": True})
def search_items(query: str, limit: int = 10) -> list[dict]:
    """Search items by keyword. Returns up to `limit` matches ranked by relevance."""
    return upstream_api.search(query, limit)

@mcp.tool(annotations={"readOnlyHint": True})
def get_item(id: str) -> dict:
    """Fetch a single item by its ID."""
    return upstream_api.get(id)

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=3000)
```

FastMCP derives the JSON schema from type hints and the docstring becomes the tool description. Keep docstrings terse and action-oriented — they land in Claude's context window verbatim.

---

## Search + execute pattern (large API surface)

When wrapping 50+ endpoints, don't register them all. Two tools:

```typescript
const CATALOG = loadActionCatalog(); // { id, description, paramSchema }[]

server.registerTool(
  "search_actions",
  {
    description: "Find available actions matching an intent. Call this first to discover what's possible. Returns action IDs, descriptions, and parameter schemas.",
    inputSchema: z.object({ intent: z.string().describe("What you want to do, in plain English") }),
    annotations: { readOnlyHint: true },
  },
  async ({ intent }) => {
    const matches = rankActions(CATALOG, intent).slice(0, 10);
    return { content: [{ type: "text", text: JSON.stringify(matches, null, 2) }] };
  },
);

server.registerTool(
  "execute_action",
  {
    description: "Execute an action by ID. Get the ID and params schema from search_actions first.",
    inputSchema: z.object({
      action_id: z.string(),
      params: z.record(z.string(), z.unknown()),
    }),
  },
  async ({ action_id, params }) => {
    const action = CATALOG.find(a => a.id === action_id);
    if (!action) throw new Error(`Unknown action: ${action_id}`);
    validate(params, action.paramSchema);
    const result = await dispatch(action, params);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  },
);
```

`rankActions` can be simple keyword matching to start. Upgrade to embeddings if precision matters.

---

## Test it

The MCP Inspector connects to any transport and lets you poke tools interactively.

```bash
# Interactive — opens a UI on localhost:6274
npx @modelcontextprotocol/inspector
# → select "Streamable HTTP", paste http://localhost:3000/mcp, Connect
```

For scripted checks (CI, smoke tests):

```bash
npx @modelcontextprotocol/inspector --cli http://localhost:3000/mcp \
  --transport http --method tools/list

npx @modelcontextprotocol/inspector --cli http://localhost:3000/mcp \
  --transport http --method tools/call --tool-name search_items --tool-arg query=test
```

---

## Connect users

Once deployed, users add the URL directly — no install step.

| Surface | How |
|---|---|
| **Claude Code** | `claude mcp add --transport http <name> <url>` (add `--scope user` for global, `--header "Authorization: Bearer ..."` for auth) |
| **Claude Desktop / Claude.ai** | Settings → Connectors → Add custom connector. **Not** `claude_desktop_config.json` — remote servers configured there are ignored. |
| **Connector directory** | Anthropic maintains a submission guide for listing in the public connector directory. |

---

## Deploy

**Fastest path:** Cloudflare Workers — two commands from zero to a live `https://` URL on the free tier. Uses a Workers-native scaffold (not Express). → `deploy-cloudflare-workers.md`

**This Express scaffold** runs on any Node host — Render, Railway, Fly.io, a VPS. Containerize it (`node:20-slim`, copy, `npm ci`, `node dist/server.js`) and ship. FastMCP is the same story with a Python base image.

---

## Deployment checklist

- [ ] `POST /mcp` responds to `initialize` with server capabilities
- [ ] `tools/list` returns your tools with complete schemas
- [ ] Errors return structured MCP errors, not HTTP 500s with HTML bodies
- [ ] CORS headers set if browser clients will connect
- [ ] `Origin` header validated on `/mcp` (spec MUST — DNS rebinding prevention)
- [ ] `MCP-Protocol-Version` header honored (return 400 for unsupported versions)
- [ ] `instructions` field set if tool-use needs hints
- [ ] Health check endpoint separate from `/mcp` (hosts poll it)
- [ ] Secrets from env vars, never hardcoded
- [ ] If OAuth: CIMD or DCR endpoint implemented — see `auth.md`
