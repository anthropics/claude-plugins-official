---
name: quote-build
description: "Produces the make-to-order quote from the intake form, comparable prior jobs and cost history, with every number traced to where it came from — material at the price actually paid on a named purchase order, machine hours per operation from a labelled ladder (current routing, closed-job actuals, the confirmed design, first principles) with setup and run kept apart, setup re-amortized at each quantity break, and margin on its own line. Checks the promised date against real shop load before committing to it. Revises in place when a customer counters, preserving what changed and why. Use when someone says \"build the quote,\" \"price this job,\" \"what should we charge,\" \"quote this RFQ,\" or \"the customer came back on price.\""
compatibility: "Requires none. Reads NetSuite or Infor M3 (or any ERP mapped into the dataset) for standard cost, actual cost on closed work orders and purchase prices, Microsoft 365 for prior quotes and templates, a planning export for shop load, and Autodesk Fusion for CAM-derived hours where connected. Runs on the intake form and pasted cost figures with no connector. Reads rates from an MFG_* variable or the plant profile, never asking each run. The quote uses the plant's own template."
---

# Quote Build

Pricing a make-to-order job means building up a cost and then applying
commercial judgment. Every job is priced fresh, which is why quoting is skilled,
slow, expert work — and why the estimator is usually the bottleneck.

**The cost basis is shown, always.** A quote that says *$14,720* is useless. One
that says *$14,720, of which $6,100 is material at the price we paid on PO-8841
in June, plus 8% scrap* is defensible.

**Quick start**

```
→ Load the intake form. Lines with no quantity or no material are skipped; quote the rest and list what's blocked
→ Find comparables; show what made each one comparable AND how this job differs
→ Flag capability BEFORE pricing. Then hours per op from the ladder: routing → actuals → confirmed design → first principles
→ Setup and run separate at every rung. A superseded routing is shown, never priced. probable_standard never outranks rung 3
→ Build up the cost: material, labor, machine, setup, outside processing, tooling
→ Resolve rates: MFG_* variable, then the plant profile. Never asked in the run, never invented
→ Re-amortize setup at every quantity break
→ Margin on its own line. Never buried
→ Check the promised date against real shop load. Never quote a date blind
→ Assemble the customer quote AND the internal cost-basis sheet. No hours, ranges, rates, paths or basis labels in the customer's
→ On a counter: revise in place with a change record. Never a second quote, never reopen CAD
```

---

## Inputs

**First, find the plant setup:** from the task's own folder (never `cd` into the plugin), run
`python3 -I <this skill's folder>/../../shared/scripts/plant_setup.py find`, do its `setup_page_first` step, then read the profile at
`profile_path` and any rate at `rates_path`, per `../../shared/replies.md`.

| Input | Source | Form |
|---|---|---|
| The intake form | `customer-inquiry-intake` | `../../shared/contracts/intake-form.md` |
| Consolidated dataset, including `routings` and `operation_actuals` (v4) | `data-consolidate` | `../../shared/contracts/consolidated-dataset.md` |
| Geometry estimate, per line | `rfq-to-quote` step 7, or typed by the estimator | `../../shared/contracts/geometry-estimate.md` |
| Machine classes, cutting data, variance threshold | `### Machining data` in the `## Plant context` block | Config |
| Standard cost and item master | The ERP (NetSuite or Infor M3), each cost read from the field the profile's cost map names (`../onboarding/reference/erp-scope.md`); a field equal to the sell price is never a cost. Infor M3 gives no standard cost: last purchase price first, per `../../shared/erp-connectors.md` | Connector |
| Actual cost on prior jobs | `production_work_orders` actual-cost columns in the dataset (v6): NetSuite closed work orders, Infor M3 work order operations, or any ERP `custom-connector` mapped | Dataset |
| Recent material purchase prices | ERP purchase orders | Connector |
| Awarded supplier bid for an outside process, with its selection record | `supplier-quote-request`, when this quote started the sourcing event | `../../shared/contracts/supplier-bid.md` |
| Prior quotes for this customer or part | M365 documents, NetSuite. Infor M3: documents only | Documents and connector |
| Labor, burden and margin rates | `MFG_*` variable, else the plant profile — see below | Config |
| Shop schedule and load | Planning export to the M365 folder | CSV/XLSX |

