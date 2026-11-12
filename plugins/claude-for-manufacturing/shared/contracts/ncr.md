# Contract: the NCR

**Emitted by** `ncr-writeup`
**Consumed by** `root-cause-capa`
**Chains** 2 (inspection to CAPA) and 5 (supplier escape to alternate source)
**Contract version** 4

Rules that govern every contract are in [README.md](README.md).

---

## The four questions an NCR must answer

A nonconformance report is the formal record that something did not meet its
requirement, and it exists to answer four things:

1. **What was found** — the observed condition, measured where possible.
   "Hole diameter 0.512 in," not "hole too big."
2. **Against which requirement** — the specific dimension, spec, standard clause
   or customer requirement violated. **An NCR without a cited requirement is not
   an NCR.**
3. **How many parts** — rarely just the one somebody found. If the cause could
   have affected the whole run, the whole run is suspect until proven otherwise.
4. **Where they physically are** — containment. Five different places, five
   different actions, five different urgencies.

The contract enforces the second one structurally: `root-cause-capa` blocks when
the cited requirement is missing, with a pointer back to `ncr-writeup`.

---

## Identification

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `contract_version` | integer | Required | |
| `ncr_ref` | string | Required | |
| `site` | string | Required | Rule 7 |
| `part_number` / `part_number_verbatim` | string | Required | Rule 3 |
| `part_revision` | string or null | Degrades | Which revision the part was found against |
| `production_wo` / `production_wo_verbatim` | string or null | Degrades | Rule 3. Never named `work_order` — a maintenance work order is a different record |
| `lot_number` / `lot_number_verbatim` | string or null | Degrades | Drives traceability scope |
| `operation` | string or null | Degrades | Which routing step it was found at |
| `found_by` | string | Required | |
| `found_at` | timestamp with zone | Required | Rule 4 |
| `disposition_pending` | boolean | Required | True until a disposition is decided elsewhere |

## The finding

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `condition_found` | string | Required | The observed condition |
| `measurements` | list of objects | Degrades | Each: characteristic, measured, nominal, tolerance, uom, gage, source_ref |
| `is_subjective` | boolean | Required | See below |
| `qty_found` | number or null | Required | Paired with `uom`, rule 5. **Null when the source does not record how many were found**, never a number filled in |
| `qty_found_reason` | string or null | Required when `qty_found` is null | What the source holds instead: *"NCR-2026-0141 records no count; its only figure is one measurement in free text"*. |
| `uom` | string | Required | |

## The requirement — the field that gates the chain

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `requirement_cited` | object or null | **Required to proceed** | Null only with the flag below |
| `requirement_not_locatable` | boolean | Required | True when the requirement could not be found |

`requirement_cited` carries:

```yaml
requirement_cited:
  source: "customer drawing"
  document: "4471-B-drawing.pdf"
  locator: "p2, datum B, 4x mounting holes"
  characteristic: "true position"
  stated_value: "0.002 in max"
```

**Never invent a requirement.** When it genuinely cannot be located, set
`requirement_not_locatable: true`, leave `requirement_cited` null, and flag the
NCR as blocking. That is a complete and honest outcome; an asserted requirement
is not.

## Affected quantity — with its reasoning

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `qty_suspect` | number | Required | The scope, not just what was found |
| `qty_suspect_is_minimum` | boolean | Required | True when `qty_suspect` is a floor and the honest scope has no known upper bound: traceability is incomplete and more work orders, lots or shipments may be involved. |
| `scope_basis` | enum | Required | `single_part`, `lot`, `production_run`, `production_window`, `widened_incomplete_traceability` |
| `scope_reasoning` | string | **Required** | Why this scope and not a narrower one |
| `traceability_complete` | boolean | Required | See below |

**The reasoning is shown, never just the number.** Whether a cause is a one-off
or run-wide is an explicit judgment with a stated assumption, and the consumer
needs it because a run-wide cause and a single-part cause point at different
root causes.

**Where traceability is incomplete, scope widens and says why it widened.**
Narrowing scope to make the number look better is the failure mode this field
exists to prevent. **And where the widened number is still only what can be
counted**, `qty_suspect_is_minimum` is true and every place the number is
printed says *at least*: "at least 660 (3 work orders x 220 ordered); other
work orders on heat H-4140-2291 not yet ruled out".

## Containment — all five locations

`containment` is a list, one entry per location, ordered by urgency. **All five
location types are addressed**, including with a zero quantity, because an
omitted location reads as "no parts there" rather than "not checked."

