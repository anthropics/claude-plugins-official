# The hours step and the ladder

**Every machine hour on the internal sheet says where it came from.** An
estimator handed "op 20: 9.5 min/pc" cannot tell a number read off a current
routing from one Fusion produced with library feeds, and those two numbers
deserve very different amounts of trust. So each operation carries its rung,
its path, its cutting-data basis, its setup and run separately, a range, and
the variance against every other source that exists.

None of it reaches the customer. The customer quote carries prices; this file
is the internal sheet's business.

---

## What the hours step reads

| Input | From | When it is absent |
|---|---|---|
| Routings | `routings` tab, consolidated dataset v4, or a routing file | No rung 1. Say so per part |
| Operation actuals | `operation_actuals` tab, dataset v4, or an actuals file | No rung 2. Say so per part |
| Geometry estimate | `../../../shared/contracts/geometry-estimate.md`, from `rfq-to-quote` step 7 or typed by the estimator | No rung 3. The internal sheet says the design step did not run and why |
| Machine classes | `Machine classes` table under `### Machining data` in the `## Plant context` block: Machine class, Work centers, Cell, Setup hours, Tool change min, Basis | Setup at rung 3 cannot be taken from the plant. Name it; the estimator supplies it or the op falls to rung 4 |
| Cutting data | `Cutting data` table in the same section (Material, Tool class, SFM, Chip load ipt, Basis), or a line `Fusion tool library: <name>` | The CAM path runs on library feeds and every op is `fusion_default`, rung 4. The feature path cannot compute a cut time |
| Variance flag threshold | `Variance flag threshold: <percent>` in the same section | Use 15%, and print it as **"15% — default threshold, not plant-set"** wherever a flag depends on it |

A value tagged `Basis: assumed` in either table is used and labelled assumed on
every op it touches. It is the plant's number, recorded as a guess.

---

## The ladder, per operation

Best available first. **The highest rung that exists for an operation is its
basis; every other rung that exists is shown beside it as a cross-check.**

| Rung | What qualifies | What does not |
|---|---|---|
| **1 — Routing** | A routing for this part **and the revision being quoted**, cited by file and row or record. A routing that records no revision is usable, labelled *"routing revision not recorded — confirm it is current for Rev X"* | A routing for another revision. It is **superseded**: shown on the internal sheet as *"Rev 1 routing — superseded, not used"*, never priced from, at any rung |
| **2 — Closed-job actuals** | Actual setup and run hours from closed production work orders for this part and operation, `actuals_confidence: recorded`. Each work order named, the count from the figures block | Actuals flagged `probable_standard`. See below |
| **3 — Geometry-derived** | Hours derived from a geometry estimate whose `approval.status` is `confirmed` — or `draft` with the estimator's explicit say-so in this run, recorded — by the CAM path or the feature path, with `cutting_data_basis` of `plant_library` or `estimator_entered` | Anything on `fusion_default` cutting data. Anything from an unconfirmed model with no say-so |
| **4 — First principles** | Everything else: library feeds, a similar part's routing, the estimator's judgement, a feature path with no cutting data. **Always names what would firm it up** — *"a current routing, or plant SFM for 4140 with a 0.5 in carbide end mill"* | Never presented as anything firmer than it is |

### `probable_standard` actuals never outrank rung 3

Actuals the backflush check flagged may be the routing standard posted under a
work order number. They are shown, with their `confidence_reason`, and ranked
**below a geometry-derived estimate and above first principles.** Where the
standard they echo belongs to a superseded routing, they echo a superseded
standard: say that, too.

### Actuals from an earlier revision

Actuals carry the revision the job ran to where the source records it. Where a
drawing revision changed something this operation cuts or holds — the revision
history names it — those actuals are a cross-check for that operation, not its
basis. Operations the change did not touch keep them at rung 2, labelled with
the revision they ran at.

### Units

