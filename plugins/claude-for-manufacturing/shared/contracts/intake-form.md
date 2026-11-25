# Contract: the intake form

**Emitted by** `customer-inquiry-intake`
**Consumed by** `quote-build`
**Chain** 1, RFQ to quote
**Contract version** 7

Rules that govern every contract are in [README.md](README.md).

---

## What this has to survive

An RFQ arrives in no standard format: a PDF drawing package with "can you do
this?" in the email body, a spreadsheet of 40 line items and no drawings, a
portal export with unfamiliar field order, a phone photo of a marked-up print, or
a forwarded thread where the real requirement is in the fourth message down.

The intake form is the single consistent shape all of that collapses into. Two
properties matter most:

**Every field carries where it came from** — which file, which page — so the
estimator can verify without re-reading the package. Rule 6, and it is the
difference between a useful extraction and one that has to be checked from
scratch.

**Missing and ambiguous are separate registers.** A field that was never stated
is a different problem from one stated contradictorily in two places. The first
needs a question to the customer; the second needs a decision. Collapsing them
loses that.

---

## Header fields

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `contract_version` | integer | Required | |
| `site` | string | Required | Which plant would build it, rule 7 |
| `customer` | string | Required | |
| `contact` | object or null | Degrades | Name, email, phone as given |
| `rfq_reference` | string or null | Degrades | The customer's own reference |
| `received_at` | timestamp with zone | Required | Rule 4. Drives quote turnaround, the metric this chain ships against |
| `response_deadline` | date or null | Degrades | |
| `supersedes_rfq` | string or null | Optional | Set when this revises an earlier RFQ. See below |
| `source_documents` | list of objects | Required | Every file in the package: name, type, page count |
| `field_sources` | object | Required | Field name to source_ref, rule 6 — covers every header and commercial-term field below, not just line items |

## Commercial terms

These are on the intake form. They are inquiry-level, not per line.
A stated term that never lands here is how it disappears between intake and the
quote. Sourced through the same inquiry-level `field_sources` object as the
header fields above — never nested inside a line item's own `field_sources`,
which is line-scoped.

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `payment` | string or null | Degrades | As stated. Null if never stated |
| `freight` | string or null | Degrades | As stated |
| `packaging` | string or null | Degrades | As stated |
| `liability` | string or null | Degrades | As stated |

A null term is not an empty string. Null goes in the missing register. A
customer term that clashes with the plant's standard is flagged; it is not
silently accepted.

## Line items

One row per part. **A multi-attachment RFQ is one inquiry with several line
items, never several inquiries.**

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `line_no` | integer | Required | |
| `part_number` / `part_number_verbatim` | string or null | Degrades | Rule 3. Often absent on a new part |
| `description` | string | Required | |
| `revision` | string or null | Degrades | |
| `quantities` | list of objects | **Required** | A structure, not a scalar. See below |
| `material` | string or null | Required | Null if never stated, and `quote-build` blocks that line. Quote the other lines and list this one as blocked |
| `specs` | list of objects | Degrades | Each: characteristic, nominal, tolerance, `reading_basis`, source_ref. See below |
| `finish` | string or null | Degrades | |
| `certifications_required` | list of strings | Degrades | |
| `required_delivery` | date or null | Degrades | Per line; lines can differ |
| `eau` | number or null | Optional | Estimated annual usage, for a repeat part |
| `geometry_inputs` | list of objects | Required, may be empty | Every file or statement the part's shape could be read from. Each: `name`, `type` (`drawing_pdf`, `drawing_image`, `drawing_text`, `step`, `other_3d`, `text_spec`, `prior_part_ref`), `revision` (string or null), `source_ref`. Empty means the package carries no geometry at all, and says so |
| `geometry_path` | enum | Required | `C2`, `C1`, `B`, `A` or `none`, classified from `geometry_inputs`. See below |
| `field_sources` | object | Required | Field name to source_ref, rule 6 |
| `line_recommendation` | enum or null | Degrades | `bid` or `no_bid` for this line alone. Lines in one RFQ often deserve different answers. |
| `line_bid_decision` | enum | Required | `draft`, `confirmed` or `declined`, for this line. Only an estimator moves it. `quote-build` quotes a line only when it is not `declined`. |

### `geometry_path` — how the shape of the part reaches the estimate

