---
name: rfq-to-quote
description: "Runs the whole RFQ-to-quote chain end to end: reads the inquiry and its drawings, checks it against what the plant can build, drafts the questions back, returns a provisional bid/no-bid, pulls cost history, routings and closed-job actuals, builds an internal estimating model in Fusion where connected (from the drawing, a prior part's model saved as new, text specs as a ROM only, or a STEP file), derives machine hours per operation with each hour's basis labelled, and drafts the quote with its cost basis shown. Four approval gates, and the chain pauses for days while the customer answers. Use when someone says \"run the RFQ chain,\" \"take this RFQ all the way to a quote,\" \"quote this end to end,\" \"quote this from the drawing,\" or names an inquiry and asks for the full workflow."
compatibility: "Requires none. Chains customer-inquiry-intake, data-consolidate and quote-build, and runs the design step itself. Reads Microsoft 365 and NetSuite or Infor M3 where connected, and Autodesk Fusion (desktop, open) for the design step and CAM hours; runs on a pasted RFQ and file exports with no connector, with every missing piece labelled. Nothing reaches a customer without the estimator releasing it. Resumable: answers arriving days later re-enter the chain rather than starting a new one."
---

# RFQ to Quote

Chain 1. `customer-inquiry-intake` → `data-consolidate` → design step →
`quote-build`.

**This chain does not run in one sitting**, and building it as though it does
is the main way it goes wrong. Steps 1 to 5 happen when the RFQ lands. Then it
pauses while the customer answers, often for days, which is usually the longest
single stretch in quote turnaround. Treat the inquiry as resumable state.

**Every member step runs through its member skill — load its SKILL.md before
the step, and produce what it produces.** Steps 1 to 5 are
`customer-inquiry-intake`; step 6 is `data-consolidate`, backflush check
included; steps 9 to 11 are `quote-build` with its
`../quote-build/reference/hours-ladder.md`, ending in its two delimited documents. A chain
that prices from memory of its members drops exactly the rules that make the
price defensible: the ladder, the default variance threshold, the outbound
check.

**Quick start**

```
→ Steps 1-5 on arrival. Then STOP and wait for the customer
→ Step 3 can short-circuit: a hard disqualifier ends the sequence before we ask anything
→ Step 5 never waits. Provisional score on what is known
→ Answers re-enter at step 2, NOT step 5. The gaps register shrinks and step 5 re-scores
→ No answer? Stale. Never cancelled, never declined
→ Step 6 BEFORE step 7: a current-revision routing makes the design a cross-check, not the basis
→ Step 7 builds an internal model per path: C2 drawing, B prior model saved as new, A text (ROM only), C1 STEP (unverified)
→ Integrity check before and after every CAD step. The prior model is never overwritten
→ Fusion missing? Hand-entered features or no design step. Labelled, never a stop
→ Four gates: send questions, confirm bid/no-bid, confirm the design, release the quote
```

---

## Inputs

**First, find the plant setup:** from the task's own folder (never `cd` into the plugin), run
`python3 -I <this skill's folder>/../../shared/scripts/plant_setup.py find`, do its `setup_page_first` step, then read the profile at
`profile_path` and any rate at `rates_path`, per `../../shared/replies.md`.

| Input | Source | Form |
|---|---|---|
| The RFQ and its drawings | M365 mail and attachments, a folder, or pasted | PDF, XLSX, DOCX, image, email body, STEP |
| Customer answers, when they arrive | Conversation, or a forwarded reply | Text |
| Routings and closed-job operation actuals | Through `data-consolidate` | Dataset v4 |
| Machining data | `### Machining data` in the `## Plant context` block | Config |
| Fusion, for the design step | The desktop app, with the connector | Live CAD connection |
| Everything else | Whatever the three member skills read | See each skill |

---

## The twelve steps

**1. The RFQ arrives**, in whatever format the customer sent it. Hand it to
`customer-inquiry-intake`. A multi-attachment package is one inquiry.

**2. Extract into the intake form**, with missing and ambiguous flagged
separately, every tolerance carrying how it was read, and **each line's
`geometry_path` classified** — `C2` drawing, `C1` STEP, `B` prior part, `A`
text only, `none`. This is also where a customer's later answer re-enters.

