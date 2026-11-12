---
name: supplier-escape-to-alternate-source
description: "Runs the cross-area chain from a nonconformance traced to purchased material through to an alternate-source RFQ: writes the NCR and its containment, establishes root cause against the supplier rather than the process, records the corrective action, then builds the sourcing package with a response format that makes the returned bids comparable. Use when someone says \"run the supplier escape chain,\" \"a supplier caused this, find us an alternate,\" \"supplier escape to alternate source,\" or asks to source around a supplier who caused a defect."
compatibility: "Requires none. Chains ncr-writeup, root-cause-capa and supplier-quote-request. Reads Microsoft 365 and the ERP (Oracle NetSuite or Infor M3) where connected; runs on pasted findings, uploaded drawings and file exports with no connector. A supplier-caused determination needs a human owner before it acts, and nothing reaches a supplier without release."
---

# Supplier-Caused Escape to Alternate Source

Chain 5. `ncr-writeup` → `root-cause-capa` → `supplier-quote-request`.

**The plugin's cross-area proof point.** A quality finding automatically
starting a sourcing action essentially never happens today, because quality and
purchasing live in different systems and different departments. That handoff is
the whole point of this chain.

If a part has exactly one qualified supplier and that supplier has a quality
problem, production stops. Sourcing an alternate is insurance, and the value is
in starting early: qualifying one takes weeks to months and nothing here
shortens that.

**Quick start**

```
→ A nonconformance traced to purchased material starts it
→ Root cause established against the SUPPLIER, not the process
→ Gate 1: a supplier-caused determination is a commercial claim. It needs an owner
→ Corrective action recorded
→ Build the alternate-source RFQ. Response format forces comparable bids
→ Gate 2: nothing outbound without release
→ THREE timestamps, not two. The middle one cannot be reconstructed later
```

---

## Inputs

| Input | Source | Form |
|---|---|---|
| The nonconformance | Inspector notes, an inspection export, a customer complaint | Conversation, M365, pasted |
| Drawing and specification | M365 document library | PDF |
| Everything else | Whatever the three member skills read | See each skill |

---

## The four steps

**1. A nonconformance traced to purchased material starts it.** `ncr-writeup`
writes it against its requirement, scopes the suspect quantity, and places every
part across the five containment locations. Where containment finds parts at or
past a customer, the escape notification drafts automatically against its
contractual clock.

**2. Root cause is established against the supplier rather than the process**,
through `root-cause-capa`. Lot clustering is the signal that points here: do
the failures group by material lot rather than by shift, operator or machine?

**Gate 1** — a supplier-caused determination is a commercially significant
claim. It says a named vendor caused a defect and it starts a search for an
alternate source. It needs a human owner.

**3. Corrective action is recorded** — the 8D, with D7 addressing the
system-level change.

**4. Build the RFQ package for an alternate source** through
`supplier-quote-request`: the drawing and specification at the verified current
revision, the demand picture, the quality clauses, the commercial terms, and a
**response schedule that forces comparable bids**.

**Gate 2** — nothing goes outbound until a person releases it.

**The chain ends at release; the sourcing event does not.** After it,
`supplier-quote-request` carries the event on: one email draft per supplier
for the buyer to send, response tracking and chases, the returned bids read
into one shape and compared, and a recommendation. The buyer decides, and the
skill records who and when. Nothing there is a third gate of this chain.

---

## Approval gates

| Gate | Where | What it protects |
|---|---|---|
| 1 | After step 2 | The supplier-caused determination has a named human owner before it acts |
| 2 | Before step 4 sends | Nothing reaches a supplier unreleased |

The flag carries its own `approval_state`, and `supplier-quote-request`
**checks the gate** rather than assuming the flag's existence implies it. An
unapproved flag is reported as a finding that needs an owner, not acted on.

---

## Three timestamps, not two

The chain's headline metric is **time from escape to alternate-source RFQ
issued**, and it cannot be owned by one skill: root cause analysis sits in the
middle of that window and can take days or weeks. So it is measured in two
segments, which needs three stamps.

