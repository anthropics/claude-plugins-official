# Contract: the downtime record

**Emitted by** `breakdown-diagnosis`
**Consumed by** `daily-production-report`, into its downtime log and exceptions
**Chain** 4, breakdown to next report
**Contract version** 3

Rules that govern every contract are in [README.md](README.md).

---

## The requirement this exists to satisfy

Chain 4's build note is unusually direct: `breakdown-diagnosis` must emit a
downtime record **in exactly the shape `daily-production-report` consumes, with
no transformation step in between**, and the schema is to be defined before
either skill is built.

There is a specific reason it has to be exact. `daily-production-report` already
reads downtime events from the MES or historian export. A record arriving from a
diagnosis is a **row in that same log**, not a separate feed. If the two shapes
differ, the report has to reconcile them, and a reconciliation step between two
sources of downtime is precisely how a stoppage gets counted twice or dropped.

**So this contract is the MES downtime export's shape, plus diagnosis fields.**
It is deliberately not a richer object.

---

## Fields

### The stoppage itself — identical to an export row

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `contract_version` | integer | Required | |
| `site` | string | Required | Rule 7 |
| `asset_id` | string, normalized | Required | Paired with verbatim, rule 3 |
| `asset_id_verbatim` | string | Required | As the source wrote it |
| `started_at` | timestamp with zone | Required | Rule 4. No naive timestamps |
| `ended_at` | timestamp with zone or null | Degrades | Null means still down. Not zero duration |
| `duration_minutes` | integer or null | Degrades | Null while `ended_at` is null. Never computed as zero |
| `reason_code` | string | Degrades | The plant's own code. Not remapped to a canonical set |
| `reason_text` | string | Optional | Free text as recorded |
| `production_wo` | string, normalized, or null | Optional | The production work order interrupted, when known. Paired with verbatim, rule 3 |
| `production_wo_verbatim` | string or null | Optional | As the source wrote it. Null whenever `production_wo` is null |
| `shift` | string | Degrades | Resolved against the site's shift pattern and day boundary |
| `production_day` | date | Required | Which day this belongs to, per the cross-midnight rule |
| `source_system` | string | Required | `breakdown_diagnosis` here; `mes_export` or `historian_export` for export rows |
| `source_ref` | string | Required | Rule 6 |

### The diagnosis fields — additive only

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `diagnosis_ref` | string or null | Optional | Pointer to the ranked diagnosis this came from |
| `leading_cause` | string or null | Optional | The top-ranked candidate, as text |
| `leading_cause_confidence` | enum or null | Optional | `high`, `medium`, `low`. Never a bare percentage |
| `cited_work_orders` | list of strings | Optional | Maintenance work orders supporting the leading cause |
| `safety_flagged` | boolean | **Required** | See below |
| `safety_reason` | string or null | Required when `safety_flagged` is set | Which trigger from `../../skills/breakdown-diagnosis/SKILL.md` (*What counts as a safety implication*) applies, with its evidence; or *"none of the safety triggers shown"* when false. |
| `pm_adjustment_proposed` | boolean | Optional | Whether a PM plan change was drafted |
| `maintenance_wo` | string or null | Optional | The maintenance ticket, if one exists. Never named `work_order` |
| `diagnosis_state` | enum | Required | `advisory`, `technician_confirmed`, `superseded` |
| `technician_step` | enum | Required | Chain 4's pause for the technician: `confirmed` (they came back and confirmed or corrected the cause), `pending` (the chain paused and is waiting), `skipped` (no technician step happened: a test, a demo, or a record folded in straight away). |

---

## Three fields that carry real weight

**`safety_flagged` is required and defaults to nothing.** `breakdown-diagnosis`
must surface a safety implication before any diagnosis, and that ordering has to
survive the handoff — a safety-critical stoppage cannot arrive in a production
report as an ordinary line ranked by minutes. The consumer leads with it.

**`duration_minutes` is null while a machine is still down, never zero.** A zero
would rank an ongoing outage last in a log sorted by minutes, which is exactly
backwards. This is `../absent-is-not-zero.md` applied to one field.

**`diagnosis_state` keeps advice labelled as advice.** Chain 4 pauses at a human
working a physical machine and the diagnosis is advisory throughout. A report
that presents an unconfirmed leading cause as the reason for the stoppage is
asserting something no one verified. **`technician_step` says why it is still
advice**: a record folded in with the pause skipped is not the same as one
waiting on a technician, and the report and the dashboard say which.

---

## Reason codes are passed through, not normalized

`reason_code` carries the plant's own code verbatim. Do not remap it to a
canonical vocabulary on the way across.

The consumer has its own job here: when reason codes are inconsistent or heavily
weighted to "Other", **that coverage problem is a finding it reports**, not
something the producer should quietly clean up. Normalizing on emit would destroy
the signal.

---

## Worked example

A four-hour spindle failure, diagnosed, technician not yet finished:

```yaml
contract_version: 3
site: Fairview
asset_id: HAAS-VF4-02
asset_id_verbatim: "Haas VF4 #2"
started_at: 2026-09-08T09:12:00-04:00
ended_at: null
duration_minutes: null
reason_code: MECH-04
reason_text: "Spindle noise then fault code SV-2"
production_wo: WO-88240
production_wo_verbatim: "88240"
shift: "1"
production_day: 2026-09-08
source_system: breakdown_diagnosis
source_ref: "diagnosis/2026-09-08/HAAS-VF4-02"

diagnosis_ref: "diagnosis/2026-09-08/HAAS-VF4-02"
leading_cause: "Spindle bearing failure, accelerated by coupling misalignment"
leading_cause_confidence: medium
cited_work_orders: ["LMB-14022", "LMB-13781"]
safety_flagged: false
safety_reason: "none of the safety triggers shown"
pm_adjustment_proposed: true
maintenance_wo: LMB-14103
diagnosis_state: advisory
technician_step: pending
```

How `daily-production-report` must read it: append as a `downtime_events` row,
lead the exceptions section with it because `ended_at` is null and the machine is
still down, price it as **unpriced so far** rather than zero minutes, and attribute
the leading cause with its confidence and its `advisory` state stated — not as
the established reason.

---

## Missing behavior for the consumer

| Situation | What `daily-production-report` does |
|---|---|
| No downtime records at all | Degrades. Say downtime data was not available. **Never render an empty section**, which reads as no downtime |
| `ended_at` and `duration_minutes` both null | Degrades. List under exceptions as ongoing; exclude from the minutes ranking and say it was excluded |
| `reason_code` absent or "Other" heavy | Degrades. Report the coverage problem as a finding |
| `production_day` absent | Blocks for that row. Without it the row cannot be attributed to a day, and guessing moves output between days |
| `started_at` naive or unresolved | Blocks for that row, per rule 4 |
| `safety_flagged` absent | Blocks. Treat a missing safety flag as unknown and say so, never as false |
| `diagnosis_state` is `advisory` | Degrades. Attribute the cause as proposed, never as established |
| `technician_step` is `skipped` or `pending` | Degrades. Say which beside the cause, in the report and on the dashboard |
| `safety_reason` absent on a version 2 record | Degrades. Show the flag; say no reason was recorded |

## If no CMMS connector is live

Limble is the worked example; it is added through `custom-connector`, not
one of the four supported connectors, so this is the default case.

The contract does not change. `maintenance_wo` and `cited_work_orders` are
populated from exported maintenance history rather than live tickets, and
`pm_adjustment_proposed` may be false because the current PM interval was not
readable.

The one thing that must change is disclosure: the record is still export-sourced
and the consumer's freshness banner names it as such, so nobody reads a nightly
export as this morning's tickets.
