---
description: Delegate a task to PACT specialist agents
argument-hint: [e.g., implement feature X]
---
Orchestrate specialist PACT agents through the PACT workflow to address: $ARGUMENTS

## Before Starting

### Task Complexity Check

Before running full PACT orchestration, evaluate task complexity:

**Simple or borderline task (ask user):**
- Single file or component mentioned
- Bug fix in one domain
- Clear single-domain keywords (React, Express, PostgreSQL, Jest, etc.)
- Small feature with unclear scope
- Refactor that might be contained
- → Use `AskUserQuestion` tool:
  - Question: "This looks like it could be handled by a single specialist. Would you like to run comPACT instead?"
  - Options: "Yes, use comPACT" / "No, proceed with full orchestration"
- If comPACT → redirect to `/PACT:comPACT`
- If orchestrate → proceed with full PACT phases below

**Complex task (proceed with orchestrate):**
- Multiple domains mentioned
- "New feature" or greenfield language
- Architectural decisions required
- → Proceed with full PACT phases

---

1. **Create feature branch** if not already on one
2. **Check for plan** in `docs/plans/` matching this task

### Plan Status Handling

| Status | Action |
|--------|--------|
| PENDING APPROVAL | `/PACT:orchestrate` = implicit approval → update to IN_PROGRESS |
| APPROVED | Update to IN_PROGRESS |
| BLOCKED | Ask user to resolve or proceed without plan |
| IN_PROGRESS | Confirm: continue or restart? |
| SUPERSEDED/IMPLEMENTED | Confirm with user before proceeding |
| No plan found | Proceed—phases will do full discovery |

---

## Context Assessment

Before executing phases, assess which are needed based on existing context:

| Phase | Run if... | Skip if... |
|-------|-----------|------------|
| **PREPARE** | Requirements unclear, external APIs to research, dependencies unmapped | Approved plan exists with Preparation Phase section, OR requirements explicit in task, OR existing `docs/preparation/` covers scope |
| **ARCHITECT** | New component or module, interface contracts undefined, architectural decisions required | Approved plan exists with Architecture Phase section, OR following established patterns, OR `docs/architecture/` covers design |
| **CODE** | Always run | Never skip |
| **TEST** | Integration/E2E tests needed, complex component interactions, security/performance verification | Unit tests from coders sufficient, no integration boundaries crossed, isolated change |

**Conflict resolution**: When both "Run if" and "Skip if" criteria apply, **run the phase** (safer default). Example: A plan exists but requirements have changed—run PREPARE to validate.

**Plan-aware fast path**: When an approved plan exists in `docs/plans/`, PREPARE and ARCHITECT are typically skippable—the plan already synthesized specialist perspectives. Skip unless scope has changed or plan appears stale (typically >2 weeks; ask user to confirm if uncertain).

**State your assessment before proceeding.** For each skipped phase, state:
1. Which skip criterion was met
2. The context source (plan path, doc path, or pattern name)

Example:

> "Approved plan found at `docs/plans/user-auth-jwt-plan.md`. Skipping PREPARE (plan has Preparation Phase section). Skipping ARCHITECT (plan has Architecture Phase section). Running CODE. Running TEST (plan specifies integration tests needed)."

Or without a plan:

> "No plan found. Running PREPARE (external API needs research). Skipping ARCHITECT (following established repository pattern in `src/repositories/`). Running CODE. Skipping TEST (isolated change, unit tests sufficient)."

The user can override your assessment if they want more or less ceremony.

---

## Handling Decisions When Phases Were Skipped

When a phase is skipped but a coder encounters a decision that would have been handled by that phase:

| Decision Scope | Examples | Action |
|----------------|----------|--------|
| **Minor** | Naming conventions, local file structure, error message wording | Coder decides, documents in commit message |
| **Moderate** | Interface shape within your module, error handling pattern, internal component boundaries | Coder decides and implements, but flags decision with rationale in handoff; orchestrator validates before next phase |
| **Major** | New module needed, cross-module contract, architectural pattern affecting multiple components | Blocker → `/PACT:imPACT` → may need to run skipped phase |

**Boundary heuristic**: If a decision affects files outside the current specialist's scope, treat it as Major.

**Coder instruction when phases were skipped**:

> "PREPARE and/or ARCHITECT were skipped based on existing context. Minor decisions (naming, local structure) are yours to make. For moderate decisions (interface shape, error patterns), decide and implement but flag the decision with your rationale in the handoff so it can be validated. Major decisions affecting other components are blockers—don't implement, escalate."

This prevents excessive ping-pong for small decisions while catching real issues.

---

## Handoff Format

Each specialist should end with a structured handoff (2-4 sentences):

```
**Handoff**:
1. Produced: [files created/modified, key artifacts]
2. Key context for next phase: [decisions made, patterns established, constraints discovered]
3. Open questions (if any): [uncertainties for next phase to resolve or confirm]
4. Decisions made (if phases skipped): [moderate decisions with rationale—for orchestrator validation]
```

**Examples**:

> **Handoff**: 1. Produced: `docs/preparation/rate-limiting-research.md` covering token bucket vs sliding window algorithms. 2. Key context: Recommended Redis-based token bucket; existing `redis-client.ts` can be reused. 3. Open questions: Should rate limits be per-user or per-API-key?

