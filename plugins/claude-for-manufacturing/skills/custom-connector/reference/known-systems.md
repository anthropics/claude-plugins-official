# The systems landscape, and where common systems land today

Give the engineer a head start, but **re-verify at build time** — this
landscape moves quickly, and a system that was Tier 3 last quarter may be
Tier 1 now.

---

## What plants actually run, by category

| Category | What plants actually run | Access reality |
|---|---|---|
| ERP | SAP S/4HANA and ECC, Infor M3, Infor CloudSuite/LN, Epicor Kinetic, Plex, Global Shop, JobBoss, E2 | Most have REST or OData APIs. SAP exposes OData services and the BTP layer. API access is sometimes a separately-priced license tier |
| MES | Tulip, Plex MES, Aegis, Critical Manufacturing — plus a great deal of homegrown | Cloud ones have APIs; homegrown usually means a database or an export |
| Historian / SCADA | AVEVA/OSIsoft PI, Ignition, Wonderware, Kepware | PI has a Web API; Ignition has a web API and SQL access. Usually on-prem and firewalled |
| Quality / QMS | ETQ, MasterControl, Greenlight Guru, IQS | Mostly REST |
| PLM | Windchill, Teamcenter, Arena, Autodesk Vault | Varies widely; Vault is on-prem |

**A large share of what's running in mid-market plants is on-prem, a
decade old, and has a SQL database but no API at all.** That's not a
failure case — it's the normal case, and the access ladder has an answer
for it at Tier 4 or Tier 7.

---

## Known-systems registry

**This table is a starting point, not an answer.** It never replaces the
Tier 1 and 2 search in `access-ladder.md`: a vendor or community MCP the
search finds outranks the tier written here. "Tier 2 seen" names candidates
to evaluate, not to trust.

| System | Tier today | Notes |
|---|---|---|
| Oracle NetSuite | 1 — supported | Vendor-native read-write MCP. Heavily customized per account — expect custom fields |
| Infor M3 | 1 — supported | The company's own M3 MCP server, one per M3 tenant. Read only in this plugin, though the server exposes writes. If an Infor M3 tool call returns an error, tell the user and fall back to a file export. |
| Microsoft 365 | 1 — supported | Anthropic connector. Read-only by default, write is admin opt-in, no Teams write path |
| Autodesk Fusion | 1 — supported | First-party integration. Desktop app only |
| Limble CMMS | 1 — vendor MCP, added via custom-connector | See *Vendor-published MCP — add via custom-connector* below |
| Onshape | 1 — vendor MCP, added via custom-connector | See *Vendor-published MCP — add via custom-connector* below |
| SAP S/4HANA | 3 | OData services / BTP. No official MCP for business data. API access may need a license tier |
| SAP ECC (on-prem) | 3 or 4 | Older estate — RFC/BAPI, or a read-only DB view. Expect a project, not an afternoon |
| Infor CloudSuite / LN | 3 | REST APIs via Infor ION. Not the M3 connector |
| Epicor Kinetic | 3 | REST API. Tier 2 seen: a CData community MCP (needs a paid CData JDBC driver, local `stdio`; evaluate per the Tier 2 checklist) |
| Plex (ERP + MES) | 3 | REST API; cloud-native, so usually straightforward |
| Global Shop / JobBoss / E2 | 4 or 7 | Typically on-prem SQL. Export is often the pragmatic answer |
| Tulip | 3 | API available |
| AVEVA / OSIsoft PI | 3 in theory, 7 in practice | PI Web API exists, but the historian is usually firewalled with no external route |
| Ignition | 3 or 4 | Web API, or direct SQL against its database |
| ETQ / MasterControl | 3 | REST |
| Windchill / Teamcenter | 3 or 4 | Heavy enterprise PLM. Scope tightly or it becomes its own engagement |
| Homegrown MES | 4 or 7 | The customer's own developer is the only reliable source of truth |

**The plugin works with four systems once they are connected: Microsoft 365,
Oracle NetSuite, Infor M3 and Autodesk Fusion. These are the supported
connectors; only Fusion is declared in the plugin's `.mcp.json`.** Every other row is a `custom-connector`
engagement — including the two with a vendor-published MCP, which are Tier 1
in reach but are not among the four, and the "3 or 4" and
"3 in theory, 7 in practice" rows are not indecision — they're the honest
answer for systems where the real tier depends on the specific customer's
deployment, license, and network posture, which is exactly what Step 1's
precise identification is for.

---

## Vendor-published MCP — add via custom-connector

Systems whose vendor publishes an MCP server. **Not among the four supported connectors**:
`onboarding` Step 12 reports them as an option, and `custom-connector` adds one
when the plant chooses. These are not setup steps for `onboarding` to quote —
they are what `custom-connector` works from.

| System | Vendor MCP | What adding it takes | Notes |
|---|---|---|---|
| **Limble CMMS** | `https://mcp.limblecmms.com/mcp` | A Limble **Super User** generates an API key at *Settings → Configuration → API Keys*. The secret is shown once. The client ID and secret are sent as the `Limble-Client-ID` and `Limble-Client-Secret` headers, set as `LIMBLE_CLIENT_ID` and `LIMBLE_CLIENT_SECRET` in the environment the connector runs in | Write scope unconfirmed. Credentials never enter the conversation |
| **Onshape** | `https://fs-mcp.labs.onshape.app/mcp` | Opt in to Onshape Labs, then open the Onshape App Store, find **FeatureScript MCP Server** and click **Subscribe**. Sign-in is automatic — there is nothing to generate | An Onshape Labs app. Whether the subscription costs anything is not stated publicly, so it is unconfirmed. **No skill in this plugin uses it:** `design-space-explore` and `rfq-to-quote` are built on Fusion, so connecting Onshape enables nothing today — say so |

---

## Setup steps for the four supported connectors, word for word

**This is the only place these steps are written.** `onboarding`,
`custom-connector`, `design-space-explore`, `rfq-to-quote` and any answer to
"which systems can you reach" **quote the row below exactly**. The same text is in the plugin's
README.

**Never describe a setup step that is not in this table.** Not "install it
from the connector directory," not "sign in and authorise," not a service name
that does not appear here. Where a row says something is unconfirmed, say it is
unconfirmed. If a customer needs a step this table does not have, say the step
is not documented here and point them to the vendor's own setup guide.

| System | What to do |
|---|---|
| **Microsoft 365** | Enable the Microsoft 365 connector in Claude's connector settings. Documents, mail and the export folder |
| **Oracle NetSuite** | Enable the Oracle NetSuite connector in Claude's connector settings. Read and write; the sign-in picks your account, so there is no account ID to enter here |
| **Infor M3** | Add your company's Infor M3 MCP server as a custom connector in Claude's connector settings, using the server address your Infor administrator gives you. The plugin only reads from it |
| **Autodesk Fusion** | In the Fusion **desktop** app: *Preferences → General → API* → enable **Fusion MCP Server**. It runs locally on your machine and needs Fusion open with a document. If you changed the port from 27182, set `FUSION_MCP_PORT` |

**Connector auth is always owner-initiated.** The plugin never attempts a
connection on anyone's behalf, so "did you try connecting it?" has one answer:
no, and here are the steps for the person who can.

**Reported live only when its tools exist in the session.** A connector is
live when its tools are present and return for this account — not because it is
declared in `.mcp.json`, and not because the customer says it is set up.
