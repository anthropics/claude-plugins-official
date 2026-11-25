# The config profile — storage format and contract

This file is the contract. Every other skill reads the profile by heading match,
so the headings and field names below are not editable per plant.

---

## Two artifacts, one source of truth

| Artifact | Form | Who reads it |
|---|---|---|
| `## Plant context` block | Markdown file at `profile_path` (`plant_setup.py find`), kept on the private `Plant setup: <company>` page | Every skill, at run time, by heading match |
| `## Plant rates` block | Markdown file at `rates_path`, kept on the private `Plant rates: <company>` page | Skills that price, per `../../../shared/secret-config.md` |

The files are authoritative; each page carries its file byte for byte plus a
readable view, rebuilt by `plant_setup.py render`, never edited by hand
(`../../../shared/replies.md`, *The plant setup and the rates*). **The setup
file never holds a rate value** and `render` refuses one: its
`### Commercial rates` lines carry each rate's state only. The rates page's
view shows each rate's state, never the number.

---

## The block

Write this under the heading `## Plant context`, in the file at
`profile_path`. **Never the export folder, a shared or synced folder, or a
file a repository commits.** Say the path it was written to. An older profile may
live in `CLAUDE.local.md` or the project's memory; a reconfigure
reads it from there and writes the new files.

```markdown
## Plant context

- **Profile version:** 2
- **Configured:** 2026-09-08
- **Company:** Example Manufacturing
- **Sites:** Fairview (default) - Brantford
- **Connectors live:** Microsoft 365, Oracle NetSuite
- **Connectors not live:** Autodesk Fusion
- **Export folder:** Shared Documents/Plant Exports
- **Export refresh:** nightly, lands by 02:00 local
- **Standards certified to:** ISO 9001:2015, AS9100D
- **Templates on file:** NCR form, 8D format
- **Templates missing:** quote layout, supplier RFQ package, trade study memo
- **Report depth:** full
- **Rates:** see Commercial rates - state per rate, values shown only on internal artifacts
- **Gaps open:** 4
```

### Systems

One line per category, from Step 1. The name is whatever the plant uses; the
state is one of `live (supported)`, `live (custom)`, `file` or `none`. Only
Microsoft 365, Oracle NetSuite, Infor M3 and Autodesk Fusion can be `live (supported)`;
anything else is `live (custom)` once `custom-connector` has connected it, and
`file` until then.

```markdown
### Systems

- **ERP:** Oracle NetSuite - live (supported)
- **CAD:** SolidWorks - file
- **CMMS:** Limble CMMS - file - connector options reviewed 2026-09-08
- **Documents:** Microsoft 365 - live (supported)
```

A skill reads the **state**, not the vendor name: "CMMS connector live" means the
CMMS line says `live (custom)`, whichever CMMS it is. "ERP live" means the ERP
line says `live (supported)`, whether it names Oracle NetSuite or Infor M3. A system whose Step 12
options were deferred says `connector options not reviewed`.

### ERP scope

From Step 1, per `erp-scope.md`: the record types checked, this plant's
subsidiary, locations and parts, where the part revision lives, which cost
field means what, where production work orders come from, which source wins
when a connector and an export overlap, and how long an RFQ may wait. Below it,
`### Approved normalizations`, which `data-consolidate` appends to on each
yes. The format is in `erp-scope.md`, *The section*. A line not yet answered
says **not set** and is on the gaps list.

### Documents read at setup

One row per file from Step 2, so a later run can tell where a value came from.

```markdown
### Documents read at setup

| File | Identified as | Fed | Status |
|---|---|---|---|
| Fairview shifts 2026.pdf | Shift calendar | Step 4 | confirmed |
| QM-001 Quality Manual RevF.pdf | Quality manual | Steps 7, 8 | confirmed |
| scan_0412.pdf | Unidentified | - | on gaps list |
```

### Export file inventory

