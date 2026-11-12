# The design step and Gate 3

**Step 7 builds an internal model of the customer's part so the plant can
estimate how long it takes to make.** It is an estimating aid. It is not the
customer's design, it is never sent, and it never changes the customer's
drawing.

The output is one geometry estimate per line, per
`../../../shared/contracts/geometry-estimate.md`, always emitted as `draft`.
Gate 3 is where an estimator turns it into something hours can be derived from.

---

## Before anything: does this line need a model?

Step 6 has already run. Per line:

- **A current-revision routing exists** — skip step 7. The routing is the
  basis. Build the model only if the estimator asks for a cross-check, and say
  which it is.
- **The only routing is for another revision** — superseded. Treat the line as
  having no routing. Name the superseded routing so nobody prices from it.
- **No routing** — step 7 runs.

Recorded actuals do not skip step 7. They are rung 2; the model is the
cross-check that tells the estimator whether they are believable, and
`probable_standard` actuals are not believable enough to skip it.

## Path classification (R1)

Read `geometry_path` from the intake form line. Where the form has no
`geometry_path`, classify from `source_documents` and say so. Then, where
the step finds something intake could not see, reclassify and record why —
the estimator naming a different part's model on file as the starting point
makes a C2 line a B line. An earlier revision of the same part never does.

| Path | What step 7 does | Section |
|---|---|---|
| `C2` drawing | **Builds the model from the drawing** in a new document. The normal case | *Building the model — path C2* |
| `B` drawing + a different prior part's model | **Opens the prior model, applies the drawing's changes, saves as a new document.** The prior model is never overwritten. Falls back to C2 when the prior model is unavailable or the changes are not its parameters | *Path B* |
| `A` text only | **Builds from the text** with the same calls as C2. Every dimension `from_text`. **ROM only, never a firm quote** | *Path A* |
| `C1` STEP, no drawing | **Imports the STEP and reads it.** Nothing generated. STEP import through the connector is **unverified** | *Path C1* |
| `none` repeat part | Nothing to build. Priced from its routing or actuals, or a question back | |

**Name the path that actually ran.** A path B line built from the drawing
because the prior model was not there is reported as C2 with the reason, never
as path B: calling it B would tell the estimator a prior part's proven geometry
was reused when it was not.

**Rules for every path.** The model is an internal estimating aid and never
goes to a customer. Tolerances are read, never inferred: a general-note
tolerance applied to a feature cites the note, and a tolerance nobody stated
goes on `unreadables`. A datum assigned from the dimension scheme is
`inferred` and shown at Gate 3. Every path passes the integrity check before
and after its CAD step, and every path stops at Gate 3.

---

## Building the model — path C2

Read `../../design-space-explore/reference/cad-adapter.md` first: the
create-from-scratch calls, and the connector behaviors that lose calls or plant
foreign geometry. The rules that matter most:

- Every script defines `run(context)` and prints what it needs back.
- Inspection calls are `readOnly: true`.
- Each call under about 25 seconds.
- Design workspace active on every call.
- Fusion open with the document active; there is no file-only path.

Then:

1. **Create a new document**, named for the inquiry, line, part and revision —
   even when the open document is empty. The open document is the user's.
   Never a customer file, never an existing model.
2. **Integrity check, before.** List bodies and sketches, read-only. A fresh
   document lists none. Anything there means the add-in is replaying an earlier
   script: stop and ask the user to restart Fusion.
3. **Stock.** Material, form and size as the drawing or its material spec
   states. Fit check: part envelope plus the cleanup allowance against the
   stock, with the allowance's source. A part that fits only without cleanup is
   flagged.
4. **Datums.** A datum whose feature the drawing identifies is `stated`. A
   datum the drawing references in a feature control frame without identifying
   its feature is assigned from the dimension scheme and marked `inferred`.
   Every inferred datum is a question for Gate 3.
5. **Features**, prismatic first: sketch, extrude, hole or cut, fillet,
   chamfer. Each feature row carries its dimension, its tolerance **as read**,
   its `reading_basis`, and its view and zone. A general-note tolerance applied
   to a feature cites the note — that is reading. **A tolerance the drawing does
   not give and no note covers is not invented**: the feature goes on
   `unreadables`.
6. **Read back** bodies, bounding box and volume, and check them against a
   hand calculation from the drawing's dimensions. Record both in
   `model_checks`.
