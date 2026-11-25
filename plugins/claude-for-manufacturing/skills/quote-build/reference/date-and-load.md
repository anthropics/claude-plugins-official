# Checking the promised date against the shop

**Quoting a date the shop cannot hit is how a plant loses a customer twice** —
once when the job is late, and again when they remember it during the next RFQ.

A price that is right and a date that is wrong is a bad quote. The date is
frequently the thing the customer actually cares about.

---

## What the check does

Read the planning or schedule export and answer one question: **given what is
already committed, can this job be delivered by the requested date?**

Work through, in order:

1. **The work content this job adds** — setup plus run hours by work centre,
   from each operation's winning rung on the ladder (`hours-ladder.md`), with
   that basis named: *"Cell B: 31.4 h, rung 2, closed-job actuals"*. A load
   check built on first-principles hours says so. Work centres come from the
   routing, or from the machine class to work centre map in the Plant context
   for a geometry-derived operation.
2. **What is already loaded** on those work centres between now and the
   requested date.
3. **Material lead time**, which frequently dominates. A four-week steel lead
   time makes a three-week delivery impossible regardless of what the machines
   are doing.
4. **Outside processing lead time**, which is easy to forget and often the real
   constraint — black oxide at five working days a lot is a week the machines
   cannot recover.
5. **Whether the requested date survives all four.**

---

## What to report

**If the date can be met**, say so and say what it depends on — usually material
arriving and the current load holding.

**If it cannot, say so, and give the earliest date that can.** A quote that
silently promises an impossible date is the failure this step exists to prevent;
one that offers a realistic alternative is a commercial conversation the
estimator can actually have.

> *"The requested 3 November is not achievable. Cell B is loaded to 92% through
> late October on committed work, and the 6061-T6 is on a four-week lead time
> against an order that has not been placed. The earliest defensible date is 21
> November, assuming material is ordered this week. If 3 November is firm, the
> conversation is about what gets displaced — worth flagging to scheduling
> before this goes out."*

**Name what was checked and what was not.** A load check that looked at machine
hours but could not see labour availability should say so. That is the
difference between a caveat the estimator can weigh and a promise they cannot.

---

## This is not finite-capacity scheduling

The same boundary `daily-production-report` holds for reschedule proposals
applies here, for the same reason.

**Producing an optimal shop schedule is a constraint-optimisation problem, and a
language model asked to do it will return a plausible-looking answer that
quietly violates constraints** — which is worse than returning nothing, because
it looks authoritative.

What is in scope is a **load check with its reasoning shown**: here is the work
this adds, here is what is already committed on those work centres, here is
where it does not fit. Not a re-optimised shop calendar.

---

## Degradation — and it must not be silent

**Without a planning or schedule export**, the quote carries a stated lead time
with an explicit caveat:

> *"Lead time quoted at 8 weeks from receipt of order, based on the routing and
> normal material lead time. **This has not been checked against current shop
> load** — no schedule export was available. Confirm with scheduling before
> release."*

**Never a silent omission.** A quote with no date caveat reads as a date that
was checked, and that is precisely the wrong impression to leave with an
estimator about to commit to a customer.

Where the export exists but is stale, state the load **as of** its last refresh
rather than as current. A load picture from three weeks ago has missed
everything booked since, and per `../../../shared/absent-is-not-zero.md` a stale
figure presented as current is the worst available outcome.