> **Handoff**: 1. Produced: `src/middleware/rateLimiter.ts`, `src/config/rateLimits.ts`, unit tests passing. 2. Key context: Used token bucket with Redis; added `X-RateLimit-*` headers per RFC 6585. 3. Open questions: None—ready for integration testing. 4. Decisions made: Chose `X-RateLimit-Remaining` header format (moderate—affects API consumers); rationale: follows RFC 6585 standard.

---

### Phase 1: PREPARE → `pact-preparer`

**Skip criteria met?** → Proceed to Phase 2.

**Plan sections to pass** (if plan exists):
- "Preparation Phase"
- "Open Questions > Require Further Research"

**Invoke `pact-preparer` with**:
- Task description
- Plan sections above (if any)
- "Reference the approved plan at `docs/plans/{slug}-plan.md` for full context."

**Before next phase**:
- [ ] Outputs exist in `docs/preparation/`
- [ ] Specialist handoff received (see Handoff Format below)
- [ ] If blocker reported → `/PACT:imPACT`

---

### Post-PREPARE Re-assessment

If PREPARE ran and ARCHITECT was marked "Skip," compare PREPARE's recommended approach to the skip rationale:

- **Approach matches rationale** → Skip holds
- **Novel approach** (new components, interfaces, expanded scope) → Override, run ARCHITECT

**Example**:
> Skip rationale: "following established pattern in `src/utils/`"
> PREPARE recommends "add helper to existing utils" → Skip holds
> PREPARE recommends "new ValidationService class" → Override, run ARCHITECT

---

### Phase 2: ARCHITECT → `pact-architect`

**Skip criteria met (after re-assessment)?** → Proceed to Phase 3.

**Plan sections to pass** (if plan exists):
- "Architecture Phase"
- "Key Decisions"
- "Interface Contracts"

**Invoke `pact-architect` with**:
- Task description
- PREPARE phase outputs
- Plan sections above (if any)
- "Reference the approved plan at `docs/plans/{slug}-plan.md` for full context."

**Before next phase**:
- [ ] Outputs exist in `docs/architecture/`
- [ ] Specialist handoff received (see Handoff Format above)
- [ ] If blocker reported → `/PACT:imPACT`

---

### Phase 3: CODE → `pact-*-coder(s)`

**Always runs.** This is the core work.

**Plan sections to pass** (if plan exists):
- "Code Phase"
- "Implementation Sequence"
- "Commit Sequence"

**Select coder(s)** based on scope:
- `pact-backend-coder` — server-side logic, APIs
- `pact-frontend-coder` — UI, client-side
- `pact-database-engineer` — schema, queries, migrations

#### Parallel vs Sequential Invocation

**Parallel-safe** (invoke together):
- Backend API + Frontend UI for same feature (independent implementation)
- Multiple independent components in same domain
- Backend + Frontend when API contract is already defined

**Sequential required** (wait for handoff):
- Database schema → Backend (backend needs schema to build models/queries)
- Backend API → Frontend (frontend needs API contract to consume)
- Shared utility/service → consumers of that utility
- Any work where one coder's output is another's input

**When in doubt**: Sequential is safer. Parallel saves time but risks rework if assumptions diverge.

**Invoke coder(s) with**:
- Task description
- ARCHITECT phase outputs (or plan's Architecture Phase if ARCHITECT was skipped)
- Plan sections above (if any)
- "Reference the approved plan at `docs/plans/{slug}-plan.md` for full context."
- If PREPARE/ARCHITECT were skipped, include: "PREPARE and/or ARCHITECT were skipped based on existing context. Minor decisions (naming, local structure) are yours to make. For moderate decisions (interface shape, error patterns), decide and implement but flag the decision with your rationale in the handoff so it can be validated. Major decisions affecting other components are blockers—don't implement, escalate."
- "Testing: Run the full test suite before completing. If your changes break existing tests, fix them."

**Before next phase**:
- [ ] Implementation complete
- [ ] All tests passing (full test suite; fix any tests your changes break)
- [ ] Decision log(s) created at `docs/decision-logs/{feature}-{domain}.md`
- [ ] Specialist handoff(s) received (see Handoff Format above)
- [ ] If blocker reported → `/PACT:imPACT`

---

### Phase 4: TEST → `pact-test-engineer`

**Skip criteria met?** → Proceed to "After All Phases Complete."

**Plan sections to pass** (if plan exists):
- "Test Phase"
- "Test Scenarios"
- "Coverage Targets"

**Invoke `pact-test-engineer` with**:
- Task description
- Decision log(s) from CODE phase: "Read the implementation decision log(s) at `docs/decision-logs/{feature}-*.md` for context on what was built, key decisions, assumptions, and areas of uncertainty."
- Plan sections above (if any)
- "Reference the approved plan at `docs/plans/{slug}-plan.md` for full context."
- "You own ALL substantive testing: unit tests, integration, E2E, edge cases. The decision log provides context—you decide what and how to test."

**Before completing**:
- [ ] Outputs exist in `docs/testing/`
- [ ] All tests passing
- [ ] Test decision log created at `docs/decision-logs/{feature}-test.md`
- [ ] Specialist handoff received (see Handoff Format above)
- [ ] If blocker reported → `/PACT:imPACT`

---

## After All Phases Complete

1. **Update plan status** (if plan exists): IN_PROGRESS → IMPLEMENTED
2. **Run `/PACT:peer-review`** to commit, create PR, and get multi-agent review
