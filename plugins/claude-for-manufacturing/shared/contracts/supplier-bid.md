# Contract: the supplier bid, and the selection record

**Emitted by** `supplier-quote-request`, when a returned bid is ingested (step 11), and when the buyer states a decision (step 13)
**Consumed by** `supplier-quote-request` at the comparison (step 12), and `quote-build` at the cost buildup, where the awarded bid becomes a sourced outside-processing line
**Chain** 5, and any sourcing event a quote started
**Contract version** 1

Rules that govern every contract are in [README.md](README.md).

---

## What this carries

**Two records, each written whole at its own emit time.**

1. **The supplier bid** — one per supplier response, written when the bid is
   ingested. It mirrors the mandated response format the package asked for
   (`../../skills/supplier-quote-request/reference/bid-comparability.md`), so a
   conforming bid fills every field and an off-format bid shows exactly where
   it fell short.
2. **The selection record** — one per sourcing event, written when the buyer
   tells the skill which bid they chose. **The buyer decides; the skill records
   it.** A recommendation is never a selection record.

**Every value is what the supplier stated, with where they stated it.** A bid
that quoted a lot price has no unit price on this record. A bid that said
nothing about the quality clauses has not accepted them. Per
`../absent-is-not-zero.md`, a field the supplier did not supply is null and
listed in `fields_missing`, never zero, never a default, never "probably
included."

**Both records are internal.** Nothing on them goes to any supplier: not the
prices, not the other bidders' names, not the ranking. Per
`../secret-config.md`, *The outbound document check*.

---

## The supplier bid

### Identification

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `contract_version` | integer | Required | |
| `site` | string | Required | Rule 7 |
| `event_ref` | string | Required | The sourcing event, e.g. `SRC-2026-10-14-PN-4471-B-BO` |
| `bid_ref` | string | Required | `<event_ref>/<supplier_id>/<n>`; `n` increments when a supplier restates |
| `supersedes` | string or null | Optional | The `bid_ref` this restatement replaces |
| `supplier_id` / `supplier_id_verbatim` | string | Required | Rule 3. The vendor record ID, or `unlisted` with the name as the supplier wrote it |
| `supplier_name` | string | Required | |
| `approval_status` | enum | Required | `approved`, `approved_single_source`, `not_confirmed_approved`, from step 8's candidate list. Never upgraded by a good bid |
| `received_at` | timestamp with zone or null | Required | Rule 4. From the email header or file; null with the reason when nothing dates it |
| `received_via` | enum | Required | `email`, `pdf`, `spreadsheet`, `pasted` |
| `source_ref` | string | Required | File name and page, sheet and row, or email subject and date. Rule 6 |
| `ingested_at` | timestamp with zone | Required | When this record was written |

### Price and quantity

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `currency` | string or null | Required | ISO code as stated. Null when not stated; never assumed from the supplier's country |
| `breaks` | list of objects | Required | One per quantity break the package asked for, **including breaks the supplier did not price** |
| `breaks[].quantity` / `breaks[].uom` | number, string | Required | The break as the package asked for it. Rule 5 |
| `breaks[].unit_price` | number or null | Required | Per unit, as stated. Null when the supplier quoted a lot, a range or nothing |
| `breaks[].as_quoted` | string | Required | The supplier's words for this break, verbatim: *"$240 per lot of up to 100 pcs"* |
| `breaks[].lead_time_first_article` | string or null | Degrades | With its unit and named start event, as stated: *"5 working days from receipt of parts"* |
| `breaks[].lead_time_production` | string or null | Degrades | Same |
| `breaks[].source_ref` | string | Required | Where this break's figures were read |
| `tooling_price` | number or null | Degrades | One-time tooling or NRE, as stated. `0` only when the supplier wrote that none is needed, with `tooling_note` quoting it |
| `tooling_in_unit_price` | boolean or null | Degrades | True when the supplier folded tooling into the piece price. Null when the bid does not say |
| `tooling_ownership` | string or null | Degrades | Who owns it at the end, as stated |
| `tooling_note` | string or null | Optional | Verbatim |
| `moq` / `moq_uom` | number or null, string | Degrades | Minimum order quantity as stated |
| `validity_until` | date or null | Degrades | Or the stated period, converted to a date in code from `received_at` and shown both ways |
| `freight_basis` | string or null | Degrades | Incoterm or freight term as stated |

### Quality and exceptions

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `quality_clause_acceptance` | enum | Required | `accepted_all`, `accepted_with_exceptions`, `not_stated`. `not_stated` is never read as accepted |
| `clause_exceptions` | list of strings | Required | Each clause the supplier excepted, with their words. Empty only under `accepted_all` |
| `exceptions` | list of strings | Required | Every other exclusion or assumption the supplier listed, verbatim. Empty list means they listed none |
| `conformance` | enum | Required | `conforming` or `off_format` |
| `fields_missing` | list of strings | **Required** | Every mandated field the supplier did not supply, by name. Present and empty only for a conforming bid |
| `restatement_requested` | boolean | Required | True once a restatement request has been drafted for the buyer to send. Drafted, not sent |

