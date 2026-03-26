---
name: build-mcp-app
description: This skill should be used when the user wants to build an "MCP app", add "interactive UI" or "widgets" to an MCP server, "render components in chat", build "MCP UI resources", make a tool that shows a "form", "picker", "dashboard" or "confirmation dialog" inline in the conversation, or mentions "apps SDK" in the context of MCP. Use AFTER the build-mcp-server skill has settled the deployment model, or when the user already knows they want UI widgets.
version: 0.1.0
---

# Build an MCP App (Interactive UI Widgets)

An MCP app is a standard MCP server that **also serves UI resources** — interactive components rendered inline in the chat surface. Build once, runs in Claude *and* ChatGPT and any other host that implements the apps surface.

The UI layer is **additive**. Under the hood it's still tools, resources, and the same wire protocol. If you haven't built a plain MCP server before, the `build-mcp-server` skill covers the base layer. This skill adds widgets on top.

---

## When a widget beats plain text

Don't add UI for its own sake — most tools are fine returning text or JSON. Add a widget when one of these is true:

| Signal | Widget type |
|---|---|
| Tool needs structured input Claude can't reliably infer | Form |
| User must pick from a list Claude can't rank (files, contacts, records) | Picker / table |
| Destructive or billable action needs explicit confirmation | Confirm dialog |
| Output is spatial or visual (charts, maps, diffs, previews) | Display widget |
| Long-running job the user wants to watch | Progress / live status |

If none apply, skip the widget. Text is faster to build and faster for the user.

---

## Widgets vs Elicitation — route correctly

Before building a widget, check if **elicitation** covers it. Elicitation is spec-native, zero UI code, works in any compliant host.

| Need | Elicitation | Widget |
|---|---|---|
| Confirm yes/no | ✅ | overkill |
| Pick from short enum | ✅ | overkill |
| Fill a flat form (name, email, date) | ✅ | overkill |
| Pick from a large/searchable list | ❌ (no scroll/search) | ✅ |
| Visual preview before choosing | ❌ | ✅ |
| Chart / map / diff view | ❌ | ✅ |
| Live-updating progress | ❌ | ✅ |

If elicitation covers it, use it. See `../build-mcp-server/references/elicitation.md`.

---

## Architecture: two deployment shapes

### Remote MCP app (most common)

Hosted streamable-HTTP server. Widget templates are served as **resources**; tool results reference them. The host fetches the resource, renders it in an iframe sandbox, and brokers messages between the widget and Claude.

```
┌──────────┐  tools/call   ┌────────────┐
│  Claude  │─────────────> │ MCP server │
│   host   │<── result ────│  (remote)  │
│          │  + widget ref │            │
│          │               │            │
│          │ resources/read│            │
│          │─────────────> │  widget    │
│ ┌──────┐ │<── template ──│  HTML/JS   │
│ │iframe│ │               └────────────┘
│ │widget│ │
│ └──────┘ │
└──────────┘
```

### MCPB-packaged MCP app (local + UI)

Same widget mechanism, but the server runs locally inside an MCPB bundle. Use this when the widget needs to drive a **local** application — e.g., a file picker that browses the actual local disk, a dialog that controls a desktop app.

For MCPB packaging mechanics, defer to the **`build-mcpb`** skill. Everything below applies to both shapes.

---

## How widgets attach to tools

A widget-enabled tool has **two separate registrations**:

1. **The tool** declares a UI resource via `_meta.ui.resourceUri`. Its handler returns plain text/JSON — NOT the HTML.
2. **The resource** is registered separately and serves the HTML.

When Claude calls the tool, the host sees `_meta.ui.resourceUri`, fetches that resource, renders it in an iframe, and pipes the tool's return value into the iframe via the `ontoolresult` event.

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { registerAppTool, registerAppResource, RESOURCE_MIME_TYPE }
  from "@modelcontextprotocol/ext-apps/server";
import { z } from "zod";

const server = new McpServer({ name: "contacts", version: "1.0.0" });

// 1. The tool — returns DATA, declares which UI to show
registerAppTool(server, "pick_contact", {
  description: "Open an interactive contact picker",
  inputSchema: { filter: z.string().optional() },
  _meta: { ui: { resourceUri: "ui://widgets/contact-picker.html" } },
}, async ({ filter }) => {
  const contacts = await db.contacts.search(filter);
  // Plain JSON — the widget receives this via ontoolresult
  return { content: [{ type: "text", text: JSON.stringify(contacts) }] };
});

// 2. The resource — serves the HTML
registerAppResource(
  server,
  "Contact Picker",
  "ui://widgets/contact-picker.html",
  {},
  async () => ({
    contents: [{
      uri: "ui://widgets/contact-picker.html",
      mimeType: RESOURCE_MIME_TYPE,
      text: pickerHtml,  // your HTML string
    }],
  }),
);
```

The URI scheme `ui://` is convention. The mime type MUST be `RESOURCE_MIME_TYPE` (`"text/html;profile=mcp-app"`) — this is how the host knows to render it as an interactive iframe, not just display the source.