**3. Check against the plant's constraints.** A **hard disqualifier stops the
sequence here** with a no-bid recommendation and its specific reason, before
the plant engages the customer at all. There is no point asking five questions
about a part the plant cannot make.

Two limits, both load-bearing. It stops the *sequence*, not the inquiry: the
estimator can override and proceed, and the inquiry stays open. And only
violations determinable from **stated facts** qualify. Anything resting on a
missing field is a scoring input for step 5, not a stop.

**4. Draft the open questions** back to the customer, as sendable email text —
including a drawing with no revision and any change the customer says is
pending. **Gate 1** — the estimator sends them. Nothing goes to a customer
from here. When they say they have, record `questions_sent_at` and `_by`: the
stale clock starts there.

**5. Return the provisional bid/no-bid**, with its reasoning and the specific
unanswered questions that would change it, **per line as well as overall**: an
RFQ whose lines deserve different answers is `partial`, with each line's
`line_recommendation`. **Gate 2** — the estimator confirms or declines, per line
where the lines differ, and `bid_decision_basis` records what they ruled on.

**Step 5 never waits.** Most RFQs arrive with at least one gap, so a
recommendation that blocked on answers would stall the chain on nearly all of
them. It sits after the questions rather than at the front because a sound call
often needs those questions already in flight, but it is still ahead of every
costing step.

**Then the chain stops.** While any drafted question is unanswered, the first
pass ends here, and says so in these terms: *"Paused after step 5, at Gate 1 and
Gate 2 — the questions are drafted for you to send, and the bid/no-bid is
provisional until you confirm it. Steps 6 to 11 run when the customer answers,
or when you tell me to quote with those questions as exclusions."* **No
customer-facing quote — no price, no lead time, no terms — is drafted in the
same pass as the questions it depends on**, even when the request was "take
this all the way to a quote." A quote built on an open question prices a guess,
and once it exists it gets sent. The estimator may still choose to quote on
exclusions; that is their call at Gate 2, made after seeing the questions, not
a default.

**A pause is saved, so a new session can resume it.** Save the intake form on
the Open work page as the contract names it, with `open_questions` word for
word as sent, set `paused_at_step` and `waiting_on`, and write the inquiry's line to the page's `## Open inquiries`
block, per `../../shared/contracts/intake-form.md` and
`../../shared/replies.md`. Name the page and the file on it. On resume, bring
in the page, read the line, open the form from it, and continue at
`paused_at_step`; never start the inquiry over.

**6. Pull cost history, comparables, routings and operation actuals** via
`data-consolidate` and the ERP, with the backflush check — load
`../data-consolidate/SKILL.md`; actuals agreeing within 1% are
`probable_standard`, all of them, not the one that happens to equal the
routing. **This runs before
the design step on purpose:** where a current-revision routing or trustworthy
actuals exist, the model is a cross-check, not the basis.

**7. The design step.** Per line, by path, build the internal estimating model
in a new Fusion document, every feature citing its source, with the
document-integrity check before and after: **C2** from the drawing; **B** by
opening a different prior part's model, applying the drawing's changes and
saving as a new document, the prior model never overwritten, falling back to
C2 when it is unavailable; **A** from text specs, every dimension `from_text`,
**a ROM only, never a firm quote**; **C1** by importing the STEP and reading
it, nothing generated, **the import unverified**. Emit the
**geometry estimate**, `approval.status: draft`, per
`../../shared/contracts/geometry-estimate.md`. **Skipped for a line with a
current-revision routing** unless the estimator asks for a cross-check. Read
`reference/design-step.md` before the first CAD call.

**8. Gate 3 — the estimator confirms the design.** The model, the tolerance
reading, the datum assumptions (every `inferred` datum, by name), the operation
list, and the open questions the model raised. A line priced from a current
routing still passes Gate 3 on the routing's operation list and the tolerance
reading. **No geometry-derived hour is computed for the quote until this yes,
or an override the estimator gives and the record keeps.**

**9. The hours step**, through `quote-build` — load `../quote-build/SKILL.md`
and `../quote-build/reference/hours-ladder.md` first: the CAM path where Fusion
Manufacturing and plant cutting data exist, the feature path always — setup
hours and run minutes per operation, low, expected and high, each labelled with
its basis, each toolpath verified by geometry.

