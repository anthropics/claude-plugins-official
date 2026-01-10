# PACT Protocols (Lean Reference)

> **Purpose**: Minimal protocols for PACT workflows. Agents reference this when needed, not memorized.
>
> **Design principle**: One-liners in prompts, details here.

---

## The PACT Workflow Family

| Workflow | When to Use | Key Idea |
|----------|-------------|----------|
| **PACT** | Complex/greenfield work | Context-aware multi-agent orchestration |
| **plan-mode** | Before complex work, need alignment | Multi-agent planning consultation, no implementation |
| **comPACT** | Focused, single-domain tasks | Single-specialist delegation with light ceremony |
| **imPACT** | When blocked or need to iterate | Triage: Redo prior phase? Additional agents needed? |

---

## plan-mode Protocol

**Purpose**: Multi-agent planning consultation before implementation. Get specialist perspectives synthesized into an actionable plan.

**When to use**:
- Complex features where upfront alignment prevents rework
- Tasks spanning multiple specialist domains
- When you want user approval before implementation begins
- Greenfield work with significant architectural decisions

**Four phases**:

| Phase | What Happens |
|-------|--------------|
| 0. Analyze | Orchestrator assesses scope, selects relevant specialists |
| 1. Consult | Specialists provide planning perspectives in parallel |
| 2. Synthesize | Orchestrator resolves conflicts, sequences work, assesses risk |
| 3. Present | Save plan to `docs/plans/`, present to user, await approval |

**Key rules**:
- **No implementation** — planning consultation only
- **No git branch** — that happens when `/PACT:orchestrate` runs
- Specialists operate in "planning-only mode" (analysis, not action)
- Conflicts surfaced and resolved (or flagged for user decision)

**Output**: `docs/plans/{feature-slug}-plan.md`

**After approval**: User runs `/PACT:orchestrate {task}`, which references the plan.

**When to recommend alternatives**:
- Trivial task → `/PACT:comPACT`
- Unclear requirements → Ask clarifying questions first
- Need research before planning → Run preparation phase alone first

---

## imPACT Protocol

**Trigger when**: Blocked; get similar errors repeatedly; or prior phase output is wrong.

**Two questions**:
1. **Redo prior phase?** — Is the issue upstream in P→A→C→T?
2. **Additional agents needed?** — Do I need subagents to assist?

**Three outcomes**:
| Outcome | When | Action |
|---------|------|--------|
| Redo solo | Prior phase broken, I can fix it | Loop back and fix yourself |
| Redo with help | Prior phase broken, need specialist | Loop back with subagent assistance |
| Proceed with help | Current phase correct, blocked on execution | Invoke subagents to help forward |

If neither question is "Yes," you're not blocked—continue.

---

## comPACT Protocol

**Core idea**: Single-specialist delegation with light ceremony.

comPACT invokes exactly ONE specialist based on the task domain. No doc artifacts, no multi-phase orchestration—just focused work.

**Available specialists**:
| Shorthand | Specialist | Use For |
|-----------|------------|---------|
| `backend` | pact-backend-coder | Server-side logic, APIs, middleware |
| `frontend` | pact-frontend-coder | UI, React, client-side |
| `database` | pact-database-engineer | Schema, queries, migrations |
| `prepare` | pact-preparer | Research, requirements |
| `test` | pact-test-engineer | Standalone test tasks |
| `architect` | pact-architect | Design guidance, pattern selection |

**Smart specialist selection**:
- *Clear task* → Auto-select (domain keywords, file types, single-domain action)
- *Ambiguous task* → Ask user which specialist

**Light ceremony instructions** (injected when invoking specialist):
- Work directly from task description
- Check docs/plans/, docs/preparation/, docs/architecture/ briefly if they exist—reference relevant context
- Do not create new documentation artifacts
- Smoke tests only: Verify it compiles, runs, and happy path doesn't crash (no comprehensive unit tests—that's TEST phase work)

**Escalate to `/PACT:orchestrate` when**:
- Task spans multiple specialist domains
- Specialist reports a blocker (run `/PACT:imPACT` first)

**If blocker reported**:
1. Receive blocker from specialist
2. Run `/PACT:imPACT` to triage
3. May escalate to `/PACT:orchestrate` if task exceeds single-specialist scope

---

## Phase Handoffs

**On completing any phase, state**:
1. What you produced (with file paths)
2. Key decisions made
3. What the next agent needs to know

Keep it brief. No templates required.

---

## Backend ↔ Database Boundary

**Sequence**: Database delivers schema → Backend implements ORM.