One row per file. Identified in Step 3 and **confirmed by the user**, never
accepted from inference alone. A file dragged into the conversation rather
than landing in the folder is recorded with cadence **manual** — it works for
a run the user starts, and no scheduled skill can rely on it.

```markdown
### Export files

| File pattern | What it is | System | Cadence | Covers |
|---|---|---|---|---|
| prod-output-*.csv | Actual production output, good and scrap | MES | daily | prior day |
| downtime-*.csv | Downtime events with reason codes | MES | daily | prior day |
| inspection-*.xlsx | Inspection results against spec | QMS | weekly | prior week |
| schedule-*.xlsx | Planned quantity by part and date | Planning | daily | next 14 days |
| cmms_maintenance.csv | Maintenance work orders | CMMS (file) | manual | last 90 days |
```

### Machining data

Read by `quote-build`'s hours ladder and `rfq-to-quote`'s design step when a
part has no current routing. Site-scoped. **Every setup and tool-change figure
carries its basis**, `measured` or `assumed`, and an assumed figure is named
whenever it accounts for a variance — that is what makes a 36% gap traceable
to a guessed tool-change time rather than a mystery.

```markdown
### Machining data

| Machine class | Work centers | Cell | Setup hours | Tool change min | Basis |
|---|---|---|---|---|---|
| SAW | SAW-01 | CELL-A | 0.25 | - | measured |
| VMC-3AX | HAAS-VF4-02, HAAS-UMC-01 | CELL-B | 1.25 | 0.5 | assumed |
| LATHE-2AX | DOOSAN-PUMA-07, DOOSAN-PUMA-03 | CELL-C | 1.00 | 0.2 | measured |
| DEBURR | BENCH-02 | CELL-D | 0.10 | - | measured |
| OUTSIDE-FINISH | (black oxide, outside) | - | 5 working days per lot | - | measured |

| Material | Tool class | SFM | Chip load ipt | Basis |
|---|---|---|---|---|
| 4140 | carbide end mill, roughing | 400 | 0.002 | assumed |
| 4140 | face mill | 600 | 0.004 | assumed |

- **Fusion tool library:** not used
- **Variance flag threshold:** 15% - default, not plant-set
- **Stale interval:** 365 days
```

- **Cutting data** is either the table or a named Fusion tool library — record
  `Fusion tool library: <name>` instead of the table when that is where the
  plant keeps it. Neither means hours derived in Fusion run on library
  defaults, which `quote-build` treats as first-principles and labels so.
- **An estimator's ballpark is `assumed`.** Never recorded as measured because
  it was typed with confidence.
- **Variance flag threshold** deferred is recorded as *15% - default, not
  plant-set*, and every flag raised on it says so.

### Approved suppliers

From Step 8. Read by `supplier-quote-request` for its candidate list.

```markdown
### Approved suppliers

| Commodity | Approved | Notes |
|---|---|---|
| 4140 bar | VEND-3310, VEND-3402 | |
| Black oxide | VEND-5120 | single source |
```

A commodity with one approved supplier is marked single source, so the
supplier skills can flag it rather than discover it.

### Source clocks

**The highest-risk configuration in the plugin.** One row per data source, per
`time-config.md`.

```markdown
### Source clocks

| Source | Timezone | Zone-aware | Observed skew | Checked |
|---|---|---|---|---|
| NetSuite | America/New_York | yes | none | 2026-09-08 |
| CMMS (Limble, live custom) | America/New_York | yes | none | 2026-09-08 |
| MES production export | America/New_York | no, naive | +1h vs NetSuite | 2026-09-08 |
| MES downtime export | America/New_York | yes, -04:00 | none | 2026-09-08 |
| Historian export | UTC | yes, +00:00 | none | 2026-09-08 |
| Quality export | America/New_York | no, naive | not checked | — |
| Planning export | America/New_York | no, naive | not checked | — |
```

**One row per source, always.** A source not yet asked about gets its own row
with "not checked," never a shared row with other sources: two exports can
carry `-04:00` and `+00:00` in the same folder, and a merged row hides
exactly that.