**10. The ladder per operation**, through `quote-build`: routing, then
recorded actuals, then geometry-derived, then first principles; variance where
two exist; setup and run apart; capability flags; the load check by work center.

**11. The customer quote and the internal sheet**, as `quote-build` emits them:
`=== CUSTOMER QUOTE — SENDABLE ===` and `=== INTERNAL COST SHEET — NOT FOR
CUSTOMER ===`, each closed with `=== END ===`, the outbound check run on the
first. **Gate 4** — the estimator reviews and releases.

**12. When something comes back.** See *Resuming*, below.

---

## Approval gates

**Four, and the count matters** — a reader who thinks there are three has lost
the one that stops an unconfirmed model pricing a job, and a reader who thinks
there are two has lost the one that stops mail reaching a customer.

| Gate | Where | What it protects |
|---|---|---|
| 1 | Step 4 | The estimator sends the questions. No mail leaves on anyone's behalf |
| 2 | Step 5 | The estimator confirms bid/no-bid. This is what makes the chain valuable rather than merely fast |
| 3 | Step 8 | The estimator confirms the model, the tolerance reading, the datum assumptions and the operation list. Hours are derived from what was confirmed, not from what was generated |
| 4 | Step 11 | The estimator releases the quote |

Nothing reaches a customer without human release. The generated model never
reaches a customer at all.

**Asked where sign-off is needed, answer with this table** — each gate, its
step, and what the estimator does there. "All four gates are still with the
estimator" is true and tells them nothing. And whenever the chain stops, it
names the gate and the step it stopped at. What a yes at a gate does and does
not cover — including that a Gate 3 yes does not carry to a later drawing
revision — is `../../shared/approval-gates.md`.

---

## Resuming

### When the answers come back

**An answer is new source material.** It re-enters at **step 2**, not step 5 —
it is extracted like anything else with its own source reference, the gaps
register shrinks, and step 5 re-scores on the fuller picture.

It **revises the existing inquiry**. It never opens a new one. When the
inquiry came from the Open work page, **the reply's first line says so**:
*"Picking up EH-RFQ-0912 from your Open work page, paused at step 5."* Match
each answer to its question by the numbers in the saved `open_questions`.

