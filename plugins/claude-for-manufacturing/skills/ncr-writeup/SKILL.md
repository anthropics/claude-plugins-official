---
name: ncr-writeup
description: "Writes the nonconformance report: what was found and measured, the specific requirement it violates cited to its document and locator, how many parts are actually suspect and why that scope rather than a narrower one, and where every one of them physically is across all five locations. Searches prior NCRs and CAPAs at the moment of writing and reports whether the earlier fix held. Where containment places parts at a customer, drafts the escape notification automatically against its contractual clock. Never asserts a requirement it cannot locate. Keeps the site's Quality Register of open NCRs up to date, and closes an NCR there when told to. Use when someone says \"write up this nonconformance,\" \"we found bad parts,\" \"raise an NCR,\" \"the inspector rejected this lot,\" \"a customer is complaining about a part,\" or \"close NCR-2026-0141.\""
compatibility: "Requires none. Reads the consolidated dataset for work orders, lots and on-hand inventory by location; the ERP (Oracle NetSuite or Infor M3) for shipments, which the workbook never carries; and Microsoft 365 for drawings, specs and the quality document library. Runs on pasted findings, inspection exports and uploaded drawings with no connector. The NCR uses the plant's or the customer's controlled template, never the house style."
---

# NCR Writeup

The formal record that something did not meet its requirement, written by
whoever found it — an inspector, an operator, a customer complaint landing in
somebody's inbox.

**It has to answer four questions**, and the skill is built around them in
order, because each one depends on the last:

1. **What was found** — the observed condition, measured where possible.
   "Hole diameter 0.512 in," not "hole too big."
2. **Against which requirement** — cited to a document and a locator.
3. **How many parts** — rarely just the one somebody found.
4. **Where they physically are** — which is containment.

**Quick start**

```
→ Capture the finding, structured: part, WO, lot, operation, condition, who, when
→ Cite the requirement. Cannot locate one? Flag blocking. Never invent one
→ Scope the suspect quantity, and show the reasoning behind the scope
→ Locate the parts across all five locations
→ Recommend containment per location, ordered by urgency
→ Search history NOW: prior NCRs and CAPAs, and whether the fix held
→ Parts at a customer? Draft the escape notification against its clock
→ Write the register row, keyed <site>_<ncr_ref>, and update the Quality Register
→ "Close NCR-…"? The user's decision: set the row closed and republish
```

---

## Inputs

**First, find the plant setup:** from the task's own folder (never `cd` into the plugin), run
`python3 -I <this skill's folder>/../../shared/scripts/plant_setup.py find`, do its `setup_page_first` step, then read the profile at
`profile_path` and any rate at `rates_path`, per `../../shared/replies.md`.

| Input | Source | Form |
|---|---|---|
| The finding | Inspector notes, operator report, customer complaint email | Conversation, M365 mail, pasted text |
| Inspection measurements | Quality system export to the M365 folder | CSV/XLSX |
| The requirement | Drawing, spec, standard clause, customer PO flow-down | M365 documents |
| Work order, lot, quantity produced | `data-consolidate` workbook, then the ERP | `../../shared/contracts/consolidated-dataset.md` |
| Where the parts are, on-hand | `inventory` tab — one row per part per location | Same workbook |
| Where the parts are, shipped | ERP shipment records. Infor M3 delivery lines carry no lot (`../../shared/erp-connectors.md`): they give candidate shipments by part and date, each unverified until confirmed | Connector |
| Prior NCRs and CAPAs | M365 quality document library | Documents |
| The plant's NCR template | `## Plant context`, captured during `onboarding` | Template |

**The inspection measurements come from the quality export rather than the
workbook**, because an NCR quotes the condition as measured — "hole diameter
0.512 in" — and that is the value the gage wrote, not the normalized one.
Everything about *identity* still comes from the dataset: which work order,
which lot, where the parts are. See *What this dataset is authoritative for* in
`../../shared/contracts/consolidated-dataset.md`.

Read the plant's vocabulary, sites, standards and template location from the
`## Plant context` block. A plant that says "traveler" gets an NCR that says
traveler.

---

## Workflow

### Step 1 — Capture the finding, structured

Part and revision, production work order, lot, the operation it was found at,
quantity found, the measured or observed condition, who found it, and when with
its timezone.

Take the measurement as recorded, with its gage. A characteristic measured on a
gage whose calibration has lapsed is a finding of its own — check the date if
one is available.

### Step 2 — Cite the requirement

