---
name: custom-connector
description: "Gets the plugin talking to a manufacturing system that has no vendor MCP, working down a seven-tier access ladder in order — vendor MCP, community MCP, a scoped API wrapper, a read-only database view, a Zapier bridge, screen automation as a last resort, or a scheduled export contract — and stopping at the highest rung that actually works. States plainly at every rung what the customer gets, what it costs, and how it will eventually break. Most often the answer is that a vendor MCP already exists and nothing needs building — just an admin turning it on. Maps whatever it reaches onto the consolidated dataset schema, so no downstream skill changes. Credentials never enter the conversation. Use when someone says \"connect our ERP,\" \"we use SAP,\" \"can you reach our MES,\" \"set up a connector for this system,\" or \"our system isn't supported.\""
compatibility: "Requires none of its own. Reads whatever the target system exposes — an existing MCP, a documented API, a database view, a Zapier connector, or a scheduled export — and produces setup instructions, a wrapper, a view definition, a Zap specification, or an export specification depending on which tier the system actually supports. Never accepts a credential in conversation."
---

# Custom Connector

SAP and Infor have the largest installed base in manufacturing, and neither
has an official MCP for business data. Neither does most of what actually
runs a mid-market plant — a large share of it is on-prem, a decade old, and
has a SQL database but no API at all. **That is not a failure case. It is
the normal case**, and this skill is what turns "your system isn't
supported" from a dead end into scoped, buildable work with a known
ceiling.

**A Claude skill produces artifacts. It does not stand up and host
infrastructure.** That boundary decides what "as far as it can go" means
at every rung of the ladder below — this is not a deployment tool, and
scoping it as one is the most common way to get it wrong.

**The most common good outcome is the one most likely to be missed.** A
vendor has often already shipped an MCP server, quietly, without
announcing it anywhere the customer would see. Recognizing that and
walking an admin through turning it on is worth more than a week of
wrapper code, and it is the first thing this skill checks, not an
afterthought.

**Quick start**

```
→ Identify the system precisely: vendor, product, version, on-prem or cloud
→ Scope the need. "Connect our ERP" is unbuildable; one data flow is
→ Work the ladder in order. Don't build before checking what already exists
→ Report the finding and its tier before building anything
→ Pick the tier, record why, and what was ruled out
→ Handle credentials narrowly. They never enter the conversation
→ Build only what Step 2 scoped, then map it onto the consolidated schema
→ Test against real data, show it back, ask what's still missing
→ Say how it will break, while the customer is still listening
```

---

## Inputs

**First, find the plant setup:** from the task's own folder (never `cd` into the plugin), run
`python3 -I <this skill's folder>/../../shared/scripts/plant_setup.py find`, do its `setup_page_first` step, then read the profile at
`profile_path` and any rate at `rates_path`, per `../../shared/replies.md`.

| Input | Source | Form |
|---|---|---|
| System identity | User, in conversation | Vendor, product, version, cloud or on-prem, who administers it |
| The specific need | User, and the skill being unblocked | What data out or action in, how often, which skill it serves |
| Consolidated dataset schema | `data-consolidate` | `../../shared/contracts/consolidated-dataset.md` — the mapping target |
| MCP registries and vendor docs | Web research | — |
| Credentials | Customer IT, through a secure path | Never in a skill file, a prompt, or the chat |

---

## Workflow

### Step 1 — Identify the system precisely

Vendor, product, version, deployment model, and who administers it inside
the customer's organization. **"We use SAP" is not enough** — S/4HANA
cloud and ECC on-prem are different problems on different tiers. Where the
name is ambiguous, ask the system's administrator for product, version and
hosting. Never infer them from a login URL. Version and hosting narrow the
search; they do not by themselves prove any rung works. Read
`reference/known-systems.md`.

### Step 2 — Scope the need before looking at access

**"Connect our ERP" is unbounded and unbuildable.** "Pull closed work
orders with actual cost, so `quote-build` has real cost history" is
buildable today. (How fresh it is depends on the tier: live at Tiers 1 to 3,
where nothing is scheduled; a stated cadence only at Tiers 4 to 7. Never
promise a nightly sync a live connector does not do.) Scope is what keeps this an afternoon instead of an
engagement.

### Step 3 — Work the ladder, in order

Vendor MCP, community MCP, documented API, database access, Zapier,
export. **Do not build before checking what already exists** — most of the
time something does. Read `reference/access-ladder.md`.

**Report each rung by the call that checked it, in the connection plan**
(step 4), not rung by rung in the reply. *"I searched the public MCP
registry for SAP and found nothing official"* — if a registry search is what
ran. Never *"I checked your connector directory"* or *"three connectors are
installed on this account"* unless the account's own connector listing was
queried in this run; which tools happen to be loaded in the session is not
that listing. A rung that could not be checked is reported as not checked,
with the reason. Per `../../shared/command-center.md`.

