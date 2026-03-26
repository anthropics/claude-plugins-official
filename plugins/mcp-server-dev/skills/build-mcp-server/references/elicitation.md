# Elicitation — spec-native user input

Elicitation lets a server pause mid-tool-call and ask the user for structured input. The client renders a native form (no iframe, no HTML). User fills it, server continues.

**This is the right answer for simple input.** Widgets (`build-mcp-app`) are for when you need rich UI — charts, searchable lists, visual previews. If you just need a confirmation, a picked option, or a few form fields, elicitation is simpler, spec-native, and works in any compliant host.

---

## ⚠️ Check capability first — support is new

Host support is very recent:

| Host | Status |
|---|---|
| Claude Code | ✅ since v2.1.76 (both `form` and `url` modes) |
| Claude Desktop | Unconfirmed — likely not yet or very recent |
| claude.ai | Unknown |

**The SDK throws `CapabilityNotSupported` if the client doesn't advertise elicitation.** There is no graceful degradation built in. You MUST check and have a fallback.

### The canonical pattern

```typescript
server.registerTool("delete_all", {
  description: "Delete all items after confirmation",
  inputSchema: {},
}, async ({}, extra) => {
  const caps = server.getClientCapabilities();
  if (caps?.elicitation) {
    const r = await server.elicitInput({
      mode: "form",
      message: "Delete all items? This cannot be undone.",
      requestedSchema: {
        type: "object",
        properties: { confirm: { type: "boolean", title: "Confirm deletion" } },
        required: ["confirm"],
      },
    });
    if (r.action === "accept" && r.content?.confirm) {
      await deleteAll();
      return { content: [{ type: "text", text: "Deleted." }] };
    }
    return { content: [{ type: "text", text: "Cancelled." }] };
  }
  // Fallback: return text asking Claude to relay the question
  return { content: [{ type: "text", text: "Confirmation required. Please ask the user: 'Delete all items? This cannot be undone.' Then call this tool again with their answer." }] };
});
```

```python
# fastmcp
from fastmcp import Context
from fastmcp.exceptions import CapabilityNotSupported

@mcp.tool
async def delete_all(ctx: Context) -> str:
    try:
        result = await ctx.elicit("Delete all items? This cannot be undone.", response_type=bool)
        if result.action == "accept" and result.data:
            await do_delete()
            return "Deleted."
        return "Cancelled."
    except CapabilityNotSupported:
        return "Confirmation required. Ask the user to confirm deletion, then retry."
```

---

## Schema constraints

Elicitation schemas are deliberately limited — keep forms simple:

- **Flat objects only** — no nesting, no arrays of objects
- **Primitives only** — `string`, `number`, `integer`, `boolean`, `enum`
- String formats limited to: `email`, `uri`, `date`, `date-time`
- Use `title` and `description` on each property — they become form labels

If your data doesn't fit these constraints, that's the signal to escalate to a widget.

---

## Three-state response

| Action | Meaning | `content` present? |
|---|---|---|
| `accept` | User submitted the form | ✅ validated against your schema |
| `decline` | User explicitly said no | ❌ |
| `cancel` | User dismissed (escape, clicked away) | ❌ |

Treat `decline` and `cancel` differently if it matters — `decline` is intentional, `cancel` might be accidental.

The TS SDK's `server.elicitInput()` auto-validates `accept` responses against your schema via Ajv. fastmcp's `ctx.elicit()` returns a typed discriminated union (`AcceptedElicitation[T] | DeclinedElicitation | CancelledElicitation`).

---

## fastmcp response_type shorthand

```python
await ctx.elicit("Pick a color", response_type=["red", "green", "blue"])  # enum
await ctx.elicit("Enter email", response_type=str)                         # string
await ctx.elicit("Confirm?", response_type=bool)                           # boolean

@dataclass
class ContactInfo:
    name: str
    email: str
await ctx.elicit("Contact details", response_type=ContactInfo)             # flat dataclass
```

Accepts: primitives, `list[str]` (becomes enum), dataclass, TypedDict, Pydantic BaseModel. All must be flat.

---

## Security

**MUST NOT request passwords, API keys, or tokens via elicitation** — spec requirement. Those go through OAuth or `user_config` with `sensitive: true` (MCPB), not runtime forms.

---

## When to escalate to widgets

Elicitation handles: confirm dialogs, enum pickers, short flat forms.

Reach for `build-mcp-app` widgets when you need:
- Nested or complex data structures
- Scrollable/searchable lists (100+ items)
- Visual preview before choosing (image thumbnails, file tree)
- Live-updating progress or streaming content
- Custom layouts, charts, maps
