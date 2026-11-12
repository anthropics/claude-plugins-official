# One backend, one interface

Fusion is the CAD backend this plugin reaches today. Nothing downstream of
this file should have to know that: build to the adapter surface below, not to
Fusion's command set directly, so a second CAD connector drops in later as an
implementation rather than a rewrite.

Three callers use this file:

- **`design-space-explore`** — variants of an existing model. It reads
  parameters, applies parameter sets, reads properties and creates variant
  documents. **It never designs from scratch.**
- **`rfq-to-quote`, step 7** — the design step. Path C2 (a drawing) and path A
  (text specs) build an estimating model in a **new** document with the
  create-from-scratch calls below. Path B adapts a prior part's model with the
  same open, apply and save-as-new mechanism `design-space-explore` uses —
  `adapt-prior-model.md`. Path C1 imports a customer's STEP file, which is
  **unverified**.
- **`quote-build`, the CAM path** — setups, operations, toolpaths and machining
  time on the model `rfq-to-quote` built and the estimator confirmed.

---

## Fusion — desktop, live geometry

Real-time modeling and command-based operations against **whatever design
is currently open in the desktop app.**

- **Desktop app only.** Does not work with Fusion's web client at all.
- **No server-side fetch path.** The skill can only act on a document
  already open on the user's machine. There is no way to reach a Fusion
  document that isn't open in front of the person running this.
- If the document is not open, **say so and stop** — this is not a
  degradation to work around, it's a precondition that isn't met yet.

There is no fallback CAD backend. No connector currently reaches SolidWorks,
Creo, NX or Inventor; a plant on any of those runs the paths that need no CAD.

---

## What every backend implementation has to expose

### Variant operations — `design-space-explore`

| Operation | What it does |
|---|---|
| Read parameters | List the model's dimensions and which are driving geometry |
| Apply a parameter set | Regenerate the model against one set of values |
| Read computed properties | Mass, volume, bounding box, whatever else the tool exposes |
| Create a variant document | A new document or named configuration, never the base |

Everything in `parametric-check.md` and `variant-generation.md` is written
against this surface.

### Open, apply, save as new — `design-space-explore` and `rfq-to-quote` path B

The sequence is `adapt-prior-model.md`. The calls it needs:

| Operation | What it does | Notes |
|---|---|---|
| Read the open document | Name, document reference, version number, unsaved changes | Read-only. The user opens the prior model; opening it from the hub by script is not verified |
| Save as new document | Copy the open model to a new name and make the copy the active document | **Before** any parameter change. Read the active document's name back before the first write |
| Apply a parameter set | As above | In the new document only |
| Read the prior model's version | Confirm it did not move | Read-only, after the run. A moved version stops the run |

**Not run through the connector in this repo.** The prior model is never
saved, never edited in place, and never the active document during a write.

### STEP import — `rfq-to-quote` path C1 (unverified)

| Operation | What it does | Notes |
|---|---|---|
| Import STEP to a new document | The customer's STEP file as bodies in a new document, named like any estimating model | **Unverified.** Never run through the connector. The file has to be on the machine running Fusion |
| Read bodies and faces | Bounding box, volume, planar and cylindrical faces with their sizes | Read-only. A STEP file carries bodies, not a feature history: holes and pockets are recognised from faces, and each one is a reading to confirm at Gate 3 |

**Nothing is generated on path C1** — no sketch, no extrude, no change to the
imported bodies. The import is read. A STEP file carries no tolerances this
path reads; every tolerance comes from a drawing or the customer's text, or
goes on `unreadables`. Where the import fails, or Fusion is not connected,
`rfq-to-quote` reads the STEP file as text without CAD, labelled unverified,
or takes a hand-entered feature list; see `../../rfq-to-quote/reference/design-step.md`.

### Create-from-scratch operations — `rfq-to-quote` step 7

Always in a **new document the step creates itself**, named for the inquiry,
line and revision (`<inquiry>_L<line>_<part>_R<rev>`). **Even when the open
document is empty** — it is the user's document, and a replayed script has
been seen to land geometry in an "empty" one. Never build in a document that
holds anything else, and never in a customer's file. Report the new document's
name.

| Operation | What it does | Notes |
|---|---|---|
| Create sketch | A sketch on a named plane or face | Dimensions from the drawing, each with its view and zone |
| Extrude | Profile to a distance, new body or join | Stock and the main prismatic form |
| Hole / cut | Through, blind or counterbored, by extrude-cut or the hole feature | The bore; a pocket |
| Fillet | Edge set and radius | Read edges back to confirm the right ones took it |
| Chamfer | Edge set and distance | A "break all edges" note is a chamfer set, cited to the note |
| Read back | Bodies, bounding box, volume | Checked against a hand calculation from the drawing |