**Tier 2 is searched, not handed back.** "A community MCP might exist, worth
ten minutes of your time" is the rung skipped. Search for one with the tools
available and report what came back, marked community and unverified; where
no search tool exists in the session, say the rung was not checked and why.
**Then land on a tier in the same turn, with reasons** — Tier 2 found and
reviewed, or Tier 3 because nothing at Tier 2 was found or fit. Deferring the
Tier-2-versus-3 call to the user is not a landing.

### Step 4 — Report the finding before building anything

**The reply leads with the decision, and the ladder research goes in the
connection plan**. For a plan or "can you connect X"
request, the reply is, in this order:

1. **The recommendation**: the path for each system in plain words (vendor
   MCP, API, database view, scheduled export), why, and that it is
   conditional on what is still open.
2. **Connection status, honestly**: nothing is connected; what this run
   confirmed, and each condition still open.
3. **Three first questions, each labelled with who answers it**: for example
   the ERP administrator (version, hosting, whether the licence includes API
   access), the MES developer (where the data lives, whether hours are
   measured or backflushed), and the person asking (what the data is for and
   how fresh it must be). Three, not a questionnaire.
4. **A short comparison of manual, export and API**: what each gives, what it
   needs, how it breaks, and a provisional effort.
5. **Where the connection plan is.** Save it as
   `connector-output/connection-plan.html` (house style, internal), one file
   saved over the last run's: per system, the tier decision record with each
   rung and the call that checked it (or *not checked*, and why), what was
   ruled out, the sources, and the proposed field mapping. Name the path.
   With no way to write a file, print it in the reply below the comparison.

No tier-by-tier walk in the reply, and about 250 words before the comparison
table; the reply never claims a check the plan does not show. **This layout
is for a plan or "how do we connect" request only.** A request to set up,
build, map files, test a connection, register or verify one, or a question
about one system is answered in the reply in full, as before: **the field
mapping onto the dataset's own column names, its transforms and the test
results are always in the reply** when the person asked for any of those,
even when the reply also leads with a recommendation. The plan file still
holds the ladder. Setup steps for a Tier 1 or 2 system are an exception: the
admin acts on them, so they stay in the reply, quoted as below.

State the tier and its consequences, in the customer's own terms, before a
line of anything gets built:

> *"Limble already publishes a hosted MCP — Tier 1, nothing to build. It
> isn't one of the plugin's four supported connectors, so it's added for your plant. A Limble
> Super User generates an API key at Settings → Configuration → API Keys. The
> secret is shown once. The client ID and secret are sent as the
> `Limble-Client-ID` and `Limble-Client-Secret` headers, set as
> `LIMBLE_CLIENT_ID` and `LIMBLE_CLIENT_SECRET` in the environment the
> connector runs in. That gives assets, work orders and maintenance history in
> real time. The one limit: write scope for closing out work orders isn't
> confirmed publicly, so plan on `breakdown-diagnosis` drafting an update the
> technician applies rather than updating the ticket itself. Want me to walk
> through it?"*

**Setup steps are quoted word for word from `reference/known-systems.md`** —
the four supported connectors from its setup-steps table, and a
vendor-published MCP (Limble, Onshape) from its *Vendor-published MCP* table;
the Limble steps above are that row. Never paraphrase a row and never add a
step it does not contain: not "install it from the connector directory," not
"sign in and authorise." For Onshape that means opt in to Onshape Labs and
Subscribe to the FeatureScript MCP Server app, with the cost stated as not
public and unconfirmed. No admin step: none is documented. **How the plant
registers the vendor's MCP address with Claude is not written in the table,
so do not invent it** — no menu path, no "ask your admin to enable it." Give
the address and what it needs, and say that registering it as a custom
connector in Claude is done by whoever manages connectors for their Claude
account.

**Readiness is conditional until this run has evidence for it.** Never write
*"works today"*, *"available now"* or *"nothing needed from IT"* unless this run
saw it: a licence or permission the customer confirmed, an export or report
they showed exists, records shown back. Otherwise name each condition still
open: whether the licence includes API access, whether the integration user
can be granted the scope, whether the deployment is reachable, whether the
export or report exists and who may schedule it. Every proposed field mapping
stays *proposed, unverified* until instance evidence exists.

**Sources: the vendor's and publisher's own documentation first.** A technical
specific (auth method, paging, endpoint names, rate limits) that no official
source in this run states stays *unknown*, and a community README that
contradicts the vendor is reported as a contradiction, not resolved. **Never
give a link this run did not open**; a file this run wrote is named by its
path. Every effort estimate is labelled *provisional* with what it assumes.

Once connected, record the system's `### Systems` line in the plant profile as
`live (custom)`, through `onboarding`'s reconfigure, so every skill that reads
"CMMS connector live" or "CAD connector live" takes its live path.

