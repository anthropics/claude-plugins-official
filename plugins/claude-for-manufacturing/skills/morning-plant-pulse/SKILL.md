---
name: morning-plant-pulse
description: "Runs the overnight chain that has the morning production report waiting before anyone asks for it: joins last night's planning, production and maintenance exports, flags the mismatched keys, then computes output against plan, OEE with its three components, downtime ranked two ways, priced losses and the exceptions needing a decision. Stores a record per production day and keeps one Operations Command Center dashboard per site up to date, with a 14 and 30 day trend. Safe to run unattended. Use when someone says \"run the morning pulse,\" \"do the overnight report,\" \"morning plant pulse,\" \"update the operations dashboard,\" or schedules the daily production run."
compatibility: "Requires none. Chains data-consolidate and daily-production-report, then publishes the site's Operations Command Center dashboard to the Claude artifact store where the artifact tools exist, else offers the page in the conversation. Reads M365 exports, NetSuite or Infor M3, and a CMMS connector where connected; runs on the export folder alone. Writes to no system of record, so it is safe to schedule. Asks nothing, is idempotent, reports its own gaps."
---

# Morning Plant Pulse

Chain 3. `data-consolidate` → `daily-production-report` → publish.

**The only scheduled chain, and the only one with no approval gate.** Those two
facts are the same fact: it reads, it produces a page, and it writes to no
system of record. The dashboard it publishes lives in the user's own Claude
artifact store, which is not a system of record either. That is precisely why
it is safe to run unattended, and why no other chain in this build should ever
be scheduled.

The page is rebuilt overnight so it exists before the morning meeting. A
supervisor otherwise spends sixty to ninety minutes assembling it by hand out
of the same four or five exports. **The first run creates one dashboard per
site; every later run updates that same dashboard**, so nobody has to save
over yesterday's page.

**Quick start**

```
→ Join last night's exports; flag mismatched keys by class
→ Compute output vs plan, OEE with its three components shown separately
→ Downtime ranked BOTH ways: by minutes and by frequency
→ Price the losses. Week-over-week movers come from the stored day records
→ Write the day record, keyed <site>_<YYYY-MM-DD>. Missing export? data_complete: false
→ Find the dashboard: stored URL, then exact title. Neither? Create it
→ Say "updated" ONLY when the publish returned a URL in this run
→ Can't publish? Page saved to pulse-output/ + "the dashboard was not updated"
→ Reply: ~150-word summary naming the page; full page in the reply only if nothing could be written
→ Export did not land? STILL RUN. Gap at the top, gap in the trend, never a zero
→ Ask nothing. There is nobody there at 4am
→ Idempotent: a re-run overwrites that day's record on the same dashboard
```

---

## Inputs

**First, find the plant setup:** from the task's own folder (never `cd` into the plugin), run
`python3 -I <this skill's folder>/../../shared/scripts/plant_setup.py find`, do its `setup_page_first` step, then read the profile at
`profile_path` and any rate at `rates_path`, per `../../shared/replies.md`.

| Input | Source | Form |
|---|---|---|
| Planning, production and maintenance exports | The M365 export folder | CSV/XLSX |
| Standard cost, open work orders | The ERP (NetSuite or Infor M3) | Connector |
| Maintenance work orders in progress | CMMS | CMMS connector, else the maintenance export |
| Stored day records, for the trend and week-over-week | The dashboard's own `pulse_days` collection | `ArtifactData` `query`, per `../../shared/contracts/pulse-day-record.md` |
| The dashboard's URL | The `## Dashboards` line on the Open work page, then an exact-title lookup | Open work page, `Artifact` `list` |
| Source clocks, shift pattern, day boundary | `## Plant context` | Config |

---

## The three steps

**First, run the compute engine.** Steps 1 and 2 are done in code that ships
with this skill, so every run computes the same numbers the same way:

```
python3 -I <this skill's folder>/scripts/pulse_compute.py --exports <export folder> \
  --out pulse-output [--day YYYY-MM-DD] [--profile <profile_path>] [--rates <rates_path>]
```

It applies the ladder, the eight classes and the integrity flags of
`data-consolidate`, and the OEE, ranking, pricing and exception rules of
`daily-production-report`, and writes `figures.csv` (the figures block, one row
per number with its filter), `pulse_model.json` (everything the page shows,
already computed) and `day_records.json` (one day record per covered day).
**Build the page from `pulse_model.json` and quote `figures.csv`. Never
recompute, retype or round a number it holds.** The judgment stays yours: the
wording, which exceptions are significant, the reschedule move, the publish.
What each key holds is `reference/compute-engine.md`. **If the engine cannot
run** (no code execution) **or exits non-zero**, do steps 1 and 2 as written
below and say which happened; never mix the two.

