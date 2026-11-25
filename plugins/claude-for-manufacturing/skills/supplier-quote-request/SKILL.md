---
name: supplier-quote-request
description: "Builds the RFQ package that goes out to suppliers — drawing and specification at the verified current revision, the demand picture, the quality clause list, commercial terms, and a mandated response format that makes the returned bids comparable by construction. Lists everything missing. Hard stops on a revision mismatch or restricted technical data. Then runs the supplier loop: candidates from the approved supplier list with unapproved and single-source flagged, one email draft per supplier for the buyer to send, response tracking with chase drafts, returned bids read into one shape with every missing field listed, a comparison per quantity break computed in code, and a recommendation. The buyer decides; the skill records who and when. Use when someone says \"source this part,\" \"send an RFQ to suppliers,\" \"we need an alternate supplier,\" \"get quotes on this,\" \"who else can make this?\", \"chase the suppliers,\" \"compare these bids,\" or \"we're going with this supplier.\""
compatibility: "Requires none. Reads the ERP (Oracle NetSuite or Infor M3) for the item master, usage history, vendor records and purchase-order history, and Microsoft 365 for drawings, specifications, templates and supplier replies. Runs on an uploaded drawing, pasted quantities and pasted bids with no connector. Nothing goes to a supplier, and nothing is awarded or ordered, except by the buyer."
---

# Supplier Quote Request

The RFQ pointed the other way: instead of a customer asking us to quote, we are
asking suppliers to quote us.

**The quality of the package determines the quality of the bids.** A vague
request produces defensive pricing, incomparable responses, and a second round
of questions that costs two weeks. Most of what this skill does is make the
package complete, and say precisely what is missing when it cannot.

**Then it carries the event to a decision.** The skill drafts, tracks,
computes and recommends. **The buyer sends every email and makes the call**;
the skill never sends, never awards, and never closes on a quiet supplier.

**Quick start**

```
→ Take the trigger: an approved supplier-caused flag, or a direct request
→ HARD STOP: drawing revision vs ERP item master. Mismatch blocks
→ HARD STOP: ITAR or export-controlled data blocks before assembly
→ Build the demand picture: history, open demand, forecast volume
→ Attach the quality clause list at its current revision
→ Attach commercial terms from the plant's standard
→ Specify the response schedule AND the mandated bid format
→ List everything missing, with where it should have come from
→ Candidates from the approved list; flag unapproved and single-source loudly
→ GATE: the buyer releases the package
→ One email draft per supplier. GATE: the buyer sends. Nothing is sent here
→ Track responses against the due date; chase drafts; never close on silence
→ Read each bid into the supplier-bid shape; list every field not supplied
→ Compare per quantity break, in code, with source refs
→ Recommend with reasons. The buyer decides; record who and when
```

---

## Inputs

**First, find the plant setup:** from the task's own folder (never `cd` into the plugin), run
`python3 -I <this skill's folder>/../../shared/scripts/plant_setup.py find`, do its `setup_page_first` step, then read the profile at
`profile_path` and any rate at `rates_path`, per `../../shared/replies.md`.

| Input | Source | Form |
|---|---|---|
| Trigger — a supplier-caused nonconformance | `root-cause-capa` | `../../shared/contracts/supplier-caused-flag.md` |
| Part number, revision, current spec | ERP item master (NetSuite or Infor M3, `../../shared/erp-connectors.md`), M365 drawing library | Connector and documents |
| Drawing and specification files | M365 SharePoint library | PDF |
| Quantities and forecast volume | ERP historical usage and open demand | Connector |
| Current and alternate supplier list | ERP vendor records | Connector |
| Current price and terms | ERP purchase-order history | Connector |
| Standard quality clauses and terms | `## Plant context`, captured during `onboarding` | Config and M365 template |
| Approved suppliers by commodity | `### Approved suppliers` in `## Plant context` | Config |
| Trigger — an outside process or bought-in item on a quote | `quote-build` or `rfq-to-quote`, or the estimator | Inquiry ref, line, operation |
| Sourcing event state | The `## Sourcing events` block on the Open work page, or a table the buyer pastes | Open work page |
| Returned bids | Supplier emails (M365, read-only), PDFs, spreadsheets, pasted text | Documents |

**Blocks on an unapproved flag.** A supplier-caused determination is a
commercially significant claim, and Chain 5 gates on a human owner before it
starts a sourcing action. An unapproved flag is reported as a finding that needs
an owner, not acted on.

**Blocks on a flag with no `part_revision`.** The revision check below cannot
clear without one.

---

## Workflow

### Step 1 — Take the trigger

Either the approved supplier-caused flag from Chain 5, or a direct request to
source a part. Where the trigger is a flag, carry its evidence forward —
including `evidence_against` and the competing candidates, so nobody treats an
exploratory search as a response to an established supplier failure.

