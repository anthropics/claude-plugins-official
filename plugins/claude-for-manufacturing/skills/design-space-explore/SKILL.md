---
name: design-space-explore
description: "Generates a batch of CAD variants directly in Autodesk Fusion by applying changed parameters to an engineer's existing model, never designing from scratch and never overwriting the base. Checks first whether the parameters the engineer wants to vary actually drive the model's geometry, and stops rather than generating garbage if they don't. Confirms the variant count with the engineer before generating anything. Captures mass, volume, bounding box and every other model-computed property per variant, and hands the batch off in the shape trade-study-report consumes — it does not run analysis itself. Use when someone says \"explore the design space,\" \"generate variants,\" \"try different wall thicknesses,\" \"run a parameter sweep,\" or \"vary this and see what happens.\""
compatibility: "Requires Autodesk Fusion (desktop, with the document open). There is no other CAD backend and no file-only path — without Fusion connected, the skill reports exactly what is needed rather than running degraded. Never overwrites the base model."
---

# Design Space Explore

An engineering team designing a part rarely has one answer. They have a
**design space** — a range of possible designs bounded by what they're
allowed to vary (wall thickness, rib count, hole pattern, material) and what
the part must satisfy (envelope, mass, load, cost, manufacturability).
Modeling one design at a time, by hand, means evaluating three to five
options and picking the best of a small set. This skill generates many at
once, directly in the CAD tool the engineer already has open.

**It does not design from scratch.** It takes a model the engineer already
has and generates variants of it — that constraint is what makes the output
trustworthy and reviewable rather than a pile of new geometry nobody asked
for.

**It does not run analysis.** It produces the variants and the manifest
describing them, so an analysis tool or a person evaluates each one and
returns results, which `trade-study-report` then consumes.

**Quick start**

```
→ Connect: Fusion, with the base model open in the desktop app
→ Read the model's parameter set. Not driving what was asked? Stop and say so
→ Confirm the variant plan — parameters, ranges, step, and the resulting count
→ Generate. Verify each regenerated; failures at range extremes are expected
→ Capture per-variant properties: parameter values, mass, volume, bounding box
→ Produce the manifest in the shape trade-study-report consumes
→ Never touch the base model. Variants are new documents, clearly named
```

---

## Inputs

| Input | Source | Form |
|---|---|---|
| The base model | Fusion (open desktop document) | Live CAD connection |
| Parameters to vary, with ranges | Engineer, in conversation | Conversation |
| Constraints | Engineer, in conversation, and the trade study definition | Conversation / document |
| Trade study targets and criteria | `trade-study-report` definition, or a document in M365 | Document |
| Prior variants and results | M365 | Documents |

---

## Workflow

### Step 1 — Connect to the CAD environment

One implementation, Fusion, behind one interface. Read
`reference/cad-adapter.md` for the interface and the connector behaviors that
break a naive script.

- **Fusion** — desktop only, and acts on the open document via command-based
  operations on live geometry. There is no server-side fetch path; if the
  document is not open on the user's machine, there is nothing to act on.

Record the backend as `cad_backend` on the manifest, so a second CAD
connector drops in later without a contract change.

### Step 2 — Read the parameter set, and check what actually drives it

**This check comes first, before anything else, and it is the single
biggest practical risk in the skill.** A parametric model is built from
driving dimensions — change `wall_thickness` and the geometry regenerates.
Many real production models are not properly parametric, and automated
variant generation on one that isn't will not work.

Read the model's parameters and report which ones are actually driving
geometry. **Where a parameter the engineer wants to vary is not a driving
dimension, stop and say so** rather than generating variants that silently
ignore it. Read `reference/parametric-check.md`.

### Step 3 — Confirm the variant plan

Before generating anything: which parameters, which ranges, which step or
sampling strategy, and **the resulting variant count, stated plainly.**

**Generating 200 variants nobody asked for is the obvious failure.** Five
parameters at five values each is 3,125 combinations — show the count and
get an explicit yes before the batch runs. Read
`reference/variant-generation.md`.

### Step 4 — Generate, and verify each one

Apply each confirmed parameter set to the existing model. After each,
verify the model regenerated without error. The open, save-as-new, apply and
untouched-check sequence is `reference/adapt-prior-model.md` — the same
mechanism `rfq-to-quote` uses to adapt a prior part's model.

**A failed regeneration is expected, not a bug** — geometry that
self-intersects or a feature that fails to rebuild at a range extreme
happens routinely and does not abort the batch. Report it per variant, with
what failed.

