---
name: daily-production-report
description: "Produces the morning production report: output against plan by line, cell and product; OEE with availability, performance and quality shown separately; the downtime log ranked both by minutes and by frequency; scrap and downtime priced in dollars; week-over-week movers; and the exceptions needing a decision today. For each significant exception it drafts a specific reschedule or changeover move with its consequences traced, never a re-optimised day. Reads the consolidated dataset and leads with data freshness. When the plant has a floor plan on file, or attaches one, it also draws each machine's OEE, availability and downtime on a schematic of the floor. Use when someone says \"morning report,\" \"production report,\" \"how did we do yesterday,\" \"what's our OEE,\" \"downtime report,\" \"what's late,\" or \"what do I take into the production meeting.\""
compatibility: "Requires a consolidated dataset from data-consolidate. Reads the ERP (Oracle NetSuite or Infor M3) for standard cost and open work orders, and a CMMS connector (Limble is the worked example) for maintenance work orders in progress, when connected. Runs on export-only data. Writes nothing to any system of record."
---

# Daily Production Report

Every plant runs a morning production meeting, and somebody spends 60 to 90
minutes before it assembling the same report by hand out of the same four or
five exports. This is that report.

**Chain 3 runs this overnight, so the page exists before anyone asks for it.**
The run is built to be safe unattended — it asks nothing, it is idempotent, and
it reports its own gaps. **The trigger is the host's, not the plugin's**: see
`../../shared/scheduling.md`. Never tell a user the report has been scheduled.
That is the clearest demonstration of the plugin's concept, and it
is why the run must be idempotent — a re-run rewrites the same report for that
production day rather than producing a second one.

**Quick start**

```
→ Confirm freshness; if last night's export didn't land, lead with that
→ Output against plan by line, cell, product, with variances
→ OEE per asset or line, three components always shown separately
→ Downtime ranked by minutes and by frequency, both
→ Price scrap and downtime in dollars, with the rate assumption stated
→ Week-over-week movers from history: the pulse's day records, or the exports
→ Fold in any breakdown diagnoses
→ Exceptions, each with its impact on a commitment
→ One traced reschedule move per significant exception, drafted not applied
→ Floor view: each machine's figures drawn where it sits; set up once from a
  floor plan, confirmed by a person, saved on the plant setup page
→ Page saved to report-output/; the reply is a ~150-word summary naming it
→ Run alone: never publishes. End with the placement line, "save it over yesterday's"
```

---

## Inputs

**First, find the plant setup:** from the task's own folder (never `cd` into the plugin), run
`python3 -I <this skill's folder>/../../shared/scripts/plant_setup.py find`, do its `setup_page_first` step, then read the profile at
`profile_path` and any rate at `rates_path`, per `../../shared/replies.md`.

| Input | Source | Form |
|---|---|---|
| Consolidated dataset | `data-consolidate` | **Primary input.** `../../shared/contracts/consolidated-dataset.md` |
| New breakdown diagnoses | `breakdown-diagnosis` | `../../shared/contracts/downtime-record.md` |
| Production plan / schedule | Planning export to the M365 folder | CSV / XLSX |
| Actual output, good and scrap | MES export to the M365 folder | CSV / XLSX |
| Downtime events with reason codes | MES or historian export | CSV |
| Standard cost per part | The ERP. Infor M3 gives none (`../../shared/erp-connectors.md`): the profile's cost read order applies | Connector |
| Open work orders and due dates | The ERP | Connector |
| Maintenance work orders in progress | CMMS | CMMS connector, else the maintenance export |
| Stored day history, inside Chain 3 only | `morning-plant-pulse` | `../../shared/contracts/pulse-day-record.md` |
| Floor layout (optional) | The `### Floor layout - <site>` section of the plant profile at `profile_path` (the plant setup page) | `../../shared/contracts/floor-layout.md` |
| Floor plan (optional, setup only) | A PDF or image the user attaches | Read once, in the setup turn of step 9a; never stored |
| OEE thresholds (optional) | The plant profile's `OEE thresholds` line | Defaults apply, labelled not confirmed, when absent |

