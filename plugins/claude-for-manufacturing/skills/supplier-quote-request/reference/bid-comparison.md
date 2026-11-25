# Bids — ingest, compare, recommend, record the decision

Steps 11 to 13. The returned bids go into one shape, the comparison is
computed from that shape, and the buyer decides. The shape is
`../../../shared/contracts/supplier-bid.md`; the format the package asked for
is `bid-comparability.md`.

---

## Step 11 — Ingest each bid

Bids arrive as a PDF, an email, a spreadsheet, or pasted text. Read each into a
supplier bid record, **one per response**, every value with its `source_ref`.

**Map, never normalise.** The record holds what the supplier stated:

- **A lot price is not a unit price.** *"$410 for 200"* goes in `as_quoted`
  and `unit_price` stays null. Dividing it is the buyer's afternoon of
  normalising that the mandated format exists to remove.
- **Tooling folded into the piece price** is `tooling_in_unit_price: true`,
  not a tooling price of zero.
- **"About a week"** is not a lead time from a named event. Keep the words,
  leave the split fields null.
- **Silence on the quality clauses** is `not_stated`, never accepted.
- **No currency stated** is null, never assumed.
- **A break the package asked for and the supplier did not price** stays on the
  record with nulls. It is the gap a buyer most needs to see.

### Off-format bids

A bid is `off_format` when any mandated field is missing or in another shape.
**List every field not supplied in `fields_missing`, by name**, by checking
each mandated field in turn — unit price at each break, currency, lead time
first article and production from a named event, tooling price or a statement
that none is needed, tooling ownership, MOQ, validity, quality clause
acceptance — not by noticing what stands out.

Then draft a restatement request for the buyer to send, per
`bid-comparability.md`, *Say what happens to a non-conforming bid*: it names
the missing fields and asks for the bid in the package's format. It goes
between `=== SUPPLIER EMAIL — SENDABLE — <supplier> ===` (or `HELD`, per
`supplier-loop.md`) and `=== END ===`, and the outbound check there applies — **nothing about other bids**.
A restated bid gets a new `bid_ref` that `supersedes` the old one.

A bid that claims to be from a supplier not on the candidate list is ingested,
marked `not_confirmed_approved`, and flagged.

**Show every record in the reply** as the summary table in
`../../../shared/replies.md` — supplier, source file, the break prices as
quoted, `fields_missing` by that name — and save the full record. The buyer
reads the reply, and a record that exists only in a file nobody opened has not
been shown; a raw YAML block is shown but not read.

---

## Step 12 — Compare, in code

**Every figure in the comparison is computed by code over the bid records**
and printed from the result, with a figures block per
`../../../shared/computed-figures.md`. No price is retyped from a PDF into the
table.

### One table per quantity break

| Supplier | Approval | Unit price | Extended (unit × qty) | Tooling | MOQ | Lead time FA / production | Clauses | Exceptions | Validity | Readiness | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|

- **Readiness** is the derived status from step 13, *ready for buyer review*
  or *provisional* with what is open, in the same table.
  There is no second full table repeating approval, readiness or open
  requirements; the per-prerequisite evidence sits in the detail below,
  collapsible, never removed.

- **Extended** is unit price × break quantity, computed. A bid with no unit
  price at that break reads *not quoted per unit*, with `as_quoted` beside it;
  where a lot price is shown divided, it is labelled *derived from a lot price,
  not quoted* and is not ranked.
- **First-order total** — extended plus one-time tooling — gets its own column
  where any bid carries tooling, labelled *includes one-time tooling*. A bid
  that is cheaper per piece and dearer once its tooling is counted is the
  finding the separate tooling line exists to show.
- **MOQ above the break quantity** is flagged on that row: the price does not
  buy that quantity.
- **A Source column on every table, naming each bid's file and page, sheet or
  email** — `bid_example-finishing_2026-10-22.txt`, not "the bid files". It is not
  optional: a figure a buyer cannot trace back is one they will re-key.
- **Different or unstated currencies are not ranked against each other.** No
  conversion; each stays as stated.
- **Absent is not zero.** A missing tooling price is *not stated*, not $0. A
  missing lead time is not the fastest.

Below the tables: who has not responded, with days past due (from
`supplier-loop.md`), and every off-format bid with its `fields_missing`.

The comparison is internal. It never goes inside any SENDABLE block.

---

## Step 13 — Recommend, then record the buyer's decision

### Recommend, never award

Recommend one bid per break, or one overall, **with the reasons and what argues
against it**: price at each break, first-order total, lead time against the
buyer's first article date from step 3, clause exceptions, approval status, and
single-source exposure. A `not_confirmed_approved` supplier may be
recommended only with its requalification named as a condition. A comparison
missing a supplier says so beside the recommendation.

**Ready for buyer review is derived, never a checklist item of its own.** Four
prerequisites are judged separately for each bid, each with its evidence:

1. **Cost comparable**: priced per unit at the break, currency stated, tooling
   and MOQ known or flagged.
