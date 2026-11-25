---
name: trade-study-report
description: "Turns a filled-in trade study matrix and its analysis results into a scored comparison and a decision memo, with every score cited to its source. Runs the sensitivity analysis every time — where the winner flips, which criterion the decision actually rests on, whether an option never wins under any plausible weighting — because a recommendation with no sensitivity check is a spreadsheet, not a decision. Disqualifies options that violate a hard constraint rather than scoring them low. Consumes design-space-explore's variant manifest when one exists, or a matrix filled in by hand when it doesn't. Use when someone says \"compare these options,\" \"write the trade study,\" \"which design should we pick,\" \"score these against the requirements,\" or \"how sensitive is this decision to the weighting.\""
compatibility: "Requires none. Reads a trade study matrix and analysis results from Microsoft 365 documents, a variant manifest from design-space-explore when one exists, and the ERP (Oracle NetSuite or Infor M3) for cost when connected. Runs entirely from a filled-in matrix and pasted figures, with no connector and no CAD backend."
---

# Trade Study Report

A trade study is the formal way an engineering team chooses between design
options: criteria that matter, weights on how much, options scored against
each one, a weighted total that ranks them, and a memo that defends the pick
in review.

**The analysis is the expert work; the memo is assembly.** An engineer runs
the simulations, then loses a day or more turning results into a document —
assembling scores, writing up the reasoning, formatting a table, defending
it the first time someone asks "what if cost mattered more?" This skill does
the assembly.

**It does not run analysis.** It reads scores that already exist — from
`design-space-explore`'s variant manifest, from a simulation report, from
engineering judgment stated plainly as judgment — and turns them into a
ranked, defensible comparison.

**Quick start**

```
→ Load the matrix: criteria, weights, options, scores. Weights sum to 100?
→ Every option scored against every criterion? Report the gap, never impute
→ Compute weighted totals and rank
→ Run the sensitivity analysis. Always — never optional
→ Check constraint compliance separately. A violation disqualifies, never
  just lowers a score
→ Write the memo: recommendation, reasoning, what was ruled out, risks
→ Produce the scored comparison table, reviewable
```

---

## Inputs

**First, find the plant setup:** from the task's own folder (never `cd` into the plugin), run
`python3 -I <this skill's folder>/../../shared/scripts/plant_setup.py find`, do its `setup_page_first` step, then read the profile at
`profile_path` and any rate at `rates_path`, per `../../shared/replies.md`.

| Input | Source | Form |
|---|---|---|
| Trade study matrix — criteria, weights, options | M365 (Excel/Word), or defined in conversation | XLSX / DOCX / conversation |
| Analysis results per option | M365 (simulation reports, test data, spreadsheets) | Documents / CSV |
| Variant manifest | `design-space-explore` output | `../../shared/contracts/variant-manifest.md` |
| Requirements and constraints | M365 requirements document | Documents |
| The plant's trade study memo template | `## Plant context`, captured during `onboarding` | Template |
| Prior trade studies | M365 | Documents — for format and precedent |
| Cost data per option | ERP cost: NetSuite standard cost, or Infor M3 last purchase price (`../../shared/erp-connectors.md`); or estimates | Connector / documents |

---

## Workflow

### Step 1 — Load the matrix

Criteria, weights, options, scores. **Validate that weights sum to 100**,
and that every option is scored against every criterion.

**Report gaps rather than imputing a score.** An unscored cell is a
finding, not a zero — filling it in with a guess is exactly the failure
this step exists to prevent. Read `reference/matrix-and-scoring.md`.

**When the options come from a `design-space-explore` manifest, three
manifest-level signals surface here, before any scoring happens** — per
`../../shared/contracts/variant-manifest.md`:

- A variant with `status: regeneration_failed` or `status: skipped` is
  listed as an unevaluated option, excluded from the ranking, and stated
  as excluded — never scored, never silently dropped from the list.
- A non-empty `requested_not_driving` means part of the requested design
  space was never explored. Say so.
- `variant_count_confirmed: false` means the variant set itself was never
  confirmed with the engineer before generation. Note that in the report.

### Step 2 — Ingest analysis results

Map each result to its criterion and option, **citing the source document
for every score.**

Where the source is `design-space-explore`'s variant manifest, read scores
from each variant's `properties` and `analysis_results` — never re-derive a
number the manifest already computed, and never re-run an analysis this
skill doesn't perform.

### Step 3 — Compute weighted totals and rank

Score × weight, summed, per option.

**Criterion direction must be explicit and verified before this step
runs.** Some criteria are lower-is-better — mass, cost — and some are
higher-is-better. Getting one backward silently inverts the result, and
nothing about the arithmetic will look wrong when it happens. Read
`reference/matrix-and-scoring.md`.

### Step 4 — Run the sensitivity analysis

**Always. Never optional.** Vary the weights across a plausible range and
report where the winner flips, which criterion the decision actually rests
on, and which options win under which weighting regimes.

**This is the most valuable part of the skill and the part most often
skipped.** Weights are subjective — somebody decided cost was 30% and
weight was 25% — and a recommendation with no sensitivity check hides
exactly how much that decision mattered. Read
`reference/sensitivity-analysis.md`.