---

## Workflow

### Step 1 — Confirm freshness

Confirm freshness via `data-consolidate` — the data quality report and each
row's `as_of`. **If last night's export did not land, say so at the top of the
report**, directly under any safety block. Nothing about data age goes above a
safety-flagged record, not even a one-line note.

A source whose timestamps run later than now is flagged `future_timestamp`:
say its dates can't be trusted and give it no age. A production report built on
stale data is worse than no production report,
because it gets believed and acted on. Never silently reuse yesterday's data.
The rule is `../../shared/absent-is-not-zero.md`.

**On reading both the dataset and the raw exports.** The dataset is the primary
input — it carries the freshness picture and the classified key mismatches. The
plan, output and downtime exports give rows at their native grain. Where the two
disagree on a count, **report both and name which is which**; a discrepancy is a
finding about the export, not a number to choose between. See *What this dataset
is authoritative for* in `../../shared/contracts/consolidated-dataset.md`.

### Step 2 — Output against plan

By line, cell and product, with variances. Use the plant's own word for the
organizational unit, from the `## Plant context` block.

**Where plan and output spell a part differently, do not match them silently,
and do not refuse to match them.** Run on raw exports, the plan says
`PN-4471-B` and the MES says `4471B`. Dropping the row makes output against
plan look broken; joining it without a word applies a fix nobody approved. So:

1. Use any normalization already approved — in the consolidated dataset, or
   on the profile's `### Approved normalizations` list — as it stands.
2. For every other match that depends on a normalization, **show the variance
   labelled provisional**, and beside it **each normalization it rests on, with
   both spellings verbatim** — `4471B` → `PN-4471-B`, format drift.
3. **Ask for a yes on each**, the same "apply?" gate `data-consolidate` uses.
   Until then the rows stay provisional, in the table and in any total built
   on them.

An unattended run cannot ask: it carries the same provisional table and lists
the normalizations as *proposed, awaiting approval*. Per
`../../shared/approval-gates.md`.

### Step 3 — Compute OEE

Per asset or line, **with the three components always shown separately**. Read
`reference/oee.md` first — the denominators carry real traps, and a missing
component is never substituted with 1.0.

**State the quality convention on every run**, as a line under the OEE table:
*"quality = good ÷ (good + scrap)"*. **Only when the export has no rework
column** does the line continue: *"no rework column, so first-pass yield could
not be applied."* Where the export does carry rework, quality is first-pass
yield, good ÷ (good + scrap + rework), and the line says so instead. Never
print the no-rework caveat against an export that has the column.

### Step 4 — Build the downtime log

Ranked **two ways, both always shown**: by total minutes, and by frequency.

**`Other` never appears in a cause ranking.** Before ranking by reason code,
count the events and minutes coded `Other` or left blank and state that share
as a finding of its own: *"18 of 39 events, 46%, carry no usable reason code."*
Then rank the named codes only, with the caveat that the picture is incomplete
by that share. A table with `Other` in row 1, priced, tells the meeting the
plant's biggest problem is a word, and it is the single most common way this
report has been wrong.

**A downtime row that ends before it starts, or whose duration disagrees with
its own start and end, has no trustworthy minutes.** It carries
`end_before_start` or `duration_mismatch` from the dataset; reading the export
raw, test it in code. Hold its minutes out of every total and the minutes
ranking, count it as an event, and state the exclusion beside the ranking with
the row: *"DOOSAN-PUMA-07, 4 Aug: ends 14:01 after starting 14:05, 56 minutes
stated, not counted."* Never pick a figure for it.

These describe different problems. One long outage and forty chronic small
stoppages can total the same minutes, and the second is usually the more fixable
of the two. A single ranking hides whichever one it does not sort by.

### Step 5 — Price the losses

Scrap × standard cost. Downtime × the plant's configured cost-per-hour.

