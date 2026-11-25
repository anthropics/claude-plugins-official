# Time alignment — the highest-risk failure mode in the skill

Getting the timeline right is most of the work in a root cause investigation,
and getting it wrong produces a **spurious correlation stated confidently**,
which is worse than producing nothing.

This is the highest-risk correctness issue in the whole plugin, alongside
shift boundaries. Treat it that way.

---

## Why it goes wrong

Four systems recording the same event will disagree about when it happened:

| Source | How it usually records time |
|---|---|
| The historian | Often UTC, often zone-naive, sampled at high frequency |
| The MES | Usually local plant time, attributed to a shift rather than a clock |
| The ERP | Local, but posted at transaction time rather than event time |
| The maintenance system | Whenever the technician got round to entering it, which may be hours later or the next morning |

None of them is wrong. They are answering different questions. But laid on one
timeline without reconciliation, a bearing that failed at 14:10 sits next to a
tolerance excursion at 18:10 and the four-hour gap disappears into a confident
sentence about causation.

**A one-hour daylight-saving offset is the classic version of this**, and it is
invisible for exactly half the year.

---

## What `onboarding` already established

Read from the `## Plant context` block rather than asking again:

- **Per-source timezone**, and whether that source's timestamps are zone-aware
  or naive
- **The production-day boundary** and the cross-midnight attribution rule
- **The observed clock skew** from the offset self-check — `onboarding`
  cross-correlates a single event recorded in two systems and reports the
  measured difference

That last one is the useful one. A declared configuration is what somebody
believes; the self-check result is what the clocks actually did.

---

## Verify, then correlate

**Verify alignment before running any pattern check**, and report the result as
part of the evidence appendix rather than as an assumption:

1. Convert every source onto one zone-aware timeline. Name the zone in the
   output.
2. Apply the known per-source offset from the self-check.
3. Find at least one event visible in two sources and confirm they now agree.
   A production stop appearing in both the MES export and the historian is the
   usual anchor.
4. State the residual uncertainty. "Aligned to within about two minutes" is a
   useful statement. "Aligned" on its own is not.

---

## Misalignment blocks correlation

**When alignment cannot be verified, refuse to correlate.** Do not fall back to
approximate matching and do not soften it with a hedge.

Report what is known, which is often still a great deal:

> *"I can't correlate the spindle-load trace to the inspection results. The
> historian export carries naive timestamps and this plant's context block
> records a 47-minute skew between the historian and the MES that has not been
> re-checked since the export path changed in July. A 47-minute error is larger
> than the window I'd be reasoning inside, so any correlation I drew would be
> unsafe.*
>
> *What I can still tell you: the lot clustering holds regardless of timing —
> all 14 failures trace to LOT-77219 and none to LOT-77188. That analysis does
> not depend on the clocks."*

That answer is more useful than a correlation, because it says which conclusions
survive and which do not.

---

## Shift boundaries are part of this

A cross-midnight shift belongs to one production day, and which one is a
per-plant rule captured during `onboarding`.

Get it wrong and clustering by shift silently inverts: night-shift events land
on the wrong day, and the pattern check reports a difference between shifts that
is really a difference in bookkeeping. **State the boundary rule in the evidence
appendix**, so the quality manager can check it against what they know.

---

## An observed skew is itself a finding

If the alignment check turns up a drift nobody knew about, that is worth
reporting to their IT independently of this investigation. A historian running
several minutes off has been quietly corrupting every correlation anyone has
drawn from it, including the ones drawn by hand in spreadsheets.
