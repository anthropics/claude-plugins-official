# Step 12 — Connector options

Runs once, after the gaps list, over every system the plant named in Step 1
that is **not** one of the four supported connectors (Microsoft 365, Oracle
NetSuite, Infor M3, Autodesk Fusion). Its job is to report what exists, so the plant can
choose. It never connects anything.

---

## The order, per system

Stop at the first rung that answers.

1. **The registry.** Look up the system's row in
   `../../custom-connector/reference/known-systems.md`. If the row is under
   *Vendor-published MCP — add via custom-connector*, say a vendor-published
   MCP exists, give its address as the row states it, and name
   `custom-connector` as the route. Quote the row's notes; add nothing.
2. **No row — search for a vendor-published MCP server.** Accept a result only
   if it is on the vendor's own domain or linked from the vendor's own
   documentation. Report:
   - vendor, URL, and the documentation page it came from
   - any beta, preview or labs label, exactly as the vendor states it
   - a third-party or community server as **unofficial, not recommended** —
     named, so nobody installs it thinking it was checked

   **Where web search is not available in this session** — common in Cowork and
   in scheduled runs — say so, and give *"not in our registry — check your
   vendor's docs for an MCP server"*. Never answer from memory: a URL recalled
   rather than found is an invented one.
3. **No MCP.** Give the registry's access tier for that kind of system (REST
   API, OData, SQL, export) and what `custom-connector` would need from the
   plant to build on it — an API user, a read-only database view, an export
   path.

---

## Output

One table, one row per named system:

| System | What exists | Route | Next step |
|---|---|---|---|
| Limble CMMS | Vendor-published MCP (registry) | `custom-connector` | Say "connect Limble" when a Limble Super User is available |
| SolidWorks | No vendor MCP found | Export (already running) | Nothing needed; revisit if a vendor MCP appears |
| Epicor Kinetic | REST API (registry, tier 3) | `custom-connector` | An Epicor API user with read access to jobs and parts |
| Homegrown MES | Nothing published | Export (already running) | The plant's own developer is the source of truth |

**Routes are one of three:** `custom-connector`, export (already running), or
planned (the plant has said it is moving systems).

**What this step never does:**

- describe setup steps for any system not in the four-row setup table — that
  is `custom-connector`'s job, once the plant chooses
- attempt a connection, or take a credential
- recommend a third-party server
- report a system as connectable because a search result looked plausible

**Deferrable.** "Later" ends the step. Each system stays on the gaps list as
*connector options not reviewed*, and "what are our connector options" runs
this step again on its own.
