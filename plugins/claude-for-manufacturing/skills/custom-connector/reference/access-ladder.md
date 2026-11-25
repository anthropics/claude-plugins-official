# The seven-tier access ladder

Work down it in order. **Stop at the highest rung that works, and tell the
customer what they gave up by not being one rung higher.** Never skip a
rung without saying why — "we built a custom API wrapper" is the wrong
answer when a vendor MCP existed and nobody looked.

| Tier | Path | Freshness | Build cost | Who maintains it | The catch |
|---|---|---|---|---|---|
| 1 | Vendor-native / hosted MCP already exists | Real-time | None — setup only | The vendor | You inherit the vendor's scope exactly, including its limits |
| 2 | Community or third-party MCP | Real-time | Low — evaluate and wire | Nobody, unless you fork it | You own it the moment it breaks |
| 3 | Documented API → scoped custom MCP wrapper | Real-time | Medium | You | API access may be a paid license tier; rate limits; vendor deprecation |
| 4 | Read-only database view or replica | Near-real-time | Medium | You and the customer's DBA | Schema changes break it silently; may void vendor support |
| 5 | Zapier / iPaaS bridge | Minutes (polled) | Low | Zapier and you | Limited to exposed triggers/actions; per-task cost; another vendor in the data path |
| 6 | Screen-level automation (RPA) | Varies | High | You, constantly | Fragile, and often prohibited by vendor terms |
| 7 | Scheduled export contract | Export cadence | Low | Customer's IT | Not real-time; silently stops running |

**One deliberate crossover:** for bulk or historical data, skip Tiers 5 and
6 and go straight to Tier 7. Pulling three months of production history
through Zapier is slow, expensive and pointless when a nightly CSV does it
properly. **Use Tier 5 for events** — "a work order was created," "a
quality hold was raised" — **Tier 7 for volume.**

---

## What the skill delivers, and what a person still does

A Claude skill produces artifacts. It does not stand up and host
infrastructure — that's the boundary that decides what "as far as it can
go" means at every rung.

| Tier | What the skill produces | What a person does |
|---|---|---|
| 1 — Vendor MCP | Research finding, plan-tier check, step-by-step setup instructions, scope recommendation, a test call once connected | The customer's admin generates credentials and enables the connector |
| 2 — Community MCP | Evaluation (currency, maintainer, requested scope, security review), a recommendation, setup instructions | The customer or engineer installs it |
| 3 — API wrapper | The API assessment, the scoped surface design, the generated wrapper code, the field mapping, deployment instructions | An engineer reviews, deploys and hosts it |
| 4 — DB view | The view definition or SQL, the field mapping, the access request to hand the DBA | The customer's DBA creates the view and grants read access |
| 5 — Zapier bridge | The Zap specification — trigger, filter, action, field mapping, destination — plus the cost estimate at their volume | The customer builds it in Zapier's UI |
| 6 — RPA | A recommendation against it, with the specific reasons | Nothing, preferably |
| 7 — Export contract | The complete export specification — fields, types, format, cadence, naming, landing path | The customer's IT builds the scheduled export |

Read down the right-hand column and the pattern holds throughout: **the
skill removes the thinking, the research and the writing; a person
performs the privileged action.** That's not a limitation — it's the same
approval boundary the rest of the plugin runs on, and it's what makes a
connector skill safe to ship.

---

## Tier 1 — A vendor-native or hosted MCP already exists

**The most common good outcome, and the one most likely to be missed.**
Several manufacturing vendors have shipped MCP servers quietly, without
announcing them anywhere the customer would see. The job here is not to
build anything — it's to recognize the situation and walk the customer's
admin through turning it on.

The output is setup instructions specific to that system, never code:

- Where in the vendor's admin console to generate credentials, named
  exactly
- What scope to request — read-only unless a write is genuinely needed
- Whether the customer's plan tier includes it, and what to do if it
  doesn't
- Where to enter the credentials on our side, with an explicit instruction
  **not** to paste them into the chat
- A test call that proves it works, with real records shown back

**Worked example — Limble CMMS**, a vendor-published MCP that is not
one of the four supported connectors, and exactly this case. Limble publishes a hosted MCP server at
`mcp.limblecmms.com`, authenticated with an API client ID and secret.
Nothing needs building. A Limble admin generates the credentials in
Limble's admin settings; those go into connector settings on our side, not
into the conversation. Once connected it gives assets, maintenance work
orders, maintenance history and PM schedules.

The ceiling to state up front: write scope for closing out or updating
work orders isn't confirmed in Limble's public setup guide. Plan for
read-only, which is why `breakdown-diagnosis` produces a draft the
technician applies rather than updating the ticket itself. If write turns
out to be available, that's an upgrade, not a redesign.

**Repercussion of landing here: none.** This is the best available
outcome. The only thing the customer gives up is whatever the vendor's MCP
doesn't expose, and that's worth naming explicitly rather than discovering
it later.

---

## Tier 2 — A community or third-party MCP exists

**Search for it; do not tell the customer to.** Query the public MCP
registries and the vendor's community with the tools the session has, and
report the hits, marked community and unverified. No search tool in the
session means the rung is reported as not checked, with that reason, and the
ladder moves on in the same turn.

