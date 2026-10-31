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

**The call fails if the client doesn't advertise elicitation.** The TypeScript SDK fails it — protocol error `-32021` on 2026-07-28 connections, an `isError` result on older ones; fastmcp throws `CapabilityNotSupported`. There is no graceful degradation built in. You MUST check and have a fallback.

### The canonical pattern

```typescript
import {
  CLIENT_CAPABILITIES_META_KEY, acceptedContent, inputRequired, inputResponse,
  type CallToolResult, type ClientCapabilities, type InputRequiredResult, type ServerContext,
} from "@modelcontextprotocol/server";

const confirmSchema = z.object({ confirm: z.boolean().meta({ title: "Confirm deletion" }) });

// 2026-07-28 requests carry the client's capabilities; older connections declare them once at initialize
function clientCapabilities(ctx: ServerContext): ClientCapabilities | undefined {
  const perRequest = (ctx.mcpReq.envelope as Record<string, unknown> | undefined)?.[CLIENT_CAPABILITIES_META_KEY];
  return (perRequest as ClientCapabilities | undefined) ?? server.server.getClientCapabilities();
}

server.registerTool("delete_all", {
  description: "Delete all items after confirmation",
  inputSchema: z.object({}),
}, async (_args, ctx): Promise<CallToolResult | InputRequiredResult> => {
  if (!clientCapabilities(ctx)?.elicitation) {
    // Fallback: return text asking Claude to relay the question
    return { content: [{ type: "text", text: "Confirmation required. Please ask the user: 'Delete all items? This cannot be undone.' Then call this tool again with their answer." }] };
  }

  // The handler runs again once the user has answered, so read the answer first
  const answer = inputResponse(ctx.mcpReq.inputResponses, "confirm");
  if (answer.kind === "elicit" && answer.action !== "accept") {
    return { content: [{ type: "text", text: "Cancelled." }] };
  }
  const confirmed = acceptedContent(ctx.mcpReq.inputResponses, "confirm", confirmSchema);
  if (confirmed === undefined) {
    return inputRequired({
      inputRequests: {
        confirm: inputRequired.elicit({
          message: "Delete all items? This cannot be undone.",
          requestedSchema: confirmSchema,
        }),
      },
    });
  }
  if (!confirmed.confirm) return { content: [{ type: "text", text: "Cancelled." }] };

  await deleteAll();
  return { content: [{ type: "text", text: "Deleted." }] };
});
```

**How the TypeScript flow works:** the handler *returns* the question instead of awaiting it. The client asks the user and retries the call with the answer in `ctx.mcpReq.inputResponses`. Nothing survives between the two runs, so do no work with side effects before the answer is in.

- One handler serves every client. On 2025-era connections the SDK sends a classic `elicitation/create` request for you and re-enters the handler with the answer.
- `ctx.mcpReq.elicitInput()` (v1's `server.elicitInput()`) works only on 2025-era connections and throws on 2026-07-28 ones. Don't use it in new code.
- A 2025-era client on a stateless HTTP server (`createMcpHandler`) has no channel for the question. The capability check comes back empty there, so the fallback runs.

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

The TS SDK's `acceptedContent()` validates an `accept` response against the schema you pass it. fastmcp's `ctx.elicit()` returns a typed discriminated union (`AcceptedElicitation[T] | DeclinedElicitation | CancelledElicitation`).

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
