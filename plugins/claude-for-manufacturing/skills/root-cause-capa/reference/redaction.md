# The customer-facing pack, and the redaction pass

The internal 8D and the version that goes to a customer are different documents,
and the difference has to be **visible and approved**, never applied quietly.

---

## What the internal 8D contains that must not leave

| Category | Examples |
|---|---|
| Cost | Scrap value, rework hours, internal rates, the financial impact of the escape |
| Other customers | Any other customer's name, part, program or order appearing in the evidence |
| Internal process detail | Machine capability, cycle times, yields, supplier pricing and terms |
| Supplier identity | Often commercially sensitive, and sometimes contractually protected |
| Personnel | Operator and technician names. See below |
| Other findings | Unrelated NCRs that surfaced during the history search |

**Personnel names come out by default.** A customer needs to know a
work-instruction gap existed and has been closed. They do not need the name of
the person on shift, and once it is in a document that leaves the building
nobody controls where it goes.

---

## What must survive

Redaction is not summarisation, and the temptation to sand off anything
uncomfortable produces a document that says nothing and satisfies no one.

The customer keeps: the requirement that was violated, the condition found with
its measurements, the affected quantity and the containment across the locations
that touch them, the root cause with its confidence, the corrective and
preventive actions, and the dates.

**A recurrence stays in.** If this has happened before and the previous fix did
not hold, the customer is entitled to know. Removing it is not redaction, it is
misrepresentation, and it is the thing that ends a supplier relationship when it
comes out later — as it does.

---

## The diff is the deliverable

**Produce the redaction as a reviewable diff, not a filtered output.**

**The diff also records what was asked for and refused.** "Take the bit about
it having happened before out of the customer version" is a removal request; it
is refused, the recurrence stays in, and the diff carries the entry: requested
by, what, refused, why. A refusal that lives only in the chat is invisible to
the quality owner who approves the diff and to the auditor who reads it later.
Where the pack is still blocked and there is no diff yet, emit a "Pending
redaction log" with the same entry now.

The quality owner approves the diff, not the redacted document. The reason is
specific: reading a clean customer version tells you nothing about what was
taken out, and the risk in this operation runs in both directions — something
sensitive left in, or something the customer needed removed.

Show, side by side, every change with its reason:

| Location | Internal | Customer version | Why |
|---|---|---|---|
| D2 | "480 parts, $18,400 at standard cost" | "480 parts" | Cost |
| D4 evidence | "LOT-77219 from Example Steel" | "the implicated material lot" | Supplier identity |
| D4 evidence | "same cell that ran 4402 for Example Medical" | "the same cell" | Another customer |
| D3 | "Held at cell B by R. Nunes" | "Held at the cell" | Personnel |
| D5 | unchanged | unchanged | — |

**Never a silent filter.** A redaction that happens invisibly is one nobody has
checked, and this document is going to a customer under a contractual format.

---

## Two things the pass must not do

**Do not soften the finding.** Redaction removes information the customer should
not have. It does not turn "the process was out of control from 08:20" into "a
process variation was observed." The second sentence is a different claim and it
is not true.

**Do not redact into incoherence.** If removing the supplier's identity leaves
D4 unreadable, that is a decision for the quality owner — say so in the diff and
let them make it. Sometimes the right answer is that the customer is told a
material supplier is implicated without being told which, and sometimes the
contract requires the name. That is their call, not the skill's.

---

## The gate

Nothing customer-facing leaves without the quality owner reviewing the diff and
approving it. This is Chain 2's closing approval gate.

The redacted pack is a draft, produced in the customer's controlled template,
handed to a person. It is not sent.