**Rates are resolved, not asked for each run**, in the order
`../../shared/secret-config.md`, *Resolving a rate*, sets, and no other:

1. `MFG_LABOR_RATE`, `MFG_BURDEN_RATE`, `MFG_MARGIN_RULES`, checked by name,
   never printed. These win; a stored value for the same rate is **never
   printed anywhere**, only named as also held.
2. A **confirmed** rate in the `## Plant rates` file at `rates_path` (an older
   profile: its `### Commercial rates`). Price on it with no label.
3. A **placeholder** in the same place. Price on it and label it, below.
4. Nothing. **Block the lines it feeds**, named; the rest is still produced.

Shown on the internal cost-basis sheet, never on the customer-facing quote.

**A rate typed into this run is not used**: say it is not on file, do not
repeat the number, and offer `onboarding`'s "update our labour rate", which
saves it with a name and date for every quote after this one.

---

## Workflow

### Step 1 — Load the intake form

**Refuse to proceed on line items with no quantity or no material.** Quote the
rest and list what is blocked and why.

A 40-line RFQ with one underspecified item produces 39 prices and one question,
not silence.

**Read the commercial terms** — payment, freight, packaging, liability. Where
the intake form states one, carry it into the quote as given. Where one is
null, quote against the plant's standard for that term, name the assumption on
the exclusions list, and keep the missing-register row — do not fill it in
silently. Where `customer-inquiry-intake` flagged a stated term as clashing
with the plant's standard, carry that flag onto the exclusions list too; it
does not resolve itself by arriving here.

**Block on missing provenance.** Where `field_sources` is absent from the
intake form, block — without provenance the estimator cannot verify a number
against the package, and a quote built on an unsourced field is a quote no
one can defend.

**Where `quantities` has only one entry but the customer's ambiguous register
shows breaks were requested**, quote what is there and state plainly that the
breaks were not captured — never invent the missing quantity points.

**Where `ambiguous_register` carries an entry on a field the quote depends
on**, quote against one value, name which, and state the other explicitly
rather than silently picking one — the same discipline the intake form itself
applies to a customer's conflicting statements.

**Where `recommendation` is `no_bid`**, it is a recommendation, not a
decision. Proceed only if the estimator says to, and say so in the quote's
assumptions when you do.

**Check `bid_decision_state`, and each line's `line_bid_decision`, never context.**
`declined` blocks the inquiry, or that line, listed as not quoted by the
estimator's decision; reopening is a new decision. `draft`, or a set
`bid_decision_reset`, means no ruling covers it: quote only if told to in the
run, and record on the quote that it proceeded on an unconfirmed recommendation.

**`inquiry_state` is a different axis, and reading it as a decision is the
error to avoid.** `superseded` blocks — a later revision exists, quote that one.
`stale` does **not** block and never means declined: it means the customer went
quiet on open questions. Quote with exclusions naming those questions, or do not
quote — but never treat the silence as a no.

**Where `recommendation_provisional` is true**, answers were still outstanding
when this was scored. Quote if the estimator says to, and carry the outstanding
questions onto the assumptions list — they are precisely what the price rests
on. Where `hard_disqualifier_stopped` is true, the plant cannot build this as
specified: quote only on an explicit override, with the disqualifying constraint
on the exclusions list.

**Read the geometry estimate's `approval.status` the same way.** `confirmed`
means the estimator passed Gate 3 on this model, tolerance reading and
operation list. **`draft` is unconfirmed: no hours derived from it reach a
quote** unless the estimator says so in this run — then the internal sheet
records who said so and that the model was unconfirmed. A
`drawing_revision_priced_to` that differs from the intake line's `revision`
blocks: that estimate is another part.

### Step 2 — Find comparables

Prior jobs for the same part number first, then similar parts by material,
process and size.