### Step 5 — Capture per-variant properties

Parameter values, mass, volume, bounding box, and any other property the
model computed.

**A property the model could not compute is absent, not zero.** A variant
with no mass reading is unmeasured, not massless, and reporting it as zero
would win a lower-is-better weight criterion outright.

### Step 6 — Produce the handoff manifest

One row per variant — its ID, its parameter values, its computed
properties, its status, and its document reference — per
`../../shared/contracts/variant-manifest.md`, in exactly the shape
`trade-study-report` consumes.

**A failed or skipped variant stays in the manifest, never dropped.** A
dropped row is indistinguishable from a variant nobody considered, and the
trade study would then report a design space narrower than the one actually
explored.

### Step 7 — Never touch the base model

Variants are new documents, or clearly-named configurations of the base —
never a modification in place. State what was created, and where.

---

## Approval gates

**Nothing generates without the variant plan being confirmed** — parameters,
ranges, and the resulting count, agreed before the batch runs. This is the
skill's one real chance to prevent a runaway job; a live CAD connection
generates 3,000 low-value variants exactly as easily as 30 good ones.

**The base model is never modified.** Every variant is a new document or a
clearly-named configuration, so there is nothing to approve or roll back on
the original.

This skill does not run analysis and does not decide anything about the
trade study — it hands the manifest off. `trade-study-report` and the
engineer own what happens next.

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

**The generated variants**, in the CAD system, consistently named and
traceable back to their parameter set.

**The variant manifest** — per
`../../shared/contracts/variant-manifest.md`: the parameters varied, the
parametric check result, and per variant its ID, parameter values, computed
properties, status, and document reference.

**The generation report** — what succeeded, what failed to regenerate and
why, what was skipped and why. Rendered in the house artifact style
(`../../shared/artifact-style.md`) when there is enough of a batch to be
worth referring back to.

**The handoff package** — the manifest plus the generation report, ready for
an analysis tool or a person to evaluate and return results into, which
`trade-study-report` then consumes.

---

## Edge cases and failure modes

- **The base model isn't properly parametric** — the most likely real-world
  blocker. Detect and report before generating anything.
- **Fusion isn't open, or the customer uses Fusion's web client** — the
  connector cannot work at all. Detect and say so plainly; there is no
  server-side fetch path.
- **The connector replays an earlier script** — geometry nobody asked for
  appears, or read-only calls fail with "cannot modify." Stop and ask the user
  to restart Fusion; see `reference/cad-adapter.md`.
- **Geometry fails to regenerate at a range extreme** — expected. Report it
  per variant; do not abort the batch.
- **The parameter combination count explodes** — five parameters at five
  values is 3,125. Always show the count and confirm before generating.
- **The model has external references or in-context relationships** —
  variant generation can break them. Detect and warn before generating.
- **CAD operations are slow** — this is a long-running batch, not a single
  blocking call. Design for progress reporting, not silence until it
  finishes.

---

## Degradation

**One CAD tool, on one platform.** The skill works for customers running
Fusion on the desktop, with no cloud path. There is no fallback CAD backend —
no connector currently reaches SolidWorks, Creo, NX or Inventor, so a customer
on any of those has no path to this skill at all. State that plainly rather
than letting a prospect discover it for the first time in a demo. Keep the
CAD-adapter layer regardless, so a CAD connector appearing later drops in
without a redesign.

**If Fusion is not available** — the skill cannot generate variants and says
so, naming exactly what is needed: Fusion desktop with the document open.
`trade-study-report` is unaffected — its manifest can be hand-authored by an
engineer with no CAD backend at all, per its own contract.

---

## Chain position

Not part of a named chain, but feeds `trade-study-report` directly — the
same producer-consumer relationship `breakdown-diagnosis` has with
`daily-production-report` in Chain 4.

**Metric.** Configurations evaluated per program; design cycle time.

---

## Reference files

| File | Load when |
|---|---|
| `reference/cad-adapter.md` | Step 1 — the backend behind the interface, and the connector behaviors to read before the first call |
| `reference/parametric-check.md` | Step 2 — always, before generating anything |
| `reference/variant-generation.md` | Steps 3 to 7 — confirming the plan, generating, and the manifest |
| `reference/adapt-prior-model.md` | Steps 4 and 7 — open the base, save as new, apply, confirm the base is untouched |
| `../../shared/contracts/variant-manifest.md` | On emit — the exact shape `trade-study-report` consumes |
