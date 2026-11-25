# Scope, then containment

Two steps that have to happen in that order, because the scope decides how many
parts containment has to go find.

Containment happens **before anyone knows the root cause.** The point is to stop
the bleeding, not to explain it. A containment plan that waits on a diagnosis is
not containment.

---

## Part 1 — How many parts are actually suspect

The quantity somebody found is almost never the quantity that is suspect.

An inspector pulls three parts for a first-article recheck and two fail. The
answer is not "2." The question is what else the same cause could have reached,
and the honest starting position is that **if the cause could have affected the
whole run, the whole run is suspect until proven otherwise.**

### Reason from the cause outward

Work through what the suspected mechanism could touch:

- **One setup, no intervening tool change** → the whole run made on that setup
- **One material lot** → every part made from that lot, which may span several
  work orders and several weeks
- **A drifting process** → a time window, bounded at each end by whatever
  evidence you actually have, not by convenience
- **A gage whose calibration lapsed** → every inspection that gage performed
  since the lapse. This is one of the most common audit findings there is, and
  the scope is usually much larger than anyone first assumes
- **A genuinely one-off event** — a dropped part, a single mis-load — → that part

### Show the reasoning, always

`scope_reasoning` is a required field and it is required for a reason. The
consumer needs it because **a run-wide cause and a single-part cause point at
completely different root causes**, and the number alone does not say which was
assumed.

> *"All 480 parts on WO-88201 were machined from LOT-77219 on one setup with no
> intervening tool change, so the whole lot is suspect until sampled. The 3 found
> were a first-article recheck, not a full inspection."*

### Where traceability is incomplete, widen — and say so

No lot number recorded, or lot recorded only at the pallet rather than the part.
The suspect scope **widens**, and `traceability_complete` goes false with the
reason attached.

**Never narrow the scope to make the number look better.** That is the failure
mode this pair of fields exists to prevent, and it is the one that turns a
contained problem into a recall. A widened scope with an honest explanation is a
defensible position; a narrow one built on traceability nobody has is not.

Downstream, `root-cause-capa` carries the widened scope forward and never
re-narrows it.

---

## Part 2 — Where the parts physically are

Five locations. **Every one is addressed in every NCR**, including with a zero
quantity, because an omitted location reads as *"no parts there"* rather than
*"nobody has checked."*

Ordered by urgency, which is roughly the reverse of how easy they are to reach:

| Location | Where to look | Typical action | Usual urgency |
|---|---|---|---|
| `installed_at_customer` | Not visible in our records at all — you have to ask | Ask the customer whether any have been installed or shipped on | Immediate |
| `at_customer` | Shipment records, delivered — the ERP, not the `inventory` tab | Notify, request quarantine of the receipt | Immediate |
| `in_transit` | Shipment records, not yet delivered — the ERP | Intercept at the carrier while it is still ours to stop | Immediate |
| `wip_at_machine` | `inventory` rows at the cell or machine, plus `production_output` | Stop the next operation, hold at the cell | Immediate |
| `finished_goods` | `inventory` rows at a warehouse or cage location | Move to quarantine, tag with the NCR reference | Same day |

Read the `inventory` tab before the ERP. It is on-hand by part and location.
A missing tab is not zero on hand.

### `checked: false` is not `qty: 0`

The most dangerous entry in a containment plan is a location nobody has walked
yet, and it must not read as clear.

- `qty: 0, checked: true` — somebody looked, there are none there.
- `qty: 0, checked: false` — nobody has looked. **Not clear. Not contained.**

`installed_at_customer` is very often the second kind, because our records
genuinely cannot answer it. Write it that way rather than leaving it out.

### Every entry cites where the quantity came from

A row on the `inventory` tab, a shipment record, a row in `production_output`. Per
rule 6 in `../../../shared/contracts/README.md`, a derived number carries its
provenance — someone will need to go stand in front of that quantity.

### Owners are left blank

`owner` is a required field with a null value. Containment actions are assigned
by a person who knows who is on shift; the skill does not guess at names.

---

## Multiple customers

Separate containment entries and a separate notification per customer. Never
merge them — the contractual clocks differ, the contacts differ, and one
customer must not appear in another's notification.
