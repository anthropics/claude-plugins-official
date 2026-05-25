---
description: Generate a phased Modernization Brief — the approved plan that transformation agents will execute against
argument-hint: <system-dir> [target-stack]
---

Synthesize everything in `analysis/$1/` into a **Modernization Brief** — the
single document a steering committee approves and engineering executes.

Target stack: `$2` (if blank, recommend one based on the assessment findings).

Read `analysis/$1/ASSESSMENT.md`, `analysis/$1/TOPOLOGY.html` (and the `.mmd`
files alongside it), and `analysis/$1/BUSINESS_RULES.md` first. If any are
missing, say so and stop — they come from `/modernize-assess`, `/modernize-map`,
and `/modernize-extract-rules` respectively. Run those first.

## The Brief

Write `analysis/$1/MODERNIZATION_BRIEF.md`:

### 1. Objective
One paragraph: from what, to what, why now.

### 2. Target Architecture
Mermaid C4 Container diagram of the *end state*. Name every service, data
store, and integration. Below it, a table mapping legacy component → target
component(s).

### 3. Phased Sequence
Break the work into 3-6 phases using **strangler-fig ordering** — lowest-risk,
fewest-dependencies first. For each phase:
- Scope (which legacy modules, which target services)
- Entry criteria (what must be true to start)
- Exit criteria (what tests/metrics prove it's done)
- Estimated effort (person-weeks, derived from COCOMO + complexity data)
- Risk level + top 2 risks + mitigation

Render the phases as a Mermaid `gantt` chart.

### 4. Behavior Contract
List the **P0 rules** from BUSINESS_RULES.md (the ones tagged `Priority: P0` —
money, regulatory, data integrity) that MUST be proven equivalent before any
phase ships. These become the regression suite. Flag any P0 rule with
Confidence < High as a blocker requiring SME confirmation before its phase
starts.

### 5. Validation Strategy
State which combination applies: characterization tests, contract tests,
parallel-run / dual-execution diff, property-based tests, manual UAT.
Justify per phase.

### 6. Open Questions
Anything requiring human/SME decision before Phase 1 starts. Each as a
checkbox the approver must tick.

### 7. Approval Block
```
Approved by: ________________  Date: __________
Approval covers: Phase 1 only | Full plan
```

## Present

Enter **plan mode** and present a summary of the brief. Do NOT proceed to any
transformation until the user explicitly approves. This gate is the
human-in-the-loop control point.
