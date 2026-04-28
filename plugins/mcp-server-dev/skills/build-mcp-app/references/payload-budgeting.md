# Payload budgeting

Hosts cap tool-result text. claude.ai and Claude Desktop truncate at roughly
**150,000 characters**; Claude Code at ~25k tokens. When a tool result exceeds
the cap, the host substitutes a file-pointer string in place of your JSON. The
widget then receives non-JSON in `ontoolresult`, `JSON.parse` throws, and the
user sees something like *"Bad payload: SyntaxError: Unexpected token 'E'"* —
with no hint that size was the cause.

## Symptom → cause

| Symptom | Likely cause |
|---|---|
| Widget shows a JSON parse error on `content[0].text` | Result over the host cap; host swapped in a file-pointer string |
| Works for one query, breaks for "all of X" | Row count × column count crossed the cap |
| Works in MCP Inspector, breaks in Desktop | Inspector has no cap; Desktop does |

## Strategy

Cap your own payload at ~130KB and degrade in order:

1. **Ship full rows** when `JSON.stringify(rows).length` is under the cap.
2. **Prune columns** to those the rendering spec actually references. Walk the
   spec for both `field: "..."` keys *and* `datum.X` / `datum['X']` inside
   expression strings — if the spec aliases a column via a `calculate`
   transform, the alias appears as `field:` but the source column only appears
   as `datum.X`, and dropping it leaves the widget with NaN.
3. **Truncate rows** as a last resort and include `{ truncated: N }` in the
   payload so the widget can label it.

```ts
const MAX = 130_000;
let out = rows;
if (JSON.stringify(out).length > MAX) {
  const keep = referencedFields(spec); // field: + datum.X refs
  out = rows.map((r) => pick(r, keep));
  if (JSON.stringify(out).length > MAX) {
    const per = JSON.stringify(out[0] ?? {}).length || 1;
    out = out.slice(0, Math.floor(MAX / per));
  }
}
```

## Heavy assets go via `callServerTool`, not the result

Geometry, image bytes, or any blob the widget needs but Claude doesn't should
be served by a separate tool the widget calls after mount:

```js
const topo = await app.callServerTool({ name: "get-topojson", arguments: { level } });
```

Mark that helper tool with `_meta.ui.visibility: ["app"]` so it doesn't appear
in Claude's tool list.
