# Contract: the supplier-caused flag

**Emitted by** `root-cause-capa`
**Consumed by** `supplier-quote-request`
**Chain** 5, supplier-caused escape to alternate source
**Contract version** 2

Rules that govern every contract are in [README.md](README.md).

---

## Why this one is different

This is **the only cross-area handoff in the plugin**, so its schema is
defined explicitly. It is the plugin's cross-area proof point: a
quality finding automatically starting a sourcing action, which essentially never
happens today because quality and purchasing live in different systems and
different departments.

That is also what makes it the most consequential payload here. **A
supplier-caused determination is a commercially significant claim.** It says a
vendor caused a defect, and it starts a search for an alternate source. Chain 5
gates on a human owner before this flag is acted on, and that approval is part of
the payload rather than an assumption the consumer makes.

---

## Fields

### The determination

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `contract_version` | integer | Required | |
| `site` | string | Required | Rule 7 |
| `determination` | enum | Required | `supplier_caused`, `supplier_contributing`, `not_supplier_caused` |
| `confidence` | enum | Required | `high`, `medium`, `low` |
| `is_leading_candidate` | boolean | Required | Whether this was the top-ranked causal chain or a lower one |
| `competing_candidates` | list of strings | **Required** | The other candidate causes and their standing. See below |
| `ncr_ref` | string | Required | The originating NCR |
| `capa_ref` | string or null | Degrades | The 8D, where drafted |

### What was supplied, and by whom

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `part_number` / `part_number_verbatim` | string | Required | Rule 3 |
| `part_revision` | string or null | **Required for sourcing** | See below |
| `lot_number` / `lot_number_verbatim` | string or null | Degrades | The implicated material lot |
| `supplier_id` / `supplier_id_verbatim` | string | Required | Rule 3 |
| `supplier_name` | string | Required | |
| `purchase_order` | string or null | Degrades | The PO the lot arrived on |
| `received_at` | timestamp with zone or null | Optional | Rule 4 |
| `qty_affected` | number | Degrades | Paired with `uom`, rule 5 |
| `uom` | string | Required with `qty_affected` | |

### Evidence

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `evidence_for` | list of strings | Required | Each citing its source, rule 6 |
| `evidence_against` | list of strings | **Required** | May be empty, but the field is present. See below |
| `lot_clustering_observed` | boolean or null | Degrades | Whether failures clustered by material lot |
| `recurrence` | enum | Degrades | `first_occurrence`, `recurrence_prior_capa_held`, `recurrence_prior_capa_failed`, `no_searchable_history` |
| `escape_occurred` | boolean | Required | Whether nonconforming parts reached a customer |

### Chain 5 instrumentation — three timestamps, not two

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `escape_detected_at` | timestamp with zone or null | **Required when `escape_occurred`** | Carried forward from `ncr.md`, where `ncr-writeup` stamped it. Opens the window |
| `determination_made_at` | timestamp with zone | **Required** | Stamped by `root-cause-capa` when this flag is raised. **The middle stamp** |

**The third stamp is not on this contract, deliberately.** `rfq_issued_at`
belongs to `supplier-quote-request`, which *consumes* this flag — it cannot
write back into a payload it received without reversing the direction of flow
this contract is built on. It records that stamp in its own sourcing record,
closing the window there.

So this contract carries the two stamps that exist **at the moment it is
emitted**, and the consumer adds the third at the moment it acts. That is the
only arrangement where each stamp is written by the skill that actually owns
the event.

Chain 5's headline metric is *time from escape to alternate-source RFQ issued*,
and it is owned in **two consecutive segments** rather than by one skill:

| Segment | Window | Owner |
|---|---|---|
| Detection and investigation | `escape_detected_at` → `determination_made_at` | `ncr-writeup` (detection, containment) and `root-cause-capa` (investigation) |
| The sourcing handoff | `determination_made_at` → `rfq_issued_at` | `supplier-quote-request` |

**`determination_made_at` is the field most likely to be dropped and the one
that cannot be recovered.** The other two bracket the window and are obvious;
the middle one is what separates investigation time from handoff time. Without
it the two segments collapse into a single number, and the second segment — the
dead time this chain actually eliminates — becomes invisible behind an
investigation that legitimately takes weeks.

Segmented is deliberate, not an accounting nicety. If the plugin cuts the
handoff from two weeks to two days, that has to show up **while the
investigation still takes a week.** One blended figure would hide which half
moved.