### Step 5 — Check constraint compliance, separately from scoring

An option that violates a hard requirement is **disqualified, not
low-scoring.** These are different things, mixing them is a common error,
and this skill keeps them apart throughout — a disqualified option never
appears in the ranked comparison, only in its own list with the violated
requirement named.

### Step 6 — Write the decision memo

Recommendation, reasoning, the sensitivity finding, what was ruled out and
why, and the residual risks in the recommended option. Read
`reference/decision-memo.md`.

**In the plant's own memo template where one was captured at `onboarding`.**
A trade study goes into the design record and gets defended in a review, so it
has to arrive in the shape that record expects. Fall back to prior trade
studies for format, then to a neutral structure — and name which was used, so
nobody mistakes the house shape for their own.

### Step 7 — Produce the scored comparison table

In a reviewable format, per Output below.

---

## Approval gates

**This skill recommends; it does not decide.** The memo is a draft an
engineer reviews, signs, and defends in the design review — nothing here
commits the plant to a design choice, the same way `customer-inquiry-intake`
recommends a bid and `root-cause-capa` ranks candidate causes without
concluding.

Nothing is written back to any system of record.

---

## Output

**Every document this skill produces is printed in the reply, in full.**
Saving a copy to a file as well is fine, as Word or Excel per `../../shared/replies.md`, never `.txt`; a file *instead of* the reply is not.
The person reads the reply, and every delimited block and outbound check lives
in it — a document only on disk has been neither seen nor checked.
**A record handed to another skill is saved and summarised, never pasted as
raw YAML**; memory blocks are written where the plant's memory lives; and the
name on an approval is asked, never taken from the account. All three per
`../../shared/replies.md`.

**The scored comparison table** — options × criteria, weighted, ranked,
with every score cited to its source. **Each cell shows its contribution**
(normalized score × weight) beside the raw score, so a reader can see where a
total came from without a calculator, and **the table carries an explicit
rank column** rather than leaving the order to be inferred from the totals.

**The sensitivity analysis** — flip points, the most decision-sensitive
criterion, and the regime-by-regime winners.

**The decision memo** — recommendation, reasoning, the sensitivity finding,
ruled-out options with their cause, and the residual risks in the
recommended option.

**The constraint compliance summary** — disqualified options listed
separately from the ranked ones, each with the requirement it violated.

**The memo is a controlled document**: it follows the plant's own trade study
template, per `../../shared/artifact-style.md`, and is never restyled. Where
no template is on file, use a plain neutral format and say the template is
missing. Only a separate internal comparison view, which the team refers back
to in review, uses the house artifact style.

---

## Edge cases and failure modes

- **Weights don't sum to 100** — report it. Do not normalize silently.
- **An option is unscored on a criterion** — report the gap. Never impute a
  score.
- **Two options are within noise of each other** — say so explicitly rather
  than presenting a false winner.
- **Scores are on inconsistent scales** — 1–5 against 1–10 against raw
  units. Normalize, and show the normalization.
- **Some criteria are lower-is-better, some higher-is-better** — direction
  must be explicit per criterion. Getting it wrong silently inverts the
  result.
- **No analysis results yet, only the matrix** — produce the scored
  comparison and clearly mark it as judgment-based, not analysis-based.

---

## Degradation

Runs entirely from a filled-in matrix and pasted figures, with no
connector and no CAD backend at all.

| Not available | What happens |
|---|---|
| A variant manifest from `design-space-explore` | The matrix and its options come from a document or conversation instead. A hand-authored manifest with `cad_backend: none` is a valid, complete input, not a fallback — per `../../shared/contracts/variant-manifest.md` |
| Analysis results, on every option | The comparison runs on judgment alone and **says so, throughout** — every score reads as judgment-based, never presented as analysis-based |
| Analysis results, on some options | Score what is analyzed, report the gap per unanalyzed option, and **never impute a score** to fill it in |
| ERP cost | Price from a supplied estimate or a document, with its source, rather than leaving cost unscored |
| The plant's memo template | Fall back to prior trade studies for format; failing that, a neutral memo structure — and **say which**, because `onboarding`'s gaps list promises exactly this degradation |
| Prior trade studies | Use a neutral memo structure and say the plant's own format was not available |

---

## Chain position

**Not part of a named chain.** Consumes from `design-space-explore`
directly — the same producer-consumer relationship `breakdown-diagnosis`
has with `daily-production-report` in Chain 4.

**Metric.** Design decisions per quarter; design cycle time.

---

## Reference files

| File | Load when |
|---|---|
| `reference/matrix-and-scoring.md` | Steps 1 to 3 — validating the matrix, citing scores, normalization, criterion direction |
| `reference/sensitivity-analysis.md` | Step 4 — always, before ranking is presented as final |
| `reference/decision-memo.md` | Steps 5 to 7 — constraint compliance, the memo, the comparison table |
| `../../shared/contracts/variant-manifest.md` | Step 2 — reading scores from a generated or hand-authored manifest |
