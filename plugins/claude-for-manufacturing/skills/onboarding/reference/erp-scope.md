# ERP scope — what the plant's ERP holds, and which part of it is this plant

Load in Step 1, once the ERP is live or its exports are in hand. Every answer
goes in the `### ERP scope` section of the `## Plant context` block
(`config-profile.md`). Each one replaces a guess a skill would otherwise make
on every run.

An ERP account is rarely one plant's. It is shared with other businesses, or
customised field by field, or both. One NetSuite account we have seen held 515
items, 10 of them the plant's parts; the rest were coffee and retail.

---

## 1. Check only the record types the plugin uses

Do not pull the full metadata catalogue. On a real account it runs past 100k
characters and hundreds of custom record types. Check these, and for each say
**present or absent**, plus its custom fields:

| Record type | Used by |
|---|---|
| `item`, `assemblyitem` | every skill: the part master, standard and average cost |
| `salesorder`, `itemfulfillment` | demand, late orders, shipments for containment |
| `purchaseorder`, `itemreceipt`, `vendor` | supplier history, heat and lot receipts |
| `inventorynumber` | lots on receipts and fulfilments |
| `workorder` | production work orders and closed-job actuals |
| `location` | where stock sits, and which locations are this plant |

A query that fails with a SuiteScript error is reported as the error, with the
query that caused it, and the record type marked **not checked**, never
absent.

## 2. This plant's scope

Three answers, each confirmed by the user, never taken from a pattern alone:

- **Subsidiary**, where the account has more than one
- **Locations** that are this plant (by name or ID)
- **Which items are its parts**: an item class, a prefix (`PN-`), or a list

Propose from what Step 1 saw (*"10 items start `PN-`; are those your parts?"*)
and record the answer. `data-consolidate` scopes every pull by it. Without it,
the skill says *scope not set* as a gap and never guesses one.

## 3. Where the part revision lives

One of:

- **a field**, named (`custitem_revision`)
- **the item-ID suffix**, with its pattern (`PN-10047-A`: the letter after the
  last hyphen)
- **not in the ERP**: it lives on the drawing only

`supplier-quote-request`'s revision hard stop and `quote-build` read this. A
skill never infers the suffix pattern on its own.

## 4. Which cost field means what

NetSuite is customised, and the same idea has several homes. Record which
field holds each, and the order skills read them in:

| Meaning | Usual NetSuite field | Read order |
|---|---|---|
| Standard cost | `standardcost` (only with Standard Costing on) | 1 |
| Average cost | `averagecost` | 2 |
| Last purchase price | `lastpurchaseprice` | 3 |
| Purchase price | `cost` | 4 |

**Check that a cost is a cost.** If a cost field equals the latest sales order
price on every item, say so and do not record it as a cost basis: it is a
price, and quoting from it gives zero margin. Where a field is empty on every
item, record it empty, not missing.

## 5. Where production work orders come from

**ERP** when `workorder` is present and returns this plant's work orders.
**MES only** when the ERP holds none, as at plants that run production in the
MES. Then `data-consolidate` takes work order identity from the MES export and
reports *"work orders: MES only, per the plant profile"*, never hundreds of
mismatches.

## 6. When a connector and an export cover the same thing

If both the live ERP and an ERP export are in hand, `data-consolidate` checks
key overlap before joining them. Where the overlap is zero or low it asks
which one is authoritative. Record the answer here, per entity, so it is asked
once.

## 7. Approved normalizations

Not asked at onboarding: written by `data-consolidate` each time the user says
yes to a fix, one row per rule. Every later run, attended or overnight, applies
the rules on this list and only these.

## 8. RFQ staleness

How many business days an inquiry may wait on the customer before it is
stale. **Default 5 business days**, labelled *default, not plant-set*, until
the plant gives a number. `MFG_RFQ_STALE_DAYS` overrides it, like the rate
variables.

## 9. When the ERP is Infor M3

The same answers, asked in M3's terms. What M3 returns and what it does not is
`../../../shared/erp-connectors.md`.

- **1, the record types:** check each call in that file's table once, with a
  narrow filter, and say **answers, empty or fails** per call. "Record does
  not exist" is *empty*. A call that fails is reported with its error and
  marked **not checked**.
- **2, the scope:** company and division come from
  `MNS150MI_GetUserData_CurrentUser`. Ask which **facilities** and
  **warehouses** are this plant (propose the user's defaults, never assume
  them), and which items are its parts.
- **3, the revision:** never a field; M3's item record holds none. The item-ID
  suffix, or the drawing.
- **4, the cost fields:** standard cost is **not available** from M3 to this
  plugin. Record the read order as last purchase price from purchase order
  lines, then a supplied cost, and put standard cost on the gaps list.
- **5, the work orders:** **ERP** when `PMS100MI_SearchMO` returns this
  facility's manufacturing orders; otherwise MES only, as above.
- **The time unit for operation times.** Ask what unit the plant's work
  centers report setup and run time in. Record it. Until then, operation times
  are not costed.

---

## The section

```markdown
### ERP scope

- **Record types:** item, assemblyitem, salesorder, purchaseorder, itemreceipt,
  inventorynumber, vendor, location - present. itemfulfillment - present, none
  for this plant. workorder - absent
- **Subsidiary:** Example Manufacturing (ID 3)
- **Locations:** Fairview Plant (ID 12), Fairview FG (ID 14)
- **Parts:** item ID prefix `PN-` - confirmed 2026-10-14
- **Part revision:** item-ID suffix, letter after the last hyphen
- **Cost fields:** standard cost - not used (Standard Costing off) - average
  cost `averagecost` - last purchase `lastpurchaseprice` - purchase price
  `cost` (equals sell price on all 10 parts: not a cost basis)
- **Production work orders:** MES only
- **Source of truth:** items, sales orders - NetSuite connector; work orders -
  MES export
- **RFQ stale after:** 5 business days (default, not plant-set)

### Approved normalizations

| Rule | Source spelling | Matches | Approved by | Date |
|---|---|---|---|---|
| format drift | `4471B` | `PN-4471-B` | J. Okafor | 2026-10-13 |
| leading zeros | `451` | `00451` | J. Okafor | 2026-10-13 |
```

With Infor M3 the lines that differ read:

```markdown
- **Calls:** MMS200MI, MMS060MI, PMS100MI, OIS100MI head, MWS411MI, PPS200MI,
  CRS620MI - answer. MMS200MI_GetItmPrice, OIS100MI_SearchQuotation - not used
- **Company / division:** 400 / AAA (from the signed-in user)
- **Facilities:** A01 - **Warehouses:** 001
- **Cost fields:** standard cost - not available from M3 (on the gaps list) -
  last purchase price from purchase order lines
- **Operation time unit:** minutes - confirmed 2026-11-06
- **Source of truth:** items, sales orders, work orders - Infor M3 connector
```

A line not yet answered says **not set** and is on the gaps list. Never
omitted: an omitted line reads as "nothing to configure."