Classified per line from what the package actually holds, because it decides
what `rfq-to-quote` can do at its design step. Classifying is reading the
package; it never builds anything.

| Value | When | At the design step |
|---|---|---|
| `C2` | A drawing — PDF, image, or text extract of one | Built from the drawing. The normal case |
| `C1` | A STEP or other 3D file, and no drawing | Imported and read, nothing generated. STEP import is unverified |
| `B` | A drawing, plus a **different** prior part whose CAD model is named as the starting point ("like PN-4402-A but 10 mm longer") | The prior model is opened, the changes applied, and the result saved as a new document; the prior model is never overwritten. Without it, `rfq-to-quote` runs the line as C2 and says so |
| `A` | Written specifications only, no drawing | Built from the text, every dimension `from_text`. Any price on it is a ROM, never a firm quote |
| `none` | No geometry at all — a repeat part named by number only | Not applicable. Priced from its routing, or a question to the customer |

A line is classified by what the package holds, **never relabelled** to a path
it is not.

**A new revision of a part the plant has made before is `C2`, not `B`.** The
drawing is the geometry. The earlier revision is history — its routing and its
actuals are step 6's business, and a superseded routing is not a model to
adapt. `B` is only for a package that names another part's model as the
starting point. Intake cannot see the CAD vault, so where a prior model turns
up later `rfq-to-quote` reclassifies at step 7 and says so.

### `reading_basis` — how each tolerance was read

Every `specs` entry says how its value got onto the form:

| Value | Meaning |
|---|---|
| `printed_callout` | Printed against the feature on the drawing |
| `general_note` | The drawing's general tolerance note, applied to this feature. **That is reading, not inferring**: the `source_ref` cites the note as well as the feature |
| `from_text` | Stated in the RFQ text or a written spec, not on a drawing |
| `unreadable_flagged` | Present but not legible. `nominal` and `tolerance` stay null and the line goes for human review |

There is no value for a tolerance worked out from the feature type or from what
is typical, because that is not permitted at all.

### `quantities` is a structure

A quantity given as a range or with price breaks has its
structure captured and **is never averaged**. Setup cost amortizes across
quantity, so quantity breaks are the whole reason unit price drops with volume —
averaging them destroys the thing `quote-build` exists to compute.

```yaml
quantities:
  - qty: 100
    uom: each
  - qty: 500
    uom: each
  - qty: 1000
    uom: each
```

## The two registers

### `missing_register` — never stated

| Field | Type | Behavior |
|---|---|---|
| `line_no` | integer or null | Required |
| `field` | string | Required |
| `why_it_matters` | string | Required |
| `should_have_come_from` | string | Required |

### `ambiguous_register` — stated more than once, differently

| Field | Type | Behavior |
|---|---|---|
| `line_no` | integer or null | Required |
| `field` | string | Required |
| `values_found` | list of objects | Required. Each value with its `source_ref` |
| `why_it_matters` | string | Required |

## Open questions and the recommendation

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `open_questions` | string | Degrades | Drafted as sendable email text, not a bullet list of field names |
| `recommendation` | enum or null | Degrades | `bid`, `no_bid`, or (from version 7) `partial`: some lines bid, some not. The roll-up of the lines' `line_recommendation`. **Never a decision** |
| `recommendation_reasoning` | list of strings | Required when `recommendation` is set | |
| `constraint_violations` | list of objects | Required when `recommendation` is set | Each: constraint, requested value, plant capability, source, and `is_hard_disqualifier` |
| `recommendation_provisional` | boolean | Required | True while any question is open. The recommendation still exists — it never waits |
| `would_change_recommendation` | list of objects | Required when provisional | Each: the open question, the line it affects (or `all`), and what that line's recommendation becomes under which answer |
| `questions_sent_at` / `questions_sent_by` | timestamp with zone / string, or null | Required once Gate 1 is passed | When, and by whom, the open questions went to the customer. **The stale clock starts here.** Set when the estimator says they sent them. |
| `hard_disqualifier_stopped` | boolean | Required | True when the constraint check ended the sequence before questions were drafted |
| `inquiry_state` | enum | Required | `open`, `stale`, or `superseded`. **Never `closed` or `declined` by this skill** |
| `stale_since` | timestamp with zone or null | Required when `inquiry_state` is `stale` | Rule 4 |
| `answers_received` | list of objects | Optional | Each answer with its date and `source_ref`, rule 6. Answers revise this inquiry; they never open a new one |
| `bid_decision_state` | enum | Required | `draft`, `confirmed` or `declined`. Rule 8 — Chain 1 gates here before the handoff |
| `bid_decision_by` | string or null | Required when state is not `draft` | Which estimator confirmed it |
| `bid_decision_at` | timestamp with zone or null | Required when state is not `draft` | Rule 4 |
| `bid_decision_basis` | object or null | Required when state is not `draft` | The recommendation the estimator ruled on, inquiry and per line, as it stood at `bid_decision_at`. |
| `bid_decision_reset` | string or null | Degrades | Set when a confirmation lapsed because re-scoring changed the recommendation: what changed, and when. |
| `paused_at_step` | integer or null | Required | The Chain 1 step the inquiry is waiting at, or null while it runs. |
| `waiting_on` | string or null | Required when `paused_at_step` is set | Who or what: *"Example Valve: answers to questions 2 and 5"*, *"estimator: Gate 2"* |
| `gates_passed` | list of objects | Required, may be empty | Each Chain 1 gate passed: `gate` (1 to 4), `by`, `at`. |

