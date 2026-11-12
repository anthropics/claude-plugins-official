# The sensitivity analysis — the most valuable part, and the most skipped

**This runs every time. It is never optional**, regardless of how confident
the ranking looks or how much time is left before the review.

---

## Why weights deserve suspicion

A weighted total looks objective. It is arithmetic on numbers someone
typed in, and one of the inputs — the weights — is a judgment call dressed
up as a fact. Somebody in a room decided cost was 30% and weight was 25%,
and a different reasonable person in the same room might have said 28 and
27.

**If the ranking only holds at exactly the weights as typed, it isn't a
finding. It's an artifact of where the sliders happened to sit.** The
sensitivity analysis is what tells the difference apart.

---

## What to compute

Vary the weights across a plausible range — not the full space of every
mathematically possible combination, but the range a reasonable reviewer
would actually consider — and answer four questions:

### 1. Does the winner change?

Recompute the ranking at each weighting in the range. If the same option
wins throughout, that is a strong, defensible recommendation and the memo
should say so plainly.

### 2. At what weighting does it flip?

Where the winner does change, **name the specific weighting where it
flips** — not "the ranking is sensitive to weighting" as a vague caveat,
but the actual numbers.

> *"Option A wins at the stated weighting — cost 30%, mass 25%. It also
> wins everywhere cost stays above 27%. Below that, Option B takes it. The
> two are separated by 0.03 on the weighted total at the stated weighting,
> which is inside the flip zone, not clear of it."*

That is a materially more useful statement than "Option A wins, 6.8 to
6.5." The second number tells a reviewer nothing about how much to trust
the first.

### 3. Which criterion is the decision actually sensitive to?

Some criteria can move a wide range without changing the outcome. One
often decides everything. **Name it.** A decision that rests entirely on
the cost weighting is a different conversation from one that rests on
manufacturability, even if both currently point to the same option.

### 4. Is there an option that never wins under any plausible weighting?

**Say so.** An option that loses across the entire plausible range isn't a
close alternative — it's not actually in contention, and the memo can
recommend dropping it from further consideration rather than carrying it
forward as a hedge.

---

## When two options are within noise

Where the weighted totals sit closer together than the scores' own
precision justifies — a 6.8 against a 6.7 built from inputs good to one
decimal place — **say so explicitly rather than presenting a false
winner.**

> *"Options B and C separate by 0.1 on a scale where the individual scores
> are only confident to about 0.3. That is not a distinguishable result.
> The recommendation below is based on [stated reason beyond the score],
> not on B's marginally higher total."*

A ranked table with two rows that differ inside their own noise floor is
technically ordered and practically meaningless, and presenting it as a
clean win is worse than saying it's a toss-up.

---

## Report the finding even when it's boring

A sensitivity analysis that comes back "stable across the whole plausible
range, no flip found" is not a wasted step. It's the evidence that makes
the recommendation strong, and it belongs in the memo with the same weight
as a finding that the decision is fragile. **The absence of sensitivity is
itself the finding**, and it's the one that lets a reviewer sign off
without re-running the numbers themselves.