7. **Integrity check, after.** Every new body and sketch is one this step
   created, by name. **Anything else is foreign geometry: the step fails** for
   this line. Record both lists. Tell the user to restart Fusion.
8. **Setups and operations** — the plant's proposed way to make it, by machine
   class from the Plant context: which faces each setup reaches, the fixture
   note, which features each operation cuts, outside processes as their own
   operations. Every assumption on the operation it belongs to.
9. **Questions** for the estimator: every inferred datum, every assumption
   that changes the operation list, every tolerance tighter than the plant has
   demonstrated on that process.
10. **Cost-down ideas** go in `cost_down_proposals` — internal, never to the
    customer.

Emit the geometry estimate with `approval.status: draft`. **The skill never
marks it confirmed.**

## Path B — adapt a prior part's model

A drawing for this line, plus a **different** part whose model on file is
named as the starting point: *"same as our PN-4402-A housing, 10 mm longer."*
A new revision of a part the plant has already made is not path B; it is C2.

Run `../../design-space-explore/reference/adapt-prior-model.md`, the same
mechanism `design-space-explore` uses for its variants:

1. **The user opens the prior model in Fusion.** Read it, read-only: name,
   reference, version, parameters, bodies, sketches, unsaved changes.
2. **Compare it with the drawing.** List every difference as *parameter: prior
   value → drawing value, view and zone*. A difference no driving parameter
   controls means path B does not fit: fall back to C2.
3. **Save as a new document** named `<inquiry>_L<line>_<part>_R<rev>`, and
   confirm it is the active document before the first write.
4. Integrity check before (the copy lists exactly what the prior model held),
   apply the parameters, verify the regeneration, read back, integrity check
   after.
5. **Confirm the prior model's version did not move.**
6. Steps 3 and 4 and 8 to 10 of the C2 build — stock, datums, setups and
   operations, questions, cost-down ideas — exactly as for C2. **Every feature
   and tolerance on the estimate is read from the customer's drawing** and
   cites its view and zone. Nothing is carried over from the prior part's
   drawing.

Emit `origin: adapted_from_prior`, `base_model_ref` the prior model and its
version, `document_ref` the new document.

**The prior model is never overwritten**, edited in place, or saved. Asked to
"just update the old model", decline in one line and save as new.

**When the prior model is not available, the line falls back to C2** — not
on file, not found, the user cannot open it, unsaved changes in it, a change
that is not its parameter, a failed regeneration, a read-back that does not
match the drawing. Say it in one line, in these words, naming both paths so
the estimator sees which one ran: *"Path B: PN-4402-A model not on file; built
from the drawing as C2."* Emit the estimate as `geometry_path: C2`,
`origin: built_from_drawing`, `base_model_ref: null`, with the fallback and its
reason as the first entry in `questions_for_estimator`.

The open, save-as-new and untouched-check calls have not been run through the
connector. Say so at Gate 3 when path B ran.

## Path A — build from text specs, ROM only

Written specifications and no drawing: *"a 4140 bracket, 2 x 1.25 x 0.75 in,
one 0.500 in through-bore."* Same build as C2, with the text in place of the
drawing:

- **Every dimension and tolerance is `reading_basis: from_text`**, and its
  `source_ref` is the file and the line or paragraph of the text it came from.
- **A dimension the text does not give is not invented.** It goes on
  `unreadables` and becomes a question to the customer. A feature that cannot
  be built without it is not built.
- **A tolerance the text does not give is not invented either**, and the
  plant's usual tolerance is not applied: there is no drawing, so there is no
  general note to apply. Null, on `unreadables`.
- Datums are almost never stated in text. Any datum the build needs is
  `inferred`, and shown at Gate 3.
- Emit `origin: built_from_text`, `drawing_revision_priced_to: null`.

**A path A line is a ROM — rough order of magnitude — and never a firm
quote.** Say so at Gate 3 and in the hand-off to `quote-build`, which labels
it ROM on the internal sheet and calls it a budgetary estimate on the customer
document, per `../../quote-build/reference/hours-ladder.md`, *Path A*. A Gate 3
yes does not make it firm, and neither does an override. A firm quote needs a
drawing, and the drawing re-runs step 7 as C2.

Without Fusion: the hand-entered feature list, prefilled from the text, every
row `from_text`, `origin: hand_entered`. Still a ROM.

## Path C1 — import a STEP file and read it

A STEP or other 3D file and no drawing. **Nothing is generated**: no sketch,
no extrude, no change to the customer's geometry.

