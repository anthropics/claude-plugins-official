---
name: breakdown-diagnosis
description: "When a machine goes down, reads the sensor window before the failure, the asset's maintenance history including the free-text close-out notes technicians actually wrote, photos of what they can see, and the manufacturer's troubleshooting tree — then ranks likely causes, each with its supporting evidence, the specific prior work orders behind it, and the cheapest test that would tell them apart. Surfaces any safety implication before any diagnosis. Drafts the PM interval change that would stop it recurring, and emits a downtime record for the next production report. Batch mode ranks bad actors across every asset. Use when someone says \"the machine is down,\" \"what's wrong with this machine,\" \"why does this keep failing,\" \"diagnose this,\" or \"which machines are hurting us most.\""
compatibility: "Requires none. Reads a CMMS connector (Limble, added through custom-connector, is the worked example) for assets, maintenance history and PM plans when connected, plus historian sensor exports, photos and manuals from Microsoft 365. Runs usefully with no sensor data and no connector. Output is always a draft the technician applies."
---

# Breakdown Diagnosis

A machine is down. Every minute it stays down, the plant is not producing — and
**the largest component of MTTR is usually not the repair, it is working out what
is wrong.**

The technician has five sources of evidence available and time to assemble none
of them. That gap is this skill.

**Quick start**

```
→ Capture the event: asset, time down, symptom, fault codes
→ SAFETY FIRST: if there is a safety implication, that leads. Always
→ Pull the sensor window; read shapes, not just threshold breaches
→ Mine maintenance history and the free-text close-out notes
→ Read the photos; consult the manual's troubleshooting tree
→ Rank candidate causes: evidence, cheapest discriminating test, expected fix
→ Cite the specific prior work orders behind each candidate
→ Draft the PM interval change that would stop it recurring
→ Emit the downtime record for the next production report
```

---

## Safety leads. Always.

**Where a failure has a safety implication, surface it first — before any
diagnosis.** Never let a diagnostic suggestion precede a safety flag.

**Every diagnosis opens with this line, flagged or not:** *"Follow your plant's
lockout procedure before anyone works on this machine. This is not a safety
assessment."* A false flag never removes it, and no step sends anyone to the
machine above it.

A technician reading a ranked list of likely causes is already reaching for
tools. If the honest answer is "this guard is defeated" or "that is a stored
energy hazard," it has to arrive before the thing that sends them toward the
machine, not underneath it.

This is a done-when condition, and it is the one non-negotiable ordering rule in
the skill.

**What counts as a safety implication.** Set `safety_flagged: true` when the
evidence shows any of these, and write which one, with its evidence, in
`safety_reason`:

