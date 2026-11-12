# OEE — the three components and the traps

Load this before computing anything.

**OEE is the number everyone in operations knows by heart.** A plant reporting
60–70% is normal; 85% is world-class. That familiarity is exactly why a wrong OEE
destroys trust in the whole report — a supervisor who sees 91% on a bad week
stops reading.

```
OEE = Availability × Performance × Quality
```

---

## Never report the composite alone

**Always show the three components separately.** This is a done-when condition,
not a presentation preference.

An OEE of 62% caused by availability is a maintenance problem. The same 62%
caused by quality is a completely different meeting with different people in it.
The composite tells a plant manager the day was bad; the components tell them who
to call.

---

## Availability

```
Availability = run time / planned production time
```

**Planned production time is a configured definition, not a derivation.**
`onboarding` captures it per site: scheduled shift hours minus whatever that plant
excludes — planned maintenance windows, breaks, scheduled changeovers. Read it
from the `## Plant context` block and **state the definition in the report**, because
two plants computing availability against different denominators are not
comparable and neither is one plant before and after a definition change.

### Four denominator traps

**Unscheduled overtime.** A machine that ran hours it was never scheduled for can
produce run time exceeding planned production time, and availability above 100%.
**Report it; do not clamp it to 100%.** An availability of 118% is a finding
about the schedule definition, and silently capping it hides both the overtime
and the definitional problem.

**Cross-midnight shifts.** A three-shift plant has a shift that starts on one
calendar day and ends on the next. The `production_day` attribution rule is
configured per site — the day the shift started, or the day it ended — and the
report states which convention is in use. Getting it wrong moves a whole shift of
output to the wrong day, which makes one day look bad and the next look good.

**Planned downtime counted as downtime.** A scheduled PM window is excluded from
the denominator, not counted as a stoppage. Counting it as unavailability
punishes a plant for doing maintenance correctly.

**A machine idle because there was nothing to run.** This is real, common, and
not a maintenance problem. Whether the plant excludes no-demand time from planned
production time is their definitional choice, captured at onboarding. Do not
decide it here.

---

## Performance

```
Performance = (ideal cycle time × total count) / run time
```

Ideal cycle time comes from the routing's standard time for the operation.
Where a plant's routing standards are stale or absent, **performance cannot be
computed** — see the rule below.

Performance above 100% means the part ran faster than its standard, which
usually means the standard is wrong rather than the machine being miraculous.
Report it as a finding about the standard.

---

## Quality

```
Quality = good count / total count
```

Total count is good plus scrap plus rework, per the plant's own convention.
**Rework is the ambiguous one** — a part reworked into conformance was not made
right the first time, so first-pass yield excludes it. State which convention was
used, on every run, as one line under the table:

- Export has a rework column → *quality = good ÷ (good + scrap + rework),
  first-pass yield.*
- Export has no rework column → *quality = good ÷ (good + scrap); no rework
  column, so first-pass yield could not be applied.*

The caveat belongs to the second case only. Printing "no rework column"
against an export that has one is a false statement about the plant's data.

---

## The rule that matters most: never substitute 1.0 for a missing component

If a component cannot be computed, **report the components you have and say the
composite is unavailable.** Do not multiply by 1.0 in place of the missing one.

This is `../../../shared/absent-is-not-zero.md` applied to the most-watched number
in the plant, and it fails in the flattering direction. A plant with no routing
standards, whose performance is therefore unknown, would report:

```
Availability 0.78 × Performance [unknown as 1.0] × Quality 0.96 = 75%
```

That 75% looks like a decent day and it is arithmetic on a value nobody measured.
Real performance of 0.71 would have made it 53%. **Absent is not zero, and absent
is also not one hundred percent.**

The honest output:

> *"Availability 78%, quality 96%. Performance can't be computed — the routing
> standards for these parts aren't in the dataset, so there's no ideal cycle time
> to compare against. Composite OEE is unavailable until those land."*

---

## Grain

Compute per asset or per line, and **state which**. An OEE averaged across a cell
of five machines hides the one machine causing the problem, which is usually the
entire point of looking.

Where the plant's vocabulary calls it a cell, a line or a work center, use their
word, per the `## Plant context` block.

---

## Sanity checks before reporting

| Check | If it fails |
|---|---|
| Each component within 0–100% | Report the value and the likely denominator cause. Never clamp |
| Composite within 0–100% | Follows from the components; a composite outside range means one is wrong |
| Total count equals good plus scrap plus rework | Report the discrepancy; it means two sources disagree |
| Run time not greater than planned production time | Usually unscheduled overtime. Report it |
| Every asset in the plan appears in the output | A missing asset is not a 0% asset. Name it as not reported |

That last row is the one most likely to be got wrong. **A machine with no data is
not a machine at 0% OEE.** It drags a plant average down and invents a
maintenance crisis. Report it as unreported and exclude it from the average,
saying so.