**1. Join the exports** through `data-consolidate`, on the records the plant
already has, with mismatched keys flagged by class.

**2. Compute the report** through `daily-production-report`: output against
plan, equipment losses ranked by minutes and by frequency, priced in dollars,
and the exceptions that need a decision today. **Week-over-week movers come
from the stored day records**, read at the start of step 3 before the page is
built, never from a prior page. The pulse hands that history to step 6 of
`daily-production-report`.

**3. Publish the dashboard.** Per `../../shared/live-dashboard.md`, which names
every tool call. In order:

1. **Find the dashboard.** The `## Dashboards` line on the Open work page first; then
   `Artifact` `list` for the exact title *"<Site>: Operations Command
   Center"*; only when both find nothing does this run create it. A scheduled
   run starts with no memory of earlier runs, so it looks every time.
2. **Build the day record** for the production day, every field, per
   `../../shared/contracts/pulse-day-record.md`, keyed `<site>_<YYYY-MM-DD>`.
   A missing export makes it `data_complete: false` with the gap named. Its
   metrics are null, never zero.
3. **Existing dashboard:** `read` it, `query` `pulse_days`, `set` the day
   record, compute the trend from the stored records in code, then publish to
   the same `url`. **First run:** back-fill (below), publish with
   `capabilities: {db: {}}` and the fixed title, `batch` the records against
   the new URL, write the URL to the `## Dashboards` line on the Open work
   page, then `open` the dashboard so it is what the person sees.
4. **Render the short Operations page,** after the publish so it can link
   to the dashboard: `python3 -I <this skill's folder>/scripts/render_short.py
   --out pulse-output [--full-page-url <url>]`. It writes
   `operations-short-<site>-<day>.html` beside the figures and checks itself;
   on a failed check it writes nothing, and the reply says so. It is a
   separate page from the dashboard and never replaces it. Per
   `reference/short-page.md`.
5. **Report it,** as the last line of the run: *"Updated **Fairview:
   Operations Command Center**, `<url>`. Private to you until you share it."*
   Or the fallback: the page saved as
   `pulse-output/operations-<site>-<day>.html` (in the reply only when no
   file can be written), its placement line, and
   *"The dashboard was not updated: [reason]."*

**Say "updated" only when the publish returned a URL in this run.** Never
"shared," never "scheduled," never "posted." The dashboard is private until
the user shares it, and the pulse never shares it. A run that says "updated"
without a URL from this run has told the meeting to trust a page nobody
rebuilt.

**Only the pulse publishes the Operations dashboard.** `daily-production-report`
run alone, and Chain 4, keep offering their page in the conversation. Two
dashboards showing the same numbers is how a meeting ends up arguing about
which one is right.

**Back-fill on the first run only.** When the exports cover several production
days, the run that creates the dashboard writes a record for every day the
planning, production and downtime exports fully cover, so the trend opens with
history. A day they only partly cover is written `data_complete: false`, so it
shows as a gap rather than as a bad day. Later runs write their own day.

What the page holds, panel by panel, is `reference/operations-dashboard.md`.

---

## What "safe to run unattended" actually requires

Three properties. Each is a real constraint, not a nicety.

**It asks nobody anything.** There is no one at 4am to answer. Where an
attended run would ask which date range or which of several exports to use, the
unattended run takes the production-day range from the `## Plant context` block
and **says which it used**. **With no Plant context at all**, it uses the latest
complete production day present in the exports, says so in the freshness
banner, and lists *no plant profile* among the gaps. It never blocks on the
missing profile, and never picks today's date, which has no data. A run that blocks on a question produces nothing,
and nothing is worse than a partial report, because the gap is only discovered
at the meeting. The publish step asks nothing either: where two artifacts carry
the exact title, it uses the stored URL's, or the most recently updated, and
names both.

**Asking nobody does not mean deciding for them.** Where plan and output spell
a part differently, the unattended run neither drops the row nor joins it
silently. It shows the variance **labelled provisional**, shows both spellings
verbatim, and lists each normalization it relied on as **proposed, awaiting
approval**, for whoever reads the page to accept or reject. Normalizations on
the profile's `### Approved normalizations` list are used as they stand; each
overnight run rebuilds the dataset, so that list is what carries a yes from one
night to the next. This is
not a gate — nothing is applied and nothing is written — and the rule is
`../../shared/approval-gates.md`, *When nobody is there to ask*.

**A list of data problems holds problems, and it is built by class number.**
Take the classified mismatches from step 1 and route each class before any
row is numbered:

| Class | Where it goes |
|---|---|
| 1 orphan, 2 format drift, 3 leading zeros, 4 revision suffix, 5 case and whitespace, 8 duplicate key | The numbered **Data problems** table, and its count |
| 7 date window | The coverage line in the freshness banner. Not a numbered row |
| 6 genuine one-sided record | **"Checked, nothing wrong"**, a separate block after the table. Never a row number, never in the count |
| 6 with `contradicted_by` set | The numbered **Data problems** table, as *one-sided, contradicted by* the named record, and its count. Never "Checked, nothing wrong" |

A record decides its class from its own type and dates, never from a part
number someone recognises. A Class 6 record that appears in the table *and*
in the recap has still been counted as a problem; it appears in the recap
only. **A duplicate key is counted by the rows that collide at the tab's
grain, from the query** (work order, shift and production day): if WO-88201
has three rows, and two of them (509 and 480 good, both 07:00)
are the duplicate; the 95 on the 23:00 shift is its own shift. Say both
numbers, and the figures block shows the filter. And a downtime record
from `breakdown-diagnosis` with no `safety_flagged` is **blocked**: listed
first under "Blocked — safety status unknown," held out of both rankings, the totals
and the pricing. MES and historian rows are untouched. Both rules are
`../daily-production-report/SKILL.md`, steps 7 and 8. The day record carries
the same split: `data_problems_count` is the table's count, and a blocked
record is outside every downtime figure stored.

**It is idempotent.** A re-run for the same production day overwrites that
day's record by key and updates the same dashboard, rather than adding a
second record or creating a second page. Somebody will re-run it, after a late
export lands or because the first run was mistrusted, and two reports for one
day is worse than one because the meeting then argues about which is right.

**It reports gaps rather than failing on them.** If last night's export did not
land, the run still completes and says so at the top. A missing export is a
finding, not an exception. Silence, stale data and a crashed run all read the
same way to a supervisor at 6am: nothing to look at. A publish that fails is a
gap of the same kind: the run falls back and says so.

---

## Approval gates

**None, by design.** This chain is read-only and writes to no system of record.
That is the whole reason it can be scheduled.

Anything that would need a gate does not belong in this chain. The reschedule
proposals it produces are drafted for the scheduler and **never applied**.

**Publishing the dashboard is not a gate.** It writes to the user's own
artifact store, not to M365 or any system of record, and the page is private
until the user shares it. The `## Dashboards` line on the Open work page is
written without a gate for the same reason; never say the page was saved
unless `saved` returned ok in this run. The `## Plant context` block is never touched by
this chain: changing it takes two turns and an approval nobody is there to
give.

---

## Scheduling

**The plugin does not schedule itself.** It provides a run that is safe to
execute unattended; the host provides the trigger. Read
`../../shared/scheduling.md`.

Never tell a user the report has been scheduled. Describing the run as
overnight is accurate; claiming to have scheduled it is not.

**Whether an unattended, scheduled session can publish is unverified.** The
run checks for the `Artifact` and `ArtifactData` tools every time and falls
back when they are absent. It never claims a scheduled run published.

---

## Output

**The reply is a summary of about 150 words; the full page is on the
dashboard or in a file**. When the publish did not
return a URL, save the full page as `pulse-output/operations-<site>-<YYYY-MM-DD>.html`
and name that path. The summary is the one in `../../shared/replies.md`
(200 words at most), plus one line per day record: its key, `data_complete`,
the gap if any, and whether it was stored. A request that picks or skips
sections is not the whole report: those sections go in the reply in full. **With no way to write a file and no publish, print
the full page in the reply instead.**
**A record handed to another skill is saved and summarised, never pasted as
raw YAML**; memory blocks are written where the plant's memory lives; and the
name on an approval is asked, never taken from the account. All three per
`../../shared/replies.md`.

**The Operations Command Center dashboard** — *"<Site>: Operations Command
Center"*, one per site, created on the first run and updated in place after
that, per `../../shared/live-dashboard.md` and
`reference/operations-dashboard.md`. Its header reads *Updated [timestamp] ·
data as of [timestamp]*. Two panels:

- **Today:** a safety-flagged diagnosis record first, then the freshness
  banner, never a footnote, then today's actions (issue, impact, next step,
  owner role, and whether it is a decision, an investigation or an
  observation, per step 4 of the report order in
  `../daily-production-report/SKILL.md`), then output against plan, OEE with its three components shown separately, downtime ranked both
  ways, priced losses, exceptions with a traced reschedule move per
  significant exception, "Blocked — safety status unknown," the numbered
  data-problems table with its count, and "Checked, nothing wrong" outside
  that count.