A non-zero skew stays in the table. It is a finding, not something to correct
away.

---

## Sites and inheritance

**One plant is still a site.** A single-site plant gets one site block named
`(default)`. This keeps the read path identical for every skill and means adding
a second site later changes nothing about how the first one is read.

Values in the top-level block are **shared**. Values in a site block are
**overrides** and win for that site only.

```markdown
### Site: Fairview (default)

- **Timezone:** America/New_York
- **Shift pattern:** three 8s - 07:00, 15:00, 23:00
- **Production day starts:** 07:00
- **Cross-midnight shift belongs to:** the day the shift started
- **Planned production time:** scheduled shift hours minus planned PM windows
- **Vocabulary:** job = production work order - cell = work center - area = department
- **Capability:** aluminium and 300-series stainless - 3-axis and 4-axis milling, turning - max envelope 600 x 400 x 300 mm - demonstrated true position 0.002 in

### Site: Brantford

- **Timezone:** America/Toronto
- **Shift pattern:** two 12s - 06:00, 18:00
- **Production day starts:** 06:00
```

Brantford inherits everything not restated. It has its own timezone, shift
pattern and day boundary, and takes Fairview's vocabulary and capability.

**Two optional lines and one optional section for the morning report's floor
view.** `- **OEE thresholds:** good at or above 75%, poor below 60% - confirmed
by <name or role>, <date>` (shared, or a site override) sets the floor view's
colours; absent, the report uses those defaults and says they are not
confirmed. `### Floor layout - <site>` is written only by
`daily-production-report`'s setup turn, after the person confirms each
machine, in the shape of `../../../shared/contracts/floor-layout.md`.
Onboarding keeps both lines as they are when it rewrites the profile.

**The failure this structure exists to prevent:** one plant's shift boundary
silently applied to another. A skill reading a site-scoped value must resolve it
through the site block first and only then fall back to shared. **When a run
spans more than one site, ask which site rather than resolving to the default.**

---

## Sensitive values — stored, not just pointed to

Labor rate, burden rate, margin rules and the downtime cost per hour derived
from them are commercially sensitive, but they **are** stored. This isn't
"treat it like a credential": a credential is used opaquely and never
displayed, but a burden rate has to be multiplied by hours and shown —
`quote-build`'s cost-basis sheet and `daily-production-report`'s priced
downtime both depend on reading the actual value, not asking a person for
it every run.

There are two routes, and the full rule is
`../../../shared/secret-config.md`: an `MFG_*` environment variable, which
wins when set, or a **confirmed** rate in the `## Plant rates` file, written by
step 10 after the plant has seen it and said yes. Cowork users have only the
second route.

Three rules govern them, wherever they're read:

- **Storage** — an `MFG_*` variable, or the `## Plant rates` file and its
  private page. Never a file in a repo, never a file copied between customers,
  never the setup file a teammate may be shown. Step 10 says where they go
  before asking.
- **Audience** — usable and displayable in internal artifacts (cost-basis
  sheets, internal margin lines, priced downtime). Never in a
  customer-facing artifact, the readable setup summary, the config profile
  page, the gaps list, sample data, or logs.
- **Echo** — shown back once, in the step 10 approval draft, so the plant can
  catch a typo. After that, used and shown where the audience rule allows,
  and confirmed by name, not value.

Every rate carries exactly one of four states. **The rates file** holds the
values, under its own heading with the company and the date:

```markdown
## Plant rates

- **Company:** Example Manufacturing
- **Configured:** 2026-10-02

### Commercial rates

- **Labor rate:** confirmed 71.00/hr - given by Pat Doyle, 2026-10-02
- **Burden rate:** set in environment (MFG_BURDEN_RATE)
- **Margin rules:** confirmed `{"default":0.32,"by_customer":{"EXAMPLE-AEROSPACE":0.28},"by_job_type":{"prototype":0.45}}` - given by Pat Doyle, 2026-10-02
- **Downtime cost per hour:** not set - see gaps
- **Scrap costing basis:** standard cost from NetSuite (not sensitive - stored in the clear)
```

