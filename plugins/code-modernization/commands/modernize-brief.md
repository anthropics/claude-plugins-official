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
for a same-stack uplift (libraries before the apps that depend on them). Name
the per-phase execution command: `/modernize-transform` (cross-stack module
rewrite), `/modernize-reimagine` (greenfield rebuild), or `/modernize-uplift`
(same-stack version bump — when the target is a newer version of the *same*
stack, this is the path, not transform). For each phase:
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

Render the phases as a Mermaid `flowchart LR` showing **sequence and
dependencies** (Phase 1 → Phase 2 → …, with branches where phases are
independent). Do **not** use a `gantt` chart — gantt encodes calendar
durations, and this plan deliberately makes no time claims.

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