- a seized or locked rotating part: spindle, chuck, bar feeder, conveyor
- a defeated, bypassed or failed guard or interlock
- stored energy: springs, counterweights, a part under load, a raised axis
- hydraulic or pneumatic pressure that has to be bled before work
- an electrical fault: a trip, a burnt smell, exposed or damaged wiring
- a fault that was cleared by restarting rather than fixed (*"ran off and
  restarted"*), now repeating

When none of these is shown, the flag is false and `safety_reason` says *"none
of the safety triggers shown"*. Never set the flag on a feeling, and never leave it off
because the diagnosis is uncertain: an uncertain stored-energy hazard is a
safety implication.

---

## Inputs

**First, find the plant setup:** from the task's own folder (never `cd` into the plugin), run
`python3 -I <this skill's folder>/../../shared/scripts/plant_setup.py find`, do its `setup_page_first` step, then read the profile at
`profile_path` and any rate at `rates_path`, per `../../shared/replies.md`.

| Input | Source | Form |
|---|---|---|
| The breakdown event | User report, or a maintenance work order | Conversation / CMMS connector or maintenance export |
| Asset record and specs | CMMS | CMMS connector, else the asset register export |
| Maintenance history and close-out notes | CMMS | CMMS connector, else the maintenance export |
| Current PM plan for the asset | CMMS | CMMS connector |
| Sensor window around the failure | Historian export to M365, scheduled or on-demand | CSV |
| Technician photos | M365, or uploaded in conversation | Images |
| Manufacturer's manual | M365 document library | PDF |
| Production context — what was running | `data-consolidate` output, or a direct MES export | `../../shared/contracts/consolidated-dataset.md` |

---

## Workflow

### Step 1 — Capture the event

Asset, time it went down, the symptom as the technician describes it, and any
fault codes the machine is showing. Take their words; do not translate a symptom
into a cause at capture.

### Step 2 — Pull the sensor window

A configurable period before the failure. **Read excursions, trends and step
changes, not just threshold breaches** — a vibration reading that climbed for six
hours without ever crossing its alarm limit is a bearing failing in plain sight.

Verify the window covers the event. If it does not, say so and do not reason
from adjacent data as if it were the event.

### Step 3 — Mine the maintenance history and close-out notes

Weight recency and symptom similarity. Search this asset, **then siblings of the
same model** — a new machine with no history is not a dead end.

**Run both searches as queries, in code, and keep what they returned.** One
filter on this asset's ID, one across every asset of the same model on the
symptom's own words. The work orders each query returned go into the figures
block (`../../shared/computed-figures.md`) by number. "This asset has eleven
prior records" and "the sister machine has no bearing history" are both claims
about a query result, and both have been wrong when written from memory: a
count is printed from the filter, and an absence names the filter that came
back empty.

**Then run the template check, every time, before any note is cited.** Group
every close-out note in the history by its exact text, and for each group count
the distinct assets and the distinct makes and models it appears on. The model
comes from the asset name where the asset record has no model column, and the
output says so. The grouped result goes in the figures block. Then:

- **Same text on assets of different makes** is a template — a default the
  technician clicked, not an observation about this machine. It is **shown**,
  labelled *"same text on N assets — not specific to this machine"*, may be
  mentioned as a fleet-wide pattern, and is **never cited as this machine's
  evidence** for any candidate.
- **The same failure recurring on siblings of the same model** is exactly what
  the sibling search is for: cite it as a fleet pattern for that model, with
  the work orders named.
- A note that appears once is this asset's evidence, and is cited.

Skipping this check is how two runs on the same data cite two different sets
of work orders. With it, the cited set is a function of the data.

The free-text close-out notes are the highest-value input here and the least used
anywhere. Read `reference/evidence-sources.md` for how to mine them and how to
report their coverage honestly.

### Step 4 — Read the photos

Visible damage, leaks, wear, part numbers on the failed component, readings on
the machine's own display. Describe what is visible; **never assert a diagnosis
from an unclear image.**

### Step 5 — Consult the manual

Match the fault code and symptom to the manufacturer's troubleshooting tree, and
cite the page. A manufacturer's stated tolerance beats an inference.

### Step 6 — Rank candidate causes

Ordered by likelihood. Each one carries three things:

1. **The evidence supporting it**, from the sources above
2. **What to check first** — the cheapest and fastest test that would
   discriminate between this candidate and the next one
3. **The expected fix**, and the repair path

That second item is the one that saves time. Ranking three causes is useful;
naming the five-minute check that eliminates two of them is what shortens MTTR.

**Every candidate is written under the same three sub-headings, in this
order: Evidence / First check / Expected fix and repair path.** Fixed
headings, every candidate, including the leading one. A candidate whose
Expected fix is missing shows an empty heading, which a reader can see; the
rerun found the leading candidate silently lacking one while candidate 2 had
it, and a fixed shape is what stops that.

### Step 7 — Cite the specific prior work orders

Behind each candidate, the actual work order numbers and close-out notes, so the
technician can read what was done last time rather than taking a ranked list on
trust.

**A candidate with no citation is a guess and is labelled as one.** Not omitted —
an experienced hunch is worth stating — but marked as reasoning rather than
evidence.

### Step 8 — Propose the PM plan adjustment

Once a diagnosis lands, the specific interval or procedure change for **that
asset and that failure mode**, drafted for the maintenance planner.

If a bearing failed from misalignment at 1,400 hours, the interval or the
procedure should probably change. This almost never happens today, because the
person diagnosing is not the person who owns the PM schedule. Closing that loop
is the reactive-to-proactive step and it is core behaviour, not an extra.

**Without the current PM plan** this degrades to a recommendation that first asks
what today's interval is. The step stays either way.

**Pricing the stoppage.** Where someone asks what the downtime cost, resolve
the downtime cost per hour per `../../shared/secret-config.md`, *Resolving a
rate* — `MFG_DOWNTIME_COST_PER_HOUR` if set, then a confirmed rate in the plant
profile, then a placeholder there, labelled — multiply hours by it, and show it
as an internal figure with its source. Where neither route holds one, report
minutes and hours, name the rate and both ways to set it, and stop — see Edge
cases. Never reach for an industry figure.

### Step 9 — Batch mode: the bad actor ranking

Run across all assets instead of one incident, ranked by total downtime minutes
**and** by failure frequency. A different question from "what is wrong with this
machine right now," which is why it is a mode here rather than a separate report.

Read `reference/bad-actor-mode.md`.

---

## Approval gates

**Everything this skill produces is a draft the technician or planner applies.**
Nothing is written back to any system of record.

A CMMS connector's write scope is not assumed — Limble's, the worked example,
is not confirmed in its public setup guide — so this is designed for read-only and treats write as an
upgrade rather than an assumption. Concretely:

- **Never update a maintenance ticket automatically.** The diagnosis is output
  the technician applies.
- **Asked to close out or update the ticket, write the close-out note as a
  labelled draft.** Say it never writes to a system of record — and, where
  no CMMS connector is live, say that too — then **produce the note itself**:
  what was found, what was done, what to watch, in the words a technician
  would put in the close-out field. "Paste it into the ticket if it is right"
  with nothing to paste hands the work back. Never offer to close it later.
  Per `../../shared/command-center.md`.
- **The PM adjustment is a draft for the planner**, who owns that schedule.
- **The diagnosis stays advisory** until a technician confirms it. Its downtime
  record carries that state explicitly, so the production report cannot present
  an unconfirmed cause as established.

---

## Output

**Every document this skill produces is printed in the reply, in full.**
Saving a copy to a file as well is fine, as Word or Excel per `../../shared/replies.md`, never `.txt`; a file *instead of* the reply is not.
The person reads the reply, and every delimited block and outbound check lives
in it — a document only on disk has been neither seen nor checked.
**A record handed to another skill is saved and summarised, never pasted as
raw YAML**; memory blocks are written where the plant's memory lives; and the
name on an approval is asked, never taken from the account. All three per
`../../shared/replies.md`.

**Ranked candidate causes** — evidence, what to check first, expected fix,
repair path.

**Cited history** — the specific prior work orders and close-out notes behind
each candidate.

**Sensor observation summary** — what the data showed in the failure window,
plainly stated, including when it showed nothing.

**The figures block** — required whenever the output states a count, a
duration, a ratio or an absence. Every record count, every "N of M notes were
usable," and every "no history found" appears here with the query behind it,
and the prose quotes it. Per `../../shared/computed-figures.md`. An absence
found by a document search is reported as *not found by search*, never as *does
not exist*.

**PM plan adjustment proposal** — drafted for the planner.

**The downtime record** — per `../../shared/contracts/downtime-record.md`, in
exactly the shape `daily-production-report` consumes with no transformation
between. Note in particular that an ongoing outage carries a null duration
rather than zero, and that `safety_flagged` travels with it.

**Bad actor ranking** — in batch mode.

**The Operations command-center page, maintenance section** — the diagnosis
and its current status, produced as an artifact you place. Nothing is written
to a system. Read `../../shared/command-center.md`. Chain 4's other half,
folding the diagnosis into the next production report's downtime log, happens
on `daily-production-report`'s side of the handoff.

Rendered in the house artifact style (`../../shared/artifact-style.md`) when the
output is something the technician will refer back to.

---

## Edge cases and failure modes

- **No sensor data for this asset** — very common; most assets are not
  instrumented. Proceed on history, notes, photos and the manual, and say clearly
  that sensor evidence was unavailable. This is the normal run, not a degraded one.
- **The sensor export does not cover the failure window** — say so. Do not reason
  from adjacent data.
- **A new asset with no history** — fall back to the manual and to sibling assets
  of the same model. State which.
- **Close-out notes are terse or useless** — "fixed," "repaired," "OK now."
  Report the coverage honestly rather than over-reading them.
- **Photos are ambiguous** — describe what is visible and name what cannot be
  told apart from the image.
- **A safety-critical failure** — the safety implication leads, before any
  diagnosis.
- **Evidence supports two candidates equally** — present both. Do not break the
  tie artificially.
- **Asked what the downtime has cost, with no rate on file** — say the rate is
  not set in either route, name `MFG_DOWNTIME_COST_PER_HOUR` and the plant
  profile ("update our downtime cost"), and report the downtime in
  minutes and hours. **No dollar-per-hour figure of any kind appears**: not a
  typical one, not a range, not an example of what *not* to use. A benchmark
  named in order to reject it is still the number that gets used. Per
  `../../shared/secret-config.md`.

---

## Degradation

**If no CMMS connector is live** (the default: Limble and other CMMS
systems are added through `custom-connector`) — this is the skill most affected.
Without Limble or any CMMS connector, it reads the maintenance export.

**What is lost:** live asset records, open maintenance work orders, and the
current PM plan.

**What survives, and it is the important part:** maintenance history including
the free-text close-out notes, because those are a field on the work order record
and export cleanly. The notes are the highest-value input in the skill, so its
core reasoning is intact.

**What actually changes is freshness.** A breakdown is a real-time event and a
nightly export is not. Diagnosing a machine that went down twenty minutes ago
means the most recent — and often most relevant — tickets are not in the data
yet. Say so rather than letting the history look current.

**Three mitigations, all built, because any one recovers most of the value:**

1. An **on-demand export** the technician can trigger before the run.
2. **Pasted or uploaded work orders** for that asset.
3. A **spoken description of recent work** in conversation. "We were in there
   last Tuesday for the same thing" is real evidence.

The PM adjustment step degrades to a recommendation that first asks what the
current interval is. It stays in the skill either way.

---

## Chain position

**Chain 4, Breakdown to next report** — step 1, feeding
`daily-production-report`. The chain pauses at step 4 by nature, because that
step is a human working a physical machine, and the diagnosis is advisory
throughout.

**Metric.** Mean time to repair.

---

## Reference files

| File | Load when |
|---|---|
| `reference/evidence-sources.md` | Steps 2 to 5 — the five sources, how to read each, and the citation rule |
| `reference/bad-actor-mode.md` | Step 9 — the batch ranking and its coverage traps |
| `../../shared/computed-figures.md` | Step 3 and on emit — the figures block, and how to state an absence |
| `../../shared/contracts/downtime-record.md` | On emit — the exact shape `daily-production-report` consumes |
