---
description: Generate a phased Modernization Brief — the approved plan that transformation agents will execute against
argument-hint: <system-dir> [target-stack]
---

Synthesize everything in `analysis/$1/` into a **Modernization Brief** — the
single document a steering committee approves and engineering executes.

Target stack: `$2` (if blank, recommend one based on the assessment findings).

Read `analysis/$1/ASSESSMENT.md`, `analysis/$1/topology.json` (plus the
`.mmd` files alongside it — do NOT read `TOPOLOGY.html`, it's an
interactive viewer with the data minified inside), and
`analysis/$1/BUSINESS_RULES.md` first. If any are missing, say so and
stop — they come from `/modernize-assess`, `/modernize-map`, and
`/modernize-extract-rules` respectively. Run those first.

Two more inputs are conditional:

- **`analysis/$1/PREFLIGHT.md`** — read it if it exists. It records two
  things nothing else has: the human's answers to `/modernize-preflight`
  Check 0 (scope, whether they can build and run tests locally and how
  long CI takes, bespoke build infrastructure, prior attempts, what is
  off-limits) and the Check 6 **scope boundary** — whether `legacy/$1` is
  a slice of a larger codebase, and what *outside* it depends on code
  *inside* it. Both constrain this plan more than anything derivable from
  the source. Never override an answer the human gave there with a guess.
- **`analysis/$1/DELTA_CATALOG.md`** — **required** whenever the target
  (`$2`, or your recommendation) is a newer version of the *same* stack.
  A same-stack uplift's phase order is decided by its version deltas, not
  by the topology alone — most of all by whether the **existing test suite
  can even execute on the target runtime**. Phasing an uplift without the
  catalog is planning blind; it is exactly how a test-framework migration
  ends up scheduled last when it must come first. If the catalog is
  missing, produce it *before* phasing — run `/modernize-uplift $1
  <source> $2` through its Step 3 (the delta-catalog step), or spawn the
  **version-delta-analyst** agent directly — then return here. Do not
  guess at the deltas.

**Staleness check:** compare modification times. If any input is newer
than an existing `MODERNIZATION_BRIEF.md`, the brief is being justifiably
regenerated; but if an existing brief is newer than all inputs and the
user re-ran this command anyway, ask what changed. Either way, note the
input timestamps in the brief's header so reviewers can see what it was
built from.

## The Brief

Write `analysis/$1/MODERNIZATION_BRIEF.md`:

### 1. Objective
One paragraph: from what, to what, why now.

### 2. Target Architecture
Mermaid C4 Container diagram of the *end state*. Name every service, data
store, and integration. Below it, a table mapping legacy component → target
component(s).

### 3. Phased Sequence
Break the work into 3-6 phases. Order by **strangler-fig** for a cross-stack
rewrite (lowest-risk, fewest-dependencies first), or **build-graph leaf-first**
for a same-stack uplift (libraries before the apps that depend on them).

