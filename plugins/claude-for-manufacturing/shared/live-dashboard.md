# Live dashboards — one page per site, updated in place

**Shared across the plugin.** Two pages are published to the Claude artifact
store and then updated in place on every later run, instead of being handed
over for the user to save over the last one:

| Dashboard | Fixed title | Published by | Records |
|---|---|---|---|
| Operations | `<Site>: Operations Command Center` | `morning-plant-pulse` only | `pulse_days`, per `contracts/pulse-day-record.md` |
| Quality | `<Site>: Quality Register` | `ncr-writeup` and `root-cause-capa` (and so `inspection-to-capa`, which runs them) | `ncrs`, per `contracts/quality-register-record.md` |

Every other command-center page stays what `command-center.md` describes: a
page offered in the conversation, with its placement line.

**This is not a write to M365 or to any system of record.** The artifact store
belongs to the user's Claude account. The M365 read-only rule in
`artifact-style.md` stands unchanged, and nothing here gives a skill a write
path into SharePoint, Teams, the ERP, the CMMS or the quality system.

---

## What "updated" means

**A skill says "updated" only when the publish call returned a URL in this
same run.** Not when it intended to publish, not when a publish was attempted,
and not because the dashboard was updated yesterday. A plant person who reads
"updated" stops checking, so the word has to be true every time it is printed.

The line that reports it names the dashboard and the URL:

> *Updated **Fairview: Operations Command Center** — `<url>`. Private to you
> until you share it.*

**The dashboard is private until the user shares it. No skill shares it, and
no skill says it is shared.** Sharing is something the user does in claude.ai.
Never write "shared with the team," "posted," "published to the plant" or
"scheduled."

---

## Fall back, never stall

**If the publish tools are not available in this session, or a call fails,
the run still completes the old way:** the page in the conversation, its
placement line, and one plain sentence saying the dashboard was not updated.

> *The dashboard was not updated: the artifact tools are not available in this
> session. Here is today's page; save it over yesterday's.*

Say why in a few words (tools not available, the publish was refused, the
record write failed). Never say "updated," "published," "scheduled" or
"shared" on a fallback run, and never offer to publish it "later" or "once
X is confirmed": that promises a run nobody has scheduled.

**Unattended publishing is unverified.** Whether a session started by a
schedule, with nobody watching, can publish and update artifacts has not been
tested. Until it is, a scheduled pulse run checks for the tools like any other
run and falls back when they are absent. **Never claim a scheduled run
published anything.** Only the run's own tool results say what happened.

---

## Where the dashboard URL lives

**In the `## Dashboards` block on the Open work page, one line per
dashboard** (`replies.md`, *The open work*). Not in the
`## Plant context` block: changing that block takes two turns and an approval
(`onboarding`, *Two turns, never one*), which an unattended run cannot do. The
URL is a pointer to the user's own page, not plant configuration, so the skill
writes this line without a gate:

```
## Dashboards
- Fairview: Operations Command Center — https://claude.ai/artifact/…
- Fairview: Quality Register — https://claude.ai/artifact/…
```

Write the line the first time a dashboard is created, and replace it if a run
has to create a new one, with `put --block "Dashboards" --entry "<title>"`, so
no other line or block changes. If the page cannot be written this session,
report the URL and say *"The link was not saved to your Open work page:
[reason]."*; the title lookup below will still find it next time.

---

## The steps, with the tool calls

These are the tools the dashboards are published and updated with. Use
exactly these.

| Step | Tool call |
|---|---|
| Find the dashboard | The `## Dashboards` line on the Open work page first. Then `Artifact` action `list`, matching the **exact** title |
| Create on first run | `Artifact` publish with the HTML file, `capabilities: {db: {}}` and the fixed `title`. Save the returned URL to the `## Dashboards` line, then `open` the dashboard so it, not the Open work page, is what the person sees (`replies.md`) |
| Update on later runs | `Artifact` action `read` with the URL, then publish with the same `url`. A publish without the read is refused |
| Write a record | `ArtifactData` action `set` (overwrite by key), or `batch` for several, against the dashboard URL |
| Read history for trends | `ArtifactData` action `query` or `list` on the collection |