2. **Supplier approved** for this process, or its requalification named.
3. **Delivery evidenced**: a lead time that meets the first article date.
4. **Technical and quality terms accepted**: every mandated clause and the
   spec accepted as written. A clause the bid is silent on is *not stated*,
   neither accepted nor refused; a clause the bid takes exception to is open
   until the buyer accepts the exception. Either keeps the bid provisional.

A bid is *ready for buyer review* only when all four hold; otherwise it is
*provisional*, with what is open named (*"Valley: provisional, change
notification clause not stated"*). The buyer's approval is a fifth thing,
recorded only when given, and never counted as a prerequisite for itself.

**The recommendation is not a decision.** The reply ends with the next-step
question below, which hands it back to the buyer. "Pursue Example Finishing" is a
next step, not a selection: a selection is recorded only when the buyer says
they are going with a bid, with their name. Never write *awarded*, *selected*, *chosen* or *placed* about a bid
the buyer has not chosen, and never draft an award notice before they have.

### The comparison page leads with the recommendation

The comparison is saved as `sourcing-output/bid-comparison.html` (house style,
internal), one file saved over the last run's, with the event reference in its
title, and the reply names that path. In order:

1. **The provisional recommendation**: the bid, the reason, the main tradeoff,
   and every requirement still open before an award.
2. **The next step, as a question**: *"Pursue <supplier>, look into the
   alternatives, or ask the suppliers to clarify?"* Choosing one is a
   preference about what to do next, never a selection or an award.
3. **The comparison table per quantity break**, with its Readiness column.
4. **Draft supplier emails, not sent**: expanded, one card per supplier with
   the supplier, the recipient or `[recipient: not on file]`, the subject and
   the full body, and its HELD or SENDABLE status per `supplier-loop.md`.
   Never inside a collapsed section.
5. **Detail, collapsible but never removed**: the per-prerequisite readiness
   evidence, the figures block and calculations, the bid records summary, and
   the sources.

The reply is the short summary in `../../../shared/replies.md`, with the
recommendation, the tradeoff, the open requirements and the next-step
question in prose, **no tables** (the table is on the page), **plus every
draft in full between its delimiters**: a draft is
something the buyer sends, so it is always in the reply. A question about the
bids ("walk me through Example Plating at 200") is answered in the reply in full. With
no way to write a file, print the whole comparison in the reply in this order.

**Looking is not choosing.** Viewing an option, switching a quantity break on
a page, or saying which option to discuss next sends nothing, places nothing,
and records no selection. Clarification drafts stay unsent and sit below the
comparison and recommendation. A revised comparison keeps the earlier one
recoverable; it never overwrites a recorded decision.

### Record the decision

**A decision is recorded only when the buyer states it**, after the comparison
was on screen, naming a supplier on it: *"Go with Example Finishing at both breaks."*
Per `../../../shared/approval-gates.md`, *Supplier send and selection*.

- **Generic continuation is not a decision.** "Go ahead," "do what you think,"
  "pick the cheapest" — the last before any comparison was shown — get the
  comparison and the question.
- **Ask for a name** when none was given. `decided_by` is the name the buyer
  gives, as given; it is not verified and does not need to be.
- **A decision against the recommendation is recorded without argument**, with
  `follows_recommendation: false` and the buyer's reason if they gave one.
- **Write the selection record** per the contract: who, when, which bids were
  on screen, which suppliers had not responded — and **show it in the reply**
  as a short summary table, with `decided_by` and `decided_at` by those names,
  as well as saving the full record. `decided_at` is the current time with its zone; when the buyer
  has given a date the session clock disagrees with, use their date and say the
  time of day is not known.

Then say what it is and is not: *"Recorded: Example Finishing, decided by Dana
Whitfield, 27 Oct 10:05. No purchase order has been raised and nothing has gone
to any supplier."* Update the `## Sourcing events` block on the Open work page: status
`decided`. Save the selection record there as `sourcing/<event-id>/decision.txt`.
Award and regret notes are drafts on request, one per supplier, each through
the outbound check; a regret note never carries the winning price or name.

### When a quote started it

**When the event was triggered by a quote** (`triggered_by.kind: quote`), the
awarded bid flows to `quote-build` as a **sourced outside-processing line**.
Emit it beside the selection record, in the shape the cost buildup reads:

```
Outside processing — EH-RFQ-0912 line 1, black oxide
  Supplier: Example Finishing (VEND-5120), approved, single source
  Unit price: 3.10 USD at 50; 2.20 USD at 200 — bid SRC-2026-10-14-PN-4471-B-BO/VEND-5120/1, received 2026-10-22
  Tooling: none stated as required · Lead time: 5 working days from receipt of parts
  Valid until: 2026-12-21 · Awarded by Dana Whitfield, 2026-10-27
```

`quote-build` cites it on the internal sheet and puts its lead time into the
date check. **The supplier's name and price stay internal**; the customer quote
carries the finished-part price only.

A bid with no selection record is not a sourced line. If the estimator wants
it used before the buyer decides, it is cited as *a supplier quote, not
awarded*.