- **Trend:** OEE and its three components, output against plan, and downtime
  minutes for the last 14 and 30 days, and the week-over-week movers, all
  from the stored day records. A day with no data is a gap, never a zero.
  With no history yet, the panel says so and week-over-week is skipped.

Plus the structured dataset behind it so the numbers can be checked —
**including the figures block**, which matters most here because nobody is
watching the run. Every count in the page, and every count in any list of data
problems, is printed from a computation and listed with its filter, and the
page quotes the block. Every trend point is in the block too, with the records
it came from. A problem count that does not equal the problems listed under it
is the defect to look for. Per `../../shared/computed-figures.md`.

**The day record(s)** — per `../../shared/contracts/pulse-day-record.md`, on
every run, stored or not: one line each in the reply (key, `data_complete`,
the gap, stored or *computed, not stored*), and the field and value table of
`../../shared/replies.md` on the page.

**The short Operations page** — a file, never pasted into the reply. Name
its path and give its decisions, one line each, above the last line. With no
code execution there is no short page; say so in one line.

**The last line** — the dashboard line with its URL; or, when the dashboard
could not be published, the page in the conversation, its placement line
(*"save it over yesterday's"*), and *"The dashboard was not updated:
[reason]."* Read `../../shared/command-center.md`.

---

## Edge cases and failure modes

- **Last night's export did not land** — run anyway, and report the gap
  prominently. Never silently reuse yesterday's data. The day is stored
  `data_complete: false`, and the trend shows a gap, never a zero.
- **Partial data, one line's export missing** — report on what is there and
  name what is missing.
- **A re-run for a day already reported** — overwrite that day's record and
  update the same dashboard. Never a second record, never a second page.
- **A late export lands after the run** — a re-run for that day overwrites its
  `data_complete: false` record with the complete one.
- **First run, no stored history** — back-fill what the exports fully cover.
  With nothing to back-fill, the trend panel says there is no history yet and
  week-over-week is skipped rather than shown empty.
- **The dashboard was renamed** — the title lookup cannot find it, so a new one
  is created. Say so, per `../../shared/live-dashboard.md`.
- **The publish fails or the tools are absent** — fall back: page in the
  conversation, placement line, "the dashboard was not updated." The run
  never stalls on it.
- **Reason codes heavily "Other"** — that coverage problem is a finding of its
  own, not something to smooth over.

---

## Degradation

| Not available | What happens |
|---|---|
| The export folder | Run connector-only and name every tab that could not be built. Never treat a missing tab as empty |
| The downtime cost-per-hour | Price scrap only, and say downtime is unpriced |
| Stored day records | Skip week-over-week; the trend panel says there is no history yet |
| The `Artifact` or `ArtifactData` tools, including on an unattended run | The page in the conversation, its placement line, and "the dashboard was not updated." The day record is still in the structured output, marked not stored. Never "updated," "scheduled" or "shared" |
| The Open work page can't be written, for the `## Dashboards` line | Find the dashboard by exact title, report the URL, and say the link was not saved |
| A CMMS connector (Limble or any other) | See below |

**If Limble isn't included, or no CMMS connector is live** — negligible for this chain. It is an overnight
batch, so an export cadence is already the correct cadence: the maintenance
rows simply arrive in the same scheduled drop as production and planning. The
freshness banner must name maintenance as an export-sourced input so nobody
assumes it is live.

---

## Chain position

**This is Chain 3 itself.** Members: `data-consolidate`,
`daily-production-report`, then this skill's own publish step.

**Metric.** OEE visibility and supervisor hours, both owned by
`daily-production-report`. The scheduled delivery is what earns the supervisor
hours: the report exists before anyone builds it by hand.

---

## Reference files

| File | Load when |
|---|---|
| `reference/compute-engine.md` | Before building the page: what `pulse_model.json` holds and how each part is labelled |
| `reference/short-page.md` | Step 3.4 — the short Operations page: what it holds, and how it differs from the dashboard |
| `../data-consolidate/SKILL.md` | Step 1 — the join and the eight mismatch classes, when the engine cannot run |
| `../daily-production-report/SKILL.md` | Step 2 — OEE, the rankings, the reschedule scope boundary |
| `../../shared/live-dashboard.md` | Step 3 — finding, creating and updating the dashboard, the tool calls, the fallback |
| `../../shared/contracts/pulse-day-record.md` | Step 3 — every field of the day record, and the gap rule |
| `reference/operations-dashboard.md` | Step 3 — the Today and Trend panels |
| `../../shared/scheduling.md` | Before claiming anything about the trigger |
| `../../shared/command-center.md` | The Operations page, and when "updated" may be said |
| `../../shared/computed-figures.md` | Before emitting — the figures block |
| `../../shared/approval-gates.md` | When a match rests on a normalization nobody has approved |
