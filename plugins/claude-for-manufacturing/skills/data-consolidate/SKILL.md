---
name: data-consolidate
description: "Joins the plant's scheduled exports and connector data into one working dataset — ERP items (NetSuite or Infor M3), sales orders, production work orders, purchase orders, inventory, routings and closed-job operation actuals; CMMS assets and maintenance work orders; and the MES, historian, quality and planning files landing in the Microsoft 365 export folder. Keys on part number, production work order, sales order, lot, asset and supplier, classifies every key that fails to match into one of eight mismatch classes, and proposes the correction rather than reporting a count, applying nothing without a yes. Runs file-only with no connector, or connector-only with no files. Use when someone says \"pull the data together,\" \"consolidate the exports,\" \"build the dataset,\" \"join production to the ERP,\" or \"why don't these numbers match,\" and before any reporting or quoting skill runs."
compatibility: "Requires none. Reads the ERP (Oracle NetSuite or Infor M3), a CMMS connector (Limble is the worked example) and the Microsoft 365 export folder when connected, and runs on files alone or connectors alone. Emits an XLSX dataset plus an HTML data quality report."
---

# Data Consolidate

The foundation layer. The dataset this skill produces is where every
data-dependent skill reads from by default, rather than going back to the raw
sources — and it is the only place the sources are joined and their key
mismatches classified.

**"By default" is exact, not a hedge.** Three skills also read a
raw export, and they are right to: see
`../../shared/contracts/consolidated-dataset.md`, *What this dataset is
authoritative for*. Nothing here carries a high-frequency sensor trace, and a
normalized value is not always the value as recorded.

**The reason it exists.** The majority of real manufacturing data does not arrive
through a connector. It arrives as a file. The plant already runs scheduled
exports out of its MES, historian, inspection system and planning tool, usually
into a shared drive for somebody's spreadsheet. This skill reads that folder plus
the live connectors, joins everything on the identifiers the plant already has,
and hands back one dataset with every unmatched record explained.

**Quick start**

> "Pull last month's production together with the ERP."

```
→ Read the export folder; identify each file by name and header signature
→ Report each source's timestamp and coverage window before joining anything
→ Pull the ERP (NetSuite or Infor M3) and any live CMMS connector scoped to the same window
→ Normalize keys up the ladder, logging every rule that fires
→ Join around the five anchors: part, production work order, sales order, lot, asset
→ Classify every mismatch, propose each fix, apply nothing without a yes
→ Emit the dataset and the data quality report
```

---

## Inputs

**First, find the plant setup:** from the task's own folder (never `cd` into the plugin), run
`python3 -I <this skill's folder>/../../shared/scripts/plant_setup.py find`, do its `setup_page_first` step, then read the profile at
`profile_path` and any rate at `rates_path`, per `../../shared/replies.md`.

| Input | Source | Form |
|---|---|---|
| Item / part master | The ERP: NetSuite or Infor M3 | Connector |
| Sales orders | The ERP | Connector |
| Production work orders | The ERP | Connector |
| Purchase orders and suppliers | The ERP | Connector |
| Inventory positions | The ERP | Connector |
| Routings — operations, work centers, setup and run standards per part and revision | NetSuite where manufacturing routings are licensed; else an ERP export or an Excel sheet dropped in. Infor M3 always takes the export | Connector, CSV / XLSX |
| Operation actuals — setup and run hours per closed production work order and operation | NetSuite closed work orders where licensed, or Infor M3 work order operations; else an export or an Excel sheet | Connector, CSV / XLSX |

Which M3 call fills each row, and what M3 does not give, is
`../../shared/erp-connectors.md`. Read it before an M3 pull.
| Assets and maintenance work orders | CMMS | CMMS connector, else the maintenance export |
| Actual production output | MES export to the M365 folder | CSV / XLSX |
| Downtime events | MES or historian export to the M365 folder | CSV |
| Inspection / quality results | Quality system export to the M365 folder | CSV / XLSX |
| Planning / schedule | Planning tool export to the M365 folder | CSV / XLSX |

Four of those have no connector and never will. File-only is the designed path,
not the degraded one. Routings and actuals are often a spreadsheet someone
keeps, and that is a complete input.

The machine class to work center and cell map, the time units, and anything
else this skill reads about machining come from `### Machining data` in the
`## Plant context` block, which `onboarding` writes. Where that section is
absent, say so once and carry on without it.

---

## Workflow

### Step 1 — Discover

Read the configured export folder. Identify each file by name pattern and header
signature, and say what each one was identified as.

**Report anything unrecognized rather than guessing.** A file that cannot be
identified is named and set aside, not silently skipped and not hopefully parsed.

