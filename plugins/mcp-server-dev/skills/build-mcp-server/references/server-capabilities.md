# Server capabilities — the rest of the spec

Features beyond the three core primitives. Most are optional, a few are near-free wins.

---

## `instructions` — system prompt injection

One line of config, lands directly in Claude's system prompt. Use it for tool-use hints that don't fit in individual tool descriptions.

```typescript
const server = new McpServer(
  { name: "my-server", version: "1.0.0" },
  { instructions: "Always call search_items before get_item — IDs aren't guessable." },
);
```

```python
mcp = FastMCP("my-server", instructions="Always call search_items before get_item — IDs aren't guessable.")
```

This is the highest-leverage one-liner in the spec. If Claude keeps misusing your tools, put the fix here.

---

## Sampling — delegate LLM calls to the host

If your tool logic needs LLM inference (summarize, classify, generate), don't ship your own model client. Ask the host to do it.

```typescript
// Inside a tool handler
const result = await extra.sendRequest({
  method: "sampling/createMessage",
  params: {
    messages: [{ role: "user", content: { type: "text", text: `Summarize: ${doc}` } }],
    maxTokens: 500,
  },
}, CreateMessageResultSchema);
```

```python
# fastmcp
response = await ctx.sample("Summarize this document", context=doc)
```

**Requires client support** — check `clientCapabilities.sampling` first. Model preference hints are substring-matched (`"claude-3-5"` matches any Claude 3.5 variant).

---

## Roots — query workspace boundaries

Instead of hardcoding a root directory, ask the host which directories the user approved.

```typescript
const caps = server.getClientCapabilities();
if (caps?.roots) {
  const { roots } = await server.server.listRoots();
  // roots: [{ uri: "file:///home/user/project", name: "My Project" }]
}
```

```python
roots = await ctx.list_roots()
```

Particularly relevant for MCPB local servers — see `build-mcpb/references/local-security.md`.

---

## Logging — structured, level-aware

Better than stderr for remote servers. Client can filter by level.

```typescript
// In a tool handler
await extra.sendNotification({
  method: "notifications/message",
  params: { level: "info", logger: "my-tool", data: { msg: "Processing", count: 42 } },
});
```

```python
await ctx.info("Processing", count=42)   # also: ctx.debug, ctx.warning, ctx.error
```

Levels follow syslog: `debug`, `info`, `notice`, `warning`, `error`, `critical`, `alert`, `emergency`. Client sets minimum via `logging/setLevel`.

---

## Progress — for long-running tools

Client sends a `progressToken` in request `_meta`. Server emits progress notifications against it.

```typescript
async (args, extra) => {
  const token = extra._meta?.progressToken;
  for (let i = 0; i < 100; i++) {
    if (token !== undefined) {
      await extra.sendNotification({
        method: "notifications/progress",
        params: { progressToken: token, progress: i, total: 100, message: `Step ${i}` },
      });
    }
    await doStep(i);
  }
  return { content: [{ type: "text", text: "Done" }] };
}
```

```python
async def long_task(ctx: Context) -> str:
    for i in range(100):
        await ctx.report_progress(progress=i, total=100, message=f"Step {i}")
        await do_step(i)
    return "Done"
```

---

## Cancellation — honor the abort signal

Long tools should check the SDK-provided `AbortSignal`:

```typescript
async (args, extra) => {
  for (const item of items) {
    if (extra.signal.aborted) throw new Error("Cancelled");
    await process(item);
  }
}
```

fastmcp handles this via asyncio cancellation — no explicit check needed if your handler is properly async.

---

## Completion — autocomplete for prompt args

If you've registered prompts or resource templates with arguments, you can offer autocomplete:

```typescript
server.registerPrompt("query", {
  argsSchema: {
    table: completable(z.string(), async (partial) => tables.filter(t => t.startsWith(partial))),
  },
}, ...);
```

Low priority unless your prompts have many valid values.

---

## Which capabilities need client support?

| Feature | Server declares | Client must support | Fallback if not |
|---|---|---|---|
| `instructions` | implicit | — | — (always works) |
| Logging | `logging: {}` | — | stderr |
| Progress | — | sends `progressToken` | silently skip |
| Sampling | — | `sampling: {}` | bring your own LLM |
| Elicitation | — | `elicitation: {}` | return text, ask Claude to relay |
| Roots | — | `roots: {}` | config env var |

Check client caps via `server.getClientCapabilities()` (TS) or `ctx.session.client_params.capabilities` (fastmcp) before using the bottom three.