| Stamp | Written by | On |
|---|---|---|
| `escape_detected_at` | `ncr-writeup`, when containment first places parts at or past a customer | `ncr.md` |
| `determination_made_at` | `root-cause-capa`, when the flag is raised | `supplier-caused-flag.md` |
| `rfq_issued_at` | `supplier-quote-request`, when the package goes out | Its own sourcing record |

**The middle one is the one that gets dropped, and the only one that cannot be
reconstructed afterwards.** The chain's output says so beside the stamp, every
run: *"determination_made_at — the middle of the three; this cannot be
reconstructed afterwards."* A stamp with no such line is the one a later
reader assumes could be backfilled. Without it the two segments collapse into a single
number, and the second segment — the dead time this chain actually eliminates —
disappears behind an investigation that legitimately takes weeks.

Keeping it segmented is what makes the improvement legible. Cutting the handoff
from two weeks to two days shows up even while the investigation still takes a
week. One blended figure would hide which half moved.

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

Two pages from one run, with different audiences:

**Quality** takes the corrective action record — the NCR, the containment plan,
the 8D. **Supply Chain** takes the supplier signal and the sourcing package —
the RFQ, the missing-items list, the candidate suppliers with any single-source
risk flagged. They are separate artifacts, not one page with two sections. Read
`../../shared/command-center.md`.

**The Quality side is the Quality Register.** The NCR and 8D steps of this chain
are `ncr-writeup` and `root-cause-capa`, and each writes its row and updates the
site's register dashboard per `../../shared/live-dashboard.md` — including the
supplier-caused flag. This chain adds no third write. The Supply Chain page
stays a page offered in the conversation, never part of the register.

Plus the escape notification draft where parts reached a customer, and the
cover email per supplier.

---

## Edge cases and failure modes

- **The drawing revision in the library disagrees with the ERP** — **hard
  stop** at step 4. Sending the wrong revision is the classic expensive error
  this exists to prevent.
- **ITAR or export-controlled data** — blocking gate before assembly, not
  before sending.
- **Only one qualified supplier exists** — flag it loudly. That is the finding,
  and it is usually more urgent than the package it appeared in.
- **The flag arrives unapproved** — block. Report it as needing an owner.
- **Evidence points at the supplier but the leading candidate is something
  else** — the flag carries `is_leading_candidate` and `competing_candidates`
  for exactly this. Proceed as an exploratory search and label it as one.

---

## Degradation

| Not available | What happens |
|---|---|
| The standard quality clause set | List the clauses found on the current part record and flag the set as **unverified** |
| No drawing exists (a commodity or catalog item) | Switch to a specification-based request rather than blocking |
| The ERP (NetSuite or Infor M3) | Demand picture and vendor list come from documents or are asked for, and the package says which |
| The quality document library | Recurrence reports "no searchable history available" rather than silence |

**Check the freshness of the usage and demand exports before quoting a volume
to a supplier.** A stale export understates demand, and a supplier priced
against the wrong annual volume returns a bid nobody can use. State the window
each figure came from.

---

## Chain position

**This is Chain 5 itself.** Members: `ncr-writeup`, `root-cause-capa`,
`supplier-quote-request`.

**Metric.** Escape response time, owned by `ncr-writeup`. Time from escape to
alternate-source RFQ issued, owned in two segments: detection and investigation
by `ncr-writeup` and `root-cause-capa`, the sourcing handoff by
`supplier-quote-request`.

**What this chain does not move: requalification lead time.** Qualifying an
alternate takes as long as sample parts, first article inspection and PPAP
take. What it compresses is the dead time before anyone starts.

---

## Reference files

| File | Load when |
|---|---|
| `../ncr-writeup/SKILL.md` | Step 1, and the escape clock |
| `../root-cause-capa/SKILL.md` | Steps 2 and 3 |
| `../supplier-quote-request/SKILL.md` | Step 4, and both hard stops |
| `../../shared/contracts/supplier-caused-flag.md` | The only cross-area handoff in the plugin |
| `../../shared/command-center.md` | The two pages, and why neither is a write |