**Show what made each one comparable and how the new job differs.** Same part,
half the quantity, different finish, eighteen months of material inflation — the
estimator needs those differences to weigh the comparable at all.

Where no comparable exists, say so clearly and **do not produce a confident
number off nothing.**

**Count the history in code.** How many orders, how many for this customer,
how many closed work orders, across what dates — each is a filter run over the
data, and each goes in the figures block (`../../shared/computed-figures.md`)
with that filter. "Consistent across five orders" written from memory misses
the sixth, and the one missed tends to be the customer's own.

### Step 3 — Flag capability, then derive the hours

**Capability flags come before any price.** Carry the intake form's
`constraint_violations`, and check every tolerance on the geometry estimate
against demonstrated capability in the Plant context: **a tolerance tighter
than the plant has demonstrated on that process is flagged by name, value and
capability**, on the internal sheet and, as a plain statement of what is
quoted, in the assumptions. Pricing it first and flagging it after is how a
plant commits to a tolerance it has never held.

**Then hours per operation, from the ladder.** Read `reference/hours-ladder.md`
before deriving any hour. Per operation, best available first:

1. **A routing for this part and revision**, cited. A routing for another
   revision is superseded — shown as such, never priced from.
2. **Closed-job actuals** not flagged `probable_standard`.
3. **Geometry-derived** from the confirmed estimate: the CAM path where Fusion
   and plant cutting data exist, the feature path always.
4. **First principles**, naming what would firm it up.

**`probable_standard` actuals never outrank rung 3.** **Library feeds
(`fusion_default`) are rung 4, labelled "library defaults, not plant data."**
Setup and run are carried separately at every rung. Where two rungs exist the
variance is computed in code and flagged above the Plant context threshold —
or 15%, printed word for word as *"default threshold, not plant-set"* — with its drivers
named. Every hour, range and variance goes to the figures block.

### Step 4 — Build up the cost

Material with its scrap allowance, labor, machine and burden, setup, outside
processing, tooling.

**Each line cites its source** — standard cost, an actual purchase price with
its PO and date, or the actual cost from a specific prior work order. Labor,
machine and setup use the hours from Step 3, rung by rung, never a single
hours rule for the whole job. Read `reference/cost-buildup.md`.

Where a required rate is not supplied, build to that point and **name exactly
which rate is missing and which lines it blocks.** Never substitute a plausible
one.

**No job-quantity total and no unit price for this job may appear while a
required rate is unset — not from standard cost, not from price history, not
as a ballpark.** Every route to a number is closed, including the ones that
look like something else:

- *Standard cost × quantity* is a price by another name. Standard cost may be
  cited as a material basis per unit, labelled standard; it is never extended
  by the job quantity into a total while labor or burden is blocked.
- *A prior sell price × quantity* is a price too. Prior sales may be listed as
  history — order, date, quantity, price, one line each — and are never
  multiplied by the requested quantity, never headed "unit price," never
  offered as a guide to this job.
- *"Just a ballpark"* and *"use a typical shop rate"* get the same answer.
  Decline the typical rate without naming one, and do not then produce the
  ballpark some other way.

**A placeholder is a rate, and prices the job.** Where the `## Plant context`
block carries a rate as a marked placeholder with its assumption — recorded by
the plant at onboarding, not invented here — build on it. Label every line it
touches, and the cost sheet as a whole, **"placeholder rate — not confirmed"**,
and put the placeholder on the assumptions list by name. The gaps list names it,
never its value. This state, "quote-build is
running on a placeholder," is expected. What is still refused is any
rate the model supplies itself, from a benchmark or a lookup.

**A confirmed rate prices the same way, without the label.** A rate the
rates file records as confirmed — given by a named person on a
date and approved at onboarding — is the plant's number, as much as one set in
`MFG_*`. Cite it on the internal sheet as *plant profile, confirmed by <name>
on <date>*, and leave it off the assumptions and gaps lists.