**Where an answer flips the recommendation, say so and say why.** A
recommendation that silently reverses between two readings is worse than either
version of it. **And an earlier Gate 2 yes lapses**: it covered the
recommendation as shown in `bid_decision_basis`, not the new one. Return the
decision (and the changed line's) to `draft`, set `bid_decision_reset` to what
changed, and ask Gate 2 again naming the change. Never quote a line on a yes
given before it flipped.

### When a revised drawing arrives

**A new drawing revision re-runs step 7** for the lines it touches: a new
model, a new geometry estimate, a new Gate 3. The previous Gate 3 yes covered
the previous revision and nothing else. Hours and price follow from the new
confirmation.

### When the customer counters on price

**A price counter does not re-run step 7 and never reopens CAD.** Nothing about
the part changed. `quote-build` re-derives from the stored operation record,
and the revision goes through Gate 4 like any other.

### When they never come back

After the interval (`MFG_RFQ_STALE_DAYS`, the profile, or 5 business days by
default, per `customer-inquiry-intake`) the inquiry surfaces as **stale**, carrying its
provisional recommendation and its still-open questions, so the estimator
quotes it with exclusions or drops it deliberately.

**A declined inquiry is never surfaced as stale**: it has been decided.

**Stale is a visibility change, never a status change.** Nothing here cancels,
declines, closes or no-bids an inquiry because a customer went quiet. Letting
it go quiet is how an RFQ joins the unbid book, which is one of this chain's
own metrics.

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

Everything the member skills produce, in order: the intake form, the open
questions as sendable text, the provisional recommendation with what would
change it, the **geometry estimate** per line (or the reason there is none),
the customer-facing quote, the internal cost-basis sheet with its **hours-basis
table** — rung, path, cutting-data basis, setup and run, range, variance and
drivers per operation — and the assumptions and exclusions list.

**The Sales command-center page** — commercial performance for the period,
carrying the intake record and the quote by reference. An artifact you place;
nothing is written to a system. Read `../../shared/command-center.md`.

---

## Edge cases and failure modes

- **A hard disqualifier fires at step 3** — the chain stops before step 4. The
  inquiry stays open and the estimator may override.
- **The estimator declines at Gate 2** — `quote-build` blocks. Reopening is a
  new decision, not a quote.
- **The estimator declines the model at Gate 3** — no geometry-derived hours.
  Correct the model and re-confirm, or price from the rungs that remain.
- **A revised RFQ arrives mid-chain** — it supersedes, and the chain resumes
  against the revision rather than running twice.
- **The customer answers only some questions** — re-score on what arrived, and
  keep the rest open. Partial is normal.
- **The only routing is for an earlier revision** — superseded. Step 7 runs as
  though there were no routing, and the old routing is shown, never priced.
- **Foreign geometry appears in the Fusion document** — the step fails. Ask
  the user to restart Fusion. Never build on top of it.
- **Asked to update the prior part's model in place (path B)** — decline in
  one line. The adapted model is always a new document.
- **Asked to send a path A line as a firm quote** — decline. A firm quote
  needs a drawing, and the drawing re-runs step 7.
- **The model suggests a cheaper way to make the part** — it goes in
  `cost_down_proposals`, on the internal sheet. Never to the customer.

---

## Degradation

| Not available | What happens |
|---|---|
| The ERP (NetSuite or Infor M3) | **Steps 5 and 6 both degrade** to document-based comparables, and the chain says so rather than quietly producing weaker output |
| The capability profile | Step 3 cannot run its constraint check. Say so; do not report a clean check that never happened |
| M365 | Accept the RFQ pasted or uploaded. The chain is otherwise unchanged |
| Fusion | **The chain still completes.** Step 7 offers a hand-entered feature list — prefilled from the drawing as read, every row cited, `origin: hand_entered` — for the estimator to confirm at Gate 3. Without it, step 7 is skipped and the ladder starts at whatever rung exists, down to first principles, labelled. Say "Fusion not connected — no model built" on the internal sheet |
| Fusion Manufacturing (CAM) | Feature path only, and the label says so |
| Plant cutting data | The CAM path runs on library feeds, labelled `fusion_default`, rung 4 |
| Routings and actuals | Tabs named missing. The ladder starts at rung 3 |
| A prior part model (path B) | **Falls back to C2**, built from the drawing in a new document, and says so with the reason. The prior model is never written to |
| CAD, on a STEP file with no drawing (path C1) | **"C1: STEP read without CAD (unverified)"** — the STEP read as a text file, every value cited and labelled unverified. Else a hand-entered feature list, else skip step 7, labelled |
| A drawing (path A, text specs only) | Built from the text, every dimension `from_text`. **A ROM, never a firm quote** — budgetary on the customer document, and nothing about how it was estimated |
| Foreign geometry in the document | Step 7 fails for that line. The user restarts Fusion |

---

## Chain position

**This is Chain 1 itself.** Members: `customer-inquiry-intake`,
`data-consolidate`, `quote-build`, with the design step run here.

**Metric.** Quote turnaround, owned jointly by `customer-inquiry-intake` and
`quote-build`. Hit rate and the unbid book, owned by `quote-build`.

---

## Reference files

| File | Load when |
|---|---|
| `../customer-inquiry-intake/SKILL.md` | Steps 1 to 5 and 2-on-return |
| `../data-consolidate/SKILL.md` | Step 6 — routings, actuals and the backflush check |
| `reference/design-step.md` | Steps 7 and 8 — the paths, the build, the integrity check and Gate 3 |
| `../design-space-explore/reference/cad-adapter.md` | Step 7, before the first Fusion call — the create-from-scratch, save-as-new and STEP import calls, and the connector behaviors that break them |
| `../design-space-explore/reference/adapt-prior-model.md` | Step 7, path B — open the prior model, apply, save as new, never overwrite |
| `../quote-build/SKILL.md` | Steps 9 to 11 |
| `../../shared/contracts/intake-form.md` | The handoff, including `geometry_path`, `bid_decision_state` and `inquiry_state` |
| `../../shared/contracts/geometry-estimate.md` | Step 7's output and what Gate 3 moves |
| `../../shared/command-center.md` | The Sales page, and why it is never a write |
| `../../shared/approval-gates.md` | At every gate — what a yes covers, and how to say where the chain stopped |
