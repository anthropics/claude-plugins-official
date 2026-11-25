# The manufacturability check, then the recommendation

**The ordering is the point, twice over.** The constraint check runs *before*
the questions go out and *before* the bid/no-bid call — so a job that cannot be
built as specified is caught at intake rather than after somebody has spent
hours pricing it, and the plant never asks a customer five questions about a
part it physically cannot make.

---

## Why a no-bid is a win

Quoting is expensive — often hours of the most senior person in the department.
**Quoting a job you will lose, or one you should not want, is pure cost.**

Wrong material, a tolerance the plant has never held, a size outside the
envelope, an impossible date: each of those is a job that either does not get
won, or gets won and then loses money. A defensible no-bid returns those hours
to the RFQs that can be won.

---

## Step 1 — Check the request against what the plant can actually build

From the capability profile captured during `onboarding`: materials, processes,
size envelope, demonstrated tolerance capability, certifications held.

**Report each violated constraint specifically**, never as a general fail:

> *"True position of 0.0005 in on the 4x mounting holes is below this plant's
> demonstrated capability on 3-axis milling, which is 0.002 in. Everything else
> on this line — 6061-T6, the envelope, clear anodize — is within profile."*

That is a sentence an estimator can act on. They may know the plant can hold it
on a different machine, or that the customer will accept a deviation, or that
this is the reason to decline. **"Does not meet plant capability" tells them
none of that** and sends them back to work out which constraint failed.

---

## The hard-disqualifier stop

Some violations end the automated sequence at the check rather than feeding the
score: **wrong process entirely, outside the size envelope, a certification the
plant does not hold.** Return a no-bid recommendation with its specific reason,
before the questions are drafted.

Two limits, and both matter:

**It stops the sequence, not the inquiry.** The estimator can override and
proceed. The inquiry stays open, and nothing about it is cancelled or closed.

**Only violations determinable from stated facts qualify.** If the disqualifier
depends on a field that is missing, it is not a disqualifier — it is a scoring
input for the recommendation below. Stopping on a blank is guessing, and it
would stop the plant from asking the very question that resolves it.

Everything softer — a tight but achievable tolerance, an awkward material, a
date that looks difficult — carries forward as scoring input and does not stop
anything.

---

## Step 2 — Score the recommendation, provisionally

Three inputs, weighted by the estimator's own priorities where those are known:

**Capability**, from the profile — how far inside or outside the plant's
demonstrated envelope this sits.

**The constraint violations** from step 1 — how many, how severe, and whether
each has a plausible workaround.

**Actual cost on comparable prior jobs**, from closed work orders in the ERP (NetSuite or Infor M3).

### Actual cost, not standard cost

This distinction is deliberate and it matters.

Standard cost is what the job was *planned* to cost. Actual cost on a closed
work order is what it *did* cost, and **that is the number that says whether the
last job of this kind made money.** A part family that consistently runs 30%
over standard is one the plant loses money on every time it wins, and the
standard cost will never say so.

Cite the specific work orders, with their dates and what made each comparable.
Note how old they are — **a comparable from two years ago was priced in a
different material market**, and the estimator should weigh it accordingly.

---

### It never waits for the customer

The recommendation runs immediately on what is known. **Most RFQs arrive with at
least one gap**, so a recommendation that blocked until every answer came back
would stall on nearly all of them — and an inquiry sitting unscored for a week
is exactly the inquiry that joins the unbid book.

While questions are open, the recommendation is **provisional**, and it names
**which specific unanswered questions would change it**:

> *"Provisional bid. If the material is 4140 rather than 4130 this becomes a
> no-bid — we have never held this tolerance in 4140 on this process."*

That is what tells the estimator which answer to chase. A provisional
recommendation that does not name its own dependencies is just a recommendation
with a caveat, and the caveat does no work.

---

## Step 3 — Fold in answers, and handle silence

**An answer is new source material.** It re-enters extraction, carrying its own
source reference, and the recommendation re-scores on the fuller picture. It
revises the existing inquiry — it never opens a new one.

**Where an answer flips the recommendation, say so plainly and say why.** A
recommendation that silently reverses between two readings is worse than either
version of it, because it destroys the estimator's ability to trust either.

**Where no answer comes**, after the configured interval the inquiry surfaces as
**stale**, carrying its provisional recommendation and its still-open questions.

**Stale is a visibility change, never a status change.** The skill does not
cancel, decline, close or no-bid an inquiry because a customer went quiet. It
stays open and the decision stays the estimator's — they quote it with
exclusions, or they drop it deliberately. Both are decisions; aging out
silently is not, and it is the single most common way an RFQ joins the unbid
book.

---

## Step 4 — Recommend, never decide

The output is `bid` or `no_bid`, with reasoning that an estimator can read and
disagree with.

**The skill never asserts a no-bid as a decision.** It does not know about the
relationship with this customer, the strategic reason to take a marginal job, or
the conversation somebody had at a trade show last month. It knows what is in
the data, and the data is not all of it.

Constraint violations stay on their own list. A `bid` can still carry them.
That is a bid with reasoning, not a third recommendation.

---

## Two degradations that must be stated, not silent

**No capability profile** → the recommendation is **constraint-free and must say
so.** It cannot have checked manufacturability against a profile it did not
have, and an unqualified "bid" that never ran the check reads exactly like one
that passed it.

**No cost history** → the recommendation scores on **capability and dates
alone, and must say so.** Without closed work orders there is no comparable, and
without a comparable the commercial half of the judgment is missing.

Per `../../../shared/absent-is-not-zero.md`, a recommendation that does not name
what it could not check is the failure this rule exists to prevent — it is
confident in exactly the shape of a recommendation that checked everything.