For an **uplift**, leaf-first has three overrides, and getting them wrong is
the most common way an uplift plan fails. Apply them *here*, at planning
time. `/modernize-uplift` Step 1 re-applies the same rules at execution
time (its list also names multi-targeting — the *technique* that satisfies
override 3's first option), and an approved order and a re-derived one must
never disagree — which is exactly what deciding the order without these
would produce:

1. **The test harness is not a leaf — it is a prerequisite.** Nothing
   migrated can be validated until the tests that validate it run on the
   target. If `DELTA_CATALOG.md` shows the test framework or its runner
   does not support the target runtime (NUnit 2 or MSTest v1 on modern
   .NET, JUnit 4 without the vintage engine, `nose` on Python 3, …), then
   migrating the test framework is **Phase 1 by itself**, before any
   production code moves.
2. **Dependency deltas that every consumer shares force a coordinated
   cut** (a major-version bump of an ORM, a namespace move like
   `javax`→`jakarta`). These cannot be done leaf-first incrementally —
   every consumer changes together — so they get their own cross-cutting
   phase.
3. **Shared nodes with consumers *outside* the scope** (PREFLIGHT.md's
   scope-boundary check) need an explicit, recorded decision in whichever
   phase touches them: keep them buildable for both old and new consumers
   through the transition (multi-targeting, publishing for both versions,
   a parallel artifact), expand the scope to include the consumers, or
   accept and schedule the break. Never silently migrate a shared node in
   place and break every consumer nobody was looking at.

Name the per-phase execution command: `/modernize-transform` (cross-stack
module rewrite), `/modernize-reimagine` (greenfield rebuild), or
`/modernize-uplift` (same-stack version bump — when the target is a newer
version of the *same* stack, this is the path, not transform). For each phase:
- Scope (which legacy modules, which target services)
- Entry criteria (what must be true to start)
- Exit criteria (what tests/metrics prove it's done)
- Relative scale (T-shirt size — S/M/L/XL — anchored to the phase's share
  of the assessment's COCOMO complexity index. This ranks phases by size
  against each other; it is **not** a duration. Do **not** state
  person-months, weeks, calendar dates, or a delivery estimate — agentic
  transformation does not follow the human-team productivity curves those
  units assume, so any time figure here would be misleading.)
- Risk level + top 2 risks + mitigation

The named execution command **reads this brief** and treats its phase's
scope, entry criteria, and exit criteria as binding gates. So write entry
criteria as *checkable preconditions* ("baseline recorded in
`analysis/$1/BASELINE.md`", "pilot playbook approved"), not aspirations —
and tell the approver they steer execution by editing this file. An edited
entry criterion is honored; a note in a chat is not.

Render the phases as a Mermaid `flowchart LR` showing **sequence and
dependencies** (Phase 1 → Phase 2 → …, with branches where phases are
independent). Do **not** use a `gantt` chart — gantt encodes calendar
durations, and this plan deliberately makes no time claims.

**Phase 1 is a pilot, and this brief is a hypothesis.** Whenever a phase's
units share one execution recipe (an uplift over many projects, a transform
over many similar modules), name **one representative unit** as that
phase's own first slice. For an uplift, `/modernize-uplift` Step 5a
*enforces* this — it will not fan out without a pilot and its playbook; for
the other execution commands the pilot lives here, written into that
phase's **entry criteria**, which they read as a gate. A reviewer should
see it in this document either way. Say explicitly in §3 that what the pilot
surfaces (a delta the analysis missed, a prerequisite that reorders the
phases, an environment fact nobody wrote down) is *expected* to revise
this brief, and that a regenerated brief after the pilot is the normal
path, not a correction. Legacy systems hide their surprises in the build
and the runtime, not in the source; no amount of reading substitutes for
one unit taken all the way through.

### 4. Business Walkthroughs
For each persona flow in `analysis/$1/topology.json` (`flows` — produced
by `/modernize-map`), a short narrative table: persona, what happens in
business language, which legacy modules implement it today, and which
phase from §3 replaces each. This is the section non-technical approvers
actually read — it connects "Phase 2" to "what happens when a customer
files a claim". If topology.json has no flows, derive 2–3 walkthroughs
from the entry points and say they need SME confirmation.

### 5. Behavior Contract
List the **P0 rules** from BUSINESS_RULES.md (the ones tagged `Priority: P0` —
money, regulatory, data integrity) that MUST be proven equivalent before any
phase ships. These become the regression suite. Flag any P0 rule with
Confidence < High as a blocker requiring SME confirmation before its phase
starts.

### 6. Validation Strategy
State which combination applies: characterization tests, contract tests,
parallel-run / dual-execution diff, property-based tests, manual UAT.
Justify per phase.

### 7. Open Questions
Anything requiring human/SME decision before Phase 1 starts. Each as a
checkbox the approver must tick.

### 8. Approval Block
```
Approved by: ________________  Date: __________
Approval covers: Phase 1 only | Full plan
```

## Present

Present a summary of the brief and **stop — write nothing further until
the user explicitly approves** (use plan mode if the session supports
it). This gate is the human-in-the-loop control point; "no objection" is
not approval.