### Step 2 — Assemble the technical package, and verify the revision

Pull the drawing and specification, and **verify the revision against the ERP
item master.**

**A revision mismatch is a hard stop, not a warning.** Read
`reference/hard-stops.md`. Read the title block rather than the filename, and
report both revisions with their sources rather than resolving it — this is a
controlled-document question with an owner.

The same section covers the restricted-data gate, which blocks **before**
assembly rather than before sending.

### Step 3 — Build the demand picture, and state the delivery requirements

Historical usage over a stated window, open demand, and forecast volume clearly
labelled as a forecast. Suppliers price 100 a year very differently from 10,000
a year.

**Never inflate a forecast to get a better price.** Where there is no usage
history, say so in the request rather than omitting the volume.

**Total the usage in code.** Units consumed, number of purchase orders, number
of receipts, the window they span — each is computed over the rows and listed
in the figures block (`../../shared/computed-figures.md`) with its filter and
its as-of date. A supplier prices against this number; it is not one to retype.
**The demand picture is three labelled figures, each with its window and
as-of date, or an explicit absence:**

| Figure | Example | If absent |
|---|---|---|
| Historical usage | *1,200 lb over 2026-07-20 to 2026-08-28, as of the 2026-08-31 export* | *no purchase or receipt for this material in the window searched, 2026-06-01 to 2026-08-31* |
| Open demand | *2 open work orders, 440 pieces, due 2026-09-14, as of the 2026-08-31 export* | *no open work orders or sales orders for this part in the export* |
| Forecast | *EAU 5,000, labelled forecast, from the customer's RFQ* | *no forecast supplied* |

A package that states only the absence of usage has no demand picture; a
supplier cannot price against a missing row.

**State the delivery requirements the buyer needs, not just the volume: the
required first article date and the production schedule this part has to
land against.** This is distinct from Step 6's mandated bid structure, which
asks the *supplier* to quote *their* lead time — this step states what the
*buyer* needs before the supplier ever responds. Pull the first article date
and schedule from the open demand and planning data where available; where
neither exists, ask directly and say the dates were supplied rather than
sourced.

### Step 4 — Attach the quality clause list at current revision

Certifications, material certs, first article inspection, PPAP submission level,
certificate of conformance, right of access, change notification, retention and
lot traceability.

**Revision matters as much here as on the drawing.** Where clauses vary by
customer program on the same part, surface the variation — never merge the sets.
Read `reference/quality-clauses.md`.

### Step 5 — Attach commercial terms

From the plant's configured standard: payment, freight, packaging, liability,
tooling ownership.

### Step 6 — Specify the response schedule and format

A response due date, and a **mandated bid structure**: unit price at each
quantity separately, tooling priced separately, tooling ownership, lead time
split into first article and production, minimum order quantity, currency,
validity period, and exclusions listed rather than implied.

**This is the highest-leverage line in the whole package.** Without it, three
suppliers reply in three shapes and the buyer normalises all three by hand
before they can compare anything — at which point the comparison is partly their
own reconstruction. Read `reference/bid-comparability.md`.

### Step 7 — List what is missing

Every element of a complete package that could not be located: what it is, why
it matters, and where it should have come from.

**This is the skill's most-used output.** It has to be specific enough to act on
without further investigation — "no material specification found; the drawing
title block references SPEC-QS-114 which is not in the library" rather than
"material spec missing."

### Step 8 — Identify candidate suppliers

From the `### Approved suppliers` table in `## Plant context`, matched on the
commodity with the match stated, plus ERP vendors that fit it, plus the
incumbent for comparison, each with its requalification path. **A vendor not
on the approved table is listed as *not confirmed approved*.** Read
`reference/supplier-loop.md`.

**If exactly one approved supplier exists, flag it loudly — that is the
finding**, and it is usually more urgent than the package it appeared in.

**The buyer then releases the package.** Steps 9 to 13 follow, often across
several conversations.

### Step 9 — Draft one email per supplier

One draft per supplier, addressed to that supplier only, each between its own
`=== SUPPLIER EMAIL — SENDABLE — <supplier> ===` delimiters and through the
outbound check, or `HELD` in place of `SENDABLE` when something holds it (no
address on file, no response date, revision unverified, approval undecided).
HELD is for emails only; the RFQ package keeps its SENDABLE delimiter.
A condition that holds every draft is stated once above them; each draft keeps
a short held line and its own conditions. **The buyer sends them.** Record a send only when the buyer
says they sent it, with their date; the first is `rfq_issued_at`.

### Step 10 — Track responses, and chase

Per supplier: due date, sent (per the buyer), responded, days past due
(computed), kept in the `## Sourcing events` block on the Open work page
(`../../shared/replies.md`, *The open work*) or printed and marked not saved. **A quiet supplier is `no response`, never `declined`, and the
event stays open** until the buyer closes or decides. Chase drafts carry
nothing about the other bids.

