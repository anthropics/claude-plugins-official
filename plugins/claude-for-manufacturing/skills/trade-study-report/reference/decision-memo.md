# Constraint compliance, the memo, and the comparison table

---

## Disqualified, not low-scoring

An option that violates a hard requirement — exceeds the envelope, misses
a mandatory certification, fails a pass/fail load case — is **disqualified,
not low-scoring.**

Mixing the two is a common error and it fails in a specific, dangerous
way: a disqualified option folded into the scored ranking can still win on
weighted total if it scores well enough on everything else, and a reviewer
skimming the ranking sees a winner rather than a design that legally
cannot ship.

**Keep the two lists separate throughout:**

- The **ranked comparison** — only options that meet every hard
  requirement.
- The **constraint compliance summary** — every disqualified option, with
  the specific requirement it violated, named plainly. Not folded into the
  bottom of the ranking as a low score.

> *"Option D is excluded from the ranking: it exceeds the 400mm envelope
> constraint at 412mm. This is disqualifying, not a scoring penalty — see
> the constraint compliance summary."*

---

## What the memo contains

The memo is the document that gets read in the review and defended
afterward. It carries:

| Section | Content |
|---|---|
| Recommendation | The option, stated plainly, in the first line |
| Reasoning | Why — grounded in the scored comparison, not restated from scratch |
| Sensitivity finding | Stable, or fragile and at what weighting it flips — always present, per `sensitivity-analysis.md` |
| Ruled-out options | Each one, with its specific cause — disqualified, or never won under any plausible weighting |
| Residual risks | What the recommended option still carries, even after winning |

### Residual risks are not optional

**Every design has open risk, including the winner.** A memo that
recommends an option and lists no risks reads as though the analysis
found none, which is a stronger claim than any real trade study supports.
Name what's still unresolved — an untested load case, a supplier not yet
qualified for the material, a tolerance close to demonstrated capability —
even when none of it changes the recommendation.

---

## Ruled-out options get their cause, not just their absence

A reviewer scanning the memo should be able to tell **why** each
non-winning option isn't the pick, without re-deriving it from the table:

- Disqualified — name the constraint.
- Never won under any plausible weighting — say so, per the sensitivity
  analysis.
- Won under some weightings but not the stated one — name where it does
  win, so a reviewer who weights things differently can see it wasn't
  ignored.

An option that simply disappears from the memo with no stated reason
invites the review to re-litigate a question this skill already answered.

---

## The comparison table, in a reviewable format

Options as rows, criteria as columns, each cell showing the raw score, the
normalized score, and — for the winning combination of weights — the
contribution to the total. The weighted total per option, ranked. Every
score's source cited per `matrix-and-scoring.md`.

The memo follows the plant's trade study template, a controlled document
per `../../../shared/artifact-style.md`; with none on file, a plain neutral
format, and the missing template named. **A separate internal comparison
view may use the house artifact style**; the memo itself never does. The
header counts the scores by basis: *"14 analysis, 5 estimate, 6 judgment."*

---

## The bar the memo has to clear

**It should read like something an engineer would put their name on.**
Not a summary of the arithmetic — a document that states a recommendation,
defends it with the evidence and the sensitivity finding, names what
didn't make it and why, and is honest about what's still unresolved. If it
reads like a printout of the scoring table with a sentence bolted on top,
it has not done the job this skill exists to do.
