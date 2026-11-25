# Contract: the quality register record

**Emitted by** `ncr-writeup` (creates and updates the row, and closes it on the user's word) and `root-cause-capa` (adds the investigation fields)
**Consumed by** the Quality Register dashboard, rebuilt from every row on each run that writes one
**Chains** 2 (inspection to CAPA) and 5 (supplier escape to alternate source)
**Contract version** 1

Rules that govern every contract are in [README.md](README.md). How records
are stored, keyed and read is `../live-dashboard.md`.

---

## Why it exists, and why it is not the NCR

A single run knows the one NCR in front of it. A register of open corrective
actions needs every other one, so each NCR and 8D run leaves a row behind in
the register's own database. The page is rebuilt from all of them.

**This is a separate contract so [ncr.md](ncr.md) stays stable.** The NCR is
the handoff between two skills; this is the register's row. It copies the few
NCR fields the register shows and adds the fields only a register needs.

**Each field is written by the skill that knows it at that moment.** The NCR
fields and the status are known when `ncr-writeup` writes the NCR. The
investigation fields are known when `root-cause-capa` drafts the 8D. A skill
never writes a field it does not know yet: it leaves it null, and the page
says *not yet*.

**References, never documents.** The row carries the NCR reference and a one-
line summary, never the NCR, the 8D or anything from a redacted customer pack.
It does carry customer names and notification deadlines, which is why the
register is internal (see `../secret-config.md`).

---

## Identification — from the NCR

| Field | Type | Producer | Behavior | Notes |
|---|---|---|---|---|
| `contract_version` | integer | both | Required | |
| `record_key` | string | `ncr-writeup` | Required | `<site>_<ncr_ref>`, e.g. `Fairview_NCR-2026-0141`. The `ArtifactData` document key in `ncrs`. A second run on the same NCR overwrites it |
| `ncr_ref` | string | `ncr-writeup` | Required | |
| `site` | string | `ncr-writeup` | Required | Rule 7 |
| `part_number` / `part_number_verbatim` | string | `ncr-writeup` | Required | Rule 3 |
| `lot_number` / `lot_number_verbatim` | string or null | `ncr-writeup` | Degrades | |
| `found_at` | timestamp with zone | `ncr-writeup` | Required | Rule 4 |
| `qty_found` / `uom` | number / string | `ncr-writeup` | Required | Rule 5 |
| `requirement_cited` | string or null | `ncr-writeup` | Degrades | One line: document and locator. Null with `status: blocked` when not locatable |
| `disposition_pending` | boolean | `ncr-writeup` | Required | |
| `summary` | string | `ncr-writeup` | Required | One line. The condition found, never the document |
| `customers` | list of strings | `ncr-writeup` | Required | Affected customers from containment. Empty list when no parts reached a customer |

## Register state

| Field | Type | Producer | Behavior | Notes |
|---|---|---|---|---|
| `status` | enum | `ncr-writeup`, `root-cause-capa` | Required | `blocked` (no locatable requirement), `awaiting_approval` (NCR not yet `approved`), `open`, `closed` |
| `approval_state` | enum | `ncr-writeup` | Required | Copied from the NCR at the time of writing: `draft`, `approved`, `rejected` |
| `containment_summary` | string | `ncr-writeup` | Required | e.g. "5 of 5 locations addressed; installed at customer not checked" |
| `escape_clock` | timestamp with zone or null | `ncr-writeup` | Degrades | The NCR's `notification_deadline`. Null when there is no escape, or when the contractual window is unknown, and then `escape_clock_unknown` is true |
| `escape_clock_unknown` | boolean | `ncr-writeup` | Required | True when parts reached a customer and no window could be computed |
| `owner` | string or null | `ncr-writeup`, `root-cause-capa` | Degrades | The person named as owner in the run. Never guessed. Null reads *unassigned* |
| `due_date` | date or null | `ncr-writeup`, `root-cause-capa` | Degrades | The next committed date: the escape clock, then a customer-stated 8D due date. Null reads *no due date*, never overdue |
| `recurrence` | enum | `ncr-writeup` | Required | The NCR's value, unchanged |
| `prior_ncr_refs` | list of strings | `ncr-writeup` | Degrades | From the NCR's `related_records` |
| `previous_fix_held` | boolean or null | `ncr-writeup` | Degrades | Null when there is no prior record or no searchable history. Never read as true |

## Investigation — from the 8D

| Field | Type | Producer | Behavior | Notes |
|---|---|---|---|---|
| `eight_d_step` | string or null | `root-cause-capa` | Degrades | The last discipline drafted, e.g. "D5 drafted; D6 and D8 placeholders". Null until an 8D is drafted |
| `leading_cause` | string or null | `root-cause-capa` | Degrades | One line. The top-ranked candidate, labelled as a candidate, never as established |
| `supplier_caused` | boolean or null | `root-cause-capa` | Degrades | True only when the supplier-caused flag was raised. Null until investigated. The supplier signal itself lives on the Supply Chain page |
| `effectiveness_check_due` | date or null | `root-cause-capa` | Degrades | Only when a date has been committed. Null until then |

## Close and provenance

| Field | Type | Producer | Behavior | Notes |
|---|---|---|---|---|
| `closed_at` | timestamp with zone or null | `ncr-writeup` | Required when `status` is `closed` | When the user said to close it |
| `closed_by` | string or null | `ncr-writeup` | Required when `status` is `closed` | Who said so, as they gave it |
| `last_written_by` | string | both | Required | `ncr-writeup` or `root-cause-capa` |
| `last_written_at` | timestamp with zone | both | Required | Rule 4 |
| `first_recorded_at` | timestamp with zone | `ncr-writeup` | Required | Kept from the first write. The oldest of these is the date in the banner |

**An update rewrites the whole row.** `ArtifactData` `set` replaces the
document, so a skill reads the existing row first and carries forward every
field it does not own. `root-cause-capa` never blanks the escape clock;
`ncr-writeup` re-run on an NCR never blanks the 8D fields.

---

## Worked example

`NCR-2026-0141` after `ncr-writeup` and then `root-cause-capa`:

```yaml
contract_version: 1
record_key: Fairview_NCR-2026-0141
ncr_ref: NCR-2026-0141
site: Fairview
part_number: PN-4471-B
part_number_verbatim: "PN-4471-B"
lot_number: H-4140-2291
lot_number_verbatim: "H-4140-2291"
found_at: 2026-08-12T09:20:00-04:00
qty_found: 3
uom: each
requirement_cited: "4471-B-drawing.pdf, p2, datum B, true position 0.002 in max"
disposition_pending: true
summary: "True position 0.0061 in against 0.002 in max; heat H-4140-2291 ran on three work orders."
customers: ["Example Hydraulics"]

status: open
approval_state: approved
containment_summary: "5 of 5 locations addressed; installed at customer not checked"
escape_clock: 2026-08-14T09:20:00-04:00
escape_clock_unknown: false
owner: "Priya Raman"
due_date: 2026-08-14
recurrence: first_occurrence
prior_ncr_refs: []
previous_fix_held: null

eight_d_step: "D5 drafted; D6 and D8 placeholders"
leading_cause: "Candidate: bar stock from heat H-4140-2291 out of straightness spec"
supplier_caused: true
effectiveness_check_due: null

closed_at: null
closed_by: null
last_written_by: root-cause-capa
last_written_at: 2026-08-13T15:02:00-04:00
first_recorded_at: 2026-08-12T10:05:00-04:00
```

Note `previous_fix_held: null`: there was no prior record, so there is no fix
to have held. That is not the same as `true`.

---

## Missing behavior

| Situation | What the register page does |
|---|---|
| `status` is `awaiting_approval` | Counted in *awaiting approval*, not in *open*. The row shows the draft state |
| `status` is `blocked` | Listed with the open items, pill *blocked*, reason "no locatable requirement" |
| `owner` null | *unassigned*. Never filled in by the reader |
| `due_date` null | *no due date*. Never counted as overdue, never as on time |
| `escape_clock_unknown` true | Sorted with the escape clocks, at the top, reading *window unknown* |
| `previous_fix_held` null | *no prior fix on record* or *history not searchable*, from `recurrence`. Never read as held |
| Investigation fields null | *not yet investigated* |
| `status` is `closed` | Out of every open count. Shown in the collapsed closed section with `closed_at` |
| `contract_version` is older | Read the fields it knows; treat the rest as absent, per the README |
