# The compute engine: what it writes and how to read it

Loaded before building the page. The engine is `../scripts/pulse_compute.py`,
standard-library Python, run once per pulse. It reads the export folder
(CSV, or XLSX one table per sheet), recognises each file by its header, and
computes every figure the Operations page prints. The page code selects and
formats; it does no arithmetic.

```
python3 -I ../scripts/pulse_compute.py --exports exports --out pulse-output \
  [--day 2026-08-31] [--profile <profile_path>] [--rates <rates_path>] [--diagnoses exports/diagnoses] \
  [--manifest columns.json] [--run-time 2026-09-01T04:10:00-04:00] [--tz America/New_York]
```

- `--day` is the production day asked for. Without it the engine takes the
  `Production day` the plant context names, else the latest day the plan,
  output and downtime exports all cover, and says which.
- `--profile` is any file holding the `## Plant context` block: `profile_path`
  from `plant_setup.py find`, or for an older profile, the memory
  file or a `plant-context.md` in the drop. Without one, the time zone and the
  day start are assumed and listed in `context.assumptions`.
- `--rates` is the `## Plant rates` file at `rates_path`; its downtime cost per
  hour wins over a value left in an older profile.
- Breakdown-diagnosis records (YAML or JSON) are read from
  `exports/diagnoses/` unless `--diagnoses` names another folder.
- `--manifest` is only for a plant whose headers the engine does not
  recognise: `{"roles": {"<file>": "output"}, "columns": {"output": {"qty_good": "<header>"}}}`.
  A file it cannot place is listed in `context.files_not_used` with the reason.

It prints a short summary, and exits 2 with the failed checks listed when a
subtotal does not reconcile. On exit 2 nothing it wrote is used.

---

## `figures.csv` — the figures block

One row per number: `id, figure, value, unit, period, source, filter`. A
value that could not be computed reads `not computable`, never 0. The page's
figures block is this file; the prose and every table quote it. A number on
the page with no row here is a defect.

## `pulse_model.json` — what the page is built from

| Key | Holds | Page rule it carries |
|---|---|---|
| `context` | Site, time zone and whether it was assumed, day start and the day-boundary rule, run time, `assumptions`, files used and not used, `part_reference`, `unit_reference` | Every assumption goes in the freshness banner or the run notes, in its own words |
| `freshness` | Production day and how it was chosen, newest day and its age, `data_as_of`, `data_complete`, `gaps`, per-source `coverage` (first, last, rows, `landed`), `activity_window`, `future_timestamps` | A gap is the banner's first row. A day whose MES output has fewer shifts than most days is a gap too (*only the 07:00 shift for …*): not a complete plant day. `future_timestamps` makes that source's dates untrusted |
| `normalizations` | Each spelling matched by a rung: verbatim, canonical, rule, class, rows, `status` | `approved` rules are used as they stand and never re-proposed. Everything else is *proposed, awaiting approval*, and its rows are provisional |
| `today` | The production day: `parts` (plan, good, variance, status, both spellings, held-out rows), `oee_by_asset` with `why_not`, site `availability` / `performance` / `quality` / `oee`, `quality_convention`, `scrap` by part, `scrap_priced_usd`, `downtime_usd`, `rate_source`, `unpriced`, `stops` | A part's `status` is the label: `comparable`, `not comparable, unit conflict` (no variance), `held out` (plan *not counted*, good *held out*), `no output recorded`. A null component is *not computable* with its `why_not`, never 1.0 |
| `periods` | `day`, `week` (Mon–Sun to date) and `month` (1st to the day) roll-ups: per-part totals, days under plan, scrap and priced scrap, held-out rows | A day whose output for a part is an unresolved duplicate is out of that part's period totals |
| `downtime` | `day`, `week`, `month` and `window` rankings: `by_asset` and `by_code`, each with events, minutes, ongoing, held out, `rank_minutes`, `rank_events` (1, 2, 2, 4); `held_out` rows; uncoded events and minutes | Both rankings, always. `by_code` never holds `Other` or blank: state `uncoded_events` of `events` as its own finding first. An ongoing stop counts as an event with no minutes |
| `data_problems` | `numbered` (classes 1–5 and 8, class 6 contradicted, and unit conflicts, each with `n`), `count`, `waiting_on_decision` (unit conflicts, normalizations awaiting approval, provisional row count, NCR keys that disagree with the ERP), `class7`, `checked_nothing_wrong`, `integrity` | The numbered table is `numbered` and its count is `count`. `checked_nothing_wrong` is a separate block, never numbered, never counted |
| `exceptions` | `items` (late job, machine down, quality hold, one-sided contradicted), `late_jobs`, `late_undeterminable`, `so_link`, `maintenance_history` per asset | A null `commitment_impact` is yours to trace through `sales_order`; with `so_link` false say *"commitment impact not traceable: no work order to sales order link in the ERP"* once, with the count |
| `diagnoses` | `safety_flagged` records (lead the page), `blocked_safety_unknown` (first list, outside every figure), `matched_to_mes_row` (records matched to an MES downtime row on asset plus start time, each with `matched_mes_row`; the stoppage is counted once), `assets_with_diagnosis` (assets with a record whose safety status is known; a blocked record does not count) | A record with the flag true or false is already in the rankings, as its own row or on the MES row it matched; a blocked one is in none |
| `week_over_week` | This week and last, from the exports, with the days each rests on; `skip` when last week has no data | Labelled *from this run's exports, not stored history* unless stored records were read |
| `checks` | How many self-checks ran, and any that failed | |

## `periods.json` and `figures-short-page.csv`

Written for the short Operations page (`short-page.md`), and read by
`../scripts/render_short.py`, not by you. `periods.json` holds a Day, Week
(Monday to Sunday) and Month-to-date roll-up for every production day, with
its partial marking; `figures-short-page.csv` holds every value in them. The
full page does not need either file; do not read them into the reply.

## `day_records.json`

One record per production day the exports cover, every field of
`../../../shared/contracts/pulse-day-record.md`, keyed `<site>_<YYYY-MM-DD>`.
The day asked for has `backfilled: false`; the rest are the first-run
back-fill. Store them as they are. In the reply, give the day's record one
line (key, `data_complete`, the gap, stored or not); on the page, and in a
reply that prints the page in full, show it as
the field and value table `../../../shared/replies.md` asks for, plain values
(`data_complete | false`), never as a YAML or JSON block. Until a `set` has
returned in this run, a record is *computed, not stored*: never write that a
day "is stored" or "was saved" on a run that could not publish. Add commitment impact to the day's
`exceptions` where you traced it; change nothing else.