Where the runtime asks for its own capabilities or design guidance to be
loaded before a publish, load it. The house style in `artifact-style.md` still
governs the look.

### 1. Find it before creating it

**Scheduled runs start in a fresh session with no memory of earlier runs**, so
the skill finds the dashboard every time rather than assuming:

1. **The stored URL.** If the `## Dashboards` line on the Open work page has one, `read` it. If the
   read works, that is the dashboard.
2. **The exact title.** If there is no stored URL, or it no longer opens,
   `list` and match the fixed title exactly. Write the URL found back to the
   `## Dashboards` line.
3. **Create it.** Only when both find nothing.

**A renamed artifact breaks the title lookup.** If someone renames the
dashboard and the stored URL is lost, the next run finds nothing and creates a
second one. Say so in the run output whenever a dashboard is created on a run
that is not the first: *"No dashboard titled 'Fairview: Operations Command
Center' was found, so a new one was created. If you renamed the old one, its
history is still there; rename it back and delete this one."*

**Two artifacts with the exact title:** use the one the stored URL names. With
no stored URL, use the most recently updated, and name both URLs in the run
output. An unattended run cannot ask which one is right, so it says which it
used.

### 2. Keyed records, written before or after the publish

History lives in the artifact's own database, one record per production day or
per NCR. **Every write is a `set` by key, so a re-run overwrites and never
adds a second record.** That is what keeps the pulse idempotent.

| Collection | Key | Contract |
|---|---|---|
| `pulse_days` | `<site>_<YYYY-MM-DD>`, e.g. `Fairview_2026-08-31` | `contracts/pulse-day-record.md` |
| `ncrs` | `<site>_<ncr_ref>`, e.g. `Fairview_NCR-2026-0141` | `contracts/quality-register-record.md` |

Order the calls so a failure loses as little as possible:

- **Dashboard already exists:** `read` it, `query` the history, `set` this
  run's record(s), then compute and publish. If the publish then fails, the
  history is already stored and the next run renders it.
- **First run:** publish first (the database belongs to the artifact, so
  there is nowhere to write until it exists), then `batch` the records against
  the new URL.

If a record write fails after a successful publish, the page is updated but
its history is not: say *"Updated the dashboard; the record for 2026-08-31 was
not stored, so the trend will show a gap for that day until this day is
re-run."*

**Every run shows its record(s) in the reply as well**, stored or not, so the
numbers can be checked and a fallback run says what would have been written —
as the summary table in `replies.md`, with the key and `data_complete` by
those names, never as a raw YAML block.

### 3. Keep the page static

**The skill reads the records, computes every figure in code, and bakes the
numbers into the HTML it publishes. The page never calls the database when
someone opens it.** That way it opens with no consent prompt, works for anyone
it is later shared with, and the figures block still covers every number on
the page. The `db` declaration gives the records somewhere to live; it is not
there so the page can read them.

Declare `capabilities: {db: {}}` on the create. On an update, omit
`capabilities` so the page keeps what it has.

### 4. Report it

The run output ends with the dashboard line: *Updated* with the URL, or the
fallback sentence. A created dashboard says *Created* with the URL. On the
Quality Register, the sensitivity line follows it (see below).

---

## Rules that carry over unchanged

A published dashboard is still a page this plugin produced, and every rule a
page follows applies:

- **House style**, per `artifact-style.md`. No new palette.
- **The freshness banner first**, never a footnote. Only a safety-flagged
  record or a blocked safety status sits above it.
- **Absent is not zero**, per `absent-is-not-zero.md`. A day whose export did
  not land is stored `data_complete: false`, and the trend shows a **gap**
  for it, never a zero plotted as if the line stopped. A metric that could
  not be computed is null in the record and blank in the chart.
