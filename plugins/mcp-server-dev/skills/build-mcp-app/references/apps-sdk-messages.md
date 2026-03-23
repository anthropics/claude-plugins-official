# ext-apps messaging — widget ↔ host ↔ server

The `@modelcontextprotocol/ext-apps` package provides the `App` class (browser side) and `registerAppTool`/`registerAppResource` helpers (server side). Messaging is bidirectional and persistent.

---

## Widget → Host

### `app.sendMessage({ role, content })`

Inject a visible message into the conversation. This is how user actions become conversation turns.

```js
app.sendMessage({
  role: "user",
  content: [{ type: "text", text: "User selected order #1234" }],
});
```

The message appears in chat and Claude responds to it. Use `role: "user"` — the widget speaks on the user's behalf.

### `app.updateModelContext({ content })`

Update Claude's context **silently** — no visible message. Use for state that informs but doesn't warrant a chat bubble.

```js
app.updateModelContext({
  content: [{ type: "text", text: "Currently viewing: orders from last 30 days" }],
});
```

### `app.callServerTool({ name, arguments })`

Call a tool on your MCP server directly, bypassing Claude. Returns the tool result.

```js
const result = await app.callServerTool({
  name: "fetch_order_details",
  arguments: { orderId: "1234" },
});
```

Use for data fetches that don't need Claude's reasoning — pagination, detail lookups, refreshes.

### `app.openLink({ url })`

Open a URL in a new browser tab, host-mediated. **Required** for any outbound navigation — the iframe sandbox blocks `window.open()` and `<a target="_blank">`.

```js
await app.openLink({ url: "https://example.com/cart" });
```

For anchors in rendered HTML, intercept the click:

```js
card.querySelector("a").addEventListener("click", (e) => {
  e.preventDefault();
  app.openLink({ url: e.currentTarget.href });
});
```

### `app.downloadFile({ name, mimeType, content })`

Host-mediated download (sandbox blocks direct `<a download>`). `content` is a base64 string.

---

## Host → Widget

### `app.ontoolresult = ({ content }) => {...}`

Fires when the tool handler's return value is piped to the widget. This is the primary data-in path.

```js
app.ontoolresult = ({ content }) => {
  const data = JSON.parse(content[0].text);
  renderUI(data);
};
```

**Set this BEFORE `await app.connect()`** — the result may arrive immediately after connection.

### `app.ontoolinput = ({ arguments }) => {...}`

Fires with the arguments Claude passed to the tool. Useful if the widget needs to know what was asked for (e.g., highlight the search term).

### `app.getHostContext()` / `app.onhostcontextchanged = (ctx) => {...}`

Read and subscribe to host context — `theme` (`"light"` / `"dark"`), locale, etc. Call `getHostContext()` **after** `connect()`. Subscribe for live updates (user toggles dark mode mid-conversation).

```js
const applyTheme = (t) =>
  document.documentElement.classList.toggle("dark", t === "dark");

app.onhostcontextchanged = (ctx) => applyTheme(ctx.theme);
await app.connect();
applyTheme(app.getHostContext()?.theme);
```

Keep colors in CSS custom props with a `:root.dark {}` override block and set `color-scheme: light | dark` so native form controls follow.

---

## Server → Widget (progress)

For long-running operations, emit progress notifications. The client sends a `progressToken` in the request's `_meta`; the server emits against it.

```typescript
// In the tool handler
async ({ query }, extra) => {
  const token = extra._meta?.progressToken;
  for (let i = 0; i < steps.length; i++) {
    if (token !== undefined) {
      await extra.sendNotification({
        method: "notifications/progress",
        params: { progressToken: token, progress: i, total: steps.length, message: steps[i].name },
      });
    }
    await steps[i].run();
  }
  return { content: [{ type: "text", text: "Complete" }] };
}
```

No `{ notify }` destructure — `extra` is `RequestHandlerExtra`; progress goes through `sendNotification`.

---

## Lifecycle

1. Claude calls a tool with `_meta.ui.resourceUri` declared
2. Host fetches the resource (your HTML) and renders it in an iframe
3. Widget script runs, sets handlers, calls `await app.connect()`
4. Host pipes the tool's return value → `ontoolresult` fires
5. Widget renders, user interacts
6. Widget calls `sendMessage` / `updateModelContext` / `callServerTool` as needed
7. Widget persists until conversation context moves on — subsequent calls to the same tool reuse the iframe and fire `ontoolresult` again

There's no explicit "submit and close" — the widget is a long-lived surface.

---

## Sandbox & CSP gotchas

The iframe runs under both an HTML `sandbox` attribute **and** a restrictive Content-Security-Policy. The practical effect is that almost nothing external is allowed — widgets should be self-contained.

| Symptom | Cause | Fix |
|---|---|---|
| Widget is a blank rectangle, nothing renders | CDN `import` of ext-apps blocked (transitive SDK fetches) | **Inline** the `ext-apps/app-with-deps` bundle — see `iframe-sandbox.md` |
| Widget renders but JS doesn't run | Inline event handlers blocked | Use `addEventListener` — never `onclick="..."` in HTML |
| `eval` / `new Function` errors | Script-src restriction | Don't use them; use JSON.parse for data |
| `fetch()` to your API fails | Cross-origin blocked | Route through `app.callServerTool()` instead |
| External CSS doesn't load | `style-src` restriction | Inline styles in a `<style>` tag |
| Fonts don't load | `font-src` restriction | Use system fonts (`font: 14px system-ui`) |
| External `<img src>` broken | CSP `img-src` + referrer hotlink blocking | Fetch server-side, inline as `data:` URL in the tool result payload |
| `window.open()` does nothing | Sandbox lacks `allow-popups` | Use `app.openLink({url})` |
| `<a target="_blank">` does nothing | Same | Intercept click → `preventDefault()` → `app.openLink` |
| Edited HTML doesn't appear in Desktop | Desktop caches UI resources | Fully quit (⌘Q) + relaunch, not just window-close |

When in doubt, open the **iframe's own** devtools console (not the main app's) — CSP violations log there. See `iframe-sandbox.md` for the bundle-inlining pattern.
