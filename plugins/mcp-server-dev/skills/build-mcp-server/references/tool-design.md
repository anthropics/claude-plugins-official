# Tool Design — Writing Tools Claude Uses Correctly

Tool schemas and descriptions are prompt engineering. They land directly in Claude's context and determine whether Claude picks the right tool with the right arguments. Most MCP integration bugs trace back to vague descriptions or loose schemas.

---

## Descriptions

**The description is the contract.** It's the only thing Claude reads before deciding whether to call the tool. Write it like a one-line manpage entry plus disambiguating hints.

### Good

```
search_issues — Search issues by keyword across title and body. Returns up
to `limit` results ranked by recency. Does NOT search comments or PRs —
use search_comments / search_prs for those.
```

- Says what it does
- Says what it returns
- Says what it *doesn't* do (prevents wrong-tool calls)

### Bad

```
search_issues — Searches for issues.
```

Claude will call this for anything vaguely search-shaped, including things it can't do.

### Disambiguate siblings

When two tools are similar, each description should say when to use the *other* one:

```
get_user      — Fetch a user by ID. If you only have an email, use find_user_by_email.
find_user_by_email — Look up a user by email address. Returns null if not found.
```

---

## Parameter schemas

**Tight schemas prevent bad calls.** Every constraint you express in the schema is one fewer thing that can go wrong at runtime.

| Instead of | Use |
|---|---|
| `z.string()` for an ID | `z.string().regex(/^usr_[a-z0-9]{12}$/)` |
| `z.number()` for a limit | `z.number().int().min(1).max(100).default(20)` |
| `z.string()` for a choice | `z.enum(["open", "closed", "all"])` |
| optional with no hint | `.optional().describe("Defaults to the caller's workspace")` |

**Describe every parameter.** The `.describe()` text shows up in the schema Claude sees. Omitting it is leaving money on the table.

```typescript
{
  query: z.string().describe("Keywords to search for. Supports quoted phrases."),
  status: z.enum(["open", "closed", "all"]).default("open")
    .describe("Filter by status. Use 'all' to include closed items."),
  limit: z.number().int().min(1).max(50).default(10)
    .describe("Max results. Hard cap at 50."),
}
```

---

## Return shapes

Claude reads whatever you put in `content[].text`. Make it parseable.

**Do:**
- Return JSON for structured data (`JSON.stringify(result, null, 2)`)
- Return short confirmations for mutations (`"Created issue #123"`)
- Include IDs Claude will need for follow-up calls
- Truncate huge payloads and say so (`"Showing 10 of 847 results. Refine the query to narrow down."`)

**Don't:**
- Return raw HTML
- Return megabytes of unfiltered API response
- Return bare success with no identifier (`"ok"` after a create — Claude can't reference what it made)

---

## How many tools?

| Tool count | Guidance |
|---|---|
| 1–15 | One tool per action. Sweet spot. |
| 15–30 | Still workable. Audit for near-duplicates that could merge. |
| 30+ | Switch to search + execute. Optionally promote the top 3–5 to dedicated tools. |

The ceiling isn't a hard protocol limit — it's context-window economics. Every tool schema is tokens Claude spends *every turn*. Thirty tools with rich schemas can eat 3–5k tokens before the conversation even starts.

---

## Errors

Return MCP tool errors, not exceptions that crash the transport. Include enough detail for Claude to recover or retry differently.

```typescript
if (!item) {
  return {
    isError: true,
    content: [{
      type: "text",
      text: `Item ${id} not found. Use search_items to find valid IDs.`,
    }],
  };
}
```

The hint ("use search_items…") turns a dead end into a next step.

---

## Tool annotations

Hints the host uses for UX — red confirm button for destructive, auto-approve for readonly. All default to unset (host assumes worst case).

| Annotation | Meaning | Host behavior |
|---|---|---|
| `readOnlyHint: true` | No side effects | May auto-approve |
| `destructiveHint: true` | Deletes/overwrites | Confirmation dialog |
| `idempotentHint: true` | Safe to retry | May retry on transient error |
| `openWorldHint: true` | Talks to external world (web, APIs) | May show network indicator |

```typescript
server.registerTool("delete_file", {
  description: "Delete a file",
  inputSchema: { path: z.string() },
  annotations: { destructiveHint: true, idempotentHint: false },
}, handler);
```

```python
@mcp.tool(annotations={"destructiveHint": True, "idempotentHint": False})
def delete_file(path: str) -> str:
    ...
```

Pair with the read/write split advice in `build-mcpb/references/local-security.md` — mark every read tool `readOnlyHint: true`.

---

## Structured output

`JSON.stringify(result)` in a text block works, but the spec has first-class typed output: `outputSchema` + `structuredContent`. Clients can validate.

```typescript
server.registerTool("get_weather", {
  description: "Get current weather",
  inputSchema: { city: z.string() },
  outputSchema: { temp: z.number(), conditions: z.string() },
}, async ({ city }) => {
  const data = await fetchWeather(city);
  return {
    content: [{ type: "text", text: JSON.stringify(data) }],  // backward compat
    structuredContent: data,                                    // typed output
  };
});
```

Always include the text fallback — not all hosts read `structuredContent` yet.

---

## Content types beyond text

Tools can return more than strings:

| Type | Shape | Use for |
|---|---|---|
| `text` | `{ type: "text", text: string }` | Default |
| `image` | `{ type: "image", data: base64, mimeType }` | Screenshots, charts, diagrams |
| `audio` | `{ type: "audio", data: base64, mimeType }` | TTS output, recordings |
| `resource_link` | `{ type: "resource_link", uri, name?, description? }` | Pointer — client fetches later |
| `resource` (embedded) | `{ type: "resource", resource: { uri, text\|blob, mimeType } }` | Inline the full content |

**`resource_link` vs embedded:** link for large payloads or when the client might not need it (let them decide). Embed when it's small and always needed.
