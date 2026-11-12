# Batch mode — the bad actor ranking

A different question from the rest of the skill, which is why it is a **mode of
this skill rather than a separate report**.

| Normal mode asks | Batch mode asks |
|---|---|
| What is wrong with this machine, right now? | Which machines are hurting us most, over time? |
| One asset, deep | Every asset, ranked |
| Read by a technician holding a wrench | Read by a maintenance manager holding a budget |

**A "bad actor" is the asset causing the most downtime.** The ranked list of them
is what maintenance managers actually use to decide where to spend — on a rebuild,
a replacement, a PM overhaul, or a spare nobody currently stocks.

---

## Rank both ways, always

Exactly as `daily-production-report` ranks its downtime log, and for the same
reason: **by total downtime minutes, and by failure frequency.**

These identify different problems and the fixes are different:

- **High minutes, low frequency** — one or two catastrophic failures. Points at a
  major component, a rebuild, or a spare that should be on the shelf.
- **High frequency, low minutes** — chronic small stoppages. Usually the more
  fixable of the two, often a PM interval, an adjustment, or a design issue that
  everyone has learned to live with.
- **High on both** — the genuine bad actor, and the easy decision.

A single ranking hides whichever problem it does not sort by, and the chronic
one is the one that hides, because forty six-minute stoppages disappear next to
one eight-hour outage.

---

## What each row carries

| Column | Notes |
|---|---|
| Asset, in the plant's own vocabulary | Per the `## Plant context` block |
| Total downtime minutes | Over a stated window |
| Failure count | Over the same window |
| MTTR | Mean time from down to running again |
| Most common reason code | And the share of events it accounts for |
| Recurring theme from close-out notes | Where the notes support one. This is the differentiated column |
| History coverage | See below |

That close-out-notes column is what makes this more than a pivot table. A
ranking that says "spindle motor, 412 minutes, 6 events" is a spreadsheet. One
that adds *"four of six close-out notes mention coupling alignment"* is a
recommendation.

---

## Coverage honesty

Three ways this ranking lies if you let it.

**An asset with no history is not a good actor.** It is unreported. Do not let a
machine with no maintenance records sit at the bottom of the ranking implying
reliability. List unreported assets separately and say so, per
`../../../shared/absent-is-not-zero.md`.

**State the window, and check every asset has data across all of it.** An asset
commissioned two months into a twelve-month window will look better than it is.
Report its actual coverage rather than its apparent total.

**Reason code coverage is a finding of its own.** Where stoppages are heavily
coded "Other," the ranking by reason is not trustworthy and the report says so.
That gap is itself worth fixing and nobody has ever mentioned it to them.

---

## Requirements and degradation

Needs maintenance history across the asset base rather than for one machine.

| Available | Behavior |
|---|---|
| Live maintenance history for all assets | Full ranking |
| Exported maintenance history | Full ranking, at the export's freshness, stated |
| Partial asset coverage | Rank what is covered, list what is not, never imply the uncovered are clean |
| No maintenance history | Say the ranking cannot be produced and what would be needed. Do not substitute the downtime log alone, which describes stoppages rather than assets |

That last row is worth holding to. Downtime events and maintenance history
answer different questions, and a ranking built only from stoppages misses every
failure that was caught before it stopped the machine — which is exactly the
population a good PM programme creates.
