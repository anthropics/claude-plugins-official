# Candidate causal chains, and the 8D

---

## Part 1 — Ranked candidates, never a verdict

**A confident wrong root cause is worse than a ranked list, because it closes
the investigation.** Everyone stops looking, a corrective action gets
implemented against the wrong mechanism, it fails, and the next occurrence is a
recurrence after a closed CAPA — the most serious finding in the vocabulary.

So the output is always **ranked candidates with supporting and contradicting
evidence**, never one unqualified answer.

### State each candidate as a chain

Not a label. A chain of steps, each one carrying its own evidence:

> **Candidate 1 — material hardness above nominal**
> `LOT-77219 hardness 232 HB against 187–217 HB required` → `tool wear
> accelerated across the run` → `true position drifted out at OP30`
>
> **For:** material cert on the lot reports 232 HB (cert-77219.pdf p2). All 14
> out-of-tolerance parts trace to LOT-77219, none to LOT-77188 run on the same
> cell that week.
> **Against:** spindle load rose across the run on both lots, which a
> material-only cause does not explain.
> **What would confirm it:** hardness-test three retained parts from each lot.
> **What would kill it:** LOT-77188 parts showing the same drift on re-measure.

Chains matter because they are testable at each link, and because a link with no
evidence behind it is where the reasoning is actually weak. A one-word cause
hides that; a chain exposes it.

### Rank by evidential strength, and say what would settle it

Every candidate carries **the test that would confirm it and the test that would
kill it.** That is what turns a ranked list into a plan — the quality engineer
picks the cheapest discriminating test rather than working the list top-down.

**Where two candidates are supported equally, present both.** Do not break the
tie artificially to produce a cleaner-looking answer. A stated tie is a real
finding: it says the evidence on hand cannot separate them, and it names the
test that would.

### Symptom versus root cause

Keep pushing until the answer is something a system-level change could prevent.

| Symptom | Root cause underneath it |
|---|---|
| The operator misread the print | Two revisions were in circulation and the shop copy was uncontrolled |
| The tool was worn | The tool-change interval was set for a different material |
| The gage read wrong | Calibration lapsed and nothing flagged it |

The left column tells you who to talk to. The right column tells you what to
change so it cannot happen again — which is what D7 needs.

---

## Part 2 — The 8D

Eight disciplines. Many customers, especially in automotive and aerospace,
contractually require this format, which is precisely why it is a good drafting
target: **it is a fixed shape.**

| | Discipline | Drafted from |
|---|---|---|
| D1 | Team | Names from the NCR — who found it, who owns quality — as a proposed team the owner edits |
| D2 | Problem description | The NCR: quantified what, where, when, how many, against which requirement |
| D3 | Interim containment | The NCR's containment plan, by location, with what has already been done |
| D4 | Root cause | The leading candidate **with its ranking and contradicting evidence intact** |
| D5 | Chosen corrective actions | Actions that address D4 specifically, each traceable to the link in the chain it breaks |
| D6 | Implement and verify | **Structured placeholder.** Needs a real-world outcome |
| D7 | Prevent recurrence | The system-level change so the class of problem cannot return |
| D8 | Close and recognize | **Structured placeholder.** Needs human sign-off |

### D6 and D8 stay empty on purpose

They require things that have not happened yet: proof that the action worked,
and a person signing their name. **Leave them as structured placeholders with
the fields laid out** — never pre-filled, never with plausible text a reviewer
might skim past and accept.

An 8D with a drafted D6 is a false record of verification, and in an audit it is
much worse than an incomplete one.

### D4 keeps its uncertainty

The temptation is to flatten the ranked candidates into a single confident D4
because that is what the form looks like it wants. Resist it.

Where the leading candidate is not clearly ahead, D4 says so and names the test
that would settle it. A customer reading an honest D4 with a stated confidence
and a verification plan is being told the truth about where the investigation
stands. That is what the discipline is for.

### D5 traces to D4, link by link

Each corrective action names **which link in the causal chain it breaks.** An
action that does not attach to a link is not a corrective action, it is an
improvement — worth doing, but it belongs somewhere else, and mixing the two is
how a CAPA closes without fixing anything.

### D7 is where recurrence gets prevented

D5 fixes this problem. D7 stops the class of problem. Incoming hardness
verification on that material, a controlled-print process, a calibration alarm
that actually fires — the change that means the mechanism cannot reach a part
again.

Where the recurrence check found a prior CAPA that failed, **D7 must address why
the earlier fix did not hold**, not simply restate it. Proposing the same action
that already failed once is the single most predictable way for this document to
be rejected.

---

## The template

The 8D goes to a customer against a contractual format. Use the plant's or the
customer's own template captured during `onboarding`, and per
`../../../shared/artifact-style.md`, **never restyle a controlled document into
the house look.** Styling it would make it wrong, not nicer.
