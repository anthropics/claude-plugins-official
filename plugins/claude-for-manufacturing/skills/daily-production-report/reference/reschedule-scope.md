# The reschedule proposal — and where it stops

Load this before proposing any schedule move.

---

## What this is not

**This is not finite-capacity scheduling.**

Producing an optimal shop schedule is a constraint-optimisation problem. A
language model asked to do it will return a plausible-looking schedule that
quietly violates constraints — and that is **worse than returning nothing**,
because a scheduler who accepts it discovers the violation on the floor, at
which point the report has actively caused a problem it was supposed to report.

So there is a hard line here, and it is drawn deliberately rather than
apologetically.

| Out of scope | In scope |
|---|---|
| Re-optimising the day | One or two specific moves |
| Sequencing every job across every cell | Moving one job, and tracing what that displaces |
| Balancing load across the plant | Naming what still misses its date after the move |
| Anything presented as optimal | Something presented as checked, with the checks listed |

---

## What a proposal must contain

Four parts. A proposal missing any of them is not actionable and should not be
offered.

1. **The move.** Specific: which job, from where, to where — and **the
   changeover it implies**: what the receiving cell was running before, and
   what switching it costs. A move that reads as free because nobody named
   the changeover is not a checked move.
2. **What it displaces.** Every job the move pushes, and where each one lands.
3. **What still misses.** After the move, which commitments are still not met.
   **A proposal that claims nothing misses is the one to distrust most.**
4. **What was checked, and what was not.** Explicitly. This is what lets a
   scheduler accept or reject without rebuilding the analysis.

An example, with the changeover made explicit:

> *"Run 4471 on cell B instead of cell A; cell B was running 4390's finishing
> pass, so this costs a changeover — call it 40 minutes on this tooling. That
> pushes 4402 to second shift, where it still makes its date; 4390 now misses
> by one day."*

Four clauses. One move with its changeover, one displacement with its
outcome, one casualty named. That is the whole deliverable. Where the
changeover cost genuinely can't be estimated, say that explicitly rather than
silently dropping it — it is degradation, per the table below, not omission.

---

## The honesty requirement

**State what was not checked.** A move traced through due dates but not through
tooling availability, operator certification, or material on hand is a partial
check, and saying so is what keeps it useful.

> *"Checked: due dates on the three affected jobs, and cell B's routing for 4471.
> Not checked: whether cell B has the fixture, whether second shift has a
> certified operator for 4402, and material availability. Worth confirming those
> before committing."*

A scheduler reading that knows exactly how much of their own judgment is still
required. A scheduler reading a bare proposal does not, and will either
over-trust it or ignore it.

---

## One or two moves, not a plan

Propose per significant exception, not for the day as a whole. Where three
exceptions each need a move and the moves interact, **say that they interact and
stop** rather than composing them into a schedule.

> *"These three exceptions all want cell B. Individually each move works; together
> they conflict, and untangling that is a scheduling decision rather than
> something I can check. Here are the three moves separately, with the conflict
> named."*

---

## Never applied

The proposal is **drafted for the scheduler**, never applied to any system. This
skill writes nothing to a system of record. It reports, prices, and proposes.

---

## Degradation

The proposal depends on the schedule export and on changeover or routing data.

| Available | Behavior |
|---|---|
| Schedule export and routing data | Propose the move, fully traced |
| Schedule export, no routing or changeover data | Propose the move; state that changeover time was not accounted for |
| Neither | **Report the exception with its impact on commitments and no proposed move — and say which** |

That last row is the important one. Per `../../../shared/absent-is-not-zero.md`,
the report says the move was not proposed because the schedule data was not
available. It does not silently omit the proposal, which reads as "nothing needed
to move."