**The setup file** holds the same lines with each value removed, so a teammate
shown the setup page sees the state and nothing more:

```markdown
### Commercial rates

- **Labor rate:** confirmed - on the rates page - given by Pat Doyle, 2026-10-02
- **Burden rate:** set in environment (MFG_BURDEN_RATE)
- **Margin rules:** confirmed - on the rates page - given by Pat Doyle, 2026-10-02
- **Downtime cost per hour:** not set - see gaps
- **Scrap costing basis:** standard cost from NetSuite
```

| State | What the rates file's line holds |
|---|---|
| **Set in environment** | The variable name only. The value lives in the environment and is read at run time |
| **Confirmed** | The value, who gave it and the date. Written only after an explicit yes on the approval draft |
| **Placeholder** | The value and its assumption, marked "not confirmed" |
| **Not set** | Nothing to price on. The gaps list names it |

Margin rules use the JSON shape of `MFG_MARGIN_RULES`: a `default`, plus
`by_customer` and `by_job_type` overrides, each a fraction of price. A rule
the plant states that does not fit that shape is recorded as said and put on
the gaps list, never forced into it.

A placeholder goes in the rates file with its assumption, like a confirmed
rate:

```markdown
- **Labor rate:** placeholder 62.00/hr - assumed from the FY25 budget, not confirmed
- **Burden rate:** placeholder 140% - assumed, not confirmed
```

`quote-build` prices on a placeholder and labels every line it touches
"placeholder rate — not confirmed". The gaps list names the placeholder, never
its value.

A rate the person answering didn't know is a **placeholder**, not a
sensitive value — it isn't the plant's real number. Its value sits in the
rates file with its assumption; the gaps list and the setup summary name it
as a placeholder. When the real value is supplied it becomes **confirmed** and the
placeholder marker drops.

**How the setup summary and the config profile page show this section.** By
state, never by value: *"Labor rate: confirmed, given by Pat Doyle on
2026-10-02"*, *"Burden rate: set in environment"*, *"Downtime cost per hour:
not set"*. A placeholder may show its value, because it is not the plant's
number.

**Never accept a credential, API key or client secret in conversation.** Those go
into connector settings on the plugin side. If someone pastes one, say plainly
that it should be rotated — **without repeating any part of it**. It is "the
token you pasted," never the string, not even inside the rotation instruction.

Commercial rates are not credentials: they are asked about directly, per
`interview.md` group 10, and stored as above. A rate typed at step 10 is shown
once in the approval draft and nowhere else in the conversation; a rate typed
to any other skill is not used for that run and not repeated, and the step 10
update is offered instead. Both rules are
`../../../shared/secret-config.md`, *Never repeat what was typed*.

---

## Degradation map

Step 11's gaps list is generated from this table. Each row is a config item, who
reads it, and **what the consuming skill does when it is missing** — which is
always "state the limit," never "guess."

