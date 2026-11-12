# Missing and ambiguous

Two states that get collapsed into "incomplete" everywhere else, and keeping
them apart is most of the value of a structured intake.

---

## Missing is not ambiguous

**A field that was never stated is a different problem from one stated
contradictorily in two places.**

| | Missing | Ambiguous |
|---|---|---|
| What happened | Nobody said | Two sources disagree |
| What it needs | A question to the customer | A decision, usually by the estimator |
| Who resolves it | Them | Us, sometimes after asking |
| How long it takes | A reply | Often minutes |

Collapsing them into one list means the estimator has to re-sort it before they
can do anything, which is the work you were trying to remove.

### The missing register

Per entry: the line, the field, **why it matters**, and **where it should have
come from.**

Those last two are what make it actionable. "Packaging not stated" is a
complaint. *"Packaging not stated — anodized parts ship with interleaving and
that is unpriced if we do not know; it should have been on the customer's terms
page"* is a question that answers itself half the time.

### The ambiguous register

Per entry: the line, the field, **every value found with its source**, and why
the difference matters.

> *Required delivery: 3 November on page 1, "week of 10 November" on page 2. A
> week decides whether current shop load can absorb it.*

**Never silently pick one.** Not the later one, not the stricter one, not the
one in the more official-looking document. The estimator picks, and downstream
`quote-build` quotes against one value while naming the other explicitly.

---

## Quantities are a structure

**Never average a range or a set of price breaks.**

Setup cost amortizes across quantity, which is the entire reason unit price
drops with volume and the reason quantity breaks exist at all. Averaging 100,
500 and 1,000 into 533 destroys the thing `quote-build` is for.

Capture each break as its own entry with its unit of measure. Where the customer
gives a range — "500 to 2,000 depending on the program" — capture the endpoints
and note that it is a range rather than a set of breaks, because the two ask for
different quotes.

---

## Drawings are read, never inferred from

Where a drawing is an image with no dimensional text, extract what is visible
and mark the line for human review.

**Never infer a tolerance.** Not from the feature type, not from what is
typical, not from the other dimensions on the print. A `specs` entry with no
source reference is rejected by the contract, and downstream `quote-build`
blocks on it — because an unsourced tolerance is an inference, and inferences get
priced and then contractually committed to.

**A stated general tolerance is not an inference.** "Unspecified tolerances
±0.005 in" is printed on the drawing; applying it to a feature with no callout
is reading the drawing, recorded as `reading_basis: general_note` with the note
cited beside the feature. What is never done is the other thing: a tolerance
taken from the feature type or from what is typical, where the drawing states
none.

**The revision is a drawing fact, and so is a pending change.** No revision on
the drawing or in the RFQ is a missing-register row: *"Drawing revision — the
quote must state which revision it is priced to; should have come from the
title block."* A customer remark that a change is coming — *"engineering
mentioned a possible change to the port thread"* — is a missing-register row
too, recorded as a risk to the revision being quoted, with their words as the
source. Both go into the questions.

---

## The open questions are an email, not a checklist

Draft them as **sendable text the estimator can actually send**, in the order a
person would ask them, with enough context that the customer can answer without
opening the file again.

A bulleted list of field names is a to-do list for the estimator. A short, clear
note is the thing that gets the answer back today. Getting the answer back today
is the metric this chain ships against.