Faster than building, but it comes with an obligation: a third-party MCP
will see the customer's production data, so it gets a real security
review, not a glance. Answer each of these in the evaluation, and say
*not found* where the listing does not say:

| Check | Why |
|---|---|
| Publisher and maintainer, and when it last changed | A stale community server is a fork you will own |
| Licence, **and what it depends on** | A free MCP that needs a paid commercial driver (a JDBC licence, a vendor SDK) is not free |
| Transport: local `stdio` or remote | A `stdio` server only reaches the session while the machine running it is on |
| Where it runs, and who hosts it | The customer's machine, their server, or the publisher's cloud: that decides who sees the data |
| Read-only, **enforced at the credential** | A listing's "read-only" claim is not enforcement. Give it a read-only account; where listings contradict themselves, assume write |
| Scope it requests, and where it sends data | A server that phones anywhere but the system is out |
| Who owns the security review | A named role at the customer, before it is wired |

**Repercussion of landing here: you own it the moment it breaks, without
having written it.** Either fork it into the customer's control or budget
for the day the vendor changes their API and the maintainer has moved on.
Say this to the customer before wiring it, not after.

---

## Tier 3 — Documented API, scoped custom wrapper

The usual answer for modern cloud ERP and QMS. Build a thin wrapper
covering only the entities the skills actually need — not the whole API.

Check three things before committing:

1. **Does the customer's license tier include API access?** Some ERP
   vendors charge separately for it. Finding this out late costs a week,
   and it's the single most common surprise at this tier.
2. **Rate limits against the data volume the skills actually need.**
3. **Auth model and token lifetime** — a token expiring every 90 days
   needs a renewal path the customer knows about.

**Repercussion of landing here: you now maintain an integration.** Vendor
API version changes arrive without warning, and the surface has to be
re-tested against them. This is where "an afternoon" becomes "a week" if
the scope isn't held narrow — hold it narrow.

---

## Tier 4 — Read-only database view or replica

Often the only path for on-prem legacy systems, and sometimes better than
the API because it exposes history the API doesn't.

Work against a read-only view or a replica, **never the live production
database directly**, and never without the customer's DBA signing off. A
badly-scoped query against a production ERP database is a plant outage,
not a bug. Have the DBA create the view; don't ask for schema-wide access.
**Supply the draft view definition in the turn that declines direct access**:
a `CREATE VIEW` over only the columns the scoped need requires, with a
comment on each column naming the dataset field it maps to, for the DBA to
review and own.

**Repercussion of landing here: two real ones.** First, vendor upgrades
change schemas silently — nothing errors, the query just returns the wrong
thing or nothing. Second, some ERP vendors treat direct schema access as
support-voiding. Ask the customer to confirm their position rather than
assuming — that's their commercial risk, not ours.

---

## Tier 5 — Zapier or iPaaS bridge

Reach for this when there's no reachable API but the system has a Zapier
(or Make, or Workato) integration. Genuinely fast to stand up, and the
right tool for event-driven pushes — "a work order was created," "a
quality hold was raised" — landing a record where the plugin can see it.

State all of these before building:

- **A paid plan is required**, and pricing is per task, so cost scales with
  volume.
- **Limited to the triggers and actions the connector exposes** — usually a
  fraction of the underlying API. If the field isn't in the connector, it
  isn't available at this tier.
- **Polling means latency** — minutes, not real-time.
- **Another vendor in the data path.** In regulated manufacturing
  (aerospace, medical, defense) that's a security and data-processing
  question the customer's IT has to sign off on, not a technical detail.

**Repercussion of landing here: it's the wrong tool for bulk history** —
go to Tier 7 for that — and the customer pays per record, forever, for
something a nightly export would do for free.

---

## Tier 6 — Screen-level automation

Named for completeness, and **recommended against.** It breaks on any UI
change, any session timeout, and anything with MFA. It's frequently
prohibited by the vendor's terms of service.

Only reach for it if the customer explicitly accepts the fragility and
confirms it's permitted under their agreement. Say plainly that it will
break, and that it will break without a useful error.

---

## Tier 7 — Scheduled export contract

The floor that always works, and the one the rest of the plugin already
assumes. A plant that can't give you an API can almost always give you a
nightly CSV, because it's already producing one for somebody's Excel
report.

The deliverable is a specification the customer's IT can implement without
a follow-up call:

- Exact fields, with types and units
- File format, encoding and delimiter
- Naming convention and landing path in the M365 folder
- Cadence, and what time window each file covers
- What to do about late or corrected records

**Repercussion of landing here: freshness is capped by the export
cadence** — everything the plugin reports is as of the last drop. That's
fine for `daily-production-report` and `quote-build`, not fine for a live
breakdown diagnosis, so say which skills degrade and by how much. Also:
exports stop running silently, which is exactly why `data-consolidate`'s
freshness check is mandatory rather than nice-to-have. **The export request names the
owner as a role** — "your ERP administrator" — even when the person is unknown;
a spec whose owner line is blank has no one to call when the folder stops
getting newer.