**Routings and operation actuals are recognized by header, not by hope.** A
routing carries part, operation sequence, work center and a setup and run
standard; an actuals file carries a production work order, an operation and
the hours booked against it. The signatures are in `reference/join-keys.md`,
*Routings and operation actuals*. A file that looks like either but misses a
signature column is unrecognized and named, not loaded with the gap filled.

**When the folder holds months of daily files**, do not read everything. Offer
the choice — latest drop, or a named date range — and state which was used.

`onboarding` owns the folder path, the file inventory and the refresh cadence —
read them from the `## Plant context` block rather than asking. If no profile
exists, ask for the path once, carry it through the run, and offer `onboarding`
so the next run does not ask again.

**If the folder is empty, missing, or there are no files at all**, do not stall
on discovery. Ask for the date window once, then go to step 3 and run
connector-only. **In an unattended run (Chain 3, triggered host-side — see
`../../shared/scheduling.md`) there is no
one to ask** — use the production-day range from the `## Plant context`
block instead, per Step 2's fallback, and say the window was chosen rather
than inherited from a file. That path is specified under Degradation.

### Step 2 — Freshness check

Record every source's last refresh timestamp and the window it covers, and put
that in front of the user **before** any joining or any figure.

**Refuse to join sources whose windows do not overlap meaningfully**, and say so
plainly rather than producing a dataset full of manufactured mismatches. The
rule is `../../shared/absent-is-not-zero.md`; a stale export is the normal
failure here, not the exotic one.

**A source timestamp later than the run time is a critical freshness
finding.** A created, last-modified or transaction date after now means the
source's clock is ahead or its data was seeded with future dates; either way
none of its `as_of` values can be trusted. Say so in the banner, by source and
with the latest such timestamp, give no "data as of" or age for that source,
and do not use its dates to set a window. The rows stay, flagged
`future_timestamp`. A due, promised or delivery date in the future is a
commitment, not this finding.

**Where the windows overlap only in part, state the overlap in dates and offer
exactly two choices, named as such:** *(1) narrow the join to the overlap,
2026-08-01 to 2026-08-31, or (2) wait for the next export and re-run.* Never
one choice, and never narrow silently: "I've scoped every total to August" is
a decision the user did not make. Whichever they pick, every total below is
labelled as scoped to that window.

**The window applies by entity, not to every row alike.** Narrowing scopes
activity records only. Open commitments are kept by status, and reference
history by a lookback, because those are exactly the records later skills
need. The three kinds, and the lookback, are in `reference/join-keys.md`,
*Date windows by entity*. Say in the report which kind each tab was scoped as.

### Step 3 — Pull connector data

The ERP (NetSuite or Infor M3) and any live CMMS connector, scoped to the same date window as the file exports. Pulling
a wider window than the files cover creates Class 7 mismatches out of nothing.

**If there are no file exports**, the window is the one the user just gave, or
the production-day range from the `## Plant context` block. Scope the connector
pull to that, and say that the window was chosen rather than inherited from a
file.

**Never hard-fail on a missing custom field.** Customers configure NetSuite
heavily and field names vary by account. Fall back, and report what could not be
read. An Infor M3 search stops at about 30 rows without saying so: pull in
slices until one returns fewer, per `../../shared/erp-connectors.md`.

**Scope every pull by the profile's `### ERP scope`**, per
`../onboarding/reference/erp-scope.md`: this plant's subsidiary, locations and
parts. With no scope set, say *scope not set* as a gap, and **ask, in so many
words: "Which of these items are your plant's parts?"**, showing what a filter
would catch (*"10 of 515 items start `PN-`"*). Never pick a filter silently, and
never answer "how many parts" with one figure until the scope is answered. Where the scope says production work orders are **MES
only**, take work order identity from the MES export and say so once; never
report every MES row as unmatched against an ERP that holds none.

**When a connector and an export cover the same entity, check key overlap
before joining them.** Zero or low overlap means they are not two views of one
system: ask which is authoritative (or read the profile's *Source of truth*
line), join only that one, and set the other aside by name. Never merge them,
and never report every record of one as unmatched against the other.

### Step 4 — Normalize keys

Apply the normalization ladder in order — trim, case, punctuation, leading zeros,
revision suffix. Read `reference/join-keys.md` for the ladder, the six keys and
their sources of truth.

Compare on the normalized form and store the original verbatim. **Every
normalization that fires is logged and reportable.** A missing part prefix
(`4471B` against `PN-4471-B`) is part of rung 3 only where exactly one part
on the `parts` tab matches once its prefix is dropped; the ladder says which prefix it used.