### Approval — rule 8

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `approved_by` | string or null | **Required to act** | The human owner who confirmed the determination |
| `approved_at` | timestamp with zone or null | Required to act | |
| `approval_state` | enum | Required | `draft`, `approved`, `rejected` |

---

## Four fields that carry real weight

**`evidence_against` is required even when empty.** `root-cause-capa` produces
ranked candidate causal chains with supporting *and contradicting* evidence, and
never a single unqualified verdict. If only supporting evidence crossed the
boundary, the consumer would receive a confident claim built from a ranked
hypothesis — which is how a supplier gets accused on half the picture.

**`competing_candidates` is required for the same reason.** A determination that
was the leading candidate among three near-equals is a different claim from one
that was clearly ahead. The buyer opening a sourcing action deserves to know
which.

**`part_revision` is required for sourcing even though it is nullable
elsewhere.** `supplier-quote-request` **hard stops** on a revision mismatch
between the document library and the ERP item master, because sending a supplier
the wrong revision is the classic and expensive error that skill exists to
prevent. A flag arriving with no revision cannot clear that check, so it blocks
rather than degrading.

**`approval_state` gates the whole payload.** A `draft` flag is a finding to
review. Only an `approved` flag starts a sourcing action, and the consumer must
never infer approval from the flag's existence.

---

## Worked example

An approved determination, leading candidate but not uncontested:

```yaml
contract_version: 2
site: Fairview

determination: supplier_caused
confidence: medium
is_leading_candidate: true
competing_candidates:
  - "Tool wear on cell B, ranked second. Supported by the tool-change interval; contradicted by the same tooling running 4402 in spec that week."
  - "Operator print revision, ranked third. No evidence of uncontrolled prints in circulation."
ncr_ref: NCR-2026-0418
capa_ref: 8D-2026-0418

part_number: PN-4471-B
part_number_verbatim: PN-4471-B
part_revision: "B"
lot_number: LOT-77219
lot_number_verbatim: "77219"
supplier_id: VEND-3310
supplier_id_verbatim: "3310"
supplier_name: "Example Steel"
purchase_order: PO-8841
received_at: 2026-08-19T00:00:00-04:00
qty_affected: 480
uom: each

evidence_for:
  - "Material cert on LOT-77219 reports hardness 232 HB against a 187-217 HB requirement (cert-77219.pdf, p2)."
  - "All 14 out-of-tolerance parts trace to LOT-77219; none to LOT-77188 run on the same cell (inspection-20260901.xlsx)."
evidence_against:
  - "Spindle load telemetry rose across the run on both lots, which a material-only cause does not explain (historian-20260901.csv)."
lot_clustering_observed: true
recurrence: recurrence_prior_capa_failed
escape_occurred: true
escape_detected_at: 2026-09-07T14:05:00-04:00
determination_made_at: 2026-09-09T11:20:00-04:00

approved_by: "Priya Raman, Quality Manager"
approved_at: 2026-09-08T11:40:00-04:00
approval_state: approved
```

Note `recurrence: recurrence_prior_capa_failed` and `escape_occurred: true`. A
recurrence after a closed CAPA is a materially more serious finding than a first
occurrence, and an escape means a customer already has parts. Both change what
the consumer does with urgency.

---

## Missing behavior for the consumer

| Situation | What `supplier-quote-request` does |
|---|---|
| `approval_state` is not `approved` | **Blocks.** Report the flag as an unapproved finding and name who needs to own it |
| `part_revision` absent | **Blocks.** The revision check cannot clear |
| `supplier_id` absent | Blocks. There is no determination without a named supplier |
| `evidence_against` absent as a field | Blocks. Its absence means the producer did not follow its own ranking discipline |
| `evidence_against` present and empty | Degrades. Proceed, and state that no contradicting evidence was found |
| `recurrence` is `no_searchable_history` | Degrades. State that history could not be searched. **Never read as a first occurrence** |
| `confidence` is `low`, or `is_leading_candidate` is false | Degrades. Proceed as an exploratory alternate-source search and label it as such, not as a response to an established supplier failure |
| `lot_number` absent | Degrades. Widen the scope and say why it had to widen, never narrow it |

## What the consumer does on receipt

Chain 5's closing step, in order:

1. **Check the gate.** No `approved` state, no outbound package.
2. **Verify the revision** against the ERP item master. Mismatch is a hard stop.
3. **Flag single-source risk.** If this part has exactly one qualified supplier
   and that supplier is the one implicated, that is the finding, and it is
   usually more urgent than the sourcing package itself.
4. **Note requalification lead time.** An alternate cannot just start shipping,
   which is why starting early is the value.
