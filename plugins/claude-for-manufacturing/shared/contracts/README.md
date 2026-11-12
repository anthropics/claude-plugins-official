# Handoff contracts

**A chain is not its steps. It is the joins between them, and the joins are where
the wrong answers live.**

Each file here defines the shape one skill emits and another consumes. They exist
as their own artifacts, separate from either skill, because a contract owned by
its producer drifts toward whatever the producer found convenient — and the
consumer discovers it in production.

---

## The contracts

| Contract | Emitted by | Consumed by | Chain |
|---|---|---|---|
| [consolidated-dataset.md](consolidated-dataset.md) | `data-consolidate` | Every data-dependent skill; the mapping target for `custom-connector` | 1, 3 |
| [intake-form.md](intake-form.md) | `customer-inquiry-intake` | `quote-build` | 1 |
| [ncr.md](ncr.md) | `ncr-writeup` | `root-cause-capa` | 2, 5 |
| [supplier-caused-flag.md](supplier-caused-flag.md) | `root-cause-capa` | `supplier-quote-request` | 5 |
| [downtime-record.md](downtime-record.md) | `breakdown-diagnosis` | `daily-production-report` | 4 |
| [variant-manifest.md](variant-manifest.md) | `design-space-explore` | `trade-study-report` | — |
| [geometry-estimate.md](geometry-estimate.md) | `rfq-to-quote` (design step), or an estimator by hand | `quote-build` | 1 |
| [supplier-bid.md](supplier-bid.md) | `supplier-quote-request` (each bid at ingest; the selection record when the buyer decides) | `supplier-quote-request` (comparison); `quote-build` (the awarded bid as an outside-processing line) | 5, and quote-triggered sourcing |
| [pulse-day-record.md](pulse-day-record.md) | `morning-plant-pulse` | The Operations dashboard's trend, read by the next pulse run | 3 |
| [quality-register-record.md](quality-register-record.md) | `ncr-writeup`, `root-cause-capa` | The Quality Register dashboard, rebuilt on each run that writes a row | 2, 5 |
| [floor-layout.md](floor-layout.md) | `daily-production-report` (setup turn) | `daily-production-report` (every later run), stored in the plant profile | 3 |

All twelve skills are now built, and both sides of every contract above exist.
Each was still written first, on purpose: defining a handoff after both sides
are built means one of them is wrong. The geometry estimate (2026-10-13) is the
seventh, and the first emitted by a chain skill rather than an atomic one,
because the design step that produces it belongs to Chain 1 itself.
The supplier bid (2026-10-13, supplier RFP loop) is the eighth: the shape the
mandated response format in
`../../skills/supplier-quote-request/reference/bid-comparability.md` asks for,
so an off-format bid shows exactly which fields it did not supply.

**The last two are stored records, not handoffs between two skills.** Their
consumer is a live dashboard, rebuilt by a later run from the rows earlier runs
wrote, per `../live-dashboard.md`. The same rules apply, and one more: every
write is keyed, so a re-run overwrites its own row and never adds a second.

---

## The rules every contract follows

### 1. No transformation step in between

The producer emits exactly what the consumer reads. Where a translation layer
appears, one of the two skills has the wrong shape and the fix belongs in the
skill, not in a converter. This is stated for the downtime record specifically
and it holds for every contract here.

### 2. Every field declares its missing behavior

A contract is not a list of fields. It is a list of fields **and what the
consumer does when each one is absent.** Three permitted behaviors, and no
others:

| Behavior | Meaning |
|---|---|
| **Required** | The consumer blocks and says which field is missing and which skill should supply it |
| **Degrades** | The consumer proceeds and states the limit in its output, in words |
| **Optional** | Genuinely additive; absence needs no comment |

**"Guess" and "default silently" are not permitted behaviors.** Per
`../absent-is-not-zero.md`, an absent field is never read as a zero, an empty
list, or a clean result.

### 3. Identifiers carry both forms

Any field holding one of the six join keys carries **the normalized key and the
source system's verbatim value**, never only one. The normalized form is what
joins; the verbatim form is what a plant person recognizes and searches for. The
ladder is in `../../skills/data-consolidate/reference/join-keys.md`.

Production work orders and maintenance work orders are separate fields with
separate names. They are different records and the two systems use the same word.

### 4. Every timestamp carries its zone

No naive timestamps cross a contract boundary. A producer reading a naive source
resolves it against the source clock declarations in the `## Plant context` block
first, and where it cannot, the field is emitted as unresolved rather than
assumed. Time handling is `../../skills/onboarding/reference/time-config.md`.

### 5. Every quantity carries its unit

Counts carry their unit of measure and money carries its currency code. A total
computed across two units is not a total, so a contract never holds a bare
number where a unit could vary.

### 6. Every derived field carries its provenance

Anything the producer worked out rather than read carries where it came from:
which file, which page, which record, which prior job. This is required
independently for extracted RFQ fields, quote cost lines, cited work orders,
recurrence findings and trade study scores, which makes it a contract rule rather
than six separate skill rules.

A consumer is entitled to know which of its inputs were read and which were
inferred, because it has to say so in its own output.

### 7. Site scope travels with the payload

Every contract carries the site it belongs to. Shift boundaries, vocabulary and
capability are site-scoped, and a payload that loses its site can be read against
another plant's configuration — the exact failure
`../../skills/onboarding/reference/config-profile.md` is structured to prevent.

### 8. Approval state is part of the payload, not an assumption

Where a chain gates before a handoff, the contract carries who approved it and
when. A consumer must be able to tell an approved determination from a draft one
without inferring it from context. This matters most for the supplier-caused
flag, where the determination is commercially significant.

---

## Versioning

Each contract carries a `contract_version` integer. It increments when the shape
changes, not when values change. A consumer reading an older version reads the
fields it knows and treats the rest as absent, following the missing behavior
above.

## Adding a contract

A new one is needed whenever a skill's structured output becomes another skill's
declared input. Write it before either side. Give every field a type, a source
and a missing behavior, and include a worked example — the example is what makes
a shape mismatch obvious to a reader, which a field table alone does not.