### Step 5 — Pick the tier, and record why

Which tier, why, and what was ruled out and on what evidence. **The
decision record matters more than the code** — it's what the next engineer
reads, and it's what stops the same question being re-litigated in three
months.

### Step 6 — Handle credentials properly

Narrowest scope that does the job. Read-only unless a write is genuinely
required and approved. A dedicated integration user, never someone's
personal login, so access can be revoked without locking a person out.
Tokens and OAuth only, never a password. Read
`reference/credentials-and-failure-modes.md`.

### Step 7 — Build scoped

Only the entities Step 2 defined. A narrow connector is easier to secure,
easier to reason about, and far less likely to break on a vendor update.

### Step 8 — Gate every write path

The same draft-and-approve rule as the rest of the plugin. A connector does
not get an exception for being infrastructure rather than a skill output.

### Step 9 — Map onto the consolidated dataset schema

So downstream skills read it without knowing it is new. **This is what makes a
connector useful rather than merely present** — one that returns data in its
own shape has moved the problem, not solved it. Per
`../../shared/contracts/consolidated-dataset.md`. Map every field the scoped
need names: closed-job cost goes to `production_work_orders`' actual-cost
columns. **Where the schema has no home for a field, say so and stop**: the
contract gains it with a version bump, or the field stays out. Never claim "no
downstream skill changes" for a field no skill can read.

**Every mapping row keeps its evidence**: the source field, its original value
and unit, the proposed destination, the transform it needs, its status
(*proposed* until instance evidence exists, *confirmed* only after Step 10), the
owner role who confirms it, and the open question. Review, never drop or force:
rate-based routing standards (pieces per hour is a stated transform to time per
piece, the original kept beside it), cost elements such as material burden,
lower-level assembly costs rolled into a parent, and units. A field with no
honest destination is listed as unmapped, with the reason.

**Job hours: measured or backflushed, and which system owns them.** Before
labour hours are offered to `quote-build` as actuals, establish whether they
are measured (clock-in, MES) or posted standards backflushed on completion, and
which system is the source of record. Until that is confirmed, map them with
`actuals_confidence` low and `confidence_reason` *"hours basis unconfirmed:
measured or backflushed not known"*; discovery and mapping go on, with the
confirmation named as the prerequisite. Where the ERP and the MES disagree on
hours for the same job, that is the two-sources-of-truth edge case below.

### Step 10 — Test against real data, and show it back

Pull actual records, display them, and ask whether anything expected is
missing. **That last question is what catches the field that quietly
wasn't mapped.** Vendor example payloads prove nothing; customized fields
are the norm in manufacturing.

**Validation has a named scope, never a blanket "verified".** Record what was
actually checked, each kind separately: fields an admin confirmed, records
sampled and compared (with how many), transforms checked, and completeness
reconciled against an independent count from the source system itself. A row
count that matches the export's own manifest proves the file is internally
consistent, not that the source query returned everything. Five records
checked verify those records, not every mapping. The status line says
*validated for <scope>* and lists what remains open.

**No real records, no registration.** Where Step 10 cannot run (no instance
yet, access not granted, a test), the connector's status is
**Untested: not registered**, stated in the reply and on the credential record, and Step 11
waits until real records have been shown back and confirmed.

### Step 11 — Register it

Only after Step 10 passed on real records. What it reaches, what it cannot do, how it refreshes, and which skills it
now unblocks — stated concretely, not as a general capability claim.

### Step 12 — Say how it will break

While the customer is still paying attention: token expiry and the
renewal path, vendor API changes that arrive without warning, rate
limits, schema drift at Tier 4, task limits at Tier 5. **A connector that
fails silently is worse than no connector.** Read
`reference/credentials-and-failure-modes.md`.

---

## Approval gates

**A write path is never assumed, only granted.** Read-only by default; a
write is proposed, its scope named, and it proceeds only on explicit
approval — the same rule every skill in this build follows for a
consequential action. **Every refusal of write scope, and every "build us the
connector," carries the sentence:** *"A Claude skill produces artifacts; it
does not stand up or host infrastructure."* What this skill produces is the
wrapper, the view definition, the Zap specification or the export
specification; an engineer, a DBA or IT deploys it.

**Tier 4 is declined with the view definition in hand.** When someone says
"just query the production database," the reply declines direct access, names
the outage risk, **and supplies the draft read-only view definition in the
same turn, in the reply itself** — the `CREATE VIEW` scoped to the entities
Step 2 named, as a SQL block the DBA can read where they are, not only a file
written to disk that "is available in the workspace". Declining without the
draft on the page hands the work back.

