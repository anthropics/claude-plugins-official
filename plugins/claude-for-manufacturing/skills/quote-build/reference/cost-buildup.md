# The cost buildup

**"Cost basis shown" is the whole point of this skill.**

An estimator will not trust — and cannot defend to a customer — a number with no
derivation. A quote that says *$14,720* is useless. One that says *$14,720, of
which $6,100 is material at the price we paid on PO-8841 in June, plus 8% scrap
allowance* is usable, defensible, and can be handed to a manager without
re-deriving it.

So every line carries **its source and its assumption.**

---

## The seven lines

### Material

Quantity × price, **plus a scrap allowance** — you buy more than the finished
part needs, because some is cut away or ruined.

Cite the price to one of three things, in order of preference:

1. **An actual purchase price with its PO number and date.** The best basis
   available, and the only one that reflects what this plant actually pays.
2. **A current supplier quote**, with its validity period.
3. **Standard cost**, clearly labelled as standard, and labelled with its
   place in this list: **"standard cost (3rd preference, no actual-cost
   comparable)"**, with the reminder that standard cost does not say whether
   the last job of this kind made money.

**No intake form is not a reason to build nothing.** "Price 250 of PN-4402-A"
in conversation is a minimal intake: part and quantity stated by the user,
everything else null and on the missing register. Build from the highest
preference available, which with standard cost only is the third, and label
it as such. A buildup with a labelled weaker basis is what the estimator
asked for; stopping on the missing form hands back nothing.

**Always state the date of the price used.** Material markets move, and a
quote built on a price as of eight months ago is a different number from one
built last week. Where the price is volatile, say so and add a validity caveat
to the quote.

### Labor

For each operation: **setup hours plus run hours at this quantity**, × the
labor rate.

The hours come from the ladder in `hours-ladder.md`, one rung per operation,
never a single rule for the whole job: a current-revision routing, cited; else
recorded closed-job actuals; else hours derived from the confirmed geometry
estimate; else first principles, naming what would firm them up. The rung, the
path and the cutting-data basis go on the internal sheet beside the line.

A routing for a superseded revision is not an estimate of anything. It is
shown as superseded and never priced from.

### Machine and burden

Machine time × a rate covering the machine's cost of ownership. Same rule: the
rate cites its source, and the time cites its rung — the same setup and run
hours the labor line used, never a second estimate of them.

### Setup

**The one-time cost of preparing a machine for the job, amortized across the
quantity.**

This is the single most important line for understanding a make-to-order quote,
because it is why unit price drops sharply with volume and why quantity breaks
exist at all. Show setup as a total *and* as its per-unit contribution at each
quantity — those two numbers together explain the entire shape of the price
curve to a customer who asks.

**Setup and run are carried separately at every rung.** A source that only gives
a lumped total has an unknown split: say so, and never re-amortize it across a
different quantity — use the highest rung that carries a split for the break
arithmetic, and show the lumped figure beside it at the quantity it came from.

### Outside processing

Heat treat, plating, coating done by a vendor. Cite the vendor price and its
date, and note the lead time it adds — outside processing is frequently the
constraint on the promised date rather than the machining.

**Where `supplier-quote-request` ran a sourcing event for this line and the
buyer recorded a decision**, the line is *sourced*: price it from the awarded
break in the selection record (`../../../shared/contracts/supplier-bid.md`)
and cite supplier, `bid_ref`, bid date, `decided_by` and `decided_at` on the
internal sheet. Its production lead time goes into the date check. A quantity
no awarded break covers is named, never interpolated; an MOQ above the quote
quantity or an expired validity is flagged on the line. A bid with no
selection record is cited as *a supplier quote, not awarded*. The supplier's
name and price stay off the customer quote.

### Tooling

Fixtures or dies. Often charged separately as NRE — non-recurring engineering —
rather than amortized.

**Whether tooling is amortized or charged separately changes the comparison
entirely**, so state which, and state who owns the tooling at the end.

### Margin

Applied on top, per the configured rules, **and always shown as its own line.**

**Never bury margin inside another line.** An estimator negotiating with a
customer needs to know exactly how much room they have, and a margin folded into
the material line is invisible to them and to their manager.

---

## Rates are resolved, not asked for each run

Labor, burden and margin rates are commercially sensitive, but `onboarding`
captures the actual values, not a pointer to who holds them. This skill
resolves each one in the order `../../../shared/secret-config.md`, *Resolving
a rate*, sets: the `MFG_*` variable if it is set, then a confirmed rate in the
plant profile, then a placeholder there, then nothing — and nothing blocks
the line.

Sensitivity here is about storage and audience, not secrecy from this
skill: the burden rate is multiplied by hours and shown on the internal
cost-basis sheet, because that's the whole point of a cost basis the
estimator can defend. It never appears on the customer-facing quote, and
it's never restated back conversationally unprompted — confirmed by name,
not value, if it needs mentioning at all.

Where a rate is a **marked placeholder** — recorded at onboarding with its
assumption because the person answering did not know — price on it, and label
every line it touches and the sheet "placeholder rate — not confirmed". The
plant supplied it and has seen it; it is their number until the real one
arrives.

Where a rate genuinely isn't on file at all (no variable, nothing confirmed and
no placeholder in the profile), **do not substitute a plausible one.**
Produce the buildup to the point the rate is needed and say exactly which
rate is missing and which lines it blocks. A quote built on an invented
burden rate is wrong in a way nobody will catch until the job runs.

**While a required rate is unset, no job-quantity total and no unit price for
this job appears — not from standard cost, not from price history.** Standard
cost times the quantity, and last year's sell price times the quantity, are
both a price arrived at by a side door, and once either is on the page it is
the number that gets quoted. Prior sales are listed as history, one order per
line, and are never extended by the requested quantity or headed "unit price."
A request for "just a ballpark" is declined the same way.

---

## Quantity breaks

**Recompute setup amortization at each quantity the customer asked for.** This
is the most common arithmetic error in hand-built quotes and the easiest to get
right mechanically.

Material scales roughly linearly. Labor scales with quantity but often improves
with a learning curve. **Setup does not scale at all** — it is the same cost
divided by more units.

Show the per-unit price at each break with the setup contribution visible, so
the customer can see why 1,000 is cheaper per piece than 100 and the estimator
can defend the spread.

Where the customer asked for a quantity **far outside anything the plant has
run**, flag the extrapolation explicitly. A price at 50,000 derived from
experience at 500 is an extrapolation, not a quote, and saying so protects
everyone.

---

## Comparables

The fastest sanity check an estimator has: *we made something like this last
year for $X.*

Search in order: **the same part number**, then similar parts by material,
process and size.

For each comparable, show **what made it comparable and how the new job
differs.** A comparable presented without its differences is misleading —
same part, half the quantity, different finish, and a material market eighteen
months older is not the same job, and the estimator needs those four facts to
weigh it.

**Where no comparable exists — a genuinely new part — say so clearly and do not
produce a confident number off nothing.** That is what the ladder is for: hours
from the confirmed geometry estimate where there is one (rung 3), and first
principles only where there is nothing better (rung 4). Either way each
operation is labelled with its rung and names what would firm it up, and the
setup and run split is kept.
