# Computed figures — a number is printed, never retyped

**Shared across the plugin.** Every skill that reports a number follows this.

The failure this exists to stop has one shape. The skill does the work
correctly, then writes the summary from memory. The summary says "eleven
maintenance records" where the data holds six, "3.1× the control limit" where
the division gives 2.36, "five orders" where the file has six — the customer's
own order being the one missed. Each figure is stated with total confidence,
and each is the first thing a quality manager or an estimator will check.

A second shape sits next to it: the confident absence. "The sister machine has
no bearing history." "There is no PM plan in the library." Said after one
search, about a record that was there.

---

## The rule

**Every count, total, ratio, percentage and "N of M" in user-facing output is
produced by code run over the data in this session, and printed from that
result. A number is never retyped, rounded from memory, or paraphrased.**

**A negative claim — "has no history," "no plan exists," "not in the file" —
cites the exact query or filter that returned nothing.** Where the search tool
may be incomplete (SharePoint search under-reports), enumerate the folder
instead, or say *"not found by search"* rather than *"does not exist."* Those
are different claims and only the first one was earned.

---

## The figures block — a required part of the output

A rule that says "check your numbers" is a rule nobody can see being skipped.
So the check is an output, not an intention.

**Every run that reports a number emits a figures block**, produced by code,
before the prose that uses it. One row per figure:

| Figure | Value | Computed from | Filter or query |
|---|---|---|---|
| Maintenance records, HAAS-VF4-02 | 9 | maintenance export | `asset_id == "HAAS-VF4-02"` |
| Sibling records mentioning "bearing" | 2 (LMB-13781, LMB-14022, both HAAS-VF4-05) | maintenance export | same model, `notes` contains "bearing" |
| Measured ÷ upper control limit | 1.87 | inspection export | measured and limit both from the same computation |
| PM plan documents found | 0 — **not found by search** | M365 library | search "PM plan"; folder not enumerated |

Then three things hold, and a reader can check all three without re-running
anything:

1. **The prose quotes the block.** A number that appears in the narrative, a
   table or a headline appears in the block with the same value. A number in
   the prose with no row in the block is a defect.
2. **A ratio comes from the same computation as its parts.** Do not compute a
   control limit in code and then divide by it in your head.
3. **A subtotal reconciles to its total in the block itself.** If 126 records
   matched, the exact and normalized rows add to 126, and each equals the sum
   of the classes it is made of. A block that does not add up is fixed before
   anything is written from it.

Where the skill already emits "the structured data behind the report," the
figures block is part of it. Where the output is a controlled document going to
a customer or supplier, the block stays on the internal side.

---

## When no code can be run

Some sessions have no code execution. Then the count was made by reading, and
the output says so: **"counted by reading, not computed — verify before
relying on it,"** on the block and beside any figure that matters. Never
present a hand count as a computed one. This is `absent-is-not-zero.md` applied
to the method rather than the data: an unverified number named as unverified is
useful, and one dressed as computed is worse than none.

---

## What this does not change

- A figure that cannot be read is still reported unreadable. The block carries
  the row with the reason, never a guess.
- Rates, whether read from an `MFG_*` variable or the plant profile, follow
  `secret-config.md`. The block names the source; the value appears only where
  the audience rule allows.
- Computing a figure is not applying a fix. Anything that changes data still
  needs its yes.