Setup in hours, run as minutes per piece. Where a source declares its unit,
converting minutes and hours is exact and is shown once (*"routing 7.00 min/pc
= 0.117 h/pc"*). **Where a source's unit is undeclared, that source is not used
for that operation** until the plant says what the unit is. The dataset's
`time_unit_flag` is carried onto the sheet.

---

## Setup and run, separately, at every rung

Setup is a cost per job; run is a cost per piece. Each rung supplies both, or
says it cannot.

**A source that gives only a lumped total has an unknown split.** State it, and
**never re-amortize it**: a total of 25 hours for 200 pieces is not 0.125 h/pc
at a quantity of 50, because nobody knows how much of the 25 was setup. For the
quantity-break arithmetic, use the highest rung that does carry a split, and
show the lumped figure beside it at the quantity it came from.

---

## The range, and where each bound comes from

Low, expected and high, setup and run, **on the internal sheet only.** Each
bound names what produced it:

- Rung 1: the routing standard is expected. Low and high come from recorded
  actuals for the same operation where they exist; otherwise the range is a
  single point, printed as *"no spread available"*.
- Rung 2: median of the recorded work orders is expected; the lowest and
  highest are low and high.
- Rung 3: the CAM path and the feature path bound each other where both ran;
  otherwise the cutting data's own spread where the table gives one; otherwise
  a single point.
- Rung 4: the range the stated assumptions produce, each assumption named.

**A range never comes from a percentage band nobody measured.** "±15%" with no
source is an invented number with a plus-minus sign.

---

## Variance

Where two or more rungs exist for an operation, compute in code, for setup and
for run separately: (other − basis) ÷ basis. Put each in the figures block.

**Flag any variance above the threshold** — the Plant context's `Variance flag
threshold`, or 15% labelled *"default threshold, not plant-set"*.

**Every flagged variance names its drivers.** What differs between the two
numbers: a tool-change allowance, a feed at nominal diameter, a finish pass one
source has and the other lacks, a revision change, a backflushed standard.

**An assumed plant value that accounts for more of a gap than the threshold is
named as a driver**, with its `Basis: assumed` tag. A 0.5 min tool change
across fourteen tool changes is seven minutes a piece, and if the measured
value is 0.15 min, that assumption is most of a 36% gap. The estimator needs to
see that the plant's own default, not the cutting, is the variance.

---

## The CAM path

Runs when Fusion is connected with its Manufacturing workspace, a confirmed
geometry estimate has a `document_ref`, and cutting data exists in the Plant
context or as a named Fusion tool library. The connector calls and the
behaviors that break them are in
`../../design-space-explore/reference/cad-adapter.md` — read it before the
first call.

1. **Integrity check first** (rule 7.5). List bodies and sketches. Anything not
   in the geometry estimate's `bodies_after` / `sketches_after` fails the step.
   Repeat after the CAM step.
2. **One setup per `setups` row**, stock and stock-to-leave set explicitly
   (rule 7.6). Create operations in `op_seq` order — they cannot be reordered.
3. **Cutting data from the plant**, per op: `cutting_data_basis` is
   `plant_library` (the Plant context table, or the named Fusion tool library),
   `estimator_entered` (typed in this run by the estimator, recorded), or
   `fusion_default`. **`fusion_default` demotes the op to rung 4, labelled
   "library defaults, not plant data"** (rule 7.1). Set the tool first, feeds
   last, and read them back.
4. **Chamfers and small features** use the effective cutting diameter or the
   plant's fixed feed, never the tool's nominal diameter (rule 7.7).
5. **Generate, then poll** `isGenerating` / `hasToolpath`. Clear an existing
   toolpath before regenerating.
6. **Verify each toolpath by geometry** (rule 7.4). Read the toolpath points
   and check them against the op's intent — outside the boss, inside the
   pocket, within the hole. `isToolpathValid` is necessary, not sufficient: a
   valid toolpath has cut the wrong region before. Record per op: points read,
   points inside the intended region, pass or fail. A failed op is not timed.
7. **Read machining time per op.** Add tool changes yourself: the Plant
   context's `Tool change min` × the op's tool-change count (rule 7.2).
   `getMachiningTime` ignores the tool-change time it is given.
8. **Rough-only times are labelled rough-only** (rule 7.6). A finish pass the
   CAM setup does not cut is added by the feature path and labelled as such.

Without Fusion Manufacturing: the feature path only, and the sheet says so.

## The feature path

Runs always where a confirmed geometry estimate exists, Fusion or not. Per
operation, from its `features` rows:

1. **Setup hours** from the operation's machine class in the `Machine classes`
   table, with its basis tag.
2. **Cut time per feature** from the cutting data for the material and tool
   class: spindle speed = SFM × 3.82 ÷ tool diameter; feed = speed × chip load ×
   flutes; time = cut length ÷ feed. Tool diameter, flutes, stepover and depth
   of cut are **assumptions, named on the op** — the estimator confirmed the
   operation list at Gate 3, not the tooling. Chamfers per rule 7.7.
3. **Tool changes** = count × `Tool change min`, labelled with its basis.
4. **Outside processes** carry no machine time. Their lead time — *"black
   oxide, 5 working days per lot"* — goes to the date check.

No cutting data for the material: the feature path cannot compute a cut time.
That op's run falls to rung 4 unless the estimator enters cutting data, which
makes it `estimator_entered`.

**No row for a tool class — a reamer, a chamfer mill — is not licence to supply
one.** Time that element on the nearest row the table does have, say which row
and that it is a stand-in, and mark the element rung 4. Never a handbook SFM,
never a "typical" feed: that is a rate the model invented, with a unit.

---

## The internal sheet, per operation

One row per operation, inside the internal cost sheet's delimiters:

| Column | Holds |
|---|---|
| Op | `op_seq` and description |
| Work center / cell | From the routing, or the machine class map |
| Rung | 1–4, and *why not higher* where a higher rung was refused (superseded, `probable_standard`, unconfirmed model) |
| Path | Routing, actuals, CAM path, feature path, first principles |
| Cutting data basis | `plant_library`, `estimator_entered`, `fusion_default`, or n/a |
| Setup h | Low / expected / high, each bound's source |
| Run min/pc | Low / expected / high, each bound's source |
| Other rungs | Each with its setup and run, and the variance against the basis |
| Variance drivers | Named, assumed plant values tagged |
| Toolpath check | CAM path only: result per op, or *"not run — feature path"* |

## The operation record

Kept with the quote, because revisions re-derive from it and because one day
someone will ask how good these estimates were. Per operation: part, revision
priced to, `op_seq`, work center, machine class, rung, path, cutting data basis,
setup and run (low, expected, high, with units), the quantity breaks they were
priced at, every source cited, the geometry estimate's `document_ref` and
approval state, and the date derived. **That is enough to compare against the
actuals when the job closes, by part, revision and operation.** The comparison
itself is not built yet.

A price counter re-derives from this record. It never reopens CAD.

---

## Path A — a ROM, never a firm quote

A line is path A when the intake form line's `geometry_path` is `A`, or its
geometry estimate's `geometry_path` is `A` or its `origin` is
`built_from_text`: text specifications and no drawing. Every dimension was
read from text, and no tolerance came from a drawing. **The price is a rough
order of magnitude, and the quote says so on both documents, in different
words.**

- **Internal sheet.** The first line inside its delimiters reads *"ROM —
  rough order of magnitude. Path A: text specs, no drawing. Not a firm quote
  and not releasable as one."* The ladder runs as usual, and every hour is
  labelled as it would be.
- **Customer document.** It stays inside `=== CUSTOMER QUOTE — SENDABLE ===`
  but is titled **Budgetary estimate**, not quotation, and its assumptions
  carry one sentence in customer terms: *"This is a budgetary estimate based on
  the written specifications you provided, for planning only. It is not an
  offer; we will send a firm quotation on receipt of a released drawing."*
  **Nothing about how it was estimated**: not "ROM", not "rough order of
  magnitude", not text specs, path, model, hours or basis. The outbound check
  rejects them in this block like any other basis label.
- **At Gate 4** the estimator may release it as a budgetary estimate. **No
  release, override or Gate 3 yes turns it into a firm quote.** Asked to, say
  so in one line: a firm quote needs a drawing, and the drawing goes back to
  `rfq-to-quote` step 7 as path C2.