| Field | Type | Behavior |
|---|---|---|
| `location` | enum | Required. `wip_at_machine`, `finished_goods`, `in_transit`, `at_customer`, `installed_at_customer` |
| `qty` | number | Required |
| `uom` | string | Required |
| `checked` | boolean | Required. False means not verified, which is different from zero |
| `action` | string | Required |
| `urgency` | enum | Required. `immediate`, `same_day`, `routine` |
| `owner` | string or null | Required field, null value. Left blank for assignment |
| `customer` | string or null | Required for customer locations. One entry per customer |
| `source_ref` | string | Required. Rule 6 |

## Recurrence — searched at creation

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `recurrence` | enum | Required | `first_occurrence`, `recurrence_prior_capa_held`, `recurrence_prior_capa_failed`, `no_searchable_history` |
| `prior_ncrs_found` | integer | Required | Prior NCRs the search found on the same part, defect, process or supplier, whatever `recurrence` says. |
| `related_records` | list of objects | Degrades | Each: ref, date, what matched, whether the fix held |
| `history_searched` | boolean | Required | |

The search runs **when the NCR is written, not on request**, because the moment
of detection is the only moment anyone is looking.

**`recurrence` judges whether a fix held; `prior_ncrs_found` says whether it
happened before.** Prior NCRs with no CAPA records to judge are
`no_searchable_history` with `prior_ncrs_found` above zero, and the NCR says
both: "4 prior NCRs on this part; no CAPA records, so whether a fix held
cannot be judged." An NCR whose part label failed the dataset's NCR-to-work
order check is not counted here.

`no_searchable_history` is a distinct value from `first_occurrence` on purpose.
Per `../absent-is-not-zero.md`, silence reads as "no recurrence," which is a much
stronger claim than the evidence supports.

## Escape

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `escape_occurred` | boolean | Required | True when containment places parts at or past a customer |
| `escape_possible` | boolean | Required | True when `escape_occurred` is false only because a customer location is `checked: false`, and the evidence makes shipment plausible: orders for the suspect parts promised before today, a shipped or partly fulfilled status, a customer named on the NCR. |
| `verify_shipment_action` | string or null | Required when `escape_possible` | The named check that settles it: *"Confirm in NetSuite or with shipping whether any of WO-88412/413/414 shipped on Example Hydraulics's 7 and 19 Sep orders"* |
| `escape_detected_at` | timestamp with zone or null | Required when `escape_occurred` | Rule 4. When containment **first placed parts at or past a customer** — not `found_at`, which is when the defect was found. Opens Chain 5's escape-to-RFQ window |
| `notification_drafted` | boolean | Required when `escape_occurred` or `escape_possible` | When only possible, the draft is conditional: it says it goes only if the shipment check finds parts shipped |
| `notification_deadline` | timestamp with zone or null | Degrades | The contractual clock, often 24–48 hours |
| `affected_customers` | list of strings | Required when `escape_occurred` | |

The draft is chained straight off containment so nobody has to remember to do it
separately, under time pressure, against a contractual window. **Missing that
window is a bigger problem than the defect.**

**Unchecked is not "no escape".** When nobody has verified the customer
locations and the parts were plausibly shipped, `escape_occurred` stays false
(nothing places parts at a customer yet), `escape_possible` is true,
`escape_detected_at` stays null, and the NCR carries a conditional notification
draft and the named shipment check. Silence on a plausible escape is how a
contractual clock runs out unnoticed.

## Approval — rule 8

| Field | Type | Behavior |
|---|---|---|
| `approval_state` | enum | Required. `draft`, `approved`, `rejected` |
| `approved_by` | string or null | Required to proceed down the chain |
| `approved_at` | timestamp with zone or null | Required to proceed |

---

## Two fields worth explaining

**`is_subjective` keeps an opinion labelled.** A finding like "surface looks
wrong" is captured as observed and flagged, because no measurable requirement was
cited. `root-cause-capa` cannot run a computed pattern check against a subjective
finding, and it needs to know that before trying.

**`checked: false` is not `qty: 0`.** A location nobody has walked yet is the most
dangerous kind of containment entry, and it must not read as clear.

---

## Worked example

Abbreviated — one measurement, containment across all five locations, a
recurrence:

