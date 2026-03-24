# Multi-View App Architecture

When a single-purpose widget isn't enough — when you have 5+ UI tools that share styling, state patterns, or a data model — consider building a **multi-view MCP app**: one React (or framework) SPA that dispatches to the right view based on which tool was called.

This doc covers the production patterns for that architecture. It assumes you've read the main `build-mcp-app` skill and the `widget-templates.md` reference.

> **Reference implementation:** [`nashville-charts-app`](https://github.com/bryankthompson/nashville-charts-app) on GitHub / npm demonstrates every pattern below. Install with `npx nashville-charts-app --stdio`.

---

## Single resource, action-dispatched views

Instead of one HTML file per tool, register **one shared resource** and point all UI tools at it. Each tool returns JSON with an `action` field that tells the app which view to render.

**Server side:**

```typescript
const RESOURCE_URI = "ui://my-app/app.html";

// Tool A — returns action + data
registerAppTool(server, "show_dashboard", {
  description: "Show the analytics dashboard",
  inputSchema: { range: z.enum(["week", "month"]) },
  _meta: { ui: { resourceUri: RESOURCE_URI } },
}, async ({ range }) => {
  const stats = await fetchStats(range);
  return {
    content: [{ type: "text", text: JSON.stringify({ action: "dashboard", stats }) }],
  };
});

// Tool B — same resource, different action
registerAppTool(server, "show_details", {
  description: "Show detail view for a specific item",
  inputSchema: { id: z.string() },
  _meta: { ui: { resourceUri: RESOURCE_URI } },
}, async ({ id }) => {
  const item = await fetchItem(id);
  return {
    content: [{ type: "text", text: JSON.stringify({ action: "detail", item }) }],
  };
});

// One resource serves all views
registerAppResource(server, "App", RESOURCE_URI, {},
  async () => ({
    contents: [{ uri: RESOURCE_URI, mimeType: RESOURCE_MIME_TYPE, text: appHtml }],
  }),
);
```

**Widget side (React):**

```tsx
function App() {
  const [view, setView] = useState(null);
  const { app } = useApp({
    appInfo: { name: "MyApp", version: "1.0.0" },
    onAppCreated: (app) => {
      app.ontoolresult = async (result) => {
        const data = JSON.parse(result.content[0].text);
        if (data.action) setView(data);
      };
    },
  });

  if (!view) return <div>Waiting for tool call...</div>;

  switch (view.action) {
    case "dashboard": return <Dashboard stats={view.stats} app={app} />;
    case "detail":    return <DetailView item={view.item} app={app} />;
    default:          return <div>Unknown view</div>;
  }
}
```

**Why this beats multiple HTML files:**
- Shared CSS, shared components, shared state (theme, loading indicators)
- One build artifact to deploy and cache
- Consistent UX across all views — users don't see a flash between different iframes
- The dispatch is just a `switch` on a string — trivial to extend

---

## Model context updates

`updateModelContext()` tells the LLM what the user is currently looking at — without adding a visible message to the chat. This is critical for multi-step workflows where Claude needs to reason about the current UI state.

**What to send:** Structured state, not a prose description. YAML or JSON works well.

```tsx
useEffect(() => {
  if (!view || !app) return;

  const ctx = {
    view: view.action,
    ...(view.action === "dashboard" && {
      range: view.stats.range,
      itemCount: view.stats.items.length,
    }),
    ...(view.action === "detail" && {
      itemId: view.item.id,
      itemName: view.item.name,
    }),
  };

  app.updateModelContext({
    content: [{ type: "text", text: JSON.stringify(ctx) }],
  }).catch(() => {
    // Host may not support updateModelContext — degrade silently
  });
}, [app, view]);
```

**When to send:** On every view change. Don't send on every keystroke or scroll — just when the semantic state changes (new view, new data, user selection).

**Always catch:** Not all hosts support `updateModelContext()`. Wrap in `.catch()` so the app doesn't break in hosts that don't implement it.

---

## Teardown guards

After the host calls `onteardown`, other callbacks (`ontoolresult`, `onhostcontextchanged`) may still fire. Without a guard, these late callbacks can cause React state updates on an unmounted component.

```tsx
const tornDown = useRef(false);

app.onteardown = async () => {
  tornDown.current = true;
  setView(null);
  return {};
};

app.ontoolresult = async (result) => {
  if (tornDown.current) return;  // Guard
  const data = JSON.parse(result.content[0].text);
  if (data.action) setView(data);
};

app.onhostcontextchanged = () => {
  if (tornDown.current) return;  // Guard
  setHostContext(app.getHostContext());
};
```

Use a `useRef` (not `useState`) — refs update synchronously and don't trigger re-renders.

---

## Bidirectional tool calls from components

When a UI component needs to call a server tool (e.g., a "Transpose" button, a "Load More" link), use `app.callServerTool()` and flow the result back through the parent's dispatch.

```tsx
// Parent holds the dispatch
function App() {
  const handleToolResult = useCallback((result) => {
    const data = JSON.parse(result.content[0].text);
    if (data.action) setView(data);
  }, []);

  return <DetailView item={view.item} app={app} onToolResult={handleToolResult} />;
}

// Child calls tools, parent re-dispatches
function DetailView({ item, app, onToolResult }) {
  const [loading, setLoading] = useState(false);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      const result = await app.callServerTool({
        name: "show_details",
        arguments: { id: item.id },
      });
      onToolResult(result);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>{item.name}</h1>
      <button onClick={handleRefresh} disabled={loading}>
        {loading ? "Loading..." : "Refresh"}
      </button>
    </div>
  );
}
```

**Pattern:** Components don't set the view directly — they call tools and the parent handles the result. This keeps the data flow unidirectional: tool result -> parent dispatch -> child render.

**App-only tools:** For tools that should only be callable from the widget (not by the LLM), use `server.registerTool` (not `registerAppTool` — these tools don't render a UI resource) with `visibility: ["app"]`:

```typescript
server.registerTool("internal_action", {
  description: "...",
  inputSchema: { ... },
  _meta: { ui: { visibility: ["app"] } },
}, handler);
```

---

## Build pipeline: Vite + esbuild

A multi-view app needs a framework build (React, Vue, etc.) bundled into a single HTML file, plus a separate server bundle. Two-step build:

**Step 1 — Vite bundles the SPA into one HTML file:**

```typescript
// vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";

export default defineConfig({
  plugins: [react(), viteSingleFile()],
  build: {
    rollupOptions: { input: process.env.INPUT },  // e.g., INPUT=app.html
    outDir: "dist",
    emptyOutDir: false,  // Don't delete dist — esbuild writes here too
  },
});
```

`vite-plugin-singlefile` inlines all JS and CSS into the HTML. The output is a self-contained `dist/app.html` — no external chunks, no asset files.

**Step 2 — esbuild bundles the server:**

```bash
# Server module
npx esbuild server/server.ts --bundle --platform=node --format=esm \
  --outfile=dist/server.js --packages=external

# CLI entry point (with shebang for npx)
npx esbuild main.ts --bundle --platform=node --format=esm \
  --outfile=dist/index.js --packages=external \
  --banner:js='#!/usr/bin/env node'
```

`--packages=external` keeps npm dependencies as imports (not bundled). The shebang banner makes `dist/index.js` directly executable.

**Combined build script:**

```json
{
  "build": "cross-env INPUT=app.html vite build && npx esbuild server/server.ts --bundle --platform=node --format=esm --outfile=dist/server.js --packages=external && npx esbuild main.ts --bundle --platform=node --format=esm --outfile=dist/index.js --packages=external --banner:js='#!/usr/bin/env node'"
}
```

**Path resolution (dev vs. prod):**

```typescript
// Works in both TypeScript (dev) and compiled JS (prod)
const DIST_DIR = import.meta.filename.endsWith(".ts")
  ? path.join(import.meta.dirname, "..", "dist")   // Running .ts directly
  : import.meta.dirname;                             // Running compiled .js

const appHtml = await fs.promises.readFile(
  path.join(DIST_DIR, "app.html"), "utf-8"
);
```

---

## Dual transport: HTTP + stdio

Support both transports from one codebase. Use a server factory function and a CLI flag.

```typescript
// main.ts
import { createServer } from "./server/server.js";

const useStdio = process.argv.includes("--stdio");

if (useStdio) {
  startStdio(createServer);
} else {
  startHTTP(createServer);
}
```

**HTTP (stateless, one server per request):**

```typescript
async function startHTTP(createServer) {
  const app = express();
  app.use(express.json());

  app.all("/mcp", async (req, res) => {
    const server = createServer();  // Fresh per request
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,  // Stateless
    });
    res.on("close", () => {
      transport.close();
      server.close();
    });
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
  });

  app.listen(process.env.PORT ?? 3001);
}
```

**stdio (persistent, one server for the session):**

```typescript
async function startStdio(createServer) {
  const server = createServer();
  const transport = new StdioServerTransport();
  await server.connect(transport);
  // Server stays alive until the process exits
}
```

**Graceful shutdown** for HTTP:

```typescript
const shutdown = () => {
  httpServer.close(() => process.exit(0));
};
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
```

---

## Debugging tips

**Keep stdout clean.** In stdio mode, stdout IS the MCP protocol. All debug output must go to stderr:

```typescript
console.error("[DEBUG] Tool called:", toolName);  // stderr — safe
console.log("...");                                // stdout — breaks protocol
```

**Extension detection.** The MCP SDK's Zod schema strips unknown fields from `capabilities` — including `extensions`, which signals UI support. To check if the client supports your widgets, intercept raw messages before SDK parsing:

```typescript
transport.onmessage = (msg) => {
  if (msg?.method === "initialize") {
    const extensions = msg.params?.capabilities?.extensions;
    if (extensions) {
      console.error("[DEBUG] Client supports extensions:", JSON.stringify(extensions));
    }
  }
};
```

Compare raw messages with SDK-parsed `server.getClientCapabilities()` to diagnose stripping.

**Resource caching in Claude Desktop.** After editing widget HTML, fully quit (Cmd+Q) and relaunch. Window-close doesn't clear the resource cache.

---

## Prompt templates as workflow orchestration

MCP prompts can guide the LLM through multi-tool workflows — acting as lightweight choreography:

```typescript
server.registerPrompt("analyze_pipeline", {
  title: "Run Full Analysis",
  description: "Fetch data, visualize, and summarize",
}, () => ({
  messages: [{
    role: "user",
    content: {
      type: "text",
      text: "Run a full analysis: use fetch-data to pull the latest numbers, " +
            "show-dashboard to visualize them, then summarize the key insights.",
    },
  }],
}));
```

The prompt tells the LLM which tools to call in which order. No dynamic data — just instructions. This surfaces as a slash-command in hosts that support prompts, giving users a one-click workflow trigger.
