# The response specification — making bids comparable by construction

**The highest-leverage line in the whole package**, and the one most often left
out.

---

## The problem it solves

Three suppliers reply to the same request in three shapes:

| Supplier | What they sent |
|---|---|
| A | $4.10 per piece, tooling included, 6 weeks |
| B | $3,180 per lot of 1,000, tooling quoted separately at $8,500, "8–10 weeks ARO" |
| C | $3.85/pc at 1,000 and $3.40 at 5,000, tooling amortized over the first order, freight collect |

Nobody can compare those. The buyer spends an afternoon normalising all three
onto one basis, guesses at the pieces that were not stated, and the comparison
they end up with is partly their own reconstruction rather than what the
suppliers actually offered.

**Specifying the response format up front is what makes the later comparison
honest**, rather than a normalisation exercise performed after the fact by
somebody with an opinion about who should win.

---

## What to mandate

### The bid structure

- **Unit price at each stated quantity, separately.** Not an average, not a
  blended rate. One line per quantity break asked for.
- **Tooling and NRE priced separately**, never folded into the piece price. A
  supplier who buries $8,500 of tooling in the unit price at 1,000 looks
  expensive at 1,000 and cheap at 10,000, and the buyer cannot see why.
- **Tooling ownership stated.** Who owns it at the end matters as much as the
  price, and it decides whether a second source is even possible later.
- **Lead time, split into first article and production**, and stated from a
  named event — receipt of order, receipt of tooling approval — rather than "8
  weeks."
- **Minimum order quantity**, which frequently turns out to exceed the quantity
  quoted.
- **Currency**, explicitly.
- **Price validity period.**
- **Any exclusions or assumptions**, listed rather than implied. This is where
  the surprises live.

### The commercial basis

State the terms the bid must assume rather than letting each supplier assume
their own: **Incoterms or freight basis, packaging, payment terms.** Otherwise
one bid is delivered and another is ex-works, and the difference is invisible
until the invoice.

### The response schedule

- A **due date** for the response
- **Who to send it to**, and how
- A **named contact** for technical questions, with the note that answers given
  to one bidder will be shared with all — which is both fair and the thing that
  stops a scope drift nobody sees

---

## Say what happens to a non-conforming bid

A required format that carries no consequence is a suggestion.

State plainly that a bid returned in a different shape will be sent back for
restatement rather than normalised on the buyer's side. Most suppliers comply
immediately, because the request is reasonable and the alternative costs them
time too.

---

## Where the quantities come from

The demand picture is what makes the bid meaningful, and it is worth being
accurate rather than optimistic.

- **Historical usage**, over a stated window, from the ERP
- **Open demand** currently on the books
- **Forecast or estimated annual usage**, clearly labelled as a forecast

**Suppliers price 100 a year very differently from 10,000 a year.** A quantity
quoted without a volume context gets priced defensively, and the plant pays for
that pessimism on every part.

**Never inflate the forecast to get a better price.** It produces a price the
supplier cannot hold, and the renegotiation arrives at the worst possible moment
— usually once the alternate source has already been qualified and the leverage
has moved.

Where usage history is unavailable or the part is new, **say so in the request**
rather than omitting the volume. "New part, no usage history, initial order 500,
annual volume not yet established" is a statement a supplier can price against.
Silence is not, and they will assume the worst.

---

## When the bids come back

Each returned bid is read into `../../../shared/contracts/supplier-bid.md`,
which mirrors the bid structure above field for field. A field the supplier did
not supply is listed in `fields_missing`, and the restatement request names it.
Read `bid-comparison.md`.