| Config item | Consumed by | Missing behavior |
|---|---|---|
| Connectors live | Every skill | Skill runs its file-only path and names which sources were file-sourced |
| CMMS connector live (custom) — Limble is the worked example | `breakdown-diagnosis`, `breakdown-to-next-report`, `daily-production-report`, `morning-plant-pulse`, `data-consolidate`, `root-cause-capa` | `breakdown-diagnosis` loses live asset records, open tickets and the current PM plan, and reads history from the export. `daily-production-report` loses its **maintenance work orders in progress** line: replaced from the maintenance export where one exists, otherwise omitted and said so. The others read maintenance from the export and name it export-sourced in the freshness banner |
| Fusion live, or a CAD connector live (custom) | `design-space-explore`, `rfq-to-quote` | `design-space-explore` cannot generate variants without one; names exactly what is needed, quoting `../../custom-connector/reference/known-systems.md`. `rfq-to-quote`'s design step is skipped and hours fall back down the ladder, labelled. `trade-study-report` is unaffected |
| Machining data | `quote-build`, `rfq-to-quote` | Hours derived from a drawing run on library defaults and rank as first-principles, labelled "library defaults, not plant data". An assumed setup or tool-change figure is used and named in every variance it drives |
| ERP scope: plant parts and locations | `data-consolidate`, every ERP reader | Says *scope not set* as a gap and pulls nothing it would have to guess the scope of; offers the item prefix it saw as a question |
| ERP scope: part revision | `supplier-quote-request`, `quote-build` | The revision check says where it looked and that the ERP's revision location is not set; the hard stop holds |
| ERP scope: cost fields | `quote-build`, `supplier-quote-request`, `daily-production-report` | Reads standard, then average, then last purchase price, naming the field each figure came from; never treats a field equal to the sell price as a cost |
| ERP scope: work order source | `data-consolidate` | Treats the ERP as the work order source; where it returns none, says so once rather than reporting every MES row unmatched |
| Approved normalizations | `data-consolidate`, `morning-plant-pulse`, `daily-production-report` | Every fix is proposed again and every affected figure is provisional |
| RFQ stale after | `customer-inquiry-intake`, `rfq-to-quote` | 5 business days, labelled *default, not plant-set* |
| Approved suppliers | `supplier-quote-request` | Candidate list from ERP vendors only, every one flagged as not confirmed approved |
| Connector options | Systems named in Step 1 | Stay on exports; listed on the gaps list as "connector options not reviewed" |
| Report depth | `ncr-writeup`, `root-cause-capa` | Full detail |
| Export folder path | `data-consolidate`, `daily-production-report` | Ask once per run; produce an export request specification if none exists |
| Export file inventory | `data-consolidate`, `daily-production-report` | Identify by header signature and ask the user to confirm each file |
| Source clocks | `root-cause-capa`, `daily-production-report` | Refuse to correlate across sources; report the alignment gap |
| Shift pattern and day boundary | `root-cause-capa`, `daily-production-report` | `root-cause-capa`: the shift-clustering check cannot run — report it among the checks that could not run, and treat cross-midnight attribution as unresolved rather than guessing which day an event belongs to. `daily-production-report`: cannot compute availability; report output only and say why |
| Vocabulary | `data-consolidate`, `breakdown-diagnosis`, every report | Use canonical names and say they are canonical, not the plant's |
| Capability profile | `customer-inquiry-intake` | Bid/no-bid degrades to a constraint-free recommendation and must say so |
| Commercial rates | `quote-build`, `daily-production-report`, `breakdown-diagnosis` | Resolved per `../../../shared/secret-config.md`: `MFG_*` variable, then a confirmed rate in this block, then a placeholder. Without a rate on file in either route, the gaps list names it (never its value) and the consuming skill states the limit — `quote-build` blocks the line the rate feeds, `daily-production-report` prices scrap only and states downtime is unpriced, `breakdown-diagnosis` reports downtime in hours only |
| Templates | `ncr-writeup`, `root-cause-capa`, `quote-build`, `supplier-quote-request`, `trade-study-report` | Use a neutral structure and flag that it is not the plant's controlled format |
| Standards and clauses | `supplier-quote-request` | List clauses found on the part record and flag the set as unverified |
| Sites | Everything | Treat as single-site; ask before applying any site-scoped value |

All twelve skills are built. This table is the contract they're built
against — the profile captures every value listed here regardless of which
skill happens to read it in a given run.

---

## Versioning and reconfigure

**`Profile version` increments when the schema changes**, not when a value
changes. A skill reading an older version fills only the fields it needs and
leaves the rest alone.

**Reconfigure never wipes unrelated configuration.** A shift pattern change
touches one site block. A newly connected system touches the connector lines,
its `### Systems` line and the source clock table. More documents ("here's
more") add rows to `### Documents read at setup` and touch only what they were
confirmed to change. Show the current value and the proposed value side by
side, change only what the user confirms, and update `Configured`.