**Scrap dollars are an estimate at standard cost, and say so** where they are
printed (*"$180 scrap, estimated at standard cost"*): they are exposure, not
a booked loss. With no rate, downtime dollars are *unknown*, never $0.

"47 parts scrapped" does not land in a production meeting. "$8,400 of scrap, 71%
of it on one part number" does, and it is the same data multiplied by a cost.

**Every quantity in the priced-losses table is the figures-block row, printed.**
The scrap count beside a part's dollar figure is the same number the dollar
figure was multiplied from; a table that says 155 units against a figure
computed from 62 has been typed, not printed. Build the table from the block,
per `../../shared/computed-figures.md`, and never from memory of it.

**A part whose scrap is recorded in a different unit from its standard cost is
unpriced, not converted.** Scrap in `box12` against a cost per `each` has no
dollar figure until the plant says what a box holds: report the quantity in
its own unit, mark the dollar cell "unpriced — unit conflict," and name the
conflict. Never price it two ways ("$5,465 if singles, $65,584 if boxes of
12"): both numbers are guesses, and the larger one is the one that gets
repeated. The rule is the same one `data-consolidate` applies at the join.

**Always state the assumption behind the downtime rate.** Resolve it per
`../../shared/secret-config.md`, *Resolving a rate* —
`MFG_DOWNTIME_COST_PER_HOUR` if set, then a confirmed rate in the plant
profile, then a placeholder there, labelled "placeholder rate — not
confirmed" — and name the source next to the priced downtime. This is an
unattended overnight run, so there's no one to ask. Without a rate in either
route, price scrap only and say plainly that downtime is unpriced, per
`../onboarding/reference/config-profile.md`.

### Step 6 — Week-over-week movers

Compare against earlier production days and surface the biggest improvements
and deteriorations. **The history comes from one of two places, never from a
prior page.** Inside Chain 3, `morning-plant-pulse` hands over the stored day
records. Run alone, this skill compares only against earlier days the exports
in front of it cover, and says that is the basis. Trend beats snapshot: a 68% OEE that was 61% last week is a
different conversation from one that was 74%.

**Compare all four: output against plan, OEE by component, downtime minutes and
scrap dollars.** A movers section that shows only OEE has missed the number the
plant manager looks at first. Each mover names the metric, last week's value,
this week's, and the change.

**With no earlier day to compare against, skip the section rather than
showing an empty comparison.**

### Step 7 — Fold in breakdown diagnoses

Any downtime record from `breakdown-diagnosis` appends into the downtime log and
the exceptions, with no transformation step. Its contract governs how — including
that an ongoing outage has a null duration rather than zero, that a safety flag
leads with its `safety_reason`, and that an advisory cause is attributed as
proposed rather than established, with its `technician_step` beside it
(*"proposed; technician step skipped"*).

**Check `safety_flagged` on every record where `source_system` is
`breakdown_diagnosis`, before it goes anywhere:**

- **Absent — block the record.** It appears only in a separate **"Blocked —
  safety status unknown"** list, **placed first, above both rankings**, with
  its asset, start time and the reason: *safety status missing on a diagnosis
  record — not ranked until confirmed.* It is not in the minutes ranking, not in the frequency ranking, not in any
  total, and not priced, until the flag is known. Labelling it "unknown" and
  ranking it anyway is not blocking it. Never read a missing flag as false.
- **True — it leads the report**, above both rankings.
- **False** — it joins the log as an ordinary row.

**No diagnosis records at all is not a clear safety status.** When the drop
holds none, write *"Safety status: not assessed (no breakdown diagnosis records
in this drop)"* once, where the safety block would sit. Never "no safety
issues", and never read an empty maintenance or quality export as nothing open.

**Rows from the MES or historian export are not contract records and are left
exactly as they are.** They never carry this field; its absence there means
nothing, and blocking them would empty the report.

### Step 8 — Identify exceptions