**Still produce everything the rates do not touch:** material at the price
actually paid on a named PO with its date; the setup amortization structure at
each quantity, with the dollar values blocked; outside processing and tooling
where sourced; and the date check against shop load. Name each missing rate
and both ways to set it — *"update our labour rate"* to record it on the
plant's rates page, or `MFG_LABOR_RATE` / `MFG_BURDEN_RATE` in the environment — say which
lines each blocks, and say the quote completes as soon as they are set.

### Step 5 — Apply quantity breaks

**Recompute setup amortization at each quantity the customer asked for.** Setup
does not scale — it is the same cost across more units, and that is the entire
reason unit price drops with volume.

Show the setup contribution per unit at each break so the spread is explicable.

**Setup and run stay separate at every break, at every rung.** Where a source
gives only a lumped total, the split is unknown: say so, and **never
re-amortize it** — use the highest rung that carries a split for the break
arithmetic.

### Step 6 — Apply margin

Per the configured rules, **shown as its own line and never buried.**
An estimator negotiating needs to see exactly how much room they have.

### Step 7 — Check the promised date against shop load

Read the planning export and answer whether the requested date is achievable
given what is already committed, plus material and outside-processing lead time.
**The work content is setup plus run hours by work center from each
operation's winning rung, and the check names that basis.**

**If it cannot be met, say so and give the earliest date that can.** Quoting a
date the shop cannot hit is how a plant loses a customer twice.

Without a planning export, the quote carries a stated lead time with an explicit
**"not checked against shop load"** caveat — never a silent omission. Read
`reference/date-and-load.md`.

### Step 8 — Assemble both documents

The **customer-facing quote** in the plant's template, and the **internal
cost-basis sheet** the estimator keeps and defends.

**Emit the customer quote between delimiters, and keep everything internal
outside them:**

```
=== CUSTOMER QUOTE — SENDABLE ===
…the quote, and only the quote…
=== END ===
```

The cost-basis sheet is its own delimited document, so both are explicit and
neither can be mistaken for the other:

```
=== INTERNAL COST SHEET — NOT FOR CUSTOMER ===
…the buildup, every source, each rate against its source, the
hours per operation with rung, path, cutting data basis, setup and run,
range, variance and drivers, the comparables, the margin line, the
figures block…
=== END ===
```

Notes to the estimator that belong to neither document go outside both
blocks. Narrative cost prose with no delimiter is not a cost sheet. **An assumption that
reveals pricing policy is internal**: "no customer was named, so the default
margin rule applies; a different rule is configured for another customer" is
useful to the estimator and must never sit inside the quote. On the internal
sheet, show each rate's value against its source — `MFG_LABOR_RATE`, *plant
profile, confirmed by <name> on <date>*, or *plant profile, placeholder* —
that is what makes the basis defensible.

**The customer quote states what was quoted, not how it was estimated.** Its
assumptions name the **drawing revision priced to** and the **tolerances as
read** — *"priced to PN-4471-B Rev 2; unspecified tolerances ±0.005 in per the
drawing's general note"* — and any capability flag as a statement of scope.

**Then read the block alone, and reject it if it holds** any hours figure —
setup, run, cycle or machine time, per piece or per job — any low, expected or
high range, any rung, path or source of an hour (routing, actuals, CAM, feature
path, geometry estimate, first principles), any cutting-data basis label
(`plant_library`, `estimator_entered`, `fusion_default`, library defaults), any
variance, `probable_standard`, or anything from `cost_down_proposals`;
any rate value —
from an `MFG_*` variable or the plant profile, or a figure that is one times
something —
the word "margin" **in any form — "margin applied," "standard margin," "at our
usual margin," a margin percentage, or a line item called margin** — any
description of which pricing rule was used, or any customer's name but the
addressee's. The customer sees prices; how they were arrived at is the
internal sheet's business. A rejected block is rewritten before anything is
sent, not annotated. The full list is
`../../shared/secret-config.md`, *The outbound document check*.

### Step 9 — Handle the negotiation loop

When a customer counters, **revise the existing quote in place and preserve a
change record** of what moved and why.

