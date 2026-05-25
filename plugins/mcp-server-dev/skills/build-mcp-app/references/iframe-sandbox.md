# Iframe sandbox constraints

MCP-app widgets run inside a sandboxed `<iframe>` in the host (Claude Desktop,
claude.ai). The sandbox and CSP attributes lock down what the widget can do.
Every item below was observed failing with a silent blank iframe until the
fix was applied — the error only appears in the iframe's own devtools console,
not the host's.

---

## Problem → fix table

| Symptom | Root cause | Fix |
|---|---|---|
| Widget renders as blank rectangle, no error | CSP `script-src` blocks esm.sh fetching transitive `@modelcontextprotocol/sdk` deps | Inline the `ext-apps/app-with-deps` bundle into the HTML |
| `window.open()` does nothing | Sandbox lacks `allow-popups` | Use `app.openLink({ url })` |
| `<a target="_blank">` does nothing | Same | `e.preventDefault()` + `app.openLink({ url })` on click |
| External `<img src>` broken | CSP `img-src` + referrer hotlink blocking | Fetch server-side, ship as `data:` URL in the tool result payload |
| Widget edits don't appear after server restart | Host caches UI resources | Fully quit the host (⌘Q / Alt+F4) and relaunch |
| Top-level `await` throws | Older iframe contexts | Wrap module body in an async IIFE |

---

## Inlining the ext-apps bundle

`@modelcontextprotocol/ext-apps` ships a self-contained browser build at the
`app-with-deps` export (~300KB). It's minified ESM ending in `export{…}`; to
use it from an inline `<script type="module">` block, rewrite the export
statement into a global assignment at build time:

```ts
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);

const bundle = readFileSync(
  require.resolve("@modelcontextprotocol/ext-apps/app-with-deps"),
  "utf8",
).replace(/export\{([^}]+)\};?\s*$/, (_, body) =>
  "globalThis.ExtApps={" +
  body.split(",").map((pair) => {
    const [local, exported] = pair.split(" as ").map((s) => s.trim());
    return `${exported ?? local}:${local}`;
  }).join(",") + "};",
);

const widgetHtml = readFileSync("./widgets/widget.html", "utf8")
  .replace("/*__EXT_APPS_BUNDLE__*/", () => bundle);
```

Widget side:

```html
<script type="module">
/*__EXT_APPS_BUNDLE__*/
const { App } = globalThis.ExtApps;
(async () => {
  const app = new App({ name: "…", version: "…" }, {});
  // …
})();
</script>
```

The `() => bundle` replacer form (rather than a bare string) is important —
`String.replace` interprets `$…` sequences in a string replacement, and the
minified bundle is full of them.

---

## Outbound links

```js
// ✗ blocked
window.open(url, "_blank");
// ✗ blocked
<a href="…" target="_blank">…</a>

// ✓ host-mediated
await app.openLink({ url });
```

Intercept anchor clicks:

```js
el.addEventListener("click", (e) => {
  e.preventDefault();
  app.openLink({ url: el.href });
});
```

---

## External images

CSP `img-src` defaults (plus many CDN referrer policies) block
`<img src="https://external-cdn/…">` from loading. Inline them server-side in
the tool handler:

```ts
async function toDataUrl(url: string): Promise<string | undefined> {
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(5000) });
    if (!res.ok) return undefined;
    const buf = Buffer.from(await res.arrayBuffer());
    const mime = res.headers.get("content-type") ?? "image/jpeg";
    return `data:${mime};base64,${buf.toString("base64")}`;
  } catch {
    return undefined;
  }
}

// in the tool handler
const inlined = await Promise.all(
  items.map(async (it) =>
    it.thumb ? { ...it, thumb: await toDataUrl(it.thumb) ?? it.thumb } : it,
  ),
);
```

Add `referrerpolicy="no-referrer"` on the `<img>` as a fallback for any URL
that survives un-inlined.

---

## Theme & host styles

The host renders the iframe inside its own card chrome — paint a **transparent** background and adopt host CSS tokens so the widget blends in across light/dark and across hosts.

```html
<meta name="color-scheme" content="light dark" />
```

```css
:root {
  --ink:  var(--color-text-primary,   #0f1111);
  --sub:  var(--color-text-secondary, #5a6270);
  --line: var(--color-border-default, #e3e6ea);
}
html, body { background: transparent; color: var(--ink); }
:root.dark .thumb { mix-blend-mode: normal; } /* multiply → images vanish in dark */
```

```js
const { App, applyHostStyleVariables } = globalThis.ExtApps;

function applyHostContext(ctx) {
  document.documentElement.classList.toggle("dark", ctx?.theme === "dark");
  if (ctx?.styles?.variables) applyHostStyleVariables(ctx.styles.variables);
}
app.onhostcontextchanged = applyHostContext;
await app.connect();
applyHostContext(app.getHostContext());
```

`applyHostStyleVariables` writes the host's `--color-*` / `--font-*` / `--border-radius-*` tokens onto `:root`; the hex values above are fallbacks for hosts that don't supply them.

---

## Debugging

The iframe has its own console. In Claude Desktop, open DevTools (View → Toggle
Developer Tools), then switch the context dropdown (top-left of the Console
tab) from "top" to the widget's iframe. CSP violations, uncaught exceptions,
and import errors all surface there — the host's main console stays silent.