Late jobs, machines down, material shortages, quality holds. **Each with its
impact on a commitment** — an exception with no stated consequence is not
actionable. The commitment is read through the work order's `sales_order`.
Where the source holds no work order to sales order link, say *"commitment
impact not traceable: no work order to sales order link in the ERP"* once,
with the count it affects, and never infer the order from part and customer.

**A genuine one-sided record is not an exception, and is never counted as
one.** A part in the item master with no plan and no production, a machine
with no downtime, a supplier with no purchase orders in the window: that is
Class 6 in `../data-consolidate/reference/mismatch-classes.md` — *report, do
not alarm* — and usually nothing is wrong at all. Build the list in two
passes:

1. Classify each candidate first. Class 6 records leave the exceptions list
   and every count of exceptions or problems.
2. Show them in a separate **"Checked, nothing wrong"** block, one line each:
   *"in the item master, not planned and not produced this month."*

Decide it by class, from the record's own type and dates, never by recognising
a part number. **Route by class number before numbering any row**: classes 1,
2, 3, 4, 5 and 8 are exceptions or problems; class 7 is the coverage line in
the freshness banner; class 6 is "Checked, nothing wrong" **unless the record
carries `contradicted_by`**. A one-sided record that another source
contradicts (WO-88412, closed with no output, while NCR-2026-0141 found bad
parts from it) is an exception, *"one-sided, contradicted by NCR-2026-0141"*,
and never sits under "nothing wrong". A duplicate key (class 8) is counted by
the rows that collide at the tab's grain, from the query: WO-88201 has three
rows, two of them (509 and 480, both 07:00) collide, and the 95 on the 23:00
shift is its own shift. State both numbers. One false alarm in the list is what makes a supervisor stop
reading the rest of it. A date-window gap (Class 7) is different: it stays a
coverage statement in the freshness banner, and is not a record-level
exception either.

### Step 9 — Propose the reschedule or changeover move

For each significant exception: the specific move, what it displaces, what still
misses its date, and what was checked versus not checked.

**Read `reference/reschedule-scope.md` before doing this.** There is a hard scope
line — one or two traced moves, never a re-optimised day — and the reason is that
a plausible-looking schedule that quietly violates constraints is worse than no
proposal at all.

Drafted for the scheduler. Never applied.

### Step 9a — Floor view

**Read `reference/floor-schematic.md` first.** It holds the setup turn, the
save, the drawing rules, the states, the thresholds and the failure modes.

- **The user attaches a floor plan, or asks for a floor view and none is on
  file:** run the setup turn. State the count first, propose each match with
  both spellings verbatim, list what did not match on either side, and **ask
  for a yes per area**. Turn 1 shows, turn 2 saves, and only with a name or
  role the person typed. Per `../../shared/approval-gates.md`.
- **A layout is on file** (the `### Floor layout - <site>` section of the
  profile): draw it from the figures block. **Compute nothing new.** An
  unconfirmed mapping is a neutral outline with no figure. No data is grey,
  never 0%. Data but no computable OEE is grey *OEE N/A* with its reason.
- **No layout:** one line saying none is on file and how to set one up.

**An unattended run never sets up, edits or re-maps a layout**, and never
draws a guess. Colours follow the profile's `OEE thresholds` line; until the
plant confirms one, the defaults are used and the legend says so.

### Step 10 — Emit

**Build the figures block first, in code, then write from it.** Every count,
total, percentage and "N of M" in the report — events per reason code, events
sharing a timestamp, minutes per asset, scrap share per part — is printed from
a computation run in this session and listed in the block with its filter. The
prose and the tables quote the block; nothing is retyped from memory. Per
`../../shared/computed-figures.md`. "Thirty of the 39 events" written beside a
log that holds thirty-one is what this step exists to stop.

Render the report and the structured data behind it, per Output below. Chain 3
emits overnight so the report exists before the morning meeting.

**The run is idempotent.** A re-run for the same production day rewrites that
day's report; it does not create a second one.

---

## Approval gates

**This skill is read-only.** It reads, computes, prices and proposes, and it
writes nothing to any system of record — which is precisely why Chain 3 is safe
to run unattended.

