# Confirming the plan, generating, and building the manifest

---

## Confirm before generating anything

**A live CAD connection makes 3,000 low-value variants exactly as easily as
30 good ones.** There is no natural ceiling the way there is with, say, a
file export — the only check is asking first.

Show, before running anything:

- Each parameter and its range
- The step or sampling strategy — a fixed step, a set of named values, or a
  sampling method — and why
- **The resulting count, as a number**, not implied by the ranges

> *"wall_thickness 3.0 to 5.0mm in 0.5mm steps (5 values) × rib_count 2 to 4
> (3 values) = 15 variants. Confirm before I generate?"*

Five parameters at five values each is 3,125 combinations. **Always compute
and show the actual count** — a plan that sounds reasonable described in
words can be an unreasonable number of variants once multiplied out, and
the engineer needs the number, not the description, to make that call.

`variant_count_confirmed` on the manifest records that this happened.
Confirmation is a hard precondition for this skill, not a best practice —
nothing generates without it, per `SKILL.md`'s Approval gates, so on any
manifest this skill produces the field is always `true`. The field can
read `false` only on a manifest `trade-study-report` receives from
elsewhere — a hand-authored manifest never routed through this skill at
all — which is why the consuming skill still has to check it rather than
assume.

---

## Generate, and verify each one

Apply each confirmed parameter set, one variant at a time, by the sequence
in `adapt-prior-model.md`: open the base read-only, save as the variant's new
document (or its named configuration), apply, verify, and confirm the base
did not move. After each variant:

**Verify the model actually regenerated without error** before recording it
as successful. A silent failure that still produces *a* geometry — just not
the one the parameters describe — is worse than an explicit failure,
because nothing downstream will know to distrust it.

### Regeneration failures are normal, not bugs

Geometry that self-intersects, or a feature that fails to rebuild, happens
routinely at range extremes — a wall thin enough to intersect a rib, a
fillet radius too large for the available edge length. **This does not
abort the batch.**

Record the variant as `status: regeneration_failed` with a specific
`status_detail` — which feature failed and why, where the tool reports it:

> *"Rib fillets self-intersect at 5.0mm wall thickness with 4 ribs; feature
> Fillet3 failed to rebuild."*

A vague `status_detail` like "failed to regenerate" is barely better than
omitting the row. The specific feature and the specific reason are what let
someone decide whether the failure is informative (the design genuinely
doesn't work at that extreme) or an artifact of how the model was built.

### A skipped variant is not a failed one

Where step 2's parametric check found a requested parameter that isn't
driving, the variants that would have varied only that parameter are
`status: skipped`, with `status_detail` pointing back to
`requested_not_driving`. Skipped and failed are different facts — one is a
model limitation discovered at generation time, the other is a configuration
that was never viable to attempt.

---

## Long-running batches need progress, not silence

Applying and verifying a parameter set is not instant, and a batch of even
a few dozen variants can run for minutes. **Report progress as it happens**
rather than returning nothing until the whole batch completes — a stalled
connection and a slow-but-working one look identical from the outside
without it.

---

## The base model is never touched

Every variant is a **new document, or a clearly-named configuration** —
never an edit to the base in place. State what was created and its
document reference as each one completes, not only at the end.

**Generation is idempotent.** Before creating a variant, look for an existing
document with the same name and the same parameter values: after a partial
batch, a re-run, or a call that executed twice. If one exists, reuse it and
record it in the manifest as `reused_existing` with its reference; never create
a second copy. Two documents for one variant leave a manifest that cannot say
which is authoritative.

**Why this matters more than it might seem to:** the base model is the
thing the engineer will keep working from after this run. An accidental
edit to it is not recoverable by re-running this skill — the input the next
run needs would already be gone.

---

## Building the manifest

One row per variant, generated or not — per
`../../../shared/contracts/variant-manifest.md`:

- `variant_id`, stable and traceable to its parameter set
- `parameter_values`, one entry per parameter in `parameters_varied`
- `status`, one of `generated`, `regeneration_failed`, `skipped`,
  `hand_authored`
- `properties`, whatever the model could compute — **absent where it
  couldn't, never zero.** A `mass: 0` variant reads as massless and would
  win a lower-is-better weight criterion outright, which is exactly the
  wrong outcome for a variant nobody could actually measure.
- `source_ref`, so every downstream score can be traced back to this run

**Never drop a failed or skipped row.** A manifest that only lists what
worked describes a design space narrower than the one actually explored,
and `trade-study-report` would score against that narrower, silently
incomplete picture without knowing it was incomplete.
