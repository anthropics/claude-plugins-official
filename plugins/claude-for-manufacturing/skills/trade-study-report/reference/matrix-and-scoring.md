# Loading the matrix, and scoring it honestly

---

## The matrix

Four parts, and the whole skill is built around them:

| Part | What it is |
|---|---|
| Criteria | What matters — cost, mass, manufacturability, lead time, stiffness, thermal performance, serviceability |
| Weights | How much each criterion matters, usually percentages summing to 100 |
| Options | The candidate designs — often the variants from `design-space-explore` |
| Scores | Each option rated against each criterion |

---

## Validate before computing anything

**Weights must sum to 100.** Where they don't, **report it and stop — do
not normalize silently.** A matrix with weights totaling 94 or 108 is
either a typo or an intentional statement that something was left out, and
silently rescaling to 100 picks an answer to a question nobody asked. Show
the total and ask.

**Every option must be scored against every criterion.** Where a cell is
empty, that is a gap, not a zero. **Report which option, which criterion,
and never impute a value to fill it in** — a filled-in guess is
indistinguishable from a real score once it's in the table, and it will be
weighted and ranked exactly like one.

---

## Cite every score to its source

A score with no citation is an assertion. For each cell:

- **From `design-space-explore`'s variant manifest** — cite the variant ID
  and which `properties` or `analysis_results` field it came from.
- **From a simulation report or test data** — cite the document and the
  specific result within it, the same discipline every other skill in this
  plugin applies to a derived number.
- **From engineering judgment** — say so explicitly. A judgment-based score
  is legitimate input, and it stops being legitimate the moment it's
  presented as though it came from analysis.

---

## Normalize inconsistent scales, and show the work

Scores rarely arrive on one scale. One criterion might be rated 1–5 by an
engineer, another measured in raw units from a simulation, a third scored
1–10 by a different reviewer on a prior study.

**Normalize onto one comparable scale before weighting, and show the
normalization** — the raw value, the scale it came from, and the
normalized value side by side. A reviewer checking the math needs to see
both, or the weighted total is unverifiable even when it's correct.

**The default method for a measured criterion is ratio normalization**:
lower-is-better scores `best ÷ value`, higher-is-better scores
`value ÷ best`, so proportions survive. Name the method on the table. **Do not
use min-max with fewer than about four options**: it turns any difference,
however small, into 0 against 1, and can flip the ranking on the same data.
Use another method only where the user asks, and say which.

**Every score carries its basis**, one of three, shown per cell and counted in
the memo header:

| Basis | What it is | Example |
|---|---|---|
| `analysis` | A result from simulation, test or the manifest's `analysis_results` | FEA deflection 0.12 mm |
| `estimate` | Computed from model values by a stated formula, with its inputs | Stiffness scaled as t³ from `wall_thickness` |
| `judgment` | A person's rating | Machinability 3 of 5, J. Okafor |

An estimate is neither analysis nor opinion. Label it `estimate`, print the
formula and inputs beside it, and never let it be read as either.

---

## Criterion direction — get this wrong and everything downstream is wrong

Every criterion is either:

- **Lower is better** — mass, cost, lead time, defect rate
- **Higher is better** — stiffness, first-pass yield, demonstrated margin

**State the direction explicitly, per criterion, before computing a single
weighted total.** This is not a formality. A cost criterion scored so that
a *higher* number wins produces a table that looks completely normal —
every cell is populated, every total computes, the ranking is internally
consistent — and it recommends the most expensive option with full
confidence. Nothing about the arithmetic signals the error; only checking
the stated direction against what was actually computed catches it.

> *"Mass: lower is better, so a 0.351 kg variant scores higher than a
> 0.418 kg one on this criterion. Confirmed against the matrix header
> before computing totals."*

Say it plainly for every criterion, even the obvious ones. The failure mode
here is not confusion about which direction is correct — it's a scoring
convention entered backward in a spreadsheet cell and never checked again.