The recommendation the skill produces is always `draft`. Only an estimator moves
it to `confirmed` or `declined`. `quote-build` reads this state rather than
inferring approval from context: a form still in `draft` is quoted only if the
estimator says so in the run, and the quote records that it proceeded on an
unconfirmed recommendation.

### `inquiry_state` and `bid_decision_state` are different axes

Confusing them is how a quiet customer silently becomes a no-bid.

`inquiry_state` is **where the inquiry is in its own life** — open, gone stale
waiting on the customer, or superseded by a revision. `bid_decision_state` is
**whether a human has ruled on it.** A stale inquiry is still `open` for
decision purposes and its `bid_decision_state` is still `draft`.

**Nothing in this contract lets a timeout become a decline.** `inquiry_state`
has no `closed` or `declined` value, and `customer-inquiry-intake` never writes
`bid_decision_state: declined` — only an estimator does.

**And a decision is never made stale.** An inquiry whose `bid_decision_state`
is `declined` is skipped by every stale check: it has been ruled on, and
surfacing it as *waiting on the customer* would put decided work back in the
unbid book.

### A confirmation covers what was shown

`bid_decision_basis` records the recommendation the estimator ruled on. If
answers arrive later and re-scoring changes it, for the inquiry or for any
line, the confirmation no longer covers it: `bid_decision_state` (and the
changed line's `line_bid_decision`) **returns to `draft`**, `bid_decision_reset`
says what changed, and Gate 2 is asked again naming the change. A stale yes
never quotes a line that has since flipped. A decline is not reset this way;
reopening it is a new decision.

### Where a paused inquiry lives between sessions

Chain 1 waits days for a customer. The intake form itself is the state. It is
saved on the private Open work page (`../replies.md`, *The open work*) as
`inquiries/<customer-slug>-<rfq_reference>.intake.txt`, never in the workspace
or the export folder, and one line per open inquiry goes in that page's
`## Open inquiries` block, pipe-separated, in this order:

```
- EH-RFQ-0912 | Example Hydraulics | file: inquiries/example-hydraulics-EH-RFQ-0912.intake.txt | paused_at_step: 5 | waiting_on: customer answers to Q1-Q3 | stale_after: 2026-11-17 | bid_decision_state: draft
```

The saved form keeps `open_questions` word for word, numbered as sent, so a new
session matches answers to questions without guessing. The line holds the
reference, the customer, the file on the page, `paused_at_step`,
`waiting_on`, `stale_after` (ISO date) and `bid_decision_state`, so a stale
check never resurfaces a declined inquiry. To resume, a new session brings in
the page, reads the line for that reference, opens the form from the page's
copy and continues at `paused_at_step`, rather than starting the inquiry
again. On quote, decline or withdrawal the line moves to `## Closed` with the
date.

### The recommendation exists even when incomplete

`recommendation` is never withheld because questions are open. It is scored on
what is known and marked `recommendation_provisional: true`, with
`would_change_recommendation` naming the specific answers that would move it.
A null recommendation means the skill could not score at all, not that it is
waiting.

When there is no capability profile, the recommendation is constraint-free and
**says so** in `recommendation_reasoning`. When there is no cost history, it
scores on capability and dates alone and **says so** there. Those two caveats
are prose on the recommendation, not flags.

## Drawings are never inferred from

Where a drawing is an image with no dimensions in text, extract what is visible
and mark the line for human review. **Never infer a tolerance from a drawing.** A
`specs` entry with no `source_ref` is not permitted, and neither is one with no
`reading_basis`.

**Two drawing facts go on the missing register when they are absent or in
doubt.** A drawing with no revision: the quote has to say which revision it is
priced to, and nobody can. And a change the customer mentions as pending — "engineering
may open up the bore in the next rev": recorded as a risk to the revision being
quoted, with the customer's words as its source, because a quote priced to a
revision about to be replaced is priced to the wrong part.

## Revisions of an earlier RFQ

`supersedes_rfq` links rather than duplicating. A revised RFQ that creates a
second inquiry is how a plant ends up quoting the same job twice against
different requirements.

---


## Worked example

One line, quotable, with a real constraint violation:

```yaml
contract_version: 7
site: Fairview
customer: "Example Aerospace"
contact: { name: "Dale Corwin", email: "dcorwin@example-aerospace.example" }
rfq_reference: "EA-RFQ-2291"
received_at: 2026-09-08T08:14:00-04:00
response_deadline: 2026-09-15
supersedes_rfq: null
payment: "Net 30"
freight: "FOB Fairview"
packaging: null
liability: "Customer's standard flow-down, including consequential damages"
source_documents:
  - { name: "EA-RFQ-2291.pdf", type: pdf, pages: 1 }
  - { name: "4471-B-drawing.pdf", type: pdf, pages: 3 }
field_sources:
  customer: "EA-RFQ-2291.pdf:p1"
  contact: "EA-RFQ-2291.pdf:p1"
  rfq_reference: "EA-RFQ-2291.pdf:p1"
  received_at: "EA-RFQ-2291.pdf:p1"
  response_deadline: "EA-RFQ-2291.pdf:p1"
  payment: "EA-RFQ-2291.pdf:p1"
  freight: "EA-RFQ-2291.pdf:p1"
  liability: "EA-RFQ-2291.pdf:p1"

line_items:
  - line_no: 1
    part_number: PN-4471-B
    part_number_verbatim: "4471-B"
    description: "Upper bracket, machined aluminium"
    revision: "B"
    quantities:
      - { qty: 250, uom: each }
      - { qty: 1000, uom: each }
    material: "6061-T6 aluminium"
    specs:
      - { characteristic: "true position, 4x mounting holes", nominal: "0.0005 in", tolerance: "max", reading_basis: printed_callout, source_ref: "4471-B-drawing.pdf:p2, view A, zone C4" }
      - { characteristic: "flange thickness", nominal: "0.250 in", tolerance: "±0.005 in", reading_basis: general_note, source_ref: "4471-B-drawing.pdf:p2, view B, zone B2; general note 1" }
    geometry_inputs:
      - { name: "4471-B-drawing.pdf", type: drawing_pdf, revision: "B", source_ref: "4471-B-drawing.pdf:p1, title block" }
    geometry_path: C2
    finish: "clear anodize"
    certifications_required: ["AS9100", "material cert"]
    required_delivery: 2026-11-03
    eau: 4000
    line_recommendation: bid
    line_bid_decision: draft
    field_sources:
      material: "4471-B-drawing.pdf:p1"
      quantities: "EA-RFQ-2291.pdf:p1"
      required_delivery: "EA-RFQ-2291.pdf:p1"

missing_register:
  - line_no: 1
    field: packaging
    why_it_matters: "Anodized parts ship with interleaving; unpriced if unstated."
    should_have_come_from: "customer terms page"

ambiguous_register:
  - line_no: 1
    field: required_delivery
    values_found:
      - { value: "2026-11-03", source_ref: "EA-RFQ-2291.pdf:p1" }
      - { value: "week of Nov 10", source_ref: "EA-RFQ-2291.pdf:p2" }
    why_it_matters: "A week's difference decides whether current shop load can absorb it."

open_questions: |
  Dale — two things before we can firm this up.
  1. The RFQ lists 3 November on page 1 and the week of 10 November on page 2.
     Which is the commitment?
  2. Is there a packaging spec for the anodized parts, or should we quote our
     standard interleaved cartons?

recommendation: bid
recommendation_provisional: true
would_change_recommendation:
  - question: "Is the material 4130 or 4140?"
    line: 1
    becomes: "no_bid if 4140 — that tolerance has never been held in 4140 on this process"
hard_disqualifier_stopped: false
inquiry_state: open
stale_since: null
answers_received: []
bid_decision_state: draft
bid_decision_by: null
bid_decision_at: null
bid_decision_basis: null
bid_decision_reset: null
questions_sent_at: null
questions_sent_by: null
paused_at_step: 4
waiting_on: "estimator: Gate 1, send the open questions"
gates_passed: []
recommendation_reasoning:
  - "Material, process and size envelope are all within demonstrated capability."
  - "One tolerance is below demonstrated capability on this process; see constraint_violations."
  - "Comparable closed work order WO-71160 on PN-4402-A returned 22% gross margin at similar volume."
constraint_violations:
  - constraint: "true position on 3-axis milling"
    requested: "0.0005 in"
    plant_capability: "0.002 in demonstrated"
    source: "## Plant context, site Fairview capability"
```

The manufacturability check runs **before** the recommendation, deliberately, so
a job that cannot be built as specified is caught at intake rather than after
someone has priced it. That ordering is the point, and the contract preserves it
by carrying `constraint_violations` alongside the recommendation it informed.

---

## Missing behavior for the consumer

| Situation | What `quote-build` does |
|---|---|
| A line has no quantity, or `material` is null | **Blocks that line.** Quote the others, list what is blocked and why |
| `quantities` has one entry where breaks were requested | Degrades. Quote what is there and state that breaks were not captured |
| `specs` entry has no `source_ref` | Blocks that spec. An unsourced tolerance is an inference, not a requirement |
| `ambiguous_register` has an entry on a field the quote depends on | Degrades. Quote against one value, name which, and state the other explicitly |
| `recommendation` is `no_bid` | Degrades. It is a recommendation, not a decision. Proceed if the estimator says to |
| `bid_decision_state` is `draft` | Degrades. Chain 1's **second** gate (the estimator confirming bid/no-bid at step 5) has not been passed. Chain 1 has four: Gate 1, sending the open questions at step 4; Gate 2, bid/no-bid at step 5; Gate 3, confirming the design, tolerance reading and operation list at step 8; Gate 4, releasing the quote at step 11. Quote only if the estimator says to in the run, and record on the quote that it proceeded on an unconfirmed recommendation |
| `bid_decision_state` is `declined` | **Blocks.** The estimator has declined this inquiry. Reopening it is a new decision, not a quote |
| A line's `line_bid_decision` is `declined` | **Blocks that line.** Quote the others, and list the declined line as not quoted, by the estimator's decision |
| `recommendation` is `partial` | Degrades. Read `line_recommendation` per line; quote the lines whose decision is not `declined` |
| `bid_decision_reset` is set | Degrades. The earlier confirmation lapsed. Treat the form as `draft` and name what changed |
| `recommendation_provisional` is true | Degrades. Quote if the estimator says to, and record on the quote which answers were still outstanding — they are the assumptions the price rests on |
| `hard_disqualifier_stopped` is true | Degrades. The plant cannot build this as specified. Quote only on an explicit override, and carry the disqualifying constraint onto the exclusions list |
| `inquiry_state` is `stale` | Degrades. Quote with exclusions naming the unanswered questions, or do not quote. **Never read stale as declined** |
| `inquiry_state` is `superseded` | **Blocks.** A later revision of this inquiry exists. Quote that one |
| `field_sources` absent | Blocks. Without provenance the estimator cannot verify anything |
| `geometry_path` is absent (a version 5 form) | Degrades. `rfq-to-quote` classifies the line itself from `source_documents` before the design step, and says it did |
| `geometry_path` is `A` | Degrades. No design step runs. Any price on the line is a ROM, never a firm quote, and the customer quote says so |
| A `specs` entry has no `reading_basis` | Degrades. Treat the tolerance as unverified and list it for the estimator at Gate 3 |
| `revision` is null on a line with a drawing | Degrades. Quote only with the revision named as unknown in the assumptions, and the missing-register row kept |
| A commercial term is null | Degrades. Quote against the plant's standard for that term, name the assumption on the exclusions list, and keep the missing-register row |