Prismatic features are verified this way, from a drawing. Anything else —
threads, lofts, sheet metal — is unverified; build it if it works, and say it
was not verified. Path A uses the same calls with dimensions read from text;
that has not been run.

### CAM operations — `quote-build` CAM path

| Operation | What it does | Notes |
|---|---|---|
| Create setup | Machine class, stock, work coordinate system | One per `setups` row of the geometry estimate. Stock-to-leave set explicitly |
| Create operation | Strategy, tool, geometry selection, feeds | In `op_seq` order — there is no reorder |
| `generateToolpath` | Start generation | Poll; do not wait on its return |
| Read toolpath | Points along the path | For the geometry check |
| `getMachiningTime` | Cycle time per operation | Ignores the tool-change time it is given; add tool changes yourself |

---

## Connector behaviors that break a naive script

Observed on the live Fusion connector (`fusion_mcp_read` and
`fusion_mcp_execute`, script feature type). Each one has produced
a wrong answer or a lost call. **Read these before the first call.**

- **A script must define `run(context)`.** Top-level code fails. **Return
  values are discarded; `print()` is the only output channel**, so every value
  you need back is printed. **The tool calls `run()` itself: a script that also
  calls `run()` at the bottom executes twice**, and a write runs twice. Define
  it; never call it.
- **There is no read command for parameters, regeneration health or physical
  properties.** Every one is a `readOnly: true` script: the parametric check
  reads `userParameters` and what drives each feature; mass, volume and
  bounding box come from the body's `physicalProperties`. **The regeneration
  test is each timeline item's `healthState`**: any item not healthy after a
  parameter change is a failed variant, recorded as such, never measured.
- **`readOnly: true` is enforced server-side.** Use it on every inspection
  call — listing bodies, reading parameters, reading a toolpath.
- **A 60-second device timeout means the call was not delivered**, not that it
  ran silently. Keep each call under about 25 seconds and split long work
  across calls. Poll toolpath generation across calls.
- **The add-in can retain an earlier script and append it to every later
  call until Fusion restarts.** The symptom is geometry nobody asked for on a
  write, and read-only calls failing with "cannot modify." There is no fix from
  the script side: **stop, and ask the user to restart Fusion.**
- **The wrapper crashes when the active product is CAM.** Make every call
  with the Design workspace active and switch to Manufacture inside the
  script. After a crash, workspace sync is lost until a person clicks a
  workspace tab — ask them to.
- **The `generateToolpath` future is unreliable.** Poll `op.isGenerating` and
  `op.hasToolpath`.
- **A parameter edit does not invalidate an existing toolpath.** Call
  `clearToolpath` before regenerating, or the old path is read as new.
- **Operations cannot be reordered** through the API. Create them in order.
- **Flute count set through operation parameters fails silently.** Set it
  through `op.tool`, which resets the feeds — so set the tool first, feeds
  last, and read both back.
- **Chain side is controlled only through `isReverted`.**
- **A stock-contour slot cannot be cleared once set, and the setup's virtual
  stock cannot be selected as a boundary.** Sketch a circle for the boundary,
  or set `useStockContours = false`.
- **Fusion must be open with the document active.** There is no file-only
  path.

---

## Document integrity — before and after every design or CAM step

Because of the replayed-script behavior above, a write can land geometry from
an earlier call.

1. **Before**, read-only: list every body and sketch in the document. A fresh
   document should list none.
2. Run the step.
3. **After**, read-only: list them again. Every new body and sketch must be one
   this step created, by name.
4. **Anything else is foreign geometry and the step fails.** Record the
   result in the geometry estimate's `document_integrity` with both lists. If
   it turned up in a fresh document, the add-in is replaying: tell the user to
   restart Fusion, and do not retry until they have.

A clean result is recorded too. "Not checked" is a result, and it is reported
as one.

## Toolpath verification — by geometry, per operation

`isToolpathValid` says the path can be cut. It does not say it cuts the right
place: a path reported valid has cut the wrong region of a part.

After generation, read the toolpath points and test them against the
operation's intent — **outside the boss** for a profile, **inside the pocket**
boundary for a pocket, **within the hole** radius for a bore. Record per
operation the points read, how many satisfy the intent, and pass or fail. A
failed operation is fixed or dropped, never timed.

---

## Record which backend ran

`cad_backend` travels with every output that came from CAD — `fusion`, or
`none` for anything hand-authored — on the variant manifest and on the geometry
estimate alike. A record with no backend is not distinguishable from one
nobody thought to check, and the day a second CAD connector appears, every
existing record needs to already carry the field it will be filtered on.