Locate the drawing, spec or clause and cite the **document, the locator inside
it, the characteristic, and the stated value.** Cite it at the revision the part
was actually built to, not the current one.

**If the requirement cannot be located, flag the NCR as blocking and say what
was searched.** Never assert one. Read `reference/requirement-citation.md` —
this is the field the whole chain gates on, and blocking here is a normal,
correct outcome.

### Step 3 — Scope the affected quantity

From the work order quantity, the lot, and the production window. Reason
explicitly from the suspected mechanism outward, and **state the assumption**.

Where traceability is incomplete, the scope widens and says why. Never narrow it
to make the number look better. **Where the widened number is still only what
can be counted, it is a floor**: set `qty_suspect_is_minimum` and write *at
least 660* everywhere it is printed. Where the source records no count of parts
found, `qty_found` is null with `qty_found_reason`, never a number filled in.
Read `reference/scope-and-containment.md`.

### Step 4 — Locate the parts

**Read the workbook first.** Place on-hand quantity from the `inventory` tab —
one row per part per location — and from `production_output` for what is still
at the machine. Map each location into the five containment types using the
plant's vocabulary from the `## Plant context` block.

Then read shipment records for in-transit and at-customer. Those are not on
`inventory`. Use the ERP when it is connected.

**If the `inventory` tab is absent**, do not treat that as zero on hand. Ask
location by location, or read the ERP / an inventory export, and record each
answer as unverified until confirmed. That is the missing behavior on
`../../shared/contracts/consolidated-dataset.md`.

**Address all five, including with a zero quantity.** An omitted location reads
as "none there" rather than "not checked," and `checked: false` is not `qty: 0`.

**Two shapes, one meaning.** In the structured record every entry carries a
number, because `../../shared/contracts/ncr.md` requires `qty` and `uom`: an
unchecked location is written `qty: 0`, `uom: <the part's unit>`,
`checked: false`, never `null`. In the human-readable containment table the
same row reads **"not checked"** and never "0 parts" — a zero in the table is
the false statement `absent-is-not-zero.md` exists to prevent. If "unknown"
ever needs to be representable in the payload itself, that is a contract
change raised with its owner, not a null emitted quietly.

**The table's quantity cell is built from `checked`, not from `qty`:**

| Location | Suspect qty | Action | Urgency |
|---|---|---|---|
| Installed at customer | **not checked** | Confirm with the customer whether any of the lot was installed | immediate |
| Finished goods | 0 (checked, none on hand) | — | routine |

A checked location with none on hand says "0 (checked)"; an unchecked one says
"not checked" and no number. The two are never the same cell.

### Step 5 — Recommend containment per location

Ordered by urgency, with the action for each and the owner left blank for
assignment. Containment happens before anyone knows the root cause — the point
is to stop the bleeding.

**The order is customer side first, always:** `installed_at_customer`,
`at_customer`, `in_transit`, `wip_at_machine`, `finished_goods`. Parts already
in a customer's product are the escape with a contractual clock running; parts
on our own shelf can wait an hour. Every entry carries its `urgency`
(`immediate`, `same_day`, `routine`), and the table is sorted by it, not by
where the parts happen to be easiest to find.

### Step 6 — Search history, now

Prior NCRs and CAPAs on the same part, the same defect, the same process, the
same supplier. **This runs when the NCR is written, not on request**, because
the moment of detection is the only moment anyone is looking.

Report **whether the earlier corrective action held** — the highest-value single
line in Chain 2. With no searchable library, say "no searchable history
available" rather than nothing. **Prior NCRs with no CAPA records are reported
as both facts**: `prior_ncrs_found` counts them, and the line says whether a fix
held cannot be judged. Read `reference/recurrence-and-escape.md`.

**A prior NCR's part label is checked before it counts as same-part
history.** Where the dataset's `ncrs` tab flags it `ncr_part_differs` or
`ncr_dated_before_wo`, or where the ERP holds a different part for the work
order the NCR cites, it is not same-part history: list it as unreliable, with
both parts, and say what it would take to settle.

### Step 7 — Draft the escape notification

If containment placed any suspect parts at or past a customer, draft the
customer notification **as the immediate next output**, with the required
content and the contractual clock stated at the top.

**If the customer locations are unchecked and shipment is plausible** (orders
for the suspect parts promised before today, a customer named on the NCR), the
escape is possible, not ruled out: set `escape_possible`, leave
`escape_detected_at` null, draft the notification **marked conditional on the
shipment check**, and name that check as an action with an owner to fill:
*"Confirm whether any of WO-88412/413/414 shipped on Example Hydraulics's 7 and 19 Sep
orders."* Saying nothing because nothing was verified is how the clock runs out.

