# The parametric check — the single biggest risk in the skill

**This runs before generation, not after.** Everything else in this skill
assumes the model can actually do what is about to be asked of it, and this
is the step that finds out.

---

## What "driving" actually means

A parametric CAD model is built from dimensions that other geometry
depends on. Change `wall_thickness` from 3mm to 4mm, and every feature
defined relative to it — fillets, ribs, mounting bosses — regenerates
automatically.

**Not every dimension that looks like a parameter is actually driving
anything.** A hole pattern might be positioned by a sketch constraint that
ignores the "hole_spacing" parameter the engineer thinks controls it. A
fillet radius might be hard-coded on one feature and parametric on another
of the same name. The model *looks* parametric in the tree and is not, and
this is exactly the failure that doesn't show up until generation is
already running.

**Many real production models are not properly parametric.** This is not
an edge case to handle gracefully — it is the single biggest practical risk
in this skill, and it is worth taking at face value.

---

## How to check it

For each parameter the engineer named:

1. **Read its current value and confirm it exists** as an actual model
   parameter, not a dimension typed into a sketch that happens to look
   similar.
2. **Test whether changing it regenerates dependent geometry.** Where the
   CAD tool supports it, this can be a small probe change and revert rather
   than a destructive test.
3. **Record the result** as `driving_parameters` (confirmed) or
   `requested_not_driving` (asked for, not actually driving) on the
   `parametric_check` block.

Also check, once, for the model as a whole:

- **External references** — does this model reference geometry in another
  document (an assembly context, a derived part)? These can break silently
  when a parameter change propagates through them. Record
  `external_references_present`, and **say so to the engineer before
  generating** — this is a warning, not just a logged flag: name what's
  referenced and that variant generation can break it, so the engineer can
  decide whether to proceed with that risk understood rather than discover
  a broken assembly reference after the batch runs.

---

## When a requested parameter isn't driving

**Stop before generating anything for that parameter**, and say precisely
which one and why:

> *"`hole_spacing` is set on the sketch that positions the mounting holes,
> but the sketch also carries a fixed 22mm dimension that isn't tied to it
> — changing `hole_spacing` won't move the holes. I can vary
> `wall_thickness` and `rib_count`, which are both genuinely driving. Do
> you want to fix the sketch constraint first, or proceed on the two that
> work?"*

This is not a reason to abandon the run. **Generate variants for the
parameters that do drive geometry, and name the ones that were requested
but can't be honored** — `requested_not_driving` on the manifest, so
`trade-study-report` can state that part of the requested design space was
not actually explored, rather than silently reporting fewer rows with no
explanation.

---

## Report the check either way

`parametric_check.ran` is always `true` once this step executes, even when
every parameter checks out clean. **A model that passed the check and one
that was never checked look identical unless the check itself is on the
record.** Per `../../../shared/absent-is-not-zero.md`, an absent
verification is not the same fact as a confirmed one, and the manifest
needs to be able to tell them apart.
