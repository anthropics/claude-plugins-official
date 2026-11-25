---
name: inspection-to-capa
description: "Runs the quality chain end to end: writes the nonconformance against the requirement it violates, searches history at the moment of writing to say whether this has happened before and whether the last fix held, reads sensor and inspection data on one verified timeline, proposes ranked candidate causes with evidence for and against, drafts the 8D, and produces the customer pack behind a redaction diff. Use when someone says \"run the CAPA chain,\" \"take this nonconformance through to an 8D,\" \"inspection to CAPA,\" or asks for the full corrective-action workflow."
compatibility: "Requires none. Chains ncr-writeup and root-cause-capa. Reads Microsoft 365 and the ERP (Oracle NetSuite or Infor M3) where connected; runs on pasted findings and file exports with no connector. Never asserts a requirement it cannot locate, never correlates across clocks it could not align, and nothing customer-facing leaves without review of the redaction diff."
---

# Inspection to CAPA

Chain 2. `ncr-writeup` → `root-cause-capa`.

The path from "we found a bad part" to "we fixed the reason, and we can prove
it." It ends on the 8D and its redacted customer pack.

**Quick start**

```
→ Write the NCR against a CITED requirement. Cannot find one? Block. Never invent
→ Search history AT CREATION, not on request. Did the earlier fix hold?
→ Gate 1: the quality owner confirms the NCR and its containment
→ Verify the clocks BEFORE correlating. Misaligned? Refuse, and say what survives
→ Ranked candidate chains with evidence FOR and AGAINST. Never one verdict
→ 8D: D1-D5 and D7 populated. D6 and D8 stay empty placeholders
→ Gate 2: nothing customer-facing leaves without the redaction diff reviewed
```

---

## Inputs

| Input | Source | Form |
|---|---|---|
| The finding | Inspector notes, an inspection export, an operator report, a customer complaint | Conversation, M365, pasted |
| Everything else | Whatever the two member skills read | See each skill |

---

## The seven steps

**1. An inspection result or a suspect lot starts it.**

**2. Write the nonconformance** against the requirement, with quantity and
location. All five containment locations are addressed, including with a zero
quantity, because an omitted location reads as "none there" rather than "not
checked."

**Gate 1** — the quality owner confirms the NCR and the containment plan.
**This is a pause, and the chain says so:** *"Paused at Gate 1, after step 2.
The NCR is a draft. A quality owner confirms four things before step 4 — the
finding, the cited requirement, the suspect scope, and the containment plan."*
A missing citation is one reason the NCR is not ready; it is not the gate.
Fixing the citation does not unblock the chain — the owner's confirmation does.
The history search in step 3 still runs at write time, because it belongs to
the NCR. Per `../../shared/approval-gates.md`.

**3. Search history for the same problem.** This runs automatically at write
time, not on request, because the moment of detection is the only moment anyone
is looking.

**Whether the earlier fix held is the highest-value single line in this
chain.** A recurrence after a *closed* CAPA is a materially different finding
from a first occurrence, and it changes what happens next. Surface it as such.

**4. Read the prior tickets, inspection data and production history together**,
aligned onto one zone-aware timeline. Verify the clocks first; where alignment
cannot be verified, refuse to correlate and say which conclusions survive
anyway.

**5. Propose ranked candidate causal chains**, each stated as a chain with
supporting *and contradicting* evidence attached to each link, and the cheapest
test that would confirm or kill it. Never one confident verdict: a confident
wrong root cause closes the investigation and the fix fails.

**6. Draft the 8D.** D1 to D5 and D7 populated from the evidence. D6 and D8
stay as structured placeholders, because they need a real-world outcome and a
human signature.

**7. Produce the customer-facing pack with a redaction pass.** **Gate 2.**

---

## Approval gates

| Gate | Where | What it protects |
|---|---|---|
| 1 | After step 2 | The quality owner confirms the finding, the cited requirement, the suspect scope and the containment plan |
| 2 | After step 7 | Nothing customer-facing leaves without review of the **redaction diff** |

