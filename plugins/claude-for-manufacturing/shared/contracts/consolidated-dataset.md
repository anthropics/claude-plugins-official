# Contract: the consolidated dataset

**Emitted by** `data-consolidate`
**Consumed by** every data-dependent skill — as the default source, not the
only one; see *What this dataset is authoritative for* below — and it is the
mapping target for `custom-connector`
**Chain** 1, RFQ to quote (step 2) and 3, Morning plant pulse (step 1)
**Contract version** 6

Rules that govern every contract are in [README.md](README.md).

This file names the tabs
and columns so a consumer and a producer cannot invent two different shapes.

---

## Form

One queryable working file. **Excel workbook, one tab per entity, is the v1
format. The writer is swappable.** The shape below is the contract.

If `data-consolidate` pulled a record type, that type has a tab. A pulled input
with no tab is how inventory went missing the first time this file was written.

---

## Entity tabs

The join hangs off five anchors: part, production work order,
sales order, lot, asset. Every other input is an entity too. It gets its
own tab. It is not folded onto an anchor.

### The five anchors

| Tab | Grain | Key | Fields |
|---|---|---|---|
| `parts` | One row per part | Part number | Description, standard cost, UOM |
| `production_work_orders` | One row per production work order | Production work order number | Part, qty ordered, due date, status, and from version 5 the sales order it is built for (`sales_order` / `sales_order_verbatim`, null where the source holds no link). From version 6, closed-job cost where the ERP holds it: `actual_material_cost`, `actual_labor_cost`, `actual_burden_cost`, `actual_subcontract_cost` (each with `currency`), `qty_completed`, `closed_date`, `revision`, all nullable |
| `sales_orders` | One row per sales order line | Sales order number | Customer, part, qty, promised date, price |
| `lots` | One row per lot or batch | Lot number | The identity stamped on a quantity of material |
| `assets` | One row per machine | Asset ID | Location |

### The other inputs

| Tab | Grain | Joins on | Fields |
|---|---|---|---|
| `inventory` | One row per part per location | Part | On-hand qty, location |
| `purchase_orders` | One row per PO line | Part, supplier ID | Supplier, part, qty, cost, delivery date |
| `production_output` | One row per work order per shift per production day | Production work order, part | Qty good, qty scrap, shift, production day. **Two rows at the same grain are a duplicate key (class 8); the same work order on another shift is not** |
| `downtime_events` | One row per stoppage | Asset | Start, end, reason code |
| `inspection_results` | One row per measurement | Lot or production work order | Measurement vs spec |
| `maintenance_work_orders` | One row per maintenance ticket | Asset | Maintenance work order, dates, close-out notes |
| `plan` | One row per part per date | Part | Planned qty, date |
| `ncrs` | One row per NCR | Production work order, part, lot | NCR ID, found at, description verbatim, status, customer. |

`inventory` is on-hand **by part and location**. A single on-hand total on
`parts` is not this tab. Containment needs the location.

Supplier is a join key, not an anchor. It lives on `purchase_orders`.

**`ncrs` is where an NCR export lands, and the NCR-to-work-order check runs on
it**: the NCR's part against the part the ERP holds for the work order it
cites, and its date against that work order's first recorded output.
`ncr-writeup` and `root-cause-capa` still read the NCR export raw for the
record as written; they read this tab for whether its part label can be
trusted.

### Routings and operation actuals

Two more inputs, for quoting. They are what `quote-build` derives
machine hours from before it ever opens a model, and the order matters: a
current-revision routing or a trustworthy set of actuals makes the design step
a cross-check rather than the basis.

| Tab | Grain | Joins on | Fields |
|---|---|---|---|
| `routings` | One row per part, revision and operation | Part | `part_revision`, `op_seq`, `work_center` / `work_center_verbatim`, `cell`, `setup_hours`, `run_time_per_unit`, `run_time_unit`, `time_unit_flag`, `routing_mismatch` |
| `operation_actuals` | One row per production work order and operation | Production work order, part | `op_seq`, `work_center` / `work_center_verbatim`, `cell`, `actual_setup_hours`, `actual_run_hours`, `qty_completed`, `uom`, `closed_date`, `time_unit_flag`, `actuals_confidence`, `confidence_reason` |

Column behavior on both tabs:

