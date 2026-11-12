# Contract: the pulse day record

**Emitted by** `morning-plant-pulse`, step 3
**Consumed by** the Operations Command Center dashboard's trend panel and week-over-week movers, read back by the next pulse run
**Chains** 3 (morning plant pulse)
**Contract version** 1

Rules that govern every contract are in [README.md](README.md). How records
are stored, keyed and read is `../live-dashboard.md`.

---

## Why it exists

The pulse used to compare against "the prior report," a page it had no way to
read back. A scheduled run starts in a fresh session and remembers nothing.
The day record is that history, stored in the dashboard's own database: one
row per site per production day, written by the run that computed it, and
read by every later run to draw the trend.

**The producer writes every field at emit time**, from the report it has just
computed. Nothing on this record is added later by a reader.

---

## Identification

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `contract_version` | integer | Required | |
| `record_key` | string | Required | `<site>_<YYYY-MM-DD>`, e.g. `Fairview_2026-08-31`. The `ArtifactData` document key in `pulse_days`. A re-run for the same day overwrites it |
| `site` | string | Required | Rule 7 |
| `production_day` | date | Required | The production day under the site's day-boundary rule from `## Plant context`, not the calendar day the run happened |
| `day_boundary` | string | Required | The convention used, e.g. "day starts 07:00; third shift belongs to the day it started" |
| `run_timestamp` | timestamp with zone | Required | Rule 4. When this record was computed |
| `data_as_of` | timestamp with zone or null | Required | The newest source refresh the figures rest on. Null only when no source could be read |

## Completeness

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `data_complete` | boolean | Required | True only when the planning, production output and downtime exports each cover the whole production day |
| `gaps` | list of strings | Required | Each missing, stale or partial input, named. Empty list only when `data_complete` is true |
| `backfilled` | boolean | Required | True when written by the first run's back-fill rather than the run for that day |

**A day with `data_complete: false` is a gap in the trend, never a zero.** A
reader that plots it as a low day has turned "we could not see it" into "it
was bad," which is the failure `../absent-is-not-zero.md` exists to stop.

## Output against plan

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `planned_qty` | object, unit → number, or null | Degrades | Rule 5. e.g. `{each: 2030, box12: 520}`. Never summed across units. Null when the planning export is missing |
| `actual_qty` | object, unit → number, or null | Degrades | Good output, same shape. Null when the production export is missing |
| `output_provisional` | boolean | Required | True when any match behind these totals rests on a normalization nobody has approved |

## OEE

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `oee` | number 0–1 or null | Degrades | Site-level for the day |
| `availability` | number or null | Degrades | May exceed 1 on unscheduled overtime. Never clamped |
| `performance` | number or null | Degrades | |
| `quality` | number 0–1 or null | Degrades | |
| `quality_convention` | string | Required | "good ÷ (good + scrap)" or first-pass yield, as the report stated it |
| `oee_basis` | string | Required | How the site figure was rolled up, and which assets were excluded and why |

**Null is not 0, and a missing component is never 1.0.** A component that
could not be computed is null, and so is `oee`. Per
`../../skills/daily-production-report/reference/oee.md`.

## Downtime

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `downtime_by_reason` | list of objects or null | Degrades | Each: `reason_code`, `minutes` (number or null), `events` (integer). Null when the downtime export is missing. Ranked records only |
| `downtime_minutes_total` | number or null | Degrades | Ranked records only. Null when the export is missing |
| `open_outages` | integer | Required | Outages still open at the day's end. Their minutes are null, not 0, and are outside the total |
| `uncoded_share` | object or null | Degrades | `{events, minutes, of_events, of_minutes}` coded `Other` or blank |
| `blocked_safety_unknown` | integer | Required | Diagnosis records held out for a missing `safety_flagged`. Outside every ranking, total and price |

## Losses

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `loss_usd` | object | Required | `{scrap, downtime, currency}`. `downtime` is null when unpriced; `scrap` is null when no standard cost was available |
| `rate_source` | enum | Required | `env_variable`, `profile_confirmed`, `profile_placeholder`, `unset`. Never the rate value itself |
| `unpriced` | list of strings | Required | Each quantity left unpriced and why, e.g. "PN-4402-A scrap, unit conflict each / box12" |