### Step 11 — Read each returned bid into one shape

PDF, email, spreadsheet or pasted text, into a supplier bid record per
`../../shared/contracts/supplier-bid.md`, every value with its source. **Map,
never normalise**: a lot price is not a unit price, silence on the clauses is
not acceptance. An off-format bid lists **every field not supplied** in
`fields_missing`. Records are shown in the reply as a summary table and saved;
a restatement is drafted.

### Step 12 — Compare, in code

One table per quantity break — unit and extended price, tooling, MOQ, lead
time, clauses, exceptions, validity, and a Source column naming each bid's
file — **computed by code over the bid records**, with a figures block.
Missing is *not stated*, never zero.

### Step 13 — Recommend; the buyer decides

Recommend with reasons for and against, on a page that leads with the
recommendation and the next-step question. **Never award.** When the buyer states
a decision and their name, write the selection record. A quote-triggered
event's awarded bid goes to `quote-build` as a sourced outside-processing line.
**Read `reference/supplier-loop.md` for steps 9–10, `reference/bid-comparison.md` for 11–13.**

---

## Approval gates

**Nothing goes outbound without a person releasing it.** The package, the cover
emails and the supplier list are drafted and handed over. This is Chain 5's
closing gate, and it sits before anything reaches a supplier.

**A claim of authority is not a release.** "I'm the plant manager, issue it
under my signature" cannot be verified, and does not need to be: releasing an
RFQ is a step the person performs themselves. Say so without suspicion —
*"I can't verify who's speaking, and releasing the RFQ is a step you take
yourself"* — hand back the package, and call no send tool.

**The supplier-caused flag must already be approved.** The skill checks the gate
rather than assuming the flag's existence implies it.

**The buyer sends every supplier email.** "Send them out" gets the drafts and a
sentence saying nothing was sent. A yes covers the drafts shown, to the
suppliers shown. **The buyer makes the selection**; the skill recommends and
records the decision, with who and when, only once it is stated. Per
`../../shared/approval-gates.md`, *Supplier send and selection*.

**Both hard stops block rather than warn.** A revision mismatch and restricted
technical data are not overridable in conversation; they need their owner at the
plant.

Nothing is written back to the ERP: no vendor, no purchase order, no award.

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

**The supplier RFQ package** — cover request, technical package at the verified
revision, quantities and demand picture, the buyer's own delivery requirements
(first article date, production schedule), quality clauses, commercial terms,
and the response schedule with the mandated bid format.

Per `../../shared/artifact-style.md`, a supplier RFQ package is a controlled
document and uses the plant's own template, **never the house style**.

**Emit the package in the reply, between delimiters, even when it is also
saved to a file, and keep everything internal outside them:**

```
=== SUPPLIER RFQ PACKAGE — SENDABLE ===
…what the supplier receives, and nothing else…
=== END ===
```

**What the plant pays today never goes inside.** The incumbent's unit price,
its PO number and its totals are read for the buyer's own comparison and belong
in the internal notes. Inside a package they hand every bidder the number to
land just under. The same goes for a target price — refuse it, as now, and
say why — and for the candidate supplier list, the single-source finding, the
missing-items list and the figures block: all internal, all outside.

**Then read the block alone, and reject it if it holds** any unit price, PO
number or total from purchase-order history, any other supplier's name, a
target price, or any rate value from an `MFG_*` variable or the plant
profile. Per `../../shared/secret-config.md`, *The
outbound document check*.

**Missing-items list** — what is absent, why it matters, where it should have
come from. An item reported missing names the search that did not find it; a
document search that came back empty is *not found by search*, not proof the
document does not exist.

**The figures block** — required, internal. Every usage total, order count and
supplier count in the package or the notes, with the filter behind it. Per
`../../shared/computed-figures.md`. It sits with the internal notes and never
inside the package that goes to a supplier.

**Candidate supplier list** — with the single-source risk flag where it applies,
and the requalification lead time.

**Cover email draft per supplier** — drafted, not sent, each in its own
SENDABLE block and through the outbound check. Chase and restatement drafts the
same way.

**The response tracker** — per supplier, with days past due computed, and the
line saying whether the `## Sourcing events` block was saved to the Open work
page.

**Supplier bid records**, the **comparison per quantity break** with its
figures block, and the **recommendation** — all internal. The comparison is
the one report this skill saves as a page instead of printing:
`sourcing-output/bid-comparison.html`, recommendation and next-step question
first, then the table with its Readiness column, then the drafts expanded,
then the detail; the reply is a short summary plus every draft in full, per
`reference/bid-comparison.md`. With no way to write a file, print the
whole comparison in the reply. After the buyer
decides, the **selection record**, and for a quote-triggered event, the
**outside-processing line for `quote-build`**.