**Until a fix is approved, the rows it would join are not joined.** They carry
`join_status: proposed_normalization`, and only a yes turns them into
`normalized`. A downstream skill reading the status alone must never take a
proposal for a join.

### Step 5 — Join

Build the dataset around the anchor entities: part, production work order, sales
order, lot, asset. Tabs, columns and required fields are fixed by
`../../shared/contracts/consolidated-dataset.md` — that schema is the plugin's
stable interface and `custom-connector` maps new systems onto it, so it changes
deliberately and with a version bump, never incidentally.

Keep production work orders and maintenance work orders distinct — the two
systems use the same word for different records.

**Detect unit-of-measure columns and flag a mismatch rather than summing across
it.** Each versus box of twelve, inches versus millimetres. A total computed
across two units is not a total. **A units conflict is an integrity flag on the
row**, carried on the dataset and named in the report: refuse a single total
for that key, report each quantity in its own unit, **and compute no
conversion** — not "about 6,200 each if box12 means twelve", not a speculative
factor of any kind. What a `box12` holds is a fact from the plant, not an
inference.

**Run the integrity checks on every row, in code**, per
`reference/join-keys.md`, *Integrity checks*: the sign of a quantity (NetSuite
writes sales order and fulfilment lines as negative; Infor M3 writes them positive), a downtime event that
ends before it starts or whose duration disagrees with its own start and end,
and an NCR whose part or date disagrees with the production work order it
cites. Each failure is a named value in the row's `integrity_flags`, counted
in the figures block and reported. None is fixed silently.

**Time units on routings and actuals get the same rule.** Record each time in
its source unit with the unit named — minutes or hours, read from the header or
a unit column, never from the size of the number. Where a unit is undeclared,
or a routing states minutes and the actuals for the same operation state hours,
**flag it on both rows and compute no conversion** into the dataset. The
backflush check below may convert for its own comparison, and prints that it
did.

**Map each work center to its cell** through the `Machine classes` table in the
Plant context (its `Work centers` and `Cell` columns). A work center the map
does not list is named, with its cell left null — not guessed from its name.

**Run the backflush check on every actuals row, in code.** Set
`actuals_confidence: probable_standard` where actual run hours ÷ quantity
matches the routing's run standard within 1%, or where two or more work
orders for the same part and operation agree on run hours per unit within
about 1%. Real shop time is not that tidy; an ERP posting the standard is.
Print the figures that set it, and **name the flag by its value,
`probable_standard`**, in the report, so the estimator can find it on the tab.
The rows stay in the dataset, shown, and
`quote-build` will not rank them above a geometry-derived estimate.

### Step 6 — Classify mismatches

Every unmatched record goes into one of the eight classes in
`reference/mismatch-classes.md`, reported separately, with counts **and example
rows**.

**Two routing findings are named by what they are.** A routing for a part the
item master does not hold is an orphan (class 1): *routing with no matching
part*. A routing written for a different revision from the one being quoted
or held as current is a *routing revision mismatch* (class 4), and **for
routings class 4 has no automatic fix**: stripping the revision to make it
join would price the new revision on the old one's operations. Detail in
`reference/mismatch-classes.md`.

**A one-sided record another source contradicts is not left as nothing
wrong.** Before calling a record Class 6, check whether another source records
the very activity whose absence made it one-sided: an NCR, inspection rows or
a lot citing a production work order with no output. Where one does, the record stays Class 6 and
carries `contradicted_by` naming that source and record, and every consumer
treats it as an exception. Downtime or maintenance on a machine with no
production does not contradict anything.

**Check the date window class first.** It explains most large mismatch counts,
and reporting the other seven on top of an unnoticed window gap sends someone
chasing problems that do not exist.

**`as_of` carries a zone, or the row says it could not.** The contract requires
a timestamp with zone on every row. A NetSuite record gives a date and time;
its zone comes from the account's company preference, or failing that from the
`## Plant context` source-clock row for NetSuite. An Infor M3 record's zone is
the server clock (`ARS200MI_ServerTimeZone`), or the source-clock row for M3. Where neither is available,
**do not invent a time or a zone**: mark the row `as_of` date-only, flag it,
and say which downstream checks that weakens (cross-source correlation in
`root-cause-capa`; cross-midnight attribution in `daily-production-report`).

### Step 7 — Count in code, and reconcile before writing

Every figure the report states — rows in, rows joined, matched exactly,
matched after normalization, rows awaiting a proposed fix, records per class,
rows per integrity flag, actuals rows flagged `probable_standard` — is
counted in code and put in
the figures block (`../../shared/computed-figures.md`). **Reconcile the block
before writing a word from it:** exact plus normalized equals matched, and the
normalized total equals the sum of the classes that make it up. A headline
that disagrees with the report's own class counts is the first thing a reader
finds, and it discredits every finding beside it.