**Asked to post, send or share the report** — to a Teams channel, by mail, to
Slack — **say it does not post, and give the text ready to paste.** *"I don't
post to Teams. Here's the report as text to paste into the Production
channel."* No send tool is called, even where one is available, and **no offer
to post later**: not "confirm the channel and I will post this." The report is
still produced in full. Per `../../shared/command-center.md`.

Two things are drafts requiring a human, not actions:

- **The reschedule proposal** is drafted for the scheduler to accept or reject.
- **A breakdown diagnosis carried in** stays labelled as advisory unless its
  contract says a technician confirmed it.

---

## Output

**The morning report is written to a file, and the reply is its summary.**
Save the full page as `report-output/morning-report.html`, one file saved over
the last run's, as the placement line says, with the site and production day
in its title; name that path in the reply, which is the short summary in
`../../shared/replies.md` (about 150 words, 200 at most). A request that picks
or skips sections is not the whole report: those sections go in the reply in
full. **With no way to write a file,
print the full page in the reply instead.** Any other document this skill
produces (a reschedule proposal handed to the scheduler, text to paste) is
printed in the reply in full.
**A record handed to another skill is saved and summarised, never pasted as
raw YAML**; memory blocks are written where the plant's memory lives; and the
name on an approval is asked, never taken from the account. All three per
`../../shared/replies.md`.

**The morning report** — an HTML page in the house style
(`../../shared/artifact-style.md`), and the Operations command-center page
(`../../shared/command-center.md`) — an artifact you place, never a write.
Chain 3 rewrites it overnight, which is the whole demonstration.

**Run alone, this skill does not publish.** It never creates or updates the
Operations Command Center dashboard and never writes a day record: only
`morning-plant-pulse` does, per `../../shared/live-dashboard.md`. A standalone
run returns its page in the conversation with the placement line, *"save it
over yesterday's,"* and never says the dashboard was updated. Two dashboards
showing the same numbers is how a meeting ends up arguing about which is
right. **The page leads with what the meeting acts on and keeps all the
evidence below it**. In order:

1. **Safety blocks, whenever they have anything in them.** A safety-flagged
   diagnosis record first, then its own section headed exactly "Blocked —
   safety status unknown", above the freshness banner
2. **Freshness banner** — required, directly under any safety block and first
   otherwise, never a footnote. It states the shifts the day actually holds;
   a day with fewer shifts than usual says so, and is not a complete plant day
3. **Headline figures**: good output against plan, total output beside good
   when they differ, OEE with its three components, downtime minutes, and
   scrap at standard cost (an estimate). Each caveat sits on its own figure
4. **Today's actions**: one row per exception that needs someone, with the
   issue, its impact (on a commitment where traceable), the next step, the
   owner role, and its type. **A decision** is something genuinely waiting
   on an approval: a normalization not yet approved, a reschedule move for the
   scheduler. **An investigation** is something to find out first: an unknown
   work order, a contradicted record, an uncoded stop. **An observation**
   needs no action today. The owner role is the one the source names, else
   *"suggested: <role>"*; never a person's name the data does not hold. With
   nothing waiting, say *"No decisions waiting today."* Never present a
   reschedule, a reserved capacity or a root cause as already approved
5. **Floor view**: the schematic, its legend, *"State as of the last
   export, [time]. Not live."* and the lists under it, per
   `reference/floor-schematic.md`. Every number is a figures-block row. With
   no layout, one line
6. **The detail**, every table the report has always held, collapsible but
   never removed: output against plan with variances; OEE per asset or line,
   three components separate; downtime ranked by minutes and by frequency;
   priced losses with the rate assumption stated; week-over-week movers,
   omitted entirely when there is no earlier day to compare; exceptions with
   their commitment impact; reschedule proposals, one per significant
   exception; then sources, methods and assumptions