## Exceptions

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `exceptions` | list of objects | Required | Each: `ref`, `kind`, `commitment_impact`. Class 6 records are never here, unless they carry `contradicted_by` in the dataset: then `kind` is `one_sided_contradicted` |
| `data_problems_count` | integer | Required | The numbered data-problems table's count: classes 1–5 and 8 |

---

## Worked example

A complete day, then a day whose downtime export did not land.

```yaml
contract_version: 1
record_key: Fairview_2026-08-30
site: Fairview
production_day: 2026-08-30
day_boundary: "day starts 07:00; third shift (23:00) belongs to the day it started"
run_timestamp: 2026-08-31T04:12:00-04:00
data_as_of: 2026-08-31T03:55:00-04:00
data_complete: true
gaps: []
backfilled: true
planned_qty: { each: 1530, box12: 520 }
actual_qty: { each: 1502, box12: 509 }
output_provisional: true
oee: 0.712
availability: 0.874
performance: 0.833
quality: 0.978
quality_convention: "good ÷ (good + scrap); no rework column"
oee_basis: "time-weighted across 5 assets; DOOSAN-PUMA-03 excluded, no output recorded"
downtime_by_reason:
  - { reason_code: MECH-01, minutes: 51, events: 1 }
  - { reason_code: MECH-03, minutes: 44, events: 1 }
downtime_minutes_total: 95
open_outages: 0
uncoded_share: { events: 0, minutes: 0, of_events: 2, of_minutes: 95 }
blocked_safety_unknown: 0
loss_usd: { scrap: 412.50, downtime: 1187.50, currency: USD }
rate_source: profile_placeholder
unpriced: ["PN-4402-A scrap, unit conflict each / box12"]
exceptions:
  - { ref: WO-88412, kind: late_job, commitment_impact: "Example Hydraulics PO ships 2 days late" }
data_problems_count: 6
---
contract_version: 1
record_key: Fairview_2026-08-31
site: Fairview
production_day: 2026-08-31
day_boundary: "day starts 07:00; third shift (23:00) belongs to the day it started"
run_timestamp: 2026-09-01T04:10:00-04:00
data_as_of: 2026-09-01T03:52:00-04:00
data_complete: false
gaps: ["downtime export did not land; availability, OEE and downtime not computed"]
backfilled: false
planned_qty: { each: 1530, box12: 520 }
actual_qty: { each: 1488, box12: 511 }
output_provisional: true
oee: null
availability: null
performance: null
quality: 0.981
quality_convention: "good ÷ (good + scrap); no rework column"
oee_basis: "not computed: no downtime export, so no availability"
downtime_by_reason: null
downtime_minutes_total: null
open_outages: 0
uncoded_share: null
blocked_safety_unknown: 0
loss_usd: { scrap: 380.00, downtime: null, currency: USD }
rate_source: profile_placeholder
unpriced: ["all downtime: no downtime export", "PN-4402-A scrap, unit conflict each / box12"]
exceptions: []
data_problems_count: 6
```

Note the second record: `downtime_minutes_total: null`, not `0`, and
`oee: null`. The trend shows a gap on 31 August for OEE and downtime, and a
point for quality, which could still be computed.

---

## Missing behavior

| Situation | What the reader does |
|---|---|
| `data_complete` is false | Plot a gap for every null metric on that day. Plot non-null metrics, marked partial. Leave the day out of week-over-week averages and say how many days each average rests on |
| A metric is null | A gap in the chart and a blank in the table, labelled *not computed* with the reason from `gaps`. Never 0, never 1.0 |
| No record for a day in the window | A gap labelled *no run for this day*. Different from a record with `data_complete: false` |
| `planned_qty` or `actual_qty` carries two units | Two series, or one per unit. Never summed |
| `output_provisional` is true | The output point carries the provisional mark, as the day's report did |
| `contract_version` is older | Read the fields it knows; treat the rest as absent, per the README |
| A second record with the same `record_key` | Cannot happen: the write is a `set` by key. If a reader ever sees two, it reports both and uses neither |
