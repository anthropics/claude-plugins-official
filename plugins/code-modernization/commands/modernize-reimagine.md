---
description: Multi-agent greenfield rebuild — extract specs from legacy, design AI-native, scaffold & validate with HITL
argument-hint: <system-dir> <target-vision>
---

The first token of `$ARGUMENTS` is the system dir (`$1`); **everything
after it is the target vision** — it is usually multiple words, so do not
truncate it to one token. Below, `<vision>` means that full remainder.

**Reimagine** `legacy/$1` as: <vision>

This is not a port — it's a rebuild from extracted intent. The legacy system
becomes the *specification source*, not the structural template. This command
orchestrates a multi-agent team with explicit human checkpoints.

## Phase A — Specification mining (parallel agents)

Spawn concurrently and show the user that all three are running:

1. **business-rules-extractor** — "Extract every business rule from legacy/$1
   into Given/When/Then form. Output to a structured list I can parse."

2. **legacy-analyst** — "Catalog every external interface of legacy/$1:
   inbound (screens, APIs, batch triggers, queues) and outbound (reports,
   files, downstream calls, DB writes). For each: name, direction, payload
   shape, frequency/SLA if discernible. Mask any credential embedded in
   endpoints or payload examples per your secret-handling rules."

3. **legacy-analyst** — "Identify the core domain entities in legacy/$1 and
   their relationships. Return as an entity list + Mermaid erDiagram."

Collect results. Write `analysis/$1/AI_NATIVE_SPEC.md` containing:
- **Capabilities** (what the system must do — derived from rules + interfaces)
- **Domain Model** (entities + erDiagram)
- **Interface Contracts** (each external interface as an OpenAPI fragment or
  AsyncAPI fragment)
- **Non-functional requirements** inferred from legacy (batch windows, volumes)
- **Behavior Contract** (the Given/When/Then rules — these are the acceptance tests)

Credential values are masked everywhere in the spec; connection details
appear as env-var placeholders (`${DATABASE_URL}`), never literals.

## Phase B — HITL checkpoint #1

Present the spec summary. Ask the user **one focused question**: "Which of
these capabilities are P0 for the reimagined system, and are there any we
should deliberately drop?" Wait for the answer. Record it in the spec.

## Phase C — Architecture (single agent, then critique)

Design the target architecture for "<vision>":
- Mermaid C4 Container diagram
- Service boundaries with rationale (which rules/entities live where)
- Technology choices with one-line justification each
- Data migration approach from legacy stores

Then spawn **architecture-critic**: "Review this proposed architecture for
<vision> against the spec in analysis/$1/AI_NATIVE_SPEC.md. Identify over-engineering,
missed requirements, scaling risks, and simpler alternatives." Incorporate
the critique. Write the result to `analysis/$1/REIMAGINED_ARCHITECTURE.md`.

## Phase D — HITL checkpoint #2

Present the architecture and **stop — scaffold nothing until the user
explicitly approves** (use plan mode if the session supports it).

## Phase E — Parallel scaffolding

This phase runs only **after** the user approved the architecture in
Phase D — the approval is what authorizes the build-out.

**Preferred — Workflow orchestration.** If the **Workflow tool** is
available, scaffold **every** service in the approved architecture — no cap;
the workflow runtime queues agents against its concurrency limit, so 8
services are as tractable as 3:

```
Workflow({
  scriptPath: "${CLAUDE_PLUGIN_ROOT}/workflows/reimagine-scaffold.js",
  args: { system: "$1", services: [
    { name: "<service-name>", responsibilities: "<one-line summary from the architecture>" },
    ...
  ] }
})
```

Tell the user the service count before launching. Each agent writes only to
its own `modernized/$1-reimagined/<service-name>/` directory (disjoint, so
parallel writes don't conflict). On return, report from the structured
result: services scaffolded (`scaffolded[]`) and `totals` (services,
acceptanceTests, pendingRules count); the actual pending rule IDs and any
planted-instruction/blocker notes are per-service at `scaffolded[].pendingRuleIds`
and `scaffolded[].blockers` (check every service's `blockers` — that's where the
untrusted-spec injection signal surfaces); plus `notScaffolded` for anything
skipped.

**Fallback** (no Workflow tool): for each service — cap at 3 to keep the run
tractable; tell the user which you deferred — spawn a **scaffolder agent
in parallel**:

"Scaffold the <service-name> service per analysis/$1/REIMAGINED_ARCHITECTURE.md
and AI_NATIVE_SPEC.md. Create: project skeleton, domain model, API stubs
matching the interface contracts, and **executable acceptance tests** for every
behavior-contract rule assigned to this service (mark unimplemented ones as
expected-failure/skip with the rule ID). No credential literal from legacy
code becomes a test fixture or config default — use fake same-shape values
and env-var placeholders. Write to modernized/$1-reimagined/<service-name>/."

Show the agents' progress. When all complete, run the acceptance test suites
and report: total tests, passing (scaffolded behavior), pending (rule IDs
awaiting implementation).

## Phase F — Knowledge graph handoff

Write `modernized/$1-reimagined/CLAUDE.md` — the persistent context file for
the new system, containing: architecture summary, service responsibilities,
where the spec lives, how to run tests, and the legacy→modern traceability
map. This file IS the knowledge graph that future agents and engineers will
load — and it gets committed: connection details and credentials appear
only as env-var names with a pointer to where they're provisioned, never
as values.

Report: services scaffolded, acceptance tests defined, % behaviors with a
home, location of all artifacts.