Chained straight off containment so nobody has to remember it separately, under
time pressure, against a 24 to 48 hour window. Missing that window is a bigger
problem than the defect.

### Step 8 — Write the register row, and update the Quality Register

A single run knows one NCR. The Quality Register lists all of them, so this
run leaves a row behind. Per `../../shared/live-dashboard.md`, which names
every tool call:

1. **Find the register.** The `## Dashboards` line on the Open work page, then `Artifact`
   `list` for the exact title *"<Site>: Quality Register"*, then create it.
2. **Build the row** per `../../shared/contracts/quality-register-record.md`,
   keyed `<site>_<ncr_ref>`: status, containment summary, the escape clock,
   the recurrence finding and whether the previous fix held. `status` is
   `blocked` when no requirement could be located, `awaiting_approval` until
   the quality owner approves the NCR, then `open`.
3. **Read the existing row first, if there is one,** and carry forward every
   field this skill does not own. A second run on the same NCR overwrites its
   row and keeps the 8D fields `root-cause-capa` wrote. **One NCR, one row.**
4. `set` the row, `list` the collection, compute the register in code and
   publish it, per the register layout in `../../shared/live-dashboard.md`.
5. **Report it:** *"Updated **Fairview: Quality Register**, `<url>`. Private
   to you until you share it."* followed by the sensitivity line, *"Internal:
   it lists customer names and notification deadlines. Check who you share it
   with."* On a fallback: the Quality page in the conversation, its placement
   line, and *"The Quality Register was not updated: [reason]."* That page
   could not read the other rows, so it shows this NCR only and says so; it
   never prints an open count it could not compute. The row is still in the
   reply's summary table, marked not stored.

**The register banner says what it is not:** *"Tracks NCRs run through this
plugin since [date]. Not your full quality library."* A manager reading
"3 open" will otherwise assume that is everything.

**Not a gate.** The register is not a system of record, the row carries the
NCR's own approval state, and nothing in it reaches a customer. The NCR's two
gates are unchanged.

### Closing an NCR

**Closing is the user's decision, never this skill's.** When the user says
*"close NCR-2026-0141,"* read that row, set `status: closed` with `closed_at`
and `closed_by` as the user gave them, and republish. It leaves every open
count and moves to the closed section. Say that this closes it in the register
only; the NCR in the plant's quality system is closed by whoever owns it.

**If the register cannot be read or written this run, the close was not
recorded.** Say so plainly: *"NCR-2026-0141 was not closed in the register:
[reason]. The Quality Register was not updated."* Never report an NCR closed
that was not written closed. There is no in-page editing.

---

## Approval gates

**Two gates, and neither is a formality.**

**Before the NCR is final** — a quality owner confirms the finding, the cited
requirement, the suspect scope and the containment plan. This is the Chain 2 and
Chain 5 gate. The NCR carries `approval_state`, and `root-cause-capa` blocks
anything customer-facing until it reads `approved`.

**Before anything reaches a customer** — the escape notification is drafted,
shown, and sent by a person. Nothing goes to a customer unattended, ever. Speed
is the point of drafting it automatically; unattended sending is not.

Nothing is written back to the ERP or to the quality system. The NCR is a
document the quality owner files.

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

**Report depth follows the plant's preference.** The `## Plant context`
block's **Report depth** line is `summary-first` or `full` (absent means
`full`). Summary-first puts a short summary — what was found, what it
affects, what happens next — above the full document; it moves nothing out and
drops nothing. Every required field is still in the document below it.

**The NCR**, in the plant's or the customer's controlled template captured
during `onboarding` — identification, requirement cited, condition found with
measurements, affected quantity with its reasoning, and the disposition-pending
flag.

Per `../../shared/artifact-style.md`, **a controlled document is never
house-styled.** An NCR has a contractual shape and restyling it would make it
wrong, not nicer.

**Containment plan** — actions by location, ordered by urgency, owners blank.

**Recurrence finding** — prior related records, and whether the previous fix
held.

**Escape notification draft** — when applicable.

**The structured NCR** — per `../../shared/contracts/ncr.md`, in exactly the
shape `root-cause-capa` consumes with no transformation between.

**The register row** — per `../../shared/contracts/quality-register-record.md`,
with its key `<site>_<ncr_ref>`, in the reply's summary table on every run, stored
or not.

