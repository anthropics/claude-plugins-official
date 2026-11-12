# Join keys and the normalization ladder

Load this before joining anything.

## Why this file exists

A plant does not have one database. It has five to eight systems bought at
different times by different departments, and the same physical thing carries a
different identifier in each one. A single part might be:

| Where | How it appears |
|---|---|
| ERP item master | `PN-4471-B` |
| MES production export | `4471B` |
| Quality inspection export | `4471-B Rev 2` |
| Maintenance spares list | `Bracket, Upper, 4471` |

All four are the same part. Only the first three are joinable, and none of them
match as-is.

## The six join keys

These are the identifiers that should be common across systems. Everything the
consolidated dataset is built around hangs off one of them.

| Join key | Links | Source of truth |
|---|---|---|
| Part number | Product ↔ production ↔ quality ↔ purchasing | ERP item master (NetSuite or Infor M3) |
| Production work order number | Production run ↔ output ↔ quality results ↔ cost | The ERP. In Infor M3 it is the manufacturing order number |
| Sales order number | Customer commitment ↔ production ↔ shipping | The ERP. In Infor M3 it is the customer order number |
| Lot / batch number | Material ↔ parts made from it ↔ customers who received them | MES or quality export |
| Asset ID | Machine ↔ downtime ↔ maintenance history | CMMS connector or maintenance export |
| Supplier ID / vendor number | Purchase orders ↔ incoming material ↔ supplier quality | The ERP |

**Source of truth decides direction.** When two sides disagree on a key's shape,
normalize toward the source of truth rather than toward whichever side has more
rows. The ERP item master is the reference for part numbers even when the MES
export has ten times the volume.

### The work order name collision

Maintenance systems also call their repair tickets "work orders." A production
work order and a maintenance work order are different records with different
numbering, and joining one to the other produces nonsense.

Always disambiguate in output and in column naming: **production work order** and
**maintenance work order**, never bare "work order" or "WO."

## The normalization ladder

Apply in this order. Each rung is more aggressive than the last, so stopping
early is safer than going further than needed.

| Rung | Transformation | Notes |
|---|---|---|
| 1 | Trim leading and trailing whitespace | Manual exports carry trailing spaces constantly |
| 2 | Normalize case | Fold to a single case for comparison only |
| 3 | Normalize punctuation | `PN-4471-B` / `PN_4471_B` / `PN4471B` collapse to one comparison form. A lost part prefix (`4471B` against `PN-4471-B`) collapses too, **only where exactly one part on the `parts` tab matches once its prefix is dropped**. Name the prefix in the log. Where two or more parts would match (`PN-4471-B` and `AX-4471-B`), nothing is matched by this rung: the record is reported with every candidate, and the plant says which |
| 4 | Restore lost leading zeros | `451` matches `00451` only if a zero-padded variant exists on the other side. Test for it; do not pad blindly |
| 5 | Strip revision suffix | `4471-B` matches `4471-B Rev 2`. The revision is extra information, not a different part |

**Rungs 1, 2 and 3 are safe to propose as automatic.** Rungs 4 and 5 change
meaning and always carry their own proposal, because a stripped revision or an
assumed zero can be wrong.

### Two hard rules

**Compare on the normalized form; store and display the original.** The
consolidated dataset carries the source system's own identifier verbatim
alongside the normalized key. A plant person searching for `PN-4471-B` in their
own vocabulary must find it. Never overwrite a source identifier with a
normalized one.

**Every normalization applied is logged and reportable.** The data quality report
names each rule that fired, how many records it touched, and an example of the
before and after. A silent normalization is indistinguishable from a bug, and the
first time a total looks wrong this log is the only way to tell them apart.

### Revision data is preserved, never discarded

When rung 5 fires, the revision that was stripped goes into its own column and
the report states that revision data existed on one side only. Stripping it to
make the join work is correct; losing it is not.

## Date windows by entity

When the user narrows the join to the overlap, the window does not apply to
every tab alike. Three kinds of record, three rules:

| Kind | Tabs | What the window does |
|---|---|---|
| **Activity** | `production_output`, `downtime_events`, `inspection_results`, `plan`, `operation_actuals` | Scoped to the overlap. A row outside it is Class 7 |
| **Open commitments** | Open `sales_orders` lines, open `production_work_orders` | **Kept by status, whatever their dates.** An open order is in scope until it closes. A sales order line that carries only a promised date and no order date is never out of window for lacking one |
| **Reference history** | `purchase_orders` and their receipts, `maintenance_work_orders`, `ncrs`, `lots` | Kept for a lookback before the window start: the Plant context's lookback if one is set, otherwise **180 days, stated as a default, not plant-set**. Labelled as history in the report and never counted in the window's totals |

Closed commitments (a shipped sales order, a closed work order) are activity:
scoped by their own close or ship date. Never class a record 7 because the
narrowing removed the history that explains it. A material receipt from
before the window is how a heat is traced to the work orders it fed, and a
repair from June is how a breakdown is read in August.