---

## Widget runtime — the `App` class

Inside the iframe, your script talks to the host via the `App` class from `@modelcontextprotocol/ext-apps`. This is a **persistent bidirectional connection** — the widget stays alive as long as the conversation is active, receiving new tool results and sending user actions.

```html
<script type="module">
  /* ext-apps bundle inlined at build time → globalThis.ExtApps */
  /*__EXT_APPS_BUNDLE__*/
  const { App } = globalThis.ExtApps;

  const app = new App({ name: "ContactPicker", version: "1.0.0" }, {});

  // Set handlers BEFORE connecting
  app.ontoolresult = ({ content }) => {
    const contacts = JSON.parse(content[0].text);
    render(contacts);
  };

  await app.connect();

  // Later, when the user clicks something:
  function onPick(contact) {
    app.sendMessage({
      role: "user",
      content: [{ type: "text", text: `Selected contact: ${contact.id}` }],
    });
  }
</script>
```

The `/*__EXT_APPS_BUNDLE__*/` placeholder gets replaced by the server at startup with the contents of `@modelcontextprotocol/ext-apps/app-with-deps` — see `references/iframe-sandbox.md` for why this is necessary and the rewrite snippet. **Do not** `import { App } from "https://esm.sh/..."`; the iframe's CSP blocks the transitive dependency fetches and the widget renders blank.

| Method | Direction | Use for |
|---|---|---|
| `app.ontoolresult = fn` | Host → widget | Receive the tool's return value |
| `app.ontoolinput = fn` | Host → widget | Receive the tool's input args (what Claude passed) |
| `app.sendMessage({...})` | Widget → host | Inject a message into the conversation |
| `app.updateModelContext({...})` | Widget → host | Update context silently (no visible message) |
| `app.callServerTool({name, arguments})` | Widget → server | Call another tool on your server |
| `app.openLink({url})` | Widget → host | Open a URL in a new tab (sandbox blocks `window.open`) |
| `app.getHostContext()` / `app.onhostcontextchanged` | Host → widget | Theme (`light`/`dark`), locale, etc. |

`sendMessage` is the typical "user picked something, tell Claude" path. `updateModelContext` is for state that Claude should know about but shouldn't clutter the chat. `openLink` is **required** for any outbound navigation — `window.open` and `<a target="_blank">` are blocked by the sandbox attribute.

**What widgets cannot do:**
- Access the host page's DOM, cookies, or storage
- Make network calls to arbitrary origins (CSP-restricted — route through `callServerTool`)
- Open popups or navigate directly — use `app.openLink({url})`
- Load remote images reliably — inline as `data:` URLs server-side

Keep widgets **small and single-purpose**. A picker picks. A chart displays. Don't build a whole sub-app inside the iframe — split it into multiple tools with focused widgets.

---

## Scaffold: minimal picker widget

**Install:**

```bash
npm install @modelcontextprotocol/sdk @modelcontextprotocol/ext-apps zod express
```

**Server (`src/server.ts`):**

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { registerAppTool, registerAppResource, RESOURCE_MIME_TYPE }
  from "@modelcontextprotocol/ext-apps/server";
import express from "express";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { z } from "zod";

const require = createRequire(import.meta.url);
const server = new McpServer({ name: "contact-picker", version: "1.0.0" });

// Inline the ext-apps browser bundle into the widget HTML.
// The iframe CSP blocks CDN script fetches — bundling is mandatory.
const bundle = readFileSync(
  require.resolve("@modelcontextprotocol/ext-apps/app-with-deps"), "utf8",
).replace(/export\{([^}]+)\};?\s*$/, (_, body) =>
  "globalThis.ExtApps={" +
  body.split(",").map((p) => {
    const [local, exported] = p.split(" as ").map((s) => s.trim());
    return `${exported ?? local}:${local}`;
  }).join(",") + "};",
);
const pickerHtml = readFileSync("./widgets/picker.html", "utf8")
  .replace("/*__EXT_APPS_BUNDLE__*/", () => bundle);

registerAppTool(server, "pick_contact", {
  description: "Open an interactive contact picker. User selects one contact.",
  inputSchema: { filter: z.string().optional().describe("Name/email prefix filter") },
  _meta: { ui: { resourceUri: "ui://widgets/picker.html" } },
}, async ({ filter }) => {
  const contacts = await db.contacts.search(filter ?? "");
  return { content: [{ type: "text", text: JSON.stringify(contacts) }] };
});

registerAppResource(server, "Contact Picker", "ui://widgets/picker.html", {},
  async () => ({
    contents: [{ uri: "ui://widgets/picker.html", mimeType: RESOURCE_MIME_TYPE, text: pickerHtml }],
  }),
);