**`fields_missing` is the reason this contract exists.** A buyer reading three
bids sees three prices; what they cannot see is that one of them never stated
a lead time, a minimum order or whether it accepts the right of access. The
list is computed at ingest by checking every mandated field, not by noticing
what stands out.

---

## The selection record

Written once per decision, when the buyer says which bid they chose, after the
comparison was on screen. Per `../approval-gates.md`, *Supplier send and
selection*.

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `contract_version` | integer | Required | |
| `site` | string | Required | Rule 7 |
| `event_ref` | string | Required | |
| `decision` | enum | Required | `award`, `split_award`, `no_award`, `rebid` |
| `awarded` | list of objects | Required for `award` and `split_award` | Each: `bid_ref`, `supplier_id`, `supplier_name`, `breaks` (quantity, uom, unit_price, currency, as on the bid), `tooling_price`, `lead_time_production`, `validity_until`, `approval_status` |
| `recommended_bid_refs` | list of strings | Required | What the skill recommended, so a decision against it stays visible. Empty when the skill made no recommendation |
| `follows_recommendation` | boolean | Required | |
| `buyer_reason` | string or null | Optional | The buyer's words, verbatim. Never written for them |
| `decided_by` | string | **Required** | The name the buyer gave, as given. The skill asks for it rather than leaving it blank |
| `decided_at` | timestamp with zone | Required | When the buyer stated the decision in this conversation. Where the buyer gave a date the session clock disagrees with, their date, with the time marked not known |
| `compared_bid_refs` | list of strings | Required | Every bid on screen when the decision was made |
| `not_responded` | list of strings | Required | Suppliers with no bid at the time of the decision. Empty list when every supplier responded |
| `triggered_by` | object | Required | `{kind: quote, inquiry_ref, line_no, operation}`, `{kind: supplier_caused_flag, ncr_ref}` or `{kind: direct}` |
| `po_raised` | boolean | Required | Always `false` from this skill. A purchase order is raised by the buyer in the ERP (NetSuite or Infor M3) |

**A selection record is not a purchase order and not an award notice.**
Nothing is written to the ERP and nothing goes to the supplier. An award
notice and regret notes, if the buyer wants them, are drafts like every other
supplier email.

---

## Worked example

Black oxide for PN-4471-B Rev 2, sourced because the Example Hydraulics quote EH-RFQ-0912
needs it. Two bids, one off-format, then the buyer's decision.