The redaction pass is a reviewable diff, never a silent filter. The internal 8D
carries cost data, other customers' names, supplier identity and internal
process detail; the customer version must not. **A recurrence stays in** —
removing it is misrepresentation, not redaction.

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

The NCR in the plant's controlled template, the containment plan ordered by
urgency, the recurrence finding with whether the previous fix held, the ranked
candidate causes with their discriminating tests, the drafted 8D, the evidence
appendix, and the redacted customer pack.

**The figures block** — required, inside the evidence appendix. Every
measurement, control limit, ratio and count the chain states is printed from
the computation and listed with it, and the prose quotes the block. Two member
skills doing the same arithmetic must not arrive at two different multiples of
the same limit. Per `../../shared/computed-figures.md`.

Where the leading candidate points at purchased material, the **supplier-caused
flag** is raised, which is the trigger into Chain 5. See
`supplier-escape-to-alternate-source`.

**The Quality command-center page: the Quality Register** — open corrective
actions, carrying the NCR and the 8D by reference, updated in place per
`../../shared/live-dashboard.md`. **The chain writes no register row of its
own.** `ncr-writeup` writes the row at step 2 and `root-cause-capa` adds the
8D fields at step 6, both keyed `<site>_<ncr_ref>`, so one chain run leaves
one row. The chain reports the register once, at the end: the dashboard line
with its URL and the sensitivity line, or the fallback with *"The Quality
Register was not updated: [reason]."* It is reported as updated only when a
publish returned a URL in this run, and never as shared. Read
`../../shared/command-center.md`.

---

## Edge cases and failure modes

- **The requirement cannot be located** — the chain **blocks at step 2**. Never
  invent one. That is a complete and honest outcome.
- **Traceability is incomplete** — the suspect scope **widens** and says why.
  Never narrow it to make the number look better.
- **The clocks cannot be aligned** — step 4 refuses to correlate. Non
  time-dependent analysis still runs, and the output says which is which.
- **Two candidates are supported equally** — present both. A stated tie is a
  real finding, and it names the test that would settle it.
- **No prior history exists** — say so. Absence of recurrence is not evidence
  of a one-off.

---

## Degradation

| Not available | What happens |
|---|---|
| The quality document library | Report "no searchable history available" at step 3. **Never silence**, which reads as "no recurrence" |
| The sensor export, or it misses the event window | Say so. Do not reason from adjacent data as if it were the event |
| The plant's 8D template | Use the standard eight-discipline structure and flag that the controlled template was unavailable |
| A CMMS connector (Limble or any other) | See below |

**Check the freshness of every export before correlating on it.** A scheduled
export that silently stopped produces a timeline with a hole in it, and the
hole looks like an absence of evidence rather than an absence of data. State
the coverage window of each source in the evidence appendix.

**If Limble isn't included, or no CMMS connector is live** — minor here. Maintenance history arrives in the
same scheduled export as everything else and the maintenance-correlation check
runs on it unchanged. What changes is freshness: name maintenance explicitly as
an export-sourced input in the evidence appendix rather than letting it read as
live, since a repair logged after the last export will not be on the timeline
at all.

---

## Chain position

**This is Chain 2 itself.** Members: `ncr-writeup`, `root-cause-capa`.

**Metric.** CAPA closure time and first-pass yield, both owned by
`root-cause-capa`. `ncr-writeup` also moves nonconformance closure time and
escape response time inside this chain; the chain does not claim them, because
it is named for the corrective-action loop.

---

## Reference files

| File | Load when |
|---|---|
| `../ncr-writeup/SKILL.md` | Steps 2 and 3 |
| `../root-cause-capa/SKILL.md` | Steps 4 to 7 |
| `../../shared/contracts/ncr.md` | The handoff, and what blocks `root-cause-capa` |
| `../../shared/command-center.md` | The Quality page, and when "updated" may be said |
| `../../shared/live-dashboard.md` | The Quality Register: one row per NCR, the banner, the fallback |
| `../../shared/computed-figures.md` | Before stating any figure — the figures block |
| `../../shared/approval-gates.md` | At both gates — a gate is a pause, and how to say where the chain stopped |
