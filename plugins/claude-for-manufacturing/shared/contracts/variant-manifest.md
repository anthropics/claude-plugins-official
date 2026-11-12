# Contract: the variant manifest

**Emitted by** `design-space-explore`
**Consumed by** `trade-study-report`
**Chain** none. This is the same producer-consumer relationship
`breakdown-diagnosis` has with `daily-production-report` in Chain 4
**Contract version** 4

Rules that govern every contract are in [README.md](README.md).

---

## The constraint that shapes this contract

`trade-study-report` is document-only and consumes a variant manifest, and
**a person can fill one in by hand** if no CAD backend is
available at all.

That is a real design requirement, not a footnote. It means:

- **The manifest must be hand-authorable.** A flat table a mechanical engineer can
  fill in a spreadsheet, not a CAD-internal dump.
- **Every CAD-specific field must be optional.** A hand-filled manifest has no
  document IDs, no regeneration status and no backend.
- **The consumer must not require anything only a CAD tool could produce.**

So the required core is small and the CAD fields sit around it.

---

## Manifest header

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `contract_version` | integer | Required | |
| `site` | string | Required | Which plant the study belongs to, rule 7. A hand-authored manifest still carries it |
| `study_ref` | string | Required | Ties the variants to a trade study |
| `base_model` | object or null | **Optional** | Null for a hand-authored manifest |
| `cad_backend` | enum or null | Optional | `fusion` or `none`. See the adapter note |
| `parameters_varied` | list of objects | Required | Each: name, unit, range, step or sampling strategy |
| `parametric_check` | object or null | Optional | See below |
| `generated_at` | timestamp with zone or null | Optional | Rule 4 |
| `variant_count_confirmed` | boolean | Required | Whether the engineer approved the count before generation |

`base_model` when present carries `document_ref`, `name` and `version`, and the
base model is **never modified** — variants are new documents or clearly-named
configurations.

## Variant rows

One row per variant. This is the part that must survive being typed by hand.

| Field | Type | Behavior | Notes |
|---|---|---|---|
| `variant_id` | string | Required | Stable, and traceable to its parameter set |
| `parameter_values` | object | Required | One entry per parameter in `parameters_varied` |
| `status` | enum | Required | `generated`, `regeneration_failed`, `skipped`, `hand_authored`, or (from version 4) `reused_existing`: a variant document with the same name and parameter values already existed, from a partial batch or a re-run, and was measured rather than created again |
| `status_detail` | string or null | Required when not `generated` | Why it failed or was skipped |
| `document_ref` | string or null | Optional | Absent on a hand-authored row |
| `properties` | object | Degrades | Model-computed values. See below |
| `analysis_results` | object or null | **Optional** | See the handoff boundary |
| `source_ref` | string | Required | Rule 6. Where each row's values came from |

### `properties`

Whatever the model could compute. Each value carries its unit, rule 5.

```yaml
properties:
  mass: { value: 0.412, uom: kg }
  volume: { value: 152.6, uom: cm3 }
  bounding_box: { x: 180, y: 96, z: 42, uom: mm }
```

**A property the model could not compute is absent, not zero.** A variant with
`mass: 0` reads as massless rather than unmeasured, which would win a
lower-is-better weight criterion outright.

---

## The handoff boundary

`design-space-explore` **does not run simulation.** It produces variants and the
manifest describing them, so an analysis tool or a person evaluates each and
returns results, which `trade-study-report` then consumes.

That is why `analysis_results` is optional and why it lives on the variant row
rather than in a separate payload. Three states the consumer must distinguish:

| State | Meaning | What `trade-study-report` does |
|---|---|---|
| `analysis_results` absent on every row | No analysis has been run | Produce the scored comparison and **clearly mark it judgment-based, not analysis-based** |
| Present on some rows | Partial analysis | Score what is analyzed, report the gap, **never impute a score** |
| Present on all rows | Complete | Score normally, citing each result to its source |

## `parametric_check`

The single biggest practical risk in `design-space-explore` is that a real
production model is not properly parametric, and the check must run **before**
generation, not after.

```yaml
parametric_check:
  ran: true
  driving_parameters: ["wall_thickness", "rib_count", "fillet_radius"]
  requested_not_driving: ["hole_pattern"]
  external_references_present: true
```

`requested_not_driving` is the field that matters. A parameter the engineer wanted
to vary that is not actually a driving dimension in the model means those variants
could not be generated, and the manifest has to say which rather than silently
producing fewer rows.

## Regeneration failures are expected

Geometry that self-intersects or features that fail to rebuild at range extremes
are **normal**, not a bug, and they do not abort the batch. Each failure is a row
with `status: regeneration_failed` and a `status_detail`.

**A failed variant is never dropped from the manifest.** A dropped row is
indistinguishable from a variant nobody considered, and the trade study would
then report a design space narrower than the one actually explored.

## Keep the adapter interface regardless