### Step 8 — Emit

The dataset and the data quality report, per Output below.

---

## Approval gates

**Propose the fix; never apply it silently.** For every mismatch class, produce
the correction rather than a count — "37 records match if the `Rev 2` suffix is
stripped; apply?" — **or, where a class has no automatic fix, say so explicitly**
rather than leaving the finding to speak for itself. The proposal (or the
explicit no-automatic-fix statement) is always shown; an applied fix always
needs an explicit yes. A flagged mismatch with neither a proposed fix nor a
stated reason there isn't one is work handed back to the user, which is the
thing this skill exists to stop.

**A yes covers what was shown.** Every class is presented with its rule, its
count and its example rows before anything is applied. Then:

- **"Apply them all" applies every class already shown in this conversation**
  with those details. It is a yes to each of them, because the user has read
  each of them.
- **Any class not yet shown is presented and asked about first.** A blanket
  yes never reaches a class nobody has read.
- **Classes with no automatic fix are never applied by any yes** — duplicate
  keys, orphans, genuine one-sided records. They are questions, and a yes to
  "apply the fixes" is not an answer to them.
- **The reply lists each class it applied, with its count**, and notes that
  the verbatim values are kept in the `_verbatim` columns so any of it can be
  undone.
- **Each approved rule is saved to the profile's `### Approved
  normalizations` list** (rule, both spellings, who said yes, date), where the
  plant's memory lives per `../../shared/replies.md`, and the reply says so.
  Every later run applies the rules on that list and only those; an overnight
  run rebuilds the dataset, and without the list every night would re-propose
  the same fixes.

The rule is `../../shared/approval-gates.md`.

**A pending decision leads the reply and the report, without replacing
either.** Above the sources and the details, one bold block headed
**DECISION REQUIRED: APPROVE OR REJECT** for each normalization still
awaiting a yes: the exact pair (`4471B` to `PN-4471-B`), why it is proposed
and its limits, the rows and quantities it touches, what approving and what
rejecting each do, and the reply asked for. A rule already on the approved
list shows as **APPROVED** and is never asked again; a rejected one stays
unmatched and is not re-proposed. Questions with no automatic fix (orphans,
duplicates, missing units) are never folded into the block, and approving
the block resolves none of them. With nothing pending, say so in one line and
lead with the real next action. The full report keeps every section it had.

- **Duplicate keys have no automatic fix, ever.** Surface both rows and let
  the user say which is real. Never pick, never sum.
- **Orphan records and genuine one-sided records have no automatic fix
  either** — they're questions, not formatting problems. Report them with
  the evidence that bears on which explanation fits.

This skill writes nothing back to any system of record. It reads, joins, and
hands back files.

---

## Output

**Every document this skill produces is printed in the reply, in full.**
Saving a copy to a file as well is fine, as Word or Excel per `../../shared/replies.md`, never `.txt`; a file *instead of* the reply is not.
The person reads the reply, and every delimited block and outbound check lives
in it — a document only on disk has been neither seen nor checked.
**A record handed to another skill is saved and summarised, never pasted as
raw YAML**; memory blocks are written where the plant's memory lives; and the
name on an approval is asked, never taken from the account. All three per
`../../shared/replies.md`.

**The consolidated dataset** — one queryable workbook, per
`../../shared/contracts/consolidated-dataset.md`. One tab per input
entity, including `inventory` (on-hand by part and location, not a
single total on `parts`), `ncrs` where an NCR export was read, and `routings`
and `operation_actuals` where those sources exist. XLSX is the v1 writer, not a commitment; the shape is the
contract.

**The data quality report** — rendered as an HTML page in the house artifact
style (`../../shared/artifact-style.md`), using the freshness banner, stat tiles
for rows in versus rows joined, a status pill per mismatch class, and a proposal
block for anything awaiting a yes. It carries:

- Source inventory with each source's freshness and coverage window
- Row counts in versus row counts joined, per entity
- Mismatches by class, each block headed by its plain-language name with the
  number in brackets — *"Format drift (class 2)"* — with its count, its example
  rows, **and how many records would join if the fix were applied**
- Every normalization rule that was applied, and what it touched
- Where routings or actuals were read: each time-unit flag with both units
  named, each work center with no cell, and each `probable_standard` row with
  the arithmetic that set it — or the routing tab named missing
- What each finding means for the plant, in one line each
- **The figures block** — every count above with the filter that produced it,
  reconciled per Step 7. The stat tiles and the prose quote it
- **A verbatim lookup, shown by example**: the report demonstrates that the
  `_verbatim` columns answer a search by the spelling a source prints — one
  lookup each for a format-drift, a revision-suffix and a case-and-whitespace
  spelling, each finding its source row. A plant person searches by the number
  their MES prints, and this is how they know they can. **When only one system
  was read**, no second spelling exists: say *not applicable: single-source
  run* for the lookups and for classes 2 to 5, rather than inventing an example
- Every integrity flag raised, by name and count, with example rows: sign
  conventions applied, downtime that ends before it starts, NCRs that
  disagree with their work order, future timestamps

**Write it for a plant person, not an engineer.** A quality manager or a
supervisor has to read this report and know what to go fix, in their own
vocabulary. If it reads like a diff, it has failed.

---

## Edge cases and failure modes

- **An export is stale by weeks and nobody noticed** — the freshness check is
  loud, at the top, never a footnote.
- **The folder holds three months of daily files** — offer latest or a range;
  never read everything by default.
- **A file is open and locked** — handle it gracefully, name the file, continue
  with the rest.
- **A customer-added NetSuite field is missing** — never hard-fail; report it.
- **An Infor M3 list call returns "Record does not exist"** — that is an empty
  result, reported as empty, not a failed pull.
- **Units differ between sources** — flag, do not sum.
- **A routing in minutes, actuals in hours** — flag both rows, convert nothing
  in the dataset.
- **Two work orders agree to the hundredth of an hour per piece** — that is
  the backflush check, not a good week. Flag `probable_standard` and show why.
- **A routing has no revision** — revision unknown, never assumed current.

---

## Degradation

**If Limble isn't included, or no CMMS connector is live** (the
default) — minor. The CMMS is one of roughly ten inputs, and
assets and maintenance work orders arrive in the same scheduled export as
everything else. The skill treats them identically; this is precisely the case it
was designed for.

The one real change: maintenance data inherits the export's freshness instead of
being live. **Name it explicitly in the freshness banner** rather than letting it
sit unlabelled among the other sources, so nobody reads exported maintenance
history as this morning's tickets.

**If no connector is available at all** — the skill runs on the export folder
alone, and that is a complete outcome. State which sources were file-sourced.

**If no files are available at all** — the skill runs on the live connectors
alone, and that is also a complete outcome. Ask for the date window (or take it
from the plant context), pull the ERP and any live CMMS connector scoped to it, and emit the
tabs those connectors can fill: parts, production work orders, sales orders,
inventory, assets, purchase orders, maintenance work orders.

Name every tab that could not be built — production output, downtime,
inspection, plan, **and lots**, because lot numbers come only from the MES or
quality exports — as missing, not empty. Per
`../../shared/contracts/consolidated-dataset.md`, an absent tab is a named gap;
an empty tab reads as "nothing happened." State that every source in this run
was connector-sourced, so the freshness banner is the connector timestamps, not
an export cadence.

Join and classify only across the keys that exist on both sides of a connector.
Do not invent MES-shaped mismatches because the MES file was never there.

**If there is no routing data at all** — no routing connector, no routing file
— the `routings` tab is **named missing, not left empty**. An empty routings
tab reads as "this part has no operations." The same holds for
`operation_actuals`. Say which quoting rungs that removes, in one line:
without routings, `quote-build` starts at closed-job actuals; without either,
at a geometry-derived or first-principles estimate.

---

## Chain position

- **Chain 1, RFQ to quote** — step 2, between `customer-inquiry-intake` and
  `quote-build`
- **Chain 3, Morning plant pulse** — step 1, feeding `daily-production-report`
- Feeds `quote-build`, `daily-production-report`, and every reporting skill

Those skills read this dataset rather than the raw sources. If the join is
wrong, they are wrong in ways that are hard to debug.

**Metric.** Enabling only. It does not move a plant number by itself; measure it
by whether downstream skills can run.

---

## Reference files

| File | Load when |
|---|---|
| `reference/join-keys.md` | Before joining — the six keys, their sources of truth, the normalization ladder, date windows by entity, the integrity checks, and the routing and actuals signatures, cell map and backflush check |
| `reference/mismatch-classes.md` | When classifying join failures — the eight classes, detection and proposed fix for each |
| `../../shared/contracts/consolidated-dataset.md` | Steps 5 and 8 — the output schema every downstream skill reads |
| `../../shared/approval-gates.md` | Before applying any fix — what a yes covers, and a blanket yes |
| `../../shared/computed-figures.md` | Step 7 — the figures block, and reconciling it before writing |