**STEP import through the connector is unverified.** It has never been run in
this repo. Say so on the line, every time.

With Fusion: import the STEP into a new document named like any estimating
model, integrity check before and after, then read bodies, bounding box,
volume and faces read-only. Holes, pockets and faces are recognised from the
faces; each is a reading to confirm at Gate 3, with its `source_ref` naming the
file and the body or face. Then stock, datums (every one `inferred`: a STEP
file identifies none), setups, operations and questions as for C2. Emit
`origin: customer_step`, `cad_backend: fusion`.

**A STEP file carries no tolerances this path reads.** Every feature's
`tolerance` is null and its `reading_basis` is `unreadable_flagged`, with the
gap on `unreadables`: *"no tolerance in the STEP file; ask the customer for
the drawing or a tolerance spec."* Tolerances are never taken from the model's
nominal geometry or from what is typical. That question goes back to the
customer through intake.

**When the import fails or Fusion is not connected**, in this order:

1. **"C1: STEP read without CAD (unverified)."** A STEP file is text. Read it
   as a file: the product name, the units, and where the file gives them, the
   overall extents and the cylindrical faces' radii. Each value cites the file
   and the entity number. Label every row unverified, `origin: customer_step`,
   `cad_backend: none`, `document_integrity: not_applicable`. Where the text
   does not yield a value, it is not estimated.
2. **Else a hand-entered feature list**: the estimator reads the STEP in
   whatever viewer they have and enters the features into the geometry
   estimate by hand, `origin: hand_entered`.
3. Else skip step 7, labelled.

A C1 line that also has a drawing is C2: the drawing is the geometry.

## When Fusion is not there

The chain completes; step 7 changes shape, and says so in one line on the
internal sheet: *"Fusion not connected — no model built."*

- **Offer a hand-entered feature list.** Prefill it from the drawing (path C2
  or B) or the text (path A) as intake read it — every feature with its view, zone and reading basis —
  with `origin: hand_entered`, `cad_backend: none`, `document_integrity:
  not_applicable`. It goes to Gate 3 exactly like a model, and once confirmed
  the feature path derives hours from it.
- **Or skip step 7.** No geometry estimate. The ladder starts at whatever rung
  exists — recorded actuals, else first principles — labelled.

Either way the chain does not stop at step 7 for want of Fusion. It still stops
at Gate 3.

---

## Gate 3 — what the estimator is shown

**Stop here, and say so:** *"Paused at Gate 3, step 8. The model for line 1 is
built and drafted below. Confirm or correct it; hours are derived from what you
confirm."*

Show, per line:

- The path that ran, and the model's document reference, or that the
  features were hand-entered, or that no model was built and why
- Path B: the prior model and its version, each parameter *from → to* with
  its drawing view and zone, and that the prior model's version did not move.
  Or the fallback to C2 and its reason
- Path A: that every dimension is `from_text`, and **that the line is a ROM
  only**
- Path C1: that the STEP import is unverified, and every feature as a
  reading to confirm
- The drawing revision every feature was read from
- **Every modelled feature with its dimension and its source** — the view
  and zone it was read from, or the general note applied to it. A feature
  list with no sources asks the estimator to re-read the drawing to check it
- **The read-back against the hand calculation**, both numbers shown —
  *"volume 1.6858 in³ (model) against 1.6858 in³ (hand calc from the
  drawing)"* — never only "matches"
- **The tolerances as read**, each with its reading basis and source
- **The datums**, stated and inferred, inferred ones by name
- The stock and its fit check, with any flag
- **The operation list**, setup by setup, with its assumptions
- The integrity result
- `questions_for_estimator`

A line with a current-revision routing is shown its routing's operation list
and the tolerance reading instead. It still passes Gate 3.

**A yes covers what was shown** — this model, these tolerances as read, these
datums, this operation list. It does not cover a later drawing revision, it
does not approve any hour (hours come after), and it does not approve a
cost-down idea. A correction is recorded in `approval.note` and the estimate is
re-emitted `confirmed` with who and when.

**The turn that shows the model does not also confirm it.** A request made
before the model was on screen — "build it and go straight to the price" — is
not a Gate 3 yes; it is generic continuation. **An override is different, and
explicit**: the estimator says to quote on the unconfirmed model. Then the
quote proceeds, the override is recorded on the internal sheet with who gave
it, and every hour it produced is labelled as resting on an unconfirmed model.