**A Tier 7 specification names its own owner role.** Every export spec ends
with: how it fails (silently, the folder stops getting newer), how that is
detected (`data-consolidate`'s freshness check, which is why that check is
mandatory), and **who owns the export, as a role** — "your ERP administrator,"
"the IT person who schedules the report" — even when no name is known. Asking
the user to designate someone is not naming the owner.

**Credentials never enter the conversation.** Not pasted, not typed, not
read back for confirmation. They go into connector settings on the
customer's side, through their own secure path. If someone pastes one
anyway, say plainly that it should be rotated because it has touched the
transcript, and that nothing was done with it. **Never repeat any part of
it** — not quoted, not in code formatting, not inside the rotation
instruction. It is "the key you pasted." Check the reply for any run of
eight or more of its characters before sending. Per
`../../shared/secret-config.md`, *Never repeat what was typed*.

**Tier 6 requires the customer's explicit, informed acceptance of the
fragility** before anything is built there — it is recommended against by
default, not merely discouraged.

---

## Output

**Every document this skill produces is printed in the reply, in full.**
Saving a copy to a file as well is fine, as Word or Excel per `../../shared/replies.md`, never `.txt`; a file *instead of* the reply is not.
The person reads the reply, and every delimited block and outbound check lives
in it — a document only on disk has been neither seen nor checked. The
connection plan is the exception: it is saved and named, per step 4, and
printed in full only when no file can be written.
**A record handed to another skill is saved and summarised, never pasted as
raw YAML**; memory blocks are written where the plant's memory lives; and the
name on an approval is asked, never taken from the account. All three per
`../../shared/replies.md`.

**A working connection** (Tiers 1–6), or **an export specification**
(Tier 7).

**Setup instructions** for the customer's admin, where the path is Tier 1
or 2 — the most common and most valuable output this skill produces. **At
Tier 1 or 2, this is the whole output — nothing gets built.** A vendor or
community MCP that already exists is a setup task, not an engineering one.

**The tier decision record** — which rung, why, what was ruled out, and
what the customer gives up by not being one rung higher. It lives in the
connection plan, `connector-output/connection-plan.html`, with each rung and
the call that checked it; the reply leads with the recommendation, status,
three questions and the manual/export/API comparison per step 4, and names
the file.

**The field mapping document** — the new system onto the consolidated
dataset schema, **so that no downstream skill ever has to change** to read
data from a newly connected system. A connector that returns data in its
own shape has moved the problem, not solved it.

**The credential and scope record** — what access was granted, to what,
read or write.

**Test results against real customer data**, shown back to the user.

**A failure-mode note** — how this breaks, what it looks like when it
does, and who fixes it. Said **up front, while the customer is still
paying attention** — never something discovered for the first time in
production.

**At Tier 7, the export specification is complete enough to hand to the
customer's IT department as-is** — exact fields with types and units,
format, encoding, naming convention, landing path, cadence, and what to
do about late or corrected records — with no follow-up call needed to
fill in something this skill should have already asked.

---

## Edge cases and failure modes

- **A vendor MCP exists but the customer's plan tier doesn't include it** —
  say what the upgrade unlocks so they can price the trade-off, then drop
  to the next viable tier.
- **License tier excludes API access** — Tier 4, 5 or 7, and say what an
  API license would buy.
- **On-prem behind a firewall with no external reachability** — Tier 7.
  Don't design around a VPN the customer hasn't agreed to.
- **Customer IT won't grant any access** — common, and it needs a named
  escalation path rather than a stalled build. Tier 7 with an export
  request usually unblocks it, because IT is far more willing to schedule
  a report than issue credentials.
- **Rate limits too low for the data volume** — move the bulk path to
  Tier 7 and keep the API for events. The two tiers coexist.
- **Vendor terms prohibit third-party access or direct schema reads** —
  stop. That's a legal question for the customer, not an engineering one.
- **ITAR or export-controlled data in scope** — blocking gate. Do not
  proceed without explicit clearance.
- **Genuinely undocumented homegrown software** — Tier 4 or 7, and expect
  the customer's own developer to be the only reliable source of truth.
- **Two systems claim to be the source of truth for the same record** —
  surface the conflict; don't silently pick one. A business decision, not
  a mapping decision.

---

## Chain position

**Not part of a chain.** A utility that widens what every other skill can
reach — like `onboarding`, it sits outside the five named chains by
design.

**Metric.** Systems reachable per customer; time to first data from an
unsupported system.

---

## Reference files

| File | Load when |
|---|---|
| `reference/access-ladder.md` | Step 3 — the seven tiers in full: path, freshness, build cost, maintainer, and the catch at each rung |
| `reference/known-systems.md` | Step 1 — the systems landscape by category, and where common systems land today |
| `reference/credentials-and-failure-modes.md` | Steps 6 and 12 — credential handling, and stating failure modes before they happen |
| `../../shared/contracts/consolidated-dataset.md` | Step 9 — the schema every new system maps onto |
