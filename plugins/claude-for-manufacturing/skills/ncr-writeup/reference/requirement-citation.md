# Citing the requirement — the field the whole chain gates on

**Nonconformance is always against a specific requirement, never just "it looked
wrong."** An NCR without a cited requirement is not an NCR, and
`root-cause-capa` blocks on one with a pointer back here.

This is the single most common way a nonconformance record is written badly, and
it is worth being strict about, because a quality manager reads the citation
before they read anything else.

---

## What counts as a requirement

A requirement is **stated, measurable, and locatable in a document.** Four
sources, roughly in order of how often they are the right one:

| Source | Where it lives | The locator you need |
|---|---|---|
| Customer drawing | M365 document library | Page, view or datum, and the feature |
| Internal specification | M365 controlled documents | Section number |
| Standard clause | The standards the plant is certified to, captured in `## Plant context` | Clause number, e.g. AS9100 8.5.1 |
| Customer purchase-order requirement | The ERP, or the PO document | The flowed-down line |

Each one produces four things: **the document, the locator inside it, the
characteristic, and the stated value.** A citation missing the locator is not
usable — "it's on the drawing somewhere" sends the next person back to do the
work again.

---

## Get the revision right

**Cite the requirement at the revision the part was actually built to**, not the
current one.

Two revisions of a print in circulation is a genuine root cause, and it is one of
the most common ones in the industry. If the shop copy was Rev A and the library
holds Rev C, that discrepancy is not a nuisance to resolve quietly — it is
probably the finding, and it belongs in the NCR.

Where the two disagree, record both and say which the part was made against. Do
not silently take the newer one.

---

## When the requirement cannot be found

This happens, and it happens most on exactly the parts where it matters.

**Never invent one.** Set `requirement_not_locatable: true`, leave
`requirement_cited` null, and flag the NCR as blocking. Per
`../../../shared/absent-is-not-zero.md`, a plausible-looking tolerance that
nobody can trace is worse than an admitted gap, because it will be believed and
then defended to a customer.

State what was searched, so the next person does not repeat it:

> *"I could not locate a requirement for surface finish on this feature. I
> searched the 4471-B drawing package (Rev B and Rev C), the internal spec
> QS-114, and the Example Aerospace flow-down on PO-4471. The drawing calls surface
> finish on two other features but not this one. Either it is uncontrolled here,
> or the requirement lives somewhere I cannot see. This NCR is blocked until
> someone confirms which."*

That is a complete, honest, useful outcome.

---

## Subjective findings

"The surface looks wrong." "It sounded rough." "The colour is off."

These are real observations and they are often correct — an experienced
inspector's eye is genuine evidence. Capture the finding **as observed**, set
`is_subjective: true`, and be explicit that no measurable requirement was cited.

The consumer needs that flag before it tries anything: `root-cause-capa` cannot
run a computed pattern check against a characteristic that was never measured,
and it needs to know that rather than discovering it.

Do not convert a subjective finding into a measured one by inventing a number
for it. Do ask whether the characteristic *could* be measured, because often it
can and nobody did.

---

## Blocking is a normal outcome

An NCR blocked on a missing requirement is not a failed run. It is the skill
doing the one thing it exists to do — refusing to record a nonconformance
against nothing — and it hands back a specific, answerable question instead of a
document that would not survive an audit.