A counter is not a new quote. Treating it as one is how a plant ends up with
four versions in circulation and no record of what was conceded. Re-derive the
affected lines rather than patching the total, and where a price dropped with no
scope change, **say that margin moved.** Re-derive from the stored operation
record — **a price counter never reopens CAD.** A new drawing revision is not a
counter: it goes back to `rfq-to-quote` step 7. Read `reference/revisions.md`.

---

## Approval gates

**Nothing reaches a customer without the estimator releasing it.** This is
Chain 1's **fourth** gate, at step 11. Gate 1 is the estimator sending the
open questions at step 4; Gate 2 is confirming the bid/no-bid at step 5; Gate 3
is confirming the design, tolerance reading and operation list at step 8 — no
geometry-derived hour is priced without it or a recorded override. The quote
is drafted, shown with its cost basis, and sent by a person.

**Every revision goes through the same gate.** A second version of an approved
quote is not pre-approved.

**Rates are resolved per `../../shared/secret-config.md` and shown only where
the audience rule allows.** Nothing is written back to the ERP; the quote is a document the
estimator files and sends. The margin line appears on the internal
cost-basis sheet, never on the customer-facing quote.

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

**The customer-facing quote** — line items, prices, quantity breaks, lead time,
validity period, terms (payment, freight, packaging, liability — as the
customer stated them, or the plant's standard where one was never stated), and
the assumptions and exclusions list.

Per `../../shared/artifact-style.md`, a quote is a controlled document and uses
the plant's own template captured during `onboarding`, **never the house style.**

**The internal cost-basis sheet** — the full buildup with every source cited,
the comparables used and how they differ, the margin applied, and every
assumption made. The estimator hands this to their manager and defends the price
without re-deriving it. **It carries the figures block** — every count of
orders, lines and comparables, and every extended figure, with the filter or
arithmetic behind it. Internal only; it never appears in the customer quote.

**The hours-basis table, on the internal sheet** — per operation: rung, path,
cutting-data basis, setup and run with their range, every other rung with its
variance, the variance drivers, and the toolpath check where the CAM path ran.
Any `cost_down_proposals` from the geometry estimate sit here, internal only.

**The operation record** — kept with the quote, so a counter re-prices without
reopening anything and the estimate can one day be compared with the job's
actuals. Its fields are in `reference/hours-ladder.md`.

**The assumptions and exclusions list** — explicit, including any commercial
term quoted against the plant's standard because the customer never stated one,
or flagged because a stated one clashed with the plant's. This is what protects
the plant when the customer's expectations diverge later, and it is the section
everyone skips.

**Revision history** — when revising, with what changed and why.

**The Sales command-center page** — Chain 1's closing step. Commercial
performance for the period, carrying the intake record and the quote by
reference so the page reads from what was actually sent rather than a separate
summary of it. Produced as an artifact you place; nothing is written to a
system. The customer-facing version carries no margin line. Read
`../../shared/command-center.md`.

---

## Edge cases and failure modes

- **No comparable exists** — a genuinely new part. Say so; do not produce a
  confident number off nothing.
- **Material price is volatile** — cite the price as of its date and add a
  validity caveat to the quote.
- **The requested date is impossible** — never quietly quote a date the shop
  cannot hit.
- **A quantity far outside anything the plant has run** — flag the extrapolation
  explicitly. A price at 50,000 derived from experience at 500 is not a quote.
- **Currency or unit mismatches between the RFQ and our cost data** — surface
  them rather than converting silently.
- **A required rate was not supplied** — name which one and which lines it
  blocks. Never invent it, and produce no total and no unit price for the job
  by any other route — see Step 4.
- **The cost history is stale** — cite each figure as of the date its work order
  closed. A comparable priced in a different material market is still useful,
  but only if its age is visible.
- **A spec on the intake form has no source reference** — block that spec. An
  unsourced tolerance is an inference, and inferences get priced and then
  committed to contractually.
- **A commercial term (payment, freight, packaging, liability) was never
  stated** — quote against the plant's standard for that term and name the
  assumption on the exclusions list. Never fill it in silently.
- **The only routing is for an earlier revision** — superseded. Show it as
  such; derive from the next rung. Never price the new revision on it.
- **Actuals agree to within 1%** — `probable_standard`. Shown, never above a
  geometry-derived estimate.
- **The geometry estimate is still `draft`** — no hours from it reach a quote
  without the estimator's say-so in the run, recorded on the internal sheet.
- **A Plant context value is tagged `assumed`** — use it, label it, and name it
  as a variance driver where it explains more of a gap than the threshold.

---

## Degradation

Runs on the intake form plus pasted cost figures with no connector at all.

| Not available | What happens |
|---|---|
| The ERP (NetSuite or Infor M3) | No standard cost, actual cost or purchase-price history. Ask for material prices and rates directly, and label the whole buildup as supplied rather than sourced |
| Closed-work-order cost | Build up from standard cost, labelled **"standard cost (3rd preference, no actual-cost comparable)"** — standard cost does not say whether the last job made money |
| The intake form | Treat the request as a minimal intake: part and quantity as the user stated them, every other field null and on the missing register. Build from the best basis available and label it. A recorded placeholder rate counts as a set rate |
| Purchase-order history | Price material from a current supplier quote or a supplied figure, with its date |
| Planning export | Quote a stated lead time with the explicit "not checked against shop load" caveat |
| Prior quotes | No precedent for this customer. State it rather than reading absence as a new relationship |
| The plant's quote template | Use a neutral quote structure covering every section above, and flag that the controlled template was unavailable |
| Routings and actuals | The ladder starts at rung 3, or rung 4 where there is no confirmed geometry estimate. Name both tabs missing |
| Geometry estimate | No rung 3 for that line. Say the design step did not run and why; the ladder runs on what exists |
| A drawing (path A, text specs only) | **A ROM, never a firm quote**: ROM on the internal sheet, a budgetary estimate on the customer document, nothing about method. An override does not make it firm. `reference/hours-ladder.md`, *Path A* |
| Fusion, or its Manufacturing workspace | Feature path only, and the internal sheet says so. No toolpath check is claimed |
| Plant cutting data | The CAM path runs on library feeds, labelled `fusion_default`, rung 4. The feature path cannot time a cut; that op is rung 4 |
| Machining data in the Plant context | No plant setup or tool-change values, no cell map, and a variance threshold of 15% printed as "default threshold, not plant-set" |

---

## Chain position

**Chain 1, RFQ to quote** — the final step, depending on `customer-inquiry-intake`
and `data-consolidate` as two independent inputs, not a pipe from one through
the other.

Both this step and the intake's bid/no-bid depend on cost history. **If the ERP
is not connected, both degrade to document-based comparables and the chain says
so** rather than quietly producing weaker output.

**Metric.** Quote turnaround; hit rate; the unbid book.

---

## Reference files

| File | Load when |
|---|---|
| `reference/hours-ladder.md` | Step 3 — always, before any hour: the ladder, setup and run, ranges, variance, the CAM and feature paths, the per-op sheet columns and the operation record |
| `reference/cost-buildup.md` | Steps 2 to 6 — the seven lines, their sources, comparables, and quantity breaks |
| `reference/date-and-load.md` | Step 7 — the load check, its scope boundary, and the caveat when it cannot run |
| `reference/revisions.md` | Step 9 — the change record, re-deriving from the operation record, and why a new drawing revision is not a counter |
| `../../shared/contracts/geometry-estimate.md` | Steps 1 and 3 — the geometry estimate, its approval state and what blocks it |
| `../../shared/computed-figures.md` | Steps 2 and 7 — the figures block every stated count is quoted from |
| `../../shared/contracts/intake-form.md` | Step 1 — the intake shape, a line with no quantity or no material, the missing behavior for a null commercial term, an ambiguous register entry, uncaptured quantity breaks, a `no_bid` recommendation, the `bid_decision_state` gate, and absent `field_sources` |