| Column | Type | Behavior | Notes |
|---|---|---|---|
| `part_revision` | string or null | Degrades on `routings` | The revision the routing was written for. **Null is not "current"**: a routing with no revision is reported as revision-unknown, never assumed to match the drawing |
| `op_seq` | integer | Required | As the source numbers it |
| `work_center` / `work_center_verbatim` | string | Required | A pair, like a join key, though it is not one of the six |
| `cell` | string or null | Degrades | From the machine class to work center map in the Plant context. Null when there is no map, and the report says so |
| `setup_hours`, `run_time_per_unit` | number | Required | As the source states them. **Never converted** |
| `run_time_unit` | enum | Required | `min`, `h`, or `undeclared`. Read from the header or a unit column, never inferred from the size of the number |
| `time_unit_flag` | string or null | Degrades | Set when a unit is undeclared, or when this tab's unit differs from the other tab's for the same part and operation. Names both units. No conversion is computed |
| `routing_mismatch` | enum or null | Degrades | `no_matching_part` (the routing's part is not in the item master — mismatch class 1) or `revision_mismatch` (the routing is for a revision other than the one being quoted or held as current — class 4, with no automatic fix). Null when neither |
| `actual_setup_hours`, `actual_run_hours` | number or null | Degrades | Null where the source lumps setup and run into one figure; then `confidence_reason` says the split is unknown |
| `qty_completed` | number | Required | With `uom` |
| `closed_date` | date | Required | The work order's close. Rule 4 applies to `as_of`; a date-only close is fine here |
| `actuals_confidence` | enum | Required | `recorded` or `probable_standard`. See below |
| `confidence_reason` | string or null | Required when `probable_standard` | The arithmetic that set it: which work orders, which figures, how far apart |

**`probable_standard` is the backflush check.** Many ERPs close an operation by
posting its standard rather than the time it took. Two tests, either sets the
flag, both run in code:

1. Actual run hours ÷ quantity matches the routing's run standard for that part
   and operation within 1%, after both are in the same unit — a unit
   conversion done for this comparison only, shown, and never written back to
   either tab.
2. Two or more work orders for the same part and operation agree on run hours
   per unit within about 1%. Real shop time is not that tidy.

Actuals flagged `probable_standard` stay on the tab and are shown. They are
**never ranked above a geometry-derived estimate** by `quote-build`, because
they may be the routing wearing a work order number.

**No routing data is a named gap.** Where no routing source exists, the
`routings` tab is absent and the report names it missing. An empty `routings`
tab would read as "this part has no operations," which is false.

---

## What this dataset is authoritative for

Every data-dependent skill reads this dataset rather than the raw sources, and
three skills also read a raw export. Both halves are deliberate. Here is how
they fit together.

**This dataset is authoritative for the join.** It is the only place the sources
are matched on the six keys, normalized through the documented ladder, and their
failures classified into the eight mismatch classes. Any question shaped *which
records go together* — which parts came off which work order, where the suspect
quantity physically sits, what a lot traces to — is answered here and nowhere
else. Going back to a raw export for that reproduces the join by hand, which is
precisely the manual work this skill exists to end.

**It is not authoritative for two things:**

| What | Why not | Who reads raw |
|---|---|---|
| **A high-frequency sensor trace** | There is no sensor tab, and there should not be. A spindle-load curve at sub-second resolution is not an entity keyed on an anchor; folding it in would produce a workbook nobody can open | `root-cause-capa` — historian export |
| **A value as recorded, rather than as normalized** | The ladder rewrites keys, and a joined view may have moved a row into a mismatch class. A computed control chart needs the measurement the way the gage wrote it | `root-cause-capa`, `ncr-writeup` — quality export |

`daily-production-report` is the third, and it is a different case: it reads the
dataset as its **primary** input, and the plan, output and
downtime exports alongside it. That is not a second opinion — the dataset gives
it the freshness picture and the classified mismatches, and the exports give it
rows at their native grain.

## When a skill reads both, the dataset wins on identity

This is the rule that matters operationally, because reading two sources is how
one report ends up carrying two different numbers for the same thing.

**On identity — which part, which work order, which lot, which asset — the
dataset wins.** Its keys are normalized and its mismatches are classified. A raw
export's key is unnormalized by definition, so preferring it silently
reintroduces the drift `data-consolidate` just resolved.

**On the measured value — the sensor reading, the inspection measurement — the
raw export wins**, because that is the value as recorded and it is why the skill
went there.

**Where the two disagree on a count, say so rather than choosing.** A discrepancy
between the joined view and the raw rows is a finding about the export, not a
number to pick between. Report both, name which is which, and let the plant tell
you which system is right. Per `../absent-is-not-zero.md`, quietly resolving it
is the failure mode — a supervisor reading one number never learns there were
two.

**Always name which source a number came from.** Every tab already carries
`source_system` and `source_ref` for exactly this. A figure read from a raw
export carries the file and row the same way.

---

## Columns every row carries

These appear on every entity tab.

| Column | Type | Behavior | Notes |
|---|---|---|---|
| `site` | string | Required | Rule 7 |
| `source_system` | string | Required | `netsuite`, `infor_m3`, `cmms` (any CMMS connector; `limble` accepted from earlier versions), `mes_export`, `historian_export`, `qms_export`, `planning_export`, `manual` |
| `source_ref` | string | Required | File and row, or connector record ID. Rule 6 |
| `as_of` | timestamp with zone | Required | When the source recorded it, not when we read it. Rule 4 |
| `join_status` | enum | Required | `matched`, `unmatched`, `normalized`, `duplicate`, `proposed_normalization`. The last is a row that matches only once a proposed fix (classes 2 to 5) is approved. It becomes `normalized` on a yes and is **not joined until then** |
| `mismatch_class` | integer or null | Degrades | 1–8 per `../../skills/data-consolidate/reference/mismatch-classes.md`, null when matched |
| `contradicted_by` | string or null | Degrades | On a class 6 row only: the source and record that show the missing activity happened (`quality_ncrs.csv NCR-2026-0141`). Null otherwise. |
| `integrity_flags` | list or null | Degrades | Named failures of the integrity checks in `../../skills/data-consolidate/reference/join-keys.md`: `sign_convention`, `mixed_sign`, `end_before_start`, `duration_mismatch`, `ncr_part_differs`, `ncr_dated_before_wo`, `future_timestamp`, `units_conflict`. Null when none. |

## Join-key columns

Every join key is a pair, per rule 3.

| Column | Type | Behavior |
|---|---|---|
| `part_number` / `part_number_verbatim` | string | Required on any tab keyed by part, including `inventory` |
| `part_revision` | string or null | Degrades. Preserved when ladder rung 5 strips it |
| `production_wo` / `production_wo_verbatim` | string | Required on production tabs |
| `sales_order` / `sales_order_verbatim` | string | Required on sales tabs |
| `lot_number` / `lot_number_verbatim` | string | Required on lot and inspection tabs |
| `asset_id` / `asset_id_verbatim` | string | Required on asset, downtime and maintenance tabs |
| `supplier_id` / `supplier_id_verbatim` | string | Required on `purchase_orders` |
| `maintenance_wo` | string | Required on `maintenance_work_orders`. Never named `work_order` |

## Quantity columns

Per rule 5: flag differing UOMs, do not silently sum.

| Column | Type | Behavior |
|---|---|---|
| `qty` | number | Required where a quantity is reported. On `sales_orders` and fulfilment rows a positive quantity: a source that signs those lines negative is read as the absolute value, flagged `sign_convention` |
| `qty_verbatim` | number or null | Degrades. The quantity as the source signed it, where `sign_convention` changed it |
| `uom` | string | Required alongside any `qty`. Never inferred |
| `amount` | number | Degrades. Standard cost, PO cost, sales price |
| `currency` | ISO 4217 code | Required alongside any `amount` |

On `production_output` the quantities are `qty_good` and `qty_scrap`, each
paired with `uom`. On `inventory` the quantity is on-hand at that location.

---

## Worked example

An `inventory` row and three `production_output` rows. The inventory row is
the one this version exists to make explicit.

```
# inventory
site,source_system,source_ref,as_of,join_status,mismatch_class,
part_number,part_number_verbatim,location,qty,uom

Fairview,netsuite,inventory/FG-A12,2026-09-08T06:10:00-04:00,matched,,
PN-4471-B,PN-4471-B,FG-A12,240,each

Fairview,netsuite,inventory/WIP-CELL-B,2026-09-08T06:10:00-04:00,matched,,
PN-4471-B,PN-4471-B,WIP-CELL-B,60,each

# production_output
site,source_system,source_ref,as_of,join_status,mismatch_class,
production_wo,production_wo_verbatim,part_number,part_number_verbatim,
part_revision,qty_good,qty_scrap,uom,shift

Fairview,mes_export,prod-output-20260907.csv:412,2026-09-07T14:22:00-04:00,
matched,,WO-88201,WO-88201,PN-4471-B,PN-4471-B,,486,14,each,2

Fairview,mes_export,prod-output-20260907.csv:413,2026-09-07T15:03:00-04:00,
normalized,2,WO-88202,wo 88202,PN-4471-B,4471B,,240,0,each,2

Fairview,mes_export,prod-output-20260901.csv:88,2026-09-01T09:10:00-04:00,
unmatched,7,WO-88231,WO-88231,PN-4402-A,PN-4402-A,,120,3,each,1
```

Reading those:

- 240 of PN-4471-B sit in finished goods. 60 are still at cell B. Same part,
  two locations, two rows. That is what containment reads.
- Production row 1 matched cleanly.
- Production row 2 matched after ladder rungs 1–3. The verbatim columns keep
  what the MES wrote.
- Production row 3 is class 7, a date-window mismatch. **Not an orphan.**

### Version 4: a routing and two actuals

```
# routings
site,source_system,source_ref,as_of,join_status,mismatch_class,
part_number,part_number_verbatim,part_revision,op_seq,work_center,
work_center_verbatim,cell,setup_hours,run_time_per_unit,run_time_unit,
time_unit_flag,routing_mismatch

Fairview,manual,erp_routings.csv:3,2025-11-12T00:00:00-05:00,matched,4,
PN-4471-B,PN-4471-B,1,20,HAAS-VF4-02,HAAS-VF4-02,CELL-B,1.25,7.00,min,
"routing in min, actuals in h - not converted",revision_mismatch

# operation_actuals
site,source_system,source_ref,as_of,join_status,mismatch_class,
production_wo,production_wo_verbatim,part_number,part_number_verbatim,
op_seq,work_center,work_center_verbatim,cell,actual_setup_hours,
actual_run_hours,qty_completed,uom,closed_date,time_unit_flag,
actuals_confidence,confidence_reason

Fairview,manual,erp_operation_actuals.csv:2,2026-03-18T00:00:00-04:00,matched,,
WO-87412,WO-87412,PN-4471-B,PN-4471-B,20,HAAS-VF4-02,HAAS-VF4-02,CELL-B,
1.30,23.33,200,each,2026-03-18,"routing in min, actuals in h - not converted",
probable_standard,"0.1167 h/pc here vs 0.1173 h/pc on WO-87655 (0.6% apart); 7.00 min routing standard = 0.1167 h/pc (0.0% apart)"
```

- The routing is for revision 1. Quoted against revision 2, it is
  `revision_mismatch`: shown as superseded, never priced from.
- The two units are named on both rows and neither is rewritten. The backflush
  check converted them for its own comparison and printed that it did.
- Both tests fired on WO-87412, so it is `probable_standard`. It is still on
  the tab, and still shown.

---

## Missing behavior for the consumer

| Situation | What the consumer does |
|---|---|
| A tab is absent entirely | Degrades. Report on what exists, name the missing entity, never treat it as empty |
| `inventory` is absent | Degrades. `ncr-writeup` cannot place parts from the dataset. Ask location by location, or read the ERP (NetSuite or Infor M3) / an inventory export, and record each answer as unverified until confirmed. Never treat absence as zero on hand |
| A row's `uom` is absent | Degrades. Report the quantity, refuse to aggregate it, say why |
| `join_status` is `duplicate` | Blocks for any total including that key. Surface both rows |
| `join_status` is `proposed_normalization` | Degrades. **Not joined.** No total treats the row as matched; any figure that would use it is shown provisional, with both spellings and the fix awaiting a yes |
| `contradicted_by` is set | Degrades. The record is an exception, *one-sided, contradicted by* the named record. Never "Checked, nothing wrong" |
| `integrity_flags` holds `end_before_start` or `duration_mismatch` | Degrades. The row's minutes are held out of every minutes total and the minutes ranking; it still counts as an event. The exclusion is stated with the row |
| `integrity_flags` holds `mixed_sign` | Blocks any total of that record type's quantities |
| `integrity_flags` holds `ncr_part_differs` or `ncr_dated_before_wo` | Degrades. The NCR's part label or date is not used for same-part history or to date a defect. Show both values |
| `integrity_flags` holds `future_timestamp` | Degrades. The source's `as_of` is untrusted; no age or "data as of" is stated from it |
| A `production_work_orders` actual-cost column is null | Degrades. That cost is not on file for that work order. `quote-build` uses the next rung for that line and says so; a null is never read as zero cost |
| `production_work_orders.sales_order` is null | Degrades. Commitment impact for that work order is "not traceable: the source holds no work order to sales order link", never guessed from part and customer |
| `join_status` is `unmatched` and `mismatch_class` is 1 | Degrades, and the orphan is named in the consumer's output |
| `as_of` cannot be resolved to a zone | Degrades. The row is usable for counting and not for correlating |
| `routings` is absent | Degrades. `quote-build` starts its hours ladder at closed-job actuals, or below. Name the tab missing, never treat it as no operations |
| `operation_actuals` is absent | Degrades. The ladder has no rung 2. Name the tab missing |
| `run_time_unit` is `undeclared`, or `time_unit_flag` is set | Degrades. The value is reported in its source unit and not used for any comparison or hours figure until the plant says what the unit is |
| `routing_mismatch` is `revision_mismatch` | Degrades. The routing is not a basis for the revision being quoted. It may be shown as superseded, never priced from |
| `actuals_confidence` is `probable_standard` | Degrades. Shown, never ranked above a geometry-derived estimate |
| `actual_setup_hours` is null | Degrades. The setup and run split is unknown for that work order; it is never re-amortized as if it were known |

---


## When a new system is mapped in

`custom-connector` maps onto this schema. Three requirements:

1. **Every mapped row carries the columns every row carries**, including
   `source_system` and `source_ref`.
2. **Keys map to the pair, not the single.** The new system's own identifier
   goes in the verbatim column; the normalized form comes from the ladder.
3. **A field with no home here does not go in.** Either the schema gains the
   field with a version bump, or the field stays out.