## Integrity checks

Run in code, on every row, after the join. A failure is a named value in the
row's `integrity_flags`, per `../../../shared/contracts/consolidated-dataset.md`.
None is a mismatch class, none is fixed silently, and each is counted in the
figures block and reported with example rows.

| Flag | Tab | Test | What happens |
|---|---|---|---|
| `sign_convention` | `sales_orders`, fulfilment rows | Every line of that record type from that source is negative. NetSuite writes sales order and item fulfilment line quantities as negative: stock leaving. Infor M3 writes them positive, so M3 rows never raise it | `qty` is the absolute value; the signed value stays in `qty_verbatim`; the rule is stated in the figures block, once per source. A demand total is never negative |
| `mixed_sign` | the same | Some lines of that record type are negative and some positive | No sign is changed and no total is computed for that record type until the plant says what the signs mean |
| `end_before_start` | `downtime_events` | `ended_at` is earlier than `started_at` | The stated duration is not trusted: the row's minutes are held out of every minutes total and the minutes ranking, the stoppage still counts as an event, and the exclusion is stated with the row |
| `duration_mismatch` | `downtime_events` | Stated duration differs from end minus start by more than a minute | Both figures shown. Minutes held out as above, until the plant says which is right |
| `ncr_part_differs` | `ncrs` | The NCR's part is not the part the ERP holds for the production work order it cites | The NCR's part label is not trusted for same-part history. Show both parts |
| `ncr_dated_before_wo` | `ncrs` | The NCR is dated before the first output recorded for the work order it cites | Show both dates. The NCR is not used to date the defect |
| `future_timestamp` | any | A created, last-modified or transaction date after the run time | The source's `as_of` is untrusted (`data-consolidate` Step 2). Due, promised and delivery dates are excluded from this test |
| `units_conflict` | any | Two units for one key, as in Step 5 | No total across them, no conversion |

A row can carry more than one flag.

## Plant vocabulary

`onboarding` captures what this plant calls its join keys and its organizational
units — job versus work order versus traveler, cell versus line versus work
center. Every output uses the plant's words, not these canonical ones.

Read the plant's words from the `## Plant context` block's `Vocabulary` line for
the relevant site. If no profile exists, use these canonical names, say that they
are canonical rather than the plant's own, and ask once per session rather than
re-asking per output.

## Routings and operation actuals

Two inputs `quote-build` derives machine hours from. Neither is keyed on a
seventh identifier: a routing joins on part, an actuals row on production work
order and part. Work center is carried as a pair like a key, but it is mapped,
not joined.

### Recognizing the files

By header signature, case-insensitive, punctuation folded the way rung 3 folds
a key. Column names vary by ERP; the meaning does not.

| File | Must carry | Usually also carries |
|---|---|---|
| Routing | a part number; an operation sequence (`op_seq`, `operation`, `oper no`); a work center or resource; a setup time; a run time per unit | revision, operation description, a time unit column, an as-of or effective date, an outside-processing flag |
| Operation actuals | a production work order; an operation sequence; a work center; hours booked (setup and run, or one lumped figure); a quantity completed | part number, closed date, unit of measure |

A file carrying a work order and hours but no operation sequence is a work
order cost file, not operation actuals. Name it as such and do not load it into
`operation_actuals`.

### Time units

Read the unit from the header (`setup_hours`, `run_min_per_unit`) or from a
unit column. **Never from the size of the number** — 0.12 is a plausible run
time in hours and in minutes. Where no unit is declared, the unit is
`undeclared` and the row is flagged.

Where the routing and the actuals for the same part and operation carry
different units, flag both rows naming both units. The dataset holds each value
as its source wrote it. Minutes to hours is an exact factor, and it is still
not applied to the dataset: the flag is there so a person sees two units, and a
silently harmonized column hides that the sources disagreed.

### Work center to cell

Read the `Machine classes` table under `### Machining data` in the
`## Plant context` block. Its `Work centers` column lists the work centers in
each machine class, and `Cell` names the cell. Fill `cell` on both tabs from
it. A work center in no row is listed in the report with `cell` null. Without
the table at all, every `cell` is null and the report says the map is missing
from the Plant context, once.

### The backflush check

Run in code, over every actuals row, after the join:

1. **Against the routing.** Put actual run hours ÷ quantity completed and the
   routing's run standard in the same unit for this comparison only. Within 1%
   of each other: `probable_standard`.
2. **Against each other.** For each part and operation with two or more closed
   work orders, compare run hours per unit. Two or more within about 1% of each
   other: every one of them is `probable_standard`.

`confidence_reason` carries the figures — which work orders, the per-unit
values, the percentage apart. Everything else is `recorded`. A lumped figure
with no setup and run split cannot be checked against a run standard; say so
in `confidence_reason` and leave it `recorded`.

**Probable, not proven.** The flag says the numbers look posted rather than
measured. The plant may know otherwise, and the report says what would settle
it: the operation's labor tickets, or the ERP's backflush setting for that
work center.
