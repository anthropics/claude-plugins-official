# Quality clauses, and the suppliers who can meet them

---

## The clause list

The requirements a supplier must meet to be allowed to ship this part. They are
part of the price — a supplier quoting without them is quoting a different job —
so they belong in the request rather than in the purchase order afterwards.

| Clause | What it obliges the supplier to do |
|---|---|
| Certification | Hold a current registration to the applicable standard — ISO 9001 general, AS9100 aerospace, IATF 16949 automotive |
| Material certification | Supply mill certs traceable to the heat or lot |
| First article inspection | Submit a full dimensional report on the first production part before running the balance |
| PPAP submission | The automotive production-part approval package, at a stated submission level. **The level changes the cost materially** |
| Certificate of conformance | Ship with a signed statement of conformance per lot |
| Right of access | Permit audits by us, our customer, and the regulator |
| Change notification | Notify before changing process, sub-tier supplier, or location |
| Record retention | Hold records for a stated period |
| Lot traceability | Maintain lot identity through their process, which is what makes ours possible |

**PPAP level is not a detail.** Level 1 is a warrant; level 3 is a full package
with dimensional results, material and performance test results, process flow,
PFMEA and control plan. Quoting the wrong level is a real and unpleasant cost
surprise, and it is one of the more common ones.

---

## Revision matters as much here as on the drawing

**Quote against the clause list at its current revision.** A superseded clause
list produces bids that are not valid, in exactly the way a superseded drawing
does — and it is far less likely that anyone notices, because nobody reads the
clause list twice.

Where the clause set captured during `onboarding` is unavailable, **list the
clauses found on the current part record and flag the whole set as unverified.**
Do not assemble a plausible standard list from what plants usually require. A
confidently wrong clause list is worse than an admitted gap, because the buyer
will not re-check it.

---

## Clauses vary by customer program — surface it, never merge it

The same part number can carry different requirements depending on which
customer's program it is being built for. One customer flows down AS9100 plus a
level-3 PPAP; another takes the same part under ISO 9001 with a certificate of
conformance.

**Surface the variation and let the buyer decide.** Do not merge the sets.

Merging fails in both directions and both are bad: take the union and you have
quoted the most expensive requirements onto every unit, so the price is wrong
and the plant loses money quietly forever. Take the intersection and you have
sourced parts that cannot legally ship to the stricter customer, which is a
nonconformance you have manufactured on purpose.

---

## Candidate suppliers

Existing qualified suppliers for this commodity, from the ERP vendor
records, plus the current supplier for comparison.

Where the trigger was a supplier-caused flag, the implicated supplier stays on
the list, clearly marked. The buyer needs to see the incumbent's price next to
the alternates, and sometimes the answer is a corrective action with the
incumbent rather than a switch.

### Single-source risk is the finding

**If exactly one qualified supplier exists, flag it loudly.** That is usually
more important than the sourcing package it appeared in.

A part with one qualified supplier means a quality problem at that supplier
stops production, with no path around it. Sourcing an alternate is insurance,
and the moment you discover you need it is the moment it is too late to get it —
which is precisely why Chain 5 exists.

### Requalification lead time is why starting early is the value

An alternate supplier cannot simply start shipping. They have to be qualified:
sample parts, first article inspection, often a full PPAP, sometimes a site
audit. **Weeks to months.**

State the expected requalification path with the candidate list, so nobody reads
an alternate source as available next month. The whole argument for starting a
sourcing action off the back of a quality finding is that the clock is long and
it has just started.