**The Quality Register** — *"<Site>: Quality Register"*, the Quality
command-center page, updated in place per `../../shared/live-dashboard.md`.
It carries this NCR by reference, never the document. The run ends with the
dashboard line and the sensitivity line, or with the fallback and *"The
Quality Register was not updated."* Never "shared," never "posted." Read
`../../shared/command-center.md`.

---

## Edge cases and failure modes

- **The requirement genuinely cannot be found** — flag as blocking, list what was
  searched. Do not invent it.
- **Traceability is incomplete, no lot recorded** — widen the suspect scope and
  say why it had to widen.
- **The finding is subjective** — "surface looks wrong." Capture as observed, set
  the subjective flag, note that no measurable requirement was cited.
- **Parts shipped to multiple customers** — separate containment and a separate
  notification per customer. Never merge.
- **Multiple defects on one part** — one NCR with multiple findings, not several
  NCRs, unless the customer's template requires otherwise.
- **The inspection export is stale or does not cover the run** — say so at the
  top. A containment scope computed from data that stops before the event is
  wrong in the dangerous direction.
- **Two revisions of the print in circulation** — record both, say which the part
  was built to. This is often the finding rather than a nuisance.
- **The same NCR written up twice** — the second run overwrites its register
  row by key. One NCR, one row, and the 8D fields already on it are kept.
- **Asked to close an NCR that has no register row** — say it is not in the
  register, and close nothing. The register only knows NCRs run through this
  plugin.

---

## Degradation

The skill runs on a pasted finding and an uploaded drawing with no connector at
all.

| Not available | What happens |
|---|---|
| Consolidated dataset, or no `inventory` tab | Ask where the parts are, location by location, or read the ERP / an inventory export. Record each answer as unverified until confirmed. Never treat a missing tab as zero on hand |
| The ERP (NetSuite or Infor M3) | On-hand can still come from the workbook. In-transit and at-customer cannot. Ask about shipments, and record those two locations as unverified until confirmed |
| Inspection export | Work from the finding as described. Measurements are whatever the inspector reports |
| Quality document library | `no_searchable_history`. Never presented as a first occurrence |
| The plant's or the customer's template | Use a neutral NCR structure covering the four questions, and flag that the controlled template was not available |
| Customer contractual terms | Draft the notification without a computed deadline and ask where the terms are recorded. Do not guess a window |
| The `Artifact` or `ArtifactData` tools | The NCR is unaffected. The Quality page is offered in the conversation, showing this NCR only, with *"The Quality Register was not updated."* A close request is not recorded, and the reply says so |

---

## Chain position

**Chain 2, inspection to CAPA** — step 1, feeding `root-cause-capa`.

**Chain 5, supplier escape to alternate source** — step 1. Where the cause turns
out to trace to purchased material, the chain runs on through `root-cause-capa`
into sourcing.

**Metric.** Nonconformance closure time; escape response time — the clock
from detection to customer notified, which step 7 is what moves.

**Chain 5's escape-to-RFQ metric is segmented, and this skill opens it.** That
window runs escape detected → supplier-caused determination → RFQ issued, and no
single skill controls it. This skill owns detection and containment speed in the
first segment, alongside `root-cause-capa`'s investigation time; the second
segment belongs to `supplier-quote-request`.

**Stamp `escape_detected_at` on the NCR when containment first places parts at
or past a customer.** That is the start of the window, it is not the same moment
as `found_at`, and it cannot be reconstructed afterwards. `root-cause-capa`
carries it forward onto the supplier-caused flag.

---

## Reference files

| File | Load when |
|---|---|
| `reference/requirement-citation.md` | Step 2 — what counts as a requirement, revisions, and what to do when there is none |
| `reference/scope-and-containment.md` | Steps 3 to 5 — reasoning the scope outward, and the five locations |
| `reference/recurrence-and-escape.md` | Steps 6 and 7 — searching at creation, and the contractual clock |
| `../../shared/contracts/consolidated-dataset.md` | Step 4 — the `inventory` tab, and what to do when it is absent |
| `../../shared/contracts/ncr.md` | On emit — the exact shape `root-cause-capa` consumes |
| `../../shared/live-dashboard.md` | Step 8 and on a close — finding and updating the Quality Register, the banner, the fallback |
| `../../shared/contracts/quality-register-record.md` | Step 8 — the register row, and which fields this skill owns |
| `../../shared/command-center.md` | When "updated" may be said |