```yaml
contract_version: 1
site: Fairview
event_ref: SRC-2026-10-14-PN-4471-B-BO
bid_ref: SRC-2026-10-14-PN-4471-B-BO/VEND-5120/1
supersedes: null
supplier_id: VEND-5120
supplier_id_verbatim: "5120"
supplier_name: "Example Finishing"
approval_status: approved_single_source
received_at: 2026-10-22T09:14:00-04:00
received_via: pdf
source_ref: "bid_example-finishing_2026-10-22.txt, p1"
ingested_at: 2026-10-22T11:02:00-04:00
currency: USD
breaks:
  - quantity: 50
    uom: each
    unit_price: 3.10
    as_quoted: "50 pcs: $3.10 ea"
    lead_time_first_article: "5 working days from receipt of parts"
    lead_time_production: "5 working days from receipt of parts"
    source_ref: "bid_example-finishing_2026-10-22.txt, price table row 1"
  - quantity: 200
    uom: each
    unit_price: 2.20
    as_quoted: "200 pcs: $2.20 ea"
    lead_time_first_article: "5 working days from receipt of parts"
    lead_time_production: "5 working days from receipt of parts"
    source_ref: "bid_example-finishing_2026-10-22.txt, price table row 2"
tooling_price: 0
tooling_in_unit_price: false
tooling_ownership: null
tooling_note: "No tooling or racking charge."
moq: 50
moq_uom: each
validity_until: 2026-12-21
freight_basis: "FOB our dock, Example Manufacturing to deliver and collect"
quality_clause_acceptance: accepted_with_exceptions
clause_exceptions:
  - "Right of access: 48 hours' notice required for customer audits."
exceptions: []
conformance: conforming
fields_missing: []
restatement_requested: false
---
contract_version: 1
site: Fairview
event_ref: SRC-2026-10-14-PN-4471-B-BO
bid_ref: SRC-2026-10-14-PN-4471-B-BO/VEND-5141/1
supersedes: null
supplier_id: VEND-5141
supplier_id_verbatim: "5141"
supplier_name: "Example Metalworks"
approval_status: not_confirmed_approved
received_at: 2026-10-24T16:40:00-04:00
received_via: email
source_ref: "email 'RE: RFQ black oxide PN-4471-B', 2026-10-24"
ingested_at: 2026-10-25T08:30:00-04:00
currency: null
breaks:
  - quantity: 50
    uom: each
    unit_price: null
    as_quoted: "$240 per lot of up to 100 pcs"
    lead_time_first_article: null
    lead_time_production: null
    source_ref: "email body, para 1"
  - quantity: 200
    uom: each
    unit_price: null
    as_quoted: "$410 for 200"
    lead_time_first_article: null
    lead_time_production: null
    source_ref: "email body, para 1"
tooling_price: null
tooling_in_unit_price: null
tooling_ownership: null
tooling_note: null
moq: null
moq_uom: each
validity_until: null
freight_basis: null
quality_clause_acceptance: not_stated
clause_exceptions: []
exceptions: ["Certs available on request."]
conformance: off_format
fields_missing:
  - "unit price at 50 (quoted per lot)"
  - "unit price at 200 (quoted per lot)"
  - "currency"
  - "lead time, first article, from a named event ('about a week')"
  - "lead time, production, from a named event"
  - "tooling price, or a statement that none is needed"
  - "tooling ownership"
  - "minimum order quantity"
  - "price validity"
  - "quality clause acceptance"
restatement_requested: true
---
# the selection record
contract_version: 1
site: Fairview
event_ref: SRC-2026-10-14-PN-4471-B-BO
decision: award
awarded:
  - bid_ref: SRC-2026-10-14-PN-4471-B-BO/VEND-5120/1
    supplier_id: VEND-5120
    supplier_name: "Example Finishing"
    breaks:
      - { quantity: 50, uom: each, unit_price: 3.10, currency: USD }
      - { quantity: 200, uom: each, unit_price: 2.20, currency: USD }
    tooling_price: 0
    lead_time_production: "5 working days from receipt of parts"
    validity_until: 2026-12-21
    approval_status: approved_single_source
recommended_bid_refs: [SRC-2026-10-14-PN-4471-B-BO/VEND-5120/1]
follows_recommendation: true
buyer_reason: "Approved source, no tooling, fits the Example Hydraulics date."
decided_by: "Dana Whitfield"
decided_at: 2026-10-27T10:05:00-04:00
compared_bid_refs:
  - SRC-2026-10-14-PN-4471-B-BO/VEND-5120/1
  - SRC-2026-10-14-PN-4471-B-BO/VEND-5133/1
  - SRC-2026-10-14-PN-4471-B-BO/VEND-5141/1
not_responded: []
triggered_by: { kind: quote, inquiry_ref: EH-RFQ-0912, line_no: 1, operation: "black oxide (OUTSIDE-FINISH)" }
po_raised: false
```

Note the Example Metalworks bid: `unit_price: null` at both breaks, with the lot prices
kept verbatim in `as_quoted`. Dividing $410 by 200 is the buyer's
normalisation the mandated format exists to avoid; the comparison may show
that division labelled *derived from a lot price, not quoted*, and never ranks
on it.

---

## Missing behavior

### For the comparison (`supplier-quote-request`, step 12)

| Situation | What it does |
|---|---|
| `breaks[].unit_price` null | The cell reads *not quoted per unit* with `as_quoted` beside it. Not ranked at that break. Never 0 |
| `currency` null, or two currencies across bids | No conversion. Each bid stays in its stated currency, and bids in different or unstated currencies are not ranked against each other |
| `tooling_in_unit_price` true | Shown, and the bid is flagged: its piece price is not comparable to a bid with tooling separate |
| `moq` above a break's quantity | Flagged on that break: the price does not buy that quantity |
| `quality_clause_acceptance: not_stated` | Shown as *not stated*, never as accepted. A recommendation that relies on it says so |
| `validity_until` before today | Flagged expired; the bid is shown and not recommended until restated |
| `approval_status: not_confirmed_approved` | Shown, and any recommendation of it names the requalification it needs first |
| `conformance: off_format` | Listed with its `fields_missing`, and the restatement request is drafted |
| A supplier with no bid | Its row reads *no response*, with the due date and days past it. Never "declined", never dropped |

### For `quote-build` (the outside-processing line)

| Situation | What it does |
|---|---|
| A selection record with `decision: award` and this line's operation | Price the outside-processing line from the awarded break, citing supplier, `bid_ref`, `received_at`, `decided_by` and `decided_at`. Its production lead time goes to the date check |
| A bid with no selection record | Cited as *a supplier quote, not awarded*, with its date. Not labelled sourced |
| The quote's quantity matches no awarded break | Name the gap. No interpolation between breaks; ask the estimator which break applies |
| `moq` above the quote's quantity | Flag it on the line: the price does not buy that quantity |
| `validity_until` before the quote's date | Flag the price as expired on the internal sheet |
| `decision` is `no_award` or `rebid` | No sourced line. The outside-processing line stays as it would have been without this event, and says the event is open |
| `contract_version` is older | Read the fields it knows; treat the rest as absent, per the README |
