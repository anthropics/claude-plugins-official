# Connector-directory submission checklist

Pre-flight before submitting a remote MCP app to the Claude connector
directory. Each item is a hard review criterion.

| Area | Requirement |
|---|---|
| **Auth** | OAuth (DCR or CIMD) or **`none`** (authless). Static bearer tokens are private-deploy only and block listing. Authless is valid for public-data servers — the server holds any upstream API keys. |
| **Tool annotations** | Every tool sets `annotations.title` plus the relevant hints: `readOnlyHint: true` for fetch/search tools, `destructiveHint` / `idempotentHint` for writes, `openWorldHint: true` if the tool reaches an external system. |
| **Tool names** | ≤ 64 characters, snake/kebab case. |
| **Widget layout** | Inline height ≤ 500px, no nested scroll containers, 44pt minimum touch targets, WCAG-AA contrast in both themes. |
| **Theming** | `html, body { background: transparent }`, `<meta name="color-scheme" content="light dark">`, adopt host CSS tokens via `applyHostStyleVariables`. |
| **External links** | Use `app.openLink`. Declare each origin (e.g. `https://api.example.com`) in the connector's *Allowed link URIs* so the link skips the confirm modal. |
| **Helper tools** | Widget-only tools (geometry/image fetchers) carry `_meta.ui.visibility: ["app"]` so they don't appear in Claude's tool list. |
| **Screenshots** | 3–5 PNGs, ≥ 1000px wide, cropped to the app response only — no prompt text in frame. |

See `abuse-protection.md` for rate-limit and IP-tiering guidance once the
authless endpoint is public.
