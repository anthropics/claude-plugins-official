# Resources & Prompts — the other two primitives

MCP defines three server-side primitives. Tools are model-controlled (Claude decides when to call them). The other two are different:

- **Resources** are application-controlled — the host decides what to pull into context
- **Prompts** are user-controlled — surfaced as slash commands or menu items

Most servers only need tools. Reach for these when the shape of your integration doesn't fit "Claude calls a function."

---

## Resources

A resource is data identified by a URI. Unlike a tool, it's not *called* — it's *read*. The host browses available resources and decides which to load into context.

**When a resource beats a tool:**
- Large reference data (docs, schemas, configs) that Claude should be able to browse
- Content that changes independently of conversation (log files, live data)
- Anything where "Claude decides to fetch" is the wrong mental model

**When a tool is better:**
- The operation has side effects
- The result depends on parameters Claude chooses
- You want Claude (not the host UI) to decide when to pull it in

### Static resources

```typescript
// TypeScript SDK
server.registerResource(
  "config",
  "config://app/settings",
  { name: "App Settings", description: "Current configuration", mimeType: "application/json" },
  async (uri) => ({
    contents: [{ uri: uri.href, mimeType: "application/json", text: JSON.stringify(config) }],
  }),
);
```

```python
# fastmcp
@mcp.resource("config://app/settings")
def get_settings() -> str:
    """Current application configuration."""
    return json.dumps(config)
```

### Dynamic resources (URI templates)

RFC 6570 templates let one registration serve many URIs:

```typescript
import { ResourceTemplate } from "@modelcontextprotocol/sdk/server/mcp.js";

server.registerResource(
  "file",
  new ResourceTemplate("file:///{path}", { list: undefined }),
  { name: "File", description: "Read a file from the workspace" },
  async (uri, { path }) => ({
    contents: [{ uri: uri.href, text: await fs.readFile(path, "utf8") }],
  }),
);
```

```python
@mcp.resource("file:///{path}")
def read_file(path: str) -> str:
    return Path(path).read_text()
```

### Subscriptions

Resources can notify the client when they change. Declare `subscribe: true` in capabilities, then emit `notifications/resources/updated`. The host re-reads. Useful for log tails, live dashboards, watched files.

---

## Prompts

A prompt is a parameterized message template. The host surfaces it as a slash command or menu item. The user picks it, fills in arguments, and the resulting messages land in the conversation.

**When to use:** canned workflows users run repeatedly — `/summarize-thread`, `/draft-reply`, `/explain-error`. Near-zero code, high UX leverage.

```typescript
server.registerPrompt(
  "summarize",
  {
    title: "Summarize document",
    description: "Generate a concise summary of the given text",
    argsSchema: { text: z.string(), max_words: z.string().optional() },
  },
  ({ text, max_words }) => ({
    messages: [{
      role: "user",
      content: { type: "text", text: `Summarize in ${max_words ?? "100"} words:\n\n${text}` },
    }],
  }),
);
```

```python
@mcp.prompt
def summarize(text: str, max_words: str = "100") -> str:
    """Generate a concise summary of the given text."""
    return f"Summarize in {max_words} words:\n\n{text}"
```

**Constraints:**
- Arguments are **string-only** (no numbers, booleans, objects) — convert inside the handler
- Returns a `messages[]` array — can include embedded resources/images, not just text
- No side effects — the handler just builds a message, it doesn't *do* anything

---

## Quick decision table

| You want to... | Use |
|---|---|
| Let Claude fetch something on demand, with parameters | **Tool** |
| Expose browsable context (files, docs, schemas) | **Resource** |
| Expose a dynamic family of things (`db://{table}`) | **Resource template** |
| Give users a one-click workflow | **Prompt** |
| Ask the user something mid-tool | **Elicitation** (see `elicitation.md`) |