- **The figures block**, per `computed-figures.md`. Every number on the page,
  including every trend point and every count in the header, is printed from
  a computation listed in the block.
- **Every count has an example row.**
- **The header carries both clocks:** *Updated [timestamp] · data as of
  [timestamp]*. "Updated" is the publish time of this run; "data as of" is
  the newest source the numbers rest on. A fallback page, which was not
  published, says *Generated [timestamp] · data as of [timestamp]* instead.

---

## Back-fill on the first run

**When the first run's exports cover several production days, the first run
stores a record for each of them, so the trend opens with history.** Only for
days the exports fully cover: the planning, production output and downtime
exports each hold that day, and each export's window runs past the day's end.
A day only partly covered is still written, as `data_complete: false` with
its gaps named, so it shows as a gap rather than as a low day.

Back-fill happens once, on the run that creates the dashboard. Later runs
write their own production day; a re-run for an earlier day overwrites that
day's record by key.

**With no history at all**, the trend panel says so in a sentence (*"First run:
no stored history yet. The trend starts tomorrow."*) and week-over-week is
skipped, not shown empty.

---

## The Quality Register

The register exists because a single run knows one NCR, and a list of open
corrective actions needs the others. Each NCR or 8D run writes its own row
and then rebuilds the page from every row in `ncrs`.

**Banner, first, always:**

> *Tracks NCRs run through this plugin since [date of the oldest record]. Not
> your full quality library.*

**The date is never dropped.** On a fallback run, with no register to read
the oldest record from, it says *"since [date unknown: the register was not
reachable this run]"* — the sentence keeps its shape, so a reader always sees
that a start date exists and what it is or why it is missing.

A manager reading "3 open" will assume that is everything. The banner is what
stops it. Where the M365 quality library is readable in this run, a read-only
check may list NCRs found there but missing from the register, as a separate
*"In the library, not in this register"* list. Nothing is written to the
library.

**Page content, in order:**

1. **Header counts:** open, overdue, awaiting approval. Each count is printed
   from the records and carries example rows below it.
2. **Open items table.** Customer-escape clocks first, soonest deadline at the
   top; then the rest by age. Columns: NCR, part, lot, status, 8D step,
   owner, due, escape clock, age in days. NCR, part and lot numbers in mono.
   Status pills use the existing semantic colors: `--critical` for an escape
   clock running or overdue, `--warn` for awaiting approval or blocked,
   `--good` for closed. An owner nobody has assigned reads *unassigned*, never
   blank.
3. **Recurrence and supplier-caused flags.** A recurrence whose previous fix
   did not hold is flagged on its row. The supplier-caused flag shows here as
   a flag only; **the supplier signal stays on its own Supply Chain page**, per
   `command-center.md`.
4. **Closed items**, in a collapsed `<details>` section, with the close date.

**Overdue** means a due date before today on a row that is not closed. A row
with no due date is *no due date*, not overdue and not on time.

**Closing an NCR is the user's decision.** For now the user tells the skill
(*"close NCR-2026-0141"*) and the skill sets that row's status to `closed`,
with who said so and when, and republishes. Closing it in the register does
not close it in the plant's quality system; say that the NCR itself is closed
by whoever owns it. If the register is unavailable this run, say the close was
**not recorded** and the register was not updated. Never report it closed.
There is no in-page editing.

**Sensitivity.** The register is internal. It holds customer names and
customer-notification deadlines. It carries the NCR and the 8D **by
reference** — the identifier and a one-line summary — never the documents,
and never any content from a redacted customer pack. Every line that reports
the register's URL is followed by:

> *Internal: it lists customer names and notification deadlines. Check who you
> share it with.*

See `secret-config.md`, *The audience rule*.

---

## One dashboard per site

A plant with two sites has two Operations dashboards and two Quality
Registers, each with its site in the title and in every record key. A record
never lands in another site's dashboard. There is no combined multi-site view
yet.
