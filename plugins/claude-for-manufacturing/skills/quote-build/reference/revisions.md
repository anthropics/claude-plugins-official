# The negotiation loop

**Most of an estimator's time goes into revisions, not first drafts.** That is
why this is core behaviour rather than a follow-up feature.

---

## A counter is not a new quote

When a customer comes back — "can you do better at 1,000?", "we need it two
weeks earlier", "drop the anodize" — **revise the existing quote in place and
preserve a change record.**

Treating a counter as a fresh quote is how a plant ends up with four versions in
circulation, no record of what was conceded, and two people quoting the same job
to the same customer at different prices. It happens constantly, and it is
entirely a bookkeeping failure.

---

## What the change record holds

Per revision:

| | |
|---|---|
| Revision number and date | Sequential, on one quote, not a new reference |
| What the customer asked for | In their words |
| What changed in the quote | Line by line, old value to new value |
| **Why it changed** | The reason, not just the delta |
| What did not change, and was asked about | The concessions that were declined |

**That "why" column is the one that matters.** Six months later somebody needs
to know whether the price dropped because the quantity went up, because a
material price was re-checked and had fallen, or because somebody gave away four
points of margin to win the job. Those are three completely different facts and
only one of them is repeatable.

**Record what was declined, too.** A customer who asked for 60-day terms and did
not get them will ask again on the next order, and the estimator should walk in
knowing that.

---

## Re-derive, do not patch

When a parameter changes, **re-run the affected buildup lines rather than
adjusting the total.**

A quantity change means setup re-amortizes across the new quantity. A material
change means a new price at a new date, a new scrap allowance, and possibly a
new routing. Patching a total by hand loses that and produces a quote whose
cost-basis sheet no longer reconciles with its own front page — which is exactly
the document the estimator was going to defend to their manager.

Re-derive, then show the diff against the prior revision.

**Re-derive from the stored operation record** (`hours-ladder.md`, *The
operation record*): the rung, path, setup and run per operation as priced. A
quantity change re-amortizes setup from it; a price counter re-prices from it.
**A price counter never reopens CAD** and never re-runs the hours step —
nothing about the part changed.

**A drawing revision is not a counter.** A new revision can change what every
operation cuts, so it goes back to `rfq-to-quote` step 7 for a new geometry
estimate and a new Gate 3, and the hours are derived again. Pricing a new
revision on the old revision's hours is the same mistake as pricing it on a
superseded routing.

---

## Margin concessions are shown, never absorbed

If the revision is a price drop with no change in scope, then **margin moved**,
and the change record says so explicitly with the before and after.

The temptation is to present a lower price as though something in the cost
changed. It did not. An estimator needs to see the margin line move so they know
how much room is left before the next round, and a manager needs to see it to
know what the job is actually worth.

---

## Watch for scope creeping in with the counter

Customers frequently bundle a scope change into what sounds like a price
negotiation. *"Can you do $3.80? And we'd need the first article two weeks
earlier."*

**Separate those.** Price the scope change as a scope change, show it as its own
line in the revision, and let the estimator decide whether it is a concession or
a new requirement. A scope change absorbed silently into a price negotiation is
how margin disappears without anyone being able to point at where.

---

## Every revision goes through the gate

A revision is a customer-facing document like any other. It is drafted, shown
with its diff, and **released by the estimator.** Nothing goes out because it is
the second version of something already approved.