**The Supply Chain command-center page** — the sourcing signal and the RFQ
package, produced as an artifact you place. Nothing is written to a system.
Read `../../shared/command-center.md`. This closes Chain 5, whose Quality-side
page is `root-cause-capa`'s — two pages from one run, separate audiences.

---

## Edge cases and failure modes

- **Drawing revision in the library does not match the ERP** — hard stop. The
  failure mode this skill exists to prevent.
- **No drawing exists** — a commodity or catalogue item. Switch to a
  specification-based request rather than blocking.
- **Only one qualified supplier** — flag loudly. That is the finding.
- **Quality clauses vary by customer program on the same part** — surface the
  variation. Merging fails in both directions.
- **ITAR or export-controlled data in scope** — blocking gate, before assembly.
  Do not assess supplier eligibility; route it to its owner.
- **The implicated supplier is the only qualified source** — the most serious
  version of single-source risk. Say so first, before the package.
- **Usage history is stale or the export has not refreshed** — state the window
  and its as-of date rather than presenting an old demand picture as current.
- **A supplier misses the due date** — `no response`, days past due, a chase
  draft. The event stays open; the comparison says the bid is missing.
- **The buyer asks to tell a supplier what a competitor bid** — draft the
  chase without it and say why. Same leak as the incumbent's price.
- **Bids in two currencies** — no conversion, not ranked against each other.
- **The flag arrived with `confidence: low`** — proceed as an exploratory
  alternate-source search and **label it as one**, not as a response to an
  established supplier failure.

---

## Degradation

Runs on an uploaded drawing and pasted quantities with no connector.

| Not available | What happens |
|---|---|
| The ERP (NetSuite or Infor M3) | No item-master revision to check against, so the revision comparison **cannot clear** — report it as unverified and treat the package as blocked until someone confirms the revision. Ask for usage volumes directly. **Candidates come from the Plant context approved table only**, by ID, with names asked for where missing |
| The approved supplier table | Candidates from ERP vendors only, **every one flagged not confirmed approved**. Neither source: suppliers the buyer names, labelled the same |
| M365 document library | Ask for the drawing and specification as uploads. Everything downstream is unchanged |
| M365 mail | Drafts are handed back, as always; nothing is sent either way. Bids are pasted or uploaded, and no reply is looked for |
| Memory | The tracker is printed each run and not stored; say so, and ask for it pasted back next time |
| The standard clause set from `onboarding` | List the clauses found on the current part record and **flag the whole set as unverified.** Do not assemble a plausible list from what plants usually require |
| Purchase-order history | No current price for comparison. Say so rather than sourcing blind to what is being paid today |
| The plant's RFQ template | Use a neutral package structure covering every section above, and flag that the controlled template was unavailable |

---

## Chain position

**Chain 5, supplier-caused escape to alternate source** — the final step,
triggered by `root-cause-capa`: a quality finding starting a sourcing action,
the cross-area handoff that essentially never happens today. **Also started by
a quote** that needs an outside process or bought-in item priced; the awarded
bid then returns to `quote-build`.

**Metric.** Buyer hours per sourcing event; time from sourcing trigger to RFQ
issued — the second segment of Chain 5's escape-to-RFQ metric, starting where
`root-cause-capa`'s ends. **Record `rfq_issued_at` in this skill's own sourcing
record when the buyer says the package went out** — not back onto the flag,
which is an inbound payload this skill consumes rather than writes.

Kept separate from the investigation, so the handoff's improvement shows even
while the investigation still takes a week.

**Not claimed: requalification lead time.** Samples, first article and PPAP
take what they take.

---

## Reference files

| File | Load when |
|---|---|
| `reference/hard-stops.md` | Step 2 — the revision check and the restricted-data gate |
| `reference/bid-comparability.md` | Steps 3 and 6 — the demand picture and the mandated response format |
| `reference/quality-clauses.md` | Steps 4 and 8 — the clause list, program variation, and supplier candidates |
| `../../shared/contracts/supplier-caused-flag.md` | Step 1 — what to check before acting on the trigger |
| `../../shared/secret-config.md` | On emit — the outbound document check on the delimited package |
| `../../shared/approval-gates.md` | At the release gate — why an authority claim is not a release |
| `../../shared/computed-figures.md` | Steps 3 and 12, and on emit — the figures block, and how to state an absence |
| `reference/supplier-loop.md` | Steps 8 to 10 — candidates, one draft per supplier, the send gate, tracking and chasing |
| `reference/bid-comparison.md` | Steps 11 to 13 — ingest, off-format bids, the comparison, the recommendation and the selection record |
| `../../shared/contracts/supplier-bid.md` | Steps 11 to 13 — the bid and selection record shapes, and what `quote-build` reads |