Fusion is the one implementation behind the interface today. `cad_backend` is
part of the contract even with one backend, so a CAD connector appearing later
drops in as a new enum value without a redesign.

**Version 3** (2026-10-13) removed the second CAD backend from the allowed
values; it was never wired up. Nothing else changed. A version 2 manifest
carrying that value is read under the missing behavior below.

---

## Worked example

Six variants: four generated, one failed at a range extreme, one whose parameter
was not driving. No analysis yet.

```yaml
contract_version: 4
site: Fairview
study_ref: TS-2026-014
base_model:
  document_ref: "fusion://Fairview/BracketUpper/v7"
  name: "Bracket, Upper, 4471"
  version: 7
cad_backend: fusion
parameters_varied:
  - { name: wall_thickness, unit: mm, range: [3.0, 5.0], step: 0.5 }
  - { name: rib_count, unit: count, range: [2, 4], step: 1 }
parametric_check:
  ran: true
  driving_parameters: ["wall_thickness", "rib_count", "fillet_radius"]
  requested_not_driving: ["hole_pattern"]
  external_references_present: false
generated_at: 2026-09-08T10:22:00-04:00
variant_count_confirmed: true

variants:
  - variant_id: V-001
    parameter_values: { wall_thickness: 3.0, rib_count: 2 }
    status: generated
    status_detail: null
    document_ref: "fusion://Fairview/BracketUpper-V001/v1"
    properties:
      mass: { value: 0.351, uom: kg }
      volume: { value: 130.0, uom: cm3 }
      bounding_box: { x: 180, y: 96, z: 42, uom: mm }
    analysis_results: null
    source_ref: "design-space-explore/2026-09-08/TS-2026-014"

  - variant_id: V-002
    parameter_values: { wall_thickness: 3.5, rib_count: 3 }
    status: generated
    status_detail: null
    document_ref: "fusion://Fairview/BracketUpper-V002/v1"
    properties:
      mass: { value: 0.418, uom: kg }
      volume: { value: 154.8, uom: cm3 }
      bounding_box: { x: 180, y: 96, z: 42, uom: mm }
    analysis_results: null
    source_ref: "design-space-explore/2026-09-08/TS-2026-014"

  - variant_id: V-005
    parameter_values: { wall_thickness: 5.0, rib_count: 4 }
    status: regeneration_failed
    status_detail: "Rib fillets self-intersect at 5.0 mm wall with 4 ribs; feature Fillet3 failed to rebuild."
    document_ref: null
    properties: {}
    analysis_results: null
    source_ref: "design-space-explore/2026-09-08/TS-2026-014"

  - variant_id: V-006
    parameter_values: { wall_thickness: 4.0, rib_count: 3 }
    status: skipped
    status_detail: "Requested hole_pattern variation is not a driving parameter in the base model; see parametric_check.requested_not_driving."
    document_ref: null
    properties: {}
    analysis_results: null
    source_ref: "design-space-explore/2026-09-08/TS-2026-014"
```

V-005 and V-006 stay in the manifest with empty `properties`. `trade-study-report`
must report them as unevaluated options rather than scoring them at zero — which
would rank them best on any lower-is-better mass criterion.

---

## Missing behavior for the consumer

| Situation | What `trade-study-report` does |
|---|---|
| `analysis_results` absent throughout | Degrades. Score on judgment and **mark the study judgment-based** |
| `analysis_results` on some rows only | Degrades. Report the gap per option. **Never impute a score** |
| A `properties` value absent | Degrades. Report the option as unscored on that criterion. Never treat as zero |
| `status` is `reused_existing` | Score it like `generated`; its `document_ref` is the existing document. Say it was reused |
| `status` is `regeneration_failed` or `skipped` | Degrades. List as an unevaluated option, excluded from the ranking, and say it was excluded |
| `requested_not_driving` is non-empty | Degrades. State that part of the requested design space was not explored |
| `variant_count_confirmed` is false | Degrades. Note that the variant set was not confirmed with the engineer |
| `source_ref` absent on a row | Blocks that row. Every score must cite its source, so an unsourced property cannot be scored |
| `base_model` and `cad_backend` both null | Degrades silently. This is a valid hand-authored manifest and needs no comment |
| `cad_backend` holds a value other than `fusion` or `none` (an older manifest) | Degrades. Read the rows as given; say the backend named is not one this plugin supports, so its document references cannot be reopened |

## What the consumer adds

The manifest carries variants and their measured properties. It does **not** carry
criteria, weights or scores — those belong to the trade study matrix that
`trade-study-report` loads separately, along with:

- **Criterion direction** per criterion, since some are lower-is-better (mass,
  cost) and some higher-is-better. Getting this wrong silently inverts the result.
- **Constraint compliance**, checked separately from scoring. An option violating
  a hard requirement is **disqualified, not low-scoring**, and mixing the two is a
  common error.