| Database Engineer Owns | Backend Engineer Owns |
|------------------------|----------------------|
| Schema design, DDL | ORM models |
| Migrations | Repository/DAL layer |
| Complex SQL queries | Application queries via ORM |
| Indexes | Connection pooling |

**Collaboration**: If Backend needs a complex query, ask Database. If Database needs to know access patterns, ask Backend.

---

## Test Engagement

| Test Type | Owner |
|-----------|-------|
| Smoke tests | Coders (minimal verification) |
| Unit tests | Test Engineer |
| Integration tests | Test Engineer |
| E2E tests | Test Engineer |

**Coders**: Your work isn't done until smoke tests pass. Smoke tests verify: "Does it compile? Does it run? Does the happy path not crash?" No comprehensive testing—that's TEST phase work.

**Test Engineer**: Engage after Code phase. You own ALL substantive testing: unit tests, integration, E2E, edge cases, adversarial testing. Target 80%+ meaningful coverage of critical paths.

### CODE → TEST Handoff

CODE phase produces decision log(s) at `docs/decision-logs/{feature}-{domain}.md`:
- `{feature}` = kebab-case feature name (match branch slug when available)
- `{domain}` = `backend`, `frontend`, or `database`
- Example: `user-authentication-backend.md`

**Decision log contents:**
```markdown
# Decision Log: {Feature Name}

## Summary
Brief description of what was implemented.

## Key Decisions
- Decision: rationale

## Assumptions
- Assumption made and why

## Known Limitations
- What wasn't handled and why

## Areas of Uncertainty
- Where bugs might hide, tricky parts

## Integration Context
- Depends on: [services, modules]
- Consumed by: [downstream code]

## Smoke Tests
- What was verified (compile, run, happy path)
```

**This is context, not prescription.** The test engineer decides what and how to test. The decision log helps inform that judgment.

**If decision log is missing**: For `/PACT:orchestrate`, request it from the orchestrator. For `/PACT:comPACT` (light ceremony), proceed with test design based on code analysis—decision logs are optional.

### TEST Decision Log

TEST phase produces its own decision log at `docs/decision-logs/{feature}-test.md`:

```markdown
# Test Decision Log: {Feature Name}

## Testing Approach
What strategy was chosen and why.

## Areas Prioritized
Referenced CODE logs: [list files read, e.g., `user-auth-backend.md`]
Focus areas based on their "areas of uncertainty".

## Edge Cases Identified
What boundary conditions and error scenarios were tested.

## Coverage Notes
What coverage was achieved, any significant gaps.

## What Was NOT Tested
Explicit scope boundaries and rationale (complexity, time, low risk).

## Known Issues
Flaky tests, environment dependencies, or unresolved concerns.
```

Focus on the **"why"** not the "what" — test code shows what was tested, the decision log explains the reasoning.

For `/PACT:comPACT` (light ceremony), this is optional.

---

## Cross-Cutting Concerns

Before completing any phase, consider:
- **Security**: Input validation, auth, data protection
- **Performance**: Query efficiency, caching
- **Accessibility**: WCAG, keyboard nav (frontend)
- **Observability**: Logging, error tracking

Not a checklist—just awareness.

---

## Architecture Review (Optional)

For complex features, before Code phase:
- Coders quickly validate architect's design is implementable
- Flag blockers early, not during implementation

Skip for simple features or when "just build it."

---

## Documentation Locations

> **Reference Skill**: For advanced filesystem-based context patterns (scratch pads, tool output offloading, sub-agent communication via files), invoke `filesystem-context` skill.

| Phase | Output Location |
|-------|-----------------|
| Plan | `docs/plans/` |
| Prepare | `docs/preparation/` |
| Architect | `docs/architecture/` |
| Code (decision logs) | `docs/decision-logs/{feature}-{domain}.md` |
| Test (decision log) | `docs/decision-logs/{feature}-test.md` |
| Test (artifacts) | `docs/testing/` |

**Plan vs. Architecture artifacts**:
- **Plans** (`docs/plans/`): Pre-approval roadmaps created by `/PACT:plan-mode`. Multi-specialist consultation synthesized into scope estimates, sequencing, and risk assessment. Created *before* implementation begins.
- **Architecture** (`docs/architecture/`): Formal specifications created by `pact-architect` *during* the Architect phase of `/PACT:orchestrate`. Detailed component designs, interface contracts, and technical decisions.

Plans inform implementation strategy; architecture documents define the technical blueprint.

---

## Session Continuity

If work spans sessions, update CLAUDE.md with:
- Current phase and task
- Blockers or open questions
- Next steps

---

## Related

- Agent definitions: `.claude/agents/`
- Commands: `.claude/commands/PACT/`