const app = express();
app.use(express.json());
app.post("/mcp", async (req, res) => {
  const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
  res.on("close", () => transport.close());
  await server.connect(transport);
  await transport.handleRequest(req, res, req.body);
});
app.listen(process.env.PORT ?? 3000);
```

For local-only widget apps (driving a desktop app, reading local files), swap the transport to `StdioServerTransport` and package via the `build-mcpb` skill.

**Widget (`widgets/picker.html`):**

```html
<!doctype html>
<meta charset="utf-8" />
<style>
  body { font: 14px system-ui; margin: 0; }
  ul { list-style: none; padding: 0; margin: 0; max-height: 300px; overflow-y: auto; }
  li { padding: 10px 14px; cursor: pointer; border-bottom: 1px solid #eee; }
  li:hover { background: #f5f5f5; }
  .sub { color: #666; font-size: 12px; }
</style>
<ul id="list"></ul>
<script type="module">
/*__EXT_APPS_BUNDLE__*/
const { App } = globalThis.ExtApps;
(async () => {
  const app = new App({ name: "ContactPicker", version: "1.0.0" }, {});
  const ul = document.getElementById("list");

  app.ontoolresult = ({ content }) => {
    const contacts = JSON.parse(content[0].text);
    ul.innerHTML = "";
    for (const c of contacts) {
      const li = document.createElement("li");
      li.innerHTML = `<div>${c.name}</div><div class="sub">${c.email}</div>`;
      li.addEventListener("click", () => {
        app.sendMessage({
          role: "user",
          content: [{ type: "text", text: `Selected contact: ${c.id} (${c.name})` }],
        });
      });
      ul.append(li);
    }
  };

  await app.connect();
})();
</script>
```

See `references/widget-templates.md` for more widget shapes.

---

## Design notes that save you a rewrite

**One widget per tool.** Resist the urge to build one mega-widget that does everything. One tool → one focused widget → one clear result shape. Claude reasons about these far better.

**Tool description must mention the widget.** Claude only sees the tool description when deciding what to call. "Opens an interactive picker" in the description is what makes Claude reach for it instead of guessing an ID.

**Widgets are optional at runtime.** Hosts that don't support the apps surface simply ignore `_meta.ui` and render the tool's text content normally. Since your tool handler already returns meaningful text/JSON (the widget's data), degradation is automatic — Claude sees the data directly instead of via the widget.

**Don't block on widget results for read-only tools.** A widget that just *displays* data (chart, preview) shouldn't require a user action to complete. Return the display widget *and* a text summary in the same result so Claude can continue reasoning without waiting.

**Layout-fork by item count, not by tool count.** If one use case is "show one result in detail" and another is "show many results side-by-side", don't make two tools — make one tool that accepts `items[]`, and let the widget pick a layout: `items.length === 1` → detail view, `> 1` → carousel. Keeps the server schema simple and lets Claude decide count naturally.

**Put Claude's reasoning in the payload.** A short `note` field on each item (why Claude picked it) rendered as a callout on the card gives users the reasoning inline with the choice. Mention this field in the tool description so Claude populates it.

**Normalize image shapes server-side.** If your data source returns images with wildly varying aspect ratios, rewrite to a predictable variant (e.g. square-bounded) *before* fetching for the data-URL inline. Then give the widget's image container a fixed `aspect-ratio` + `object-fit: contain` so everything sits centered.

**Follow host theme.** `app.getHostContext()?.theme` (after `connect()`) plus `app.onhostcontextchanged` for live updates. Toggle a `.dark` class on `<html>`, keep colors in CSS custom props with a `:root.dark {}` override block, set `color-scheme`. Disable `mix-blend-mode: multiply` in dark — it makes images vanish.

---

## Testing

**Claude Desktop** — current builds still require the `command`/`args` config shape (no native `"type": "http"`). Wrap with `mcp-remote` and force `http-only` transport so the SSE probe doesn't swallow widget-capability negotiation:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://localhost:3000/mcp",
               "--allow-http", "--transport", "http-only"]
    }
  }
}
```

Desktop caches UI resources aggressively. After editing widget HTML, **fully quit** (⌘Q / Alt+F4, not window-close) and relaunch to force a cold resource re-fetch.

**Headless JSON-RPC loop** — fast iteration without clicking through Desktop:

```bash
# test.jsonl — one JSON-RPC message per line
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"t","version":"0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/list"}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"your_tool","arguments":{...}}}

(cat test.jsonl; sleep 10) | npx mcp-remote http://localhost:3000/mcp --allow-http
```

The `sleep` keeps stdin open long enough to collect all responses. Parse the jsonl output with `jq` or a Python one-liner.

**Host fallback** — use a host without the apps surface (or MCP Inspector) and confirm the tool's text content degrades gracefully.

**CSP debugging** — open the iframe's own devtools console. CSP violations are the #1 reason widgets silently fail (blank rectangle, no error in the main console). See `references/iframe-sandbox.md`.

---

## Reference files

- `references/iframe-sandbox.md` — CSP/sandbox constraints, the bundle-inlining pattern, image handling
- `references/widget-templates.md` — reusable HTML scaffolds for picker / confirm / progress / display
- `references/apps-sdk-messages.md` — the `App` class API: widget ↔ host ↔ server messaging
