---
name: breakdown-to-next-report
description: "Runs the chain from a machine going down to the diagnosis landing in tomorrow's production report: reads the sensor window, the maintenance history and its free-text close-out notes, technician photographs and the manufacturer's manual together, ranks likely causes with the cheapest test that tells them apart, then folds the diagnosis and its downtime into the next morning's downtime log and exceptions. Use when someone says \"run the breakdown chain,\" \"a machine went down,\" \"diagnose this and get it into the report,\" or \"breakdown to next report.\""
compatibility: "Requires none. Chains breakdown-diagnosis and daily-production-report. Reads a CMMS connector (Limble is the worked example) for assets, history and PM plans when connected, plus a historian export and uploaded photos. Runs with no sensor data and no connector at all. Safety implications surface before any diagnosis. The diagnosis is advisory throughout and is never written back to a ticket."
---

# Breakdown to Next Report

Chain 4. `breakdown-diagnosis` → `daily-production-report`.

Every minute a machine is down, the plant is not producing. The largest
component of MTTR is usually not the repair; it is working out what is actually
wrong. This chain does that part, then makes sure the answer does not evaporate
before the morning meeting.

**Quick start**

```
→ Capture the event: asset, time down, symptom, fault codes
→ SAFETY FIRST. Any safety implication surfaces before any diagnosis. Always
→ Read sensor window, maintenance history, close-out notes, photos, the manual
→ Rank causes. Each CITES specific prior work orders. No citation means a guess
→ The technician works the list. The chain pauses here by nature
→ The diagnosis and its downtime land in the next report's log and exceptions
```

---

## Inputs

| Input | Source | Form |
|---|---|---|
| The breakdown event | A user report, or a maintenance work order | Conversation, CMMS connector or maintenance export |
| Sensor window around the failure | Historian export, scheduled or on demand | CSV |
| Technician photos | Uploaded, or M365 | Images |
| Everything else | Whatever the two member skills read | See each skill |

---

## The five steps

**1. A machine goes down.**

**2. Read the evidence together** — the recent sensor window, the maintenance
history including its free-text close-out notes, the technician's photographs,
and the manufacturer's manual. The close-out notes are the highest-signal input
and the least used: what the technician actually wrote about what they found,
in prose, which nobody ever aggregates.

**3. Rank the likely causes**, each with the evidence supporting it, **the
cheapest and fastest test that tells it apart from the others**, and the
expected fix. Every candidate cites the specific prior work orders behind it,
so the technician can read what was actually done last time. A candidate with
no citation is a guess and is labelled as one.

**4. The technician works the list.** The chain pauses here by nature: this is
a person at a physical machine.

**5. The diagnosis and the resulting downtime feed into the next production
report's downtime log and exceptions**, through `daily-production-report`.

**State the match rule, and say the stoppage was counted once.** The
diagnosis record and the MES downtime row describe the same stoppage. The
chain matches them on **asset plus start time** — same `asset_id`, and
`started_at` within the same shift — and the report carries one row for the
stoppage, with the diagnosis fields attached to it. Two required lines in the
output: *"Matched the diagnosis record to MES row <asset, started_at> on asset
plus start time"* and *"counted once."* Where no MES row matches, say that,
and the diagnosis record stands alone as the row. Flagging the possible
double count without stating the rule leaves the reader to reconcile it.

---

## Approval gates

**Step 4 is the pause, and it is not a gate the plugin enforces** — it is a
human working a machine. The chain simply has nothing to do until they are
done.

**Say whether step 4 happened.** The record carries `technician_step`:
`confirmed` when the technician came back with a confirmed or corrected cause,
`pending` while the chain waits, `skipped` when the record was folded in with
no technician step (a test, a demo, or "put it in the report now"). The output
states it in one line, and the report carries it beside the cause: *"cause
proposed, technician step skipped"* reads differently from *"cause proposed,
technician still working"*.