```yaml
contract_version: 4
ncr_ref: NCR-2026-0418
site: Fairview
part_number: PN-4471-B
part_number_verbatim: "4471-B Rev 2"
part_revision: "B"
production_wo: WO-88201
production_wo_verbatim: "88201"
lot_number: LOT-77219
lot_number_verbatim: "77219"
operation: "OP30 mill"
found_by: "T. Alvarez, Inspection"
found_at: 2026-09-07T13:40:00-04:00
disposition_pending: true

condition_found: "True position on 4x mounting holes measured 0.0041 in against a 0.002 in maximum."
measurements:
  - { characteristic: "true position", measured: "0.0041", nominal: "0", tolerance: "0.002 max", uom: in, gage: "CMM-01", source_ref: "inspection-20260907.xlsx:r88" }
is_subjective: false
qty_found: 3
qty_found_reason: null
uom: each

requirement_cited:
  source: "customer drawing"
  document: "4471-B-drawing.pdf"
  locator: "p2, datum B, 4x mounting holes"
  characteristic: "true position"
  stated_value: "0.002 in max"
requirement_not_locatable: false

qty_suspect: 480
qty_suspect_is_minimum: false
scope_basis: lot
scope_reasoning: "All 480 parts on WO-88201 were machined from LOT-77219 on one setup with no intervening tool change, so the whole lot is suspect until sampled. The 3 found were a first-article recheck, not a full inspection."
traceability_complete: true

containment:
  - { location: at_customer, qty: 120, uom: each, checked: true, action: "Notify Example Aerospace; request quarantine of PO-4471 receipt.", urgency: immediate, owner: null, customer: "Example Aerospace", source_ref: "netsuite:shipment/SH-30211" }
  - { location: in_transit, qty: 60, uom: each, checked: true, action: "Intercept shipment SH-30244 at carrier.", urgency: immediate, owner: null, customer: "Example Aerospace", source_ref: "netsuite:shipment/SH-30244" }
  - { location: wip_at_machine, qty: 60, uom: each, checked: true, action: "Stop OP40; hold at cell B.", urgency: immediate, owner: null, customer: null, source_ref: "prod-output-20260907.csv:r412" }
  - { location: installed_at_customer, qty: 0, uom: each, checked: false, action: "Ask Example Aerospace whether any of the 120 have been installed.", urgency: immediate, owner: null, customer: "Example Aerospace", source_ref: "not verifiable from our records" }
  - { location: finished_goods, qty: 240, uom: each, checked: true, action: "Move to quarantine cage, tag NCR-2026-0418.", urgency: same_day, owner: null, customer: null, source_ref: "netsuite:inventory/FG-A12" }

recurrence: recurrence_prior_capa_failed
related_records:
  - { ref: NCR-2025-0912, date: 2025-11-04, what_matched: "same characteristic, same operation, same cell", fix_held: false }
prior_ncrs_found: 1
history_searched: true

escape_occurred: true
escape_possible: false
verify_shipment_action: null
escape_detected_at: 2026-09-07T16:20:00-04:00
notification_drafted: true
notification_deadline: 2026-09-09T13:40:00-04:00
affected_customers: ["Example Aerospace"]

approval_state: approved
approved_by: "Priya Raman, Quality Manager"
approved_at: 2026-09-07T16:05:00-04:00
```

Note the last containment entry: `qty: 0` with `checked: false`. Nobody knows
whether parts are installed, and the entry says so rather than being omitted.

---

## Missing behavior for the consumer

| Situation | What `root-cause-capa` does |
|---|---|
| `requirement_cited` null and `requirement_not_locatable` true | **Blocks**, with a pointer back to `ncr-writeup`. Nonconformance is always against a requirement |
| `requirement_cited` null and the flag is false | Blocks. The producer did not follow its own rule |
| `approval_state` is not `approved` | Blocks for anything customer-facing; investigation may proceed as draft |
| `is_subjective` is true | Degrades. Skip computed pattern checks that need a measured characteristic and say why |
| `measurements` empty | Degrades. Reason from the condition as described; no SPC drift check is possible |
| `lot_number` absent | Degrades. Lot-clustering analysis cannot run, so a supplier-caused determination cannot be reached on lot evidence |
| `recurrence` is `no_searchable_history` | Degrades. State that history could not be searched. **Never read as a first occurrence** |
| `traceability_complete` is false | Degrades. Carry the widened scope forward with its reasoning; never re-narrow it |
| `qty_suspect_is_minimum` is true | Degrades. Print the scope as *at least* N everywhere it appears, the 8D and the customer pack included |
| `qty_found` is null | Degrades. Use `qty_found_reason`; never fill in a count |
| `escape_possible` is true | Degrades. Carry the conditional notification and the shipment check forward; no customer-facing pack treats the escape as ruled out |
| `prior_ncrs_found` above zero with `no_searchable_history` | Degrades. Say prior NCRs exist and that whether a fix held cannot be judged |
| A version 3 record lacks the version 4 fields | Degrades. Read `qty_suspect` as possibly a minimum and the escape as not ruled out, and say the record predates those fields |
| A containment entry has `checked: false` | Degrades. Carry it forward as unverified. Never treat as zero |