**Safety leads the report, freshness comes straight after it.** A safety
implication goes before anything else, and a banner of source ages is not
a reason for a lockout instruction to sit second. **When there is a safety
block, it is the first thing under the title.** The title names the site and
the production day, nothing else: no data age, no scope line, no intro
sentence above the safety block. *"Fairview: morning report, 31 Aug"*, then
the safety block, then the freshness banner. Both stay above every
ranking and figure. "Blocked — safety status unknown" lists every diagnosis
record held out of the rankings. **"Checked, nothing wrong"** follows the
exceptions, holding the one-sided records that were looked at and are fine —
outside every problem count.

**The structured data behind the report**, so every number can be checked rather
than taken on trust. **It includes the figures block** — required on every
run, attended or not: each stated figure, its value, and the filter that
produced it, per `../../shared/computed-figures.md`.

---

## Edge cases and failure modes

- **Last night's export did not land** — report the gap prominently. Never
  silently reuse yesterday's data.
- **Partial data, one line's export missing** — report on what is there, name
  what is missing. Never let a section quietly shrink.
- **Reason codes inconsistent or heavily "Other"** — report the coverage problem.
  That is a finding of its own, not a data-cleaning task.
- **A machine ran unscheduled overtime** — availability can exceed 100%. Report
  it; do not clamp it.
- **Three shifts crossing midnight** — the production-day attribution rule is
  configured per site, and the report states which convention is in use.
- **No earlier day in the history or the exports** — skip week-over-week.
- **An asset in the plan with no output data** — it is unreported, **not 0% OEE**.
  Name it and exclude it from averages, saying so.
- **No standard cost available** — report scrap in units and say it could not be
  priced.
- **Anything in the floor view** (an unreadable plan, a label that could be
  two assets, a down machine, an asset added later, a busy drawing) — per
  `reference/floor-schematic.md`, *Failure modes*.

---

## Degradation

**If Limble isn't included, or no CMMS connector is live** — minor. The report loses its "maintenance work
orders in progress" line. Replace it from the maintenance export where one
exists, or omit the line **and say so** — never leave a silently empty section,
which reads as "no open maintenance" rather than "we could not see it."

Chain 3 is unaffected in any meaningful way: it is an overnight batch, so export
cadence is already the right cadence. The freshness banner names maintenance as
export-sourced so nobody assumes it is live.

**Without a planning export** — output against plan cannot be computed. Report
actual output and say plan comparison was unavailable.

**Without a downtime cost rate** — price scrap only, and state that downtime is
unpriced.

**Without a floor layout** — one line saying none is on file and how to set
one up. Nothing else changes. Without OEE thresholds, the defaults, labelled.

---

## Chain position

- **Chain 3, Morning plant pulse (scheduled)** — step 2, from `data-consolidate`.
  The only scheduled chain, read-only throughout, which is why it needs no
  approval gate.
- **Chain 4, Breakdown to next report** — step 2, from `breakdown-diagnosis`.
  Step 7 folds its downtime record into the log and exceptions with no
  transformation, per `../../shared/contracts/downtime-record.md`.

**Metric.** OEE visibility; supervisor hours; downtime and scrap cost
visibility — step 5 prices both on every run, not only when a breakdown fed
in.

---

## Reference files

| File | Load when |
|---|---|
| `reference/oee.md` | Step 3 — the three components, the denominator traps, and the never-substitute-1.0 rule |
| `reference/reschedule-scope.md` | Step 9 — what a proposal must contain and where the scope stops |
| `reference/floor-schematic.md` | Step 9a — the setup turn, the drawing rules, the OEE thresholds |
| `../../shared/contracts/floor-layout.md` | Step 9a — the stored layout's shape and missing behaviors |
| `../../shared/contracts/consolidated-dataset.md` | Step 1 — the primary input's schema and its missing behaviors |
| `../../shared/contracts/downtime-record.md` | Step 7 — the shape a breakdown diagnosis arrives in |
| `../../shared/approval-gates.md` | Step 2 — a match that rests on an unapproved normalization is provisional |
| `../../shared/computed-figures.md` | Step 10 — the figures block every stated number is quoted from |