**The diagnosis is advisory throughout.** A CMMS connector's write scope for
closing or updating work orders is unconfirmed (Limble's is not public), so the output is a draft the technician
applies, never an automatic ticket update. Nothing here writes to a system.

**Safety outranks the sequence.** Where a failure has a safety implication, it
surfaces **first**, before any diagnosis. Never let a diagnosis suggestion
precede a safety flag.

---

## The handoff is the chain's whole risk

`breakdown-diagnosis` emits a downtime record in **exactly** the shape
`daily-production-report` consumes, with **no transformation step in between**.

The reason is specific: the report already reads downtime events from the MES
or historian export. A record arriving from a diagnosis is a **row in that same
log**, not a separate feed. If the two shapes differ, the report has to
reconcile them, and a reconciliation step between two sources of downtime is
exactly how a stoppage gets counted twice or dropped.

Read `../../shared/contracts/downtime-record.md`.

Two fields carry weight across the handoff. `safety_flagged` is required, and a
missing value is treated as unknown rather than false. `duration_minutes` is
null while the machine is still down and **never zero**, because a zero would
rank an ongoing outage last in a log sorted by minutes.

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

The ranked candidate causes with their evidence and discriminating tests, the
cited history behind each, a plain statement of what the sensor data showed,
the PM plan adjustment drafted for the planner, and the structured downtime
record that flows into the next report.

**The figures block** — required. How many maintenance records the asset has,
how many carried usable notes, how many downtime events and minutes: each is
printed from a query run in this session, listed with that query, and quoted by
the prose rather than retyped. A chain summary is where a count most often
drifts from the step that produced it. Per
`../../shared/computed-figures.md`.

**The Operations command-center page, maintenance section** — an artifact you
place. Read `../../shared/command-center.md`.

---

## Edge cases and failure modes

- **No sensor data for this asset** — very common, most machines are not
  instrumented. Proceed on history, notes, photos and the manual, and say
  clearly that sensor evidence was unavailable.
- **A new machine with no history** — fall back to the manual and to sibling
  assets of the same model.
- **Close-out notes are terse or useless** — report the coverage honestly
  rather than over-reading "fixed."
- **Photos are ambiguous** — describe what is visible. Do not assert a
  diagnosis from an unclear image.
- **The machine is still down when the report runs** — the record carries a
  null duration, leads the exceptions, and is excluded from the minutes ranking
  with that exclusion stated.

---

## Degradation

| Not available | What happens |
|---|---|
| The historian export | Run on history, notes, photos and the manual. Say sensor evidence was unavailable |
| The current PM plan | The PM-plan-adjustment step degrades to a recommendation that first asks what today's interval is. **The step stays either way** |
| **A CMMS connector** (Limble or any other) | See below |

**Check the freshness of anything export-sourced, and say it.** A scheduled
export that silently stopped is the normal failure here, and a diagnosis built
on a stale sensor window or stale history reads exactly like one built on
current data. Name the age of each source in the output.

**If Limble isn't included, or no CMMS connector is live** — the
default — this is the chain that changes most. It still
runs end to end: step 2 reads maintenance history from a scheduled export
rather than live tickets, and everything downstream is unchanged. What is lost
is the chain's real-time character. A breakdown is happening *now* and a nightly
export is not, so the tickets closest to the event are exactly the ones
missing.

**Any of three mitigations satisfies step 2**, and all three are cheap: an
on-demand export the technician triggers, pasted or uploaded work orders for
that asset, or the technician simply describing recent work in conversation.
Build the chain so any one of them is enough.

---

## Chain position

**This is Chain 4 itself.** Members: `breakdown-diagnosis`,
`daily-production-report`.

**Metric.** MTTR, owned by `breakdown-diagnosis`. Downtime cost visibility,
owned by `daily-production-report`, which prices downtime against the
configured cost-per-hour on every run.

---

## Reference files

| File | Load when |
|---|---|
| `../breakdown-diagnosis/SKILL.md` | Steps 2 and 3, and the bad-actor batch mode |
| `../daily-production-report/SKILL.md` | Step 5 |
| `../../shared/contracts/downtime-record.md` | The handoff — the shape that must not be transformed |
| `../../shared/command-center.md` | The Operations page, and why it is never a write |
| `../../shared/computed-figures.md` | Before stating any count — the figures block |
