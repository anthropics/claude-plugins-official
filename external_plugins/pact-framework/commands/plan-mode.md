---
description: Multi-agent planning consultation (no implementation)
argument-hint: [e.g., add user authentication with JWT]
---
Create a comprehensive implementation plan for: $ARGUMENTS

**This is PLANNING ONLY** — no code changes, no git branches, no implementation.

## Your Workflow

### Phase 0: Orchestrator Analysis

Using extended thinking, analyze the task:
- What is the full scope of this task?
- Which PACT phases are involved?
- Which specialists should be consulted?
- What are the key planning questions for each specialist?
- What's the estimated complexity (Low/Medium/High/Very High)?

Determine which specialists to invoke based on the task:
- **📚 pact-preparer**: Always include for research/context needs
- **🏛️ pact-architect**: Include for any structural or design decisions
- **💻 pact-backend-coder**: Include if server-side work is involved
- **🎨 pact-frontend-coder**: Include if client-side work is involved
- **🗄️ pact-database-engineer**: Include if data layer work is involved
- **🧪 pact-test-engineer**: Always include for testing strategy

Skip specialists clearly not relevant (e.g., skip database engineer for pure UI work).

**Derive the feature slug** for the plan filename:
- Convert task to lowercase kebab-case
- Keep it concise (3-5 words max)
- Examples:
  - "Add user authentication with JWT" → `user-auth-jwt`
  - "Refactor payment processing module" → `refactor-payment-processing`
  - "Fix dashboard loading performance" → `fix-dashboard-performance`

### Phase 1: Parallel Specialist Consultation

Invoke relevant specialists **in parallel**, each in **planning-only mode**.

**Use this prompt template for each specialist:**

```
PLANNING CONSULTATION ONLY — No implementation, no code changes.

Task: {task description}

As the {role} specialist, provide your planning perspective:

1. SCOPE IN YOUR DOMAIN
   - What work is needed in your area of expertise?
   - What's the estimated effort (Low/Medium/High)?

2. DEPENDENCIES & INTERFACES
   - What dependencies exist with other domains?
   - What interfaces or contracts need definition?
   - What do you need from other specialists?

3. KEY DECISIONS & TRADE-OFFS
   - What are the important decisions in your domain?
   - What are the options and trade-offs?
   - What's your recommendation?

4. RISKS & CONCERNS
   - What could go wrong?
   - What unknowns need investigation?
   - What assumptions are you making?

5. RECOMMENDED APPROACH
   - What's your suggested approach?
   - What sequence of steps do you recommend?
   - What should be done first?

Output your analysis with clear headers matching the 5 sections above.
Do NOT implement anything — planning consultation only.
```

**Domain-specific additions to the template:**

For **📚 pact-preparer**, also ask:
- What documentation/research is needed before implementation?
- What external APIs or libraries need investigation?
- What stakeholder clarifications are needed?

For **🏛️ pact-architect**, also ask:
- What components/modules are affected or needed?
- What design patterns should be applied?
- What interface contracts need definition?

For **coders** (backend/frontend/database), also ask:
- What files need modification or creation?
- What existing patterns in the codebase should be followed?
- What's the implementation sequence?

For **🧪 pact-test-engineer**, also ask:
- What test scenarios are critical (happy path, errors, edge cases)?
- What coverage targets make sense?
- What test data or fixtures are needed?

**Handling incomplete or missing responses**:

If a specialist provides minimal, incomplete, or off-topic output:
1. Note the gap — record which specialist and which sections are missing
2. Proceed with synthesis — use the inputs you have
3. Flag in the plan — add to "Limitations" section with specific gaps identified
4. Do NOT re-invoke — avoid infinite loops; missing input is data for the plan

If a specialist fails entirely (timeout, error):
1. Log the failure in synthesis notes
2. Proceed without that perspective
3. Flag prominently in "Open Questions" that this domain was not consulted
4. Recommend the user consider re-running plan-mode or consulting that specialist manually

### Phase 2: Orchestrator Synthesis

After collecting all specialist outputs, use extended thinking to synthesize:

1. **Identify Agreements**
   - Where do specialists align?
   - What's the consensus approach?

2. **Identify and Classify Conflicts**

   Where do specialists disagree? Classify each conflict:

   | Severity | Definition | Action |
   |----------|------------|--------|
   | **Minor** | Different approaches, either works | Orchestrator chooses, documents rationale |
   | **Major** | Fundamental disagreement affecting design | Flag for user decision with options |
   | **Blocking** | Cannot proceed without resolution | Escalate immediately (see below) |

   **Blocking conflict escalation**:
   If a conflict prevents meaningful synthesis (e.g., two specialists propose mutually exclusive architectures):
   1. Stop synthesis
   2. Present partial plan with explicit "BLOCKED" status
   3. Clearly describe the conflict and why it blocks progress
   4. Ask user to resolve before continuing
   5. User may re-run plan-mode after providing direction

3. **Determine Sequencing**
   - What's the optimal order of phases?
   - What can be parallelized?
   - What are the dependencies?

4. **Assess Cross-Cutting Concerns**
   - Security implications?
   - Performance implications?
   - Accessibility implications? (if frontend)
   - Observability/logging needs?

5. **Build Unified Roadmap**
   - Create step-by-step implementation plan
   - Map steps to specialists
   - Identify the commit sequence

6. **Risk Assessment**
   - Aggregate risks from all specialists
   - Assess overall project risk
   - Identify mitigation strategies

7. **Synthesis Validation Checkpoint**

   Before proceeding to Phase 3, verify:
   - [ ] At least 2 specialists contributed meaningful input
   - [ ] No blocking conflicts remain unresolved
   - [ ] All mandatory plan sections can be populated
   - [ ] Cross-cutting concerns have been considered

   If validation fails:
   - For insufficient specialist input → Flag in "Limitations", proceed with available data
   - For unresolved blocking conflict → Present partial plan with BLOCKED status
   - For missing mandatory sections → Populate with "TBD - requires {specific input}"

### Phase 3: Plan Output

Save the synthesized plan to `docs/plans/{feature-slug}-plan.md`.

**Handling existing plans**:

If a plan already exists for this feature slug:
1. Check the existing plan's status and use `AskUserQuestion` tool when user input is needed:
   - **PENDING APPROVAL**: Ask user with options: "Overwrite existing plan" / "Rename new plan" / "Cancel"
   - **APPROVED**: Ask user with options: "Overwrite (plan not yet started)" / "Cancel"
   - **IN_PROGRESS**: Warn that implementation is underway, ask with options: "Overwrite anyway" / "Cancel"
   - **IMPLEMENTED**: Previous version completed; create new version with date suffix (no question needed)
   - **SUPERSEDED**: Safe to overwrite (no question needed)
2. If creating a new version:
   - First attempt: `{feature-slug}-plan-{YYYY-MM-DD}.md`
   - If that exists: `{feature-slug}-plan-{YYYY-MM-DD}-v2.md` (increment as needed)
3. Update the old plan's status to SUPERSEDED if overwriting

**Use this structure:**

```markdown
# Implementation Plan: {Feature Name}

> Generated by `/PACT:plan-mode` on {YYYY-MM-DD}
> Status: PENDING APPROVAL

<!-- Status Lifecycle:
     PENDING APPROVAL → APPROVED → IN_PROGRESS → IMPLEMENTED
                    ↘ SUPERSEDED (if replaced by newer plan)
                    ↘ BLOCKED (if unresolved conflicts)

     Transition Ownership:
     - PENDING APPROVAL → APPROVED: User (explicit approval)
     - APPROVED → IN_PROGRESS: Orchestrator (when /PACT:orchestrate starts)
     - IN_PROGRESS → IMPLEMENTED: Orchestrator (after successful completion)
     - Any → SUPERSEDED: plan-mode (when creating replacement plan)
     - Any → BLOCKED: plan-mode (when unresolved blocking conflicts)
-->

## Summary

{2-3 sentence overview of what will be implemented and the high-level approach}

<!-- If there are limitations or gaps, add this callout: -->
> **Limitations**: This plan has gaps due to incomplete specialist input. See [Limitations](#limitations) section before approving.

---

## Specialist Perspectives

### 📋 Preparation Phase
**Effort**: {Low/Medium/High}

#### Research Needed
- [ ] {Research item}

#### Dependencies to Map
- {Dependency}

#### Questions to Resolve
- [ ] {Question}

---

### 🏗️ Architecture Phase
**Effort**: {Low/Medium/High}

#### Components Affected
| Component | Change Type | Impact |
|-----------|-------------|--------|
| {Name} | New/Modify | {Description} |

#### Design Approach
{Description of architectural approach}

#### Key Decisions
| Decision | Options | Recommendation | Rationale |
|----------|---------|----------------|-----------|
| {Decision} | {A, B, C} | {B} | {Why} |

#### Interface Contracts
{Interface definitions or descriptions}

---

### 💻 Code Phase
**Effort**: {Low/Medium/High}

#### Files to Modify
| File | Changes |
|------|---------|
| {path} | {description} |

#### Files to Create
| File | Purpose |
|------|---------|
| {path} | {description} |

#### Implementation Sequence
1. {Step}
2. {Step}

---

### 🧪 Test Phase
**Effort**: {Low/Medium/High}

#### Test Scenarios
| Scenario | Type | Priority |
|----------|------|----------|
| {Scenario} | Unit/Integration/E2E | P0/P1/P2 |

#### Coverage Targets
- Critical path: {X}%
- Overall target: {Y}%

#### Test Data Needs
- {Requirement}

---

## Synthesized Implementation Roadmap

### Phase Sequence
{Visual or textual representation of the workflow}

### Commit Sequence (Proposed)
1. `{type}: {description}` — {what this commit does}
2. `{type}: {description}` — {what this commit does}

---

## Cross-Cutting Concerns

| Concern | Status | Notes |
|---------|--------|-------|
| Security | {Ready/Needs attention/N/A} | {Notes} |
| Performance | {Ready/Needs attention/N/A} | {Notes} |
| Accessibility | {Ready/Needs attention/N/A} | {Notes} |
| Observability | {Ready/Needs attention/N/A} | {Notes} |

---

## Open Questions

### Require User Decision
- [ ] **{Question}**: {Context and options for user to decide}

### Require Further Research
- [ ] **{Question}**: {What needs investigation during Prepare phase}

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| {Risk} | Low/Med/High | Low/Med/High | {Strategy} |

---

## Limitations

<!-- Include this section if any specialists provided incomplete input or failed -->

| Gap | Impact | Recommendation |
|-----|--------|----------------|
| {Missing perspective or incomplete section} | {How this affects the plan} | {Suggested action} |

---

## Scope Assessment

- **Overall Complexity**: {Low/Medium/High/Very High}
- **Estimated Files**: {N} modified, {M} new
- **Specialists Required**: {List}
- **External Dependencies**: {Yes/No — details}

---

## Next Steps

To implement this plan after approval:
```
/PACT:orchestrate {task description}
```

The orchestrator should reference this plan during execution.
```

### Phase 4: Present and Resolve

After saving the plan:

1. Present a concise summary to the user
2. Note the **overall complexity and scope**

**Resolve open questions before exiting plan mode:**

3. If there are items under **"Open Questions > Require User Decision"**:
   - Use `AskUserQuestion` to resolve each decision point
   - Update the plan file with the user's decisions (move resolved items to the appropriate sections, e.g., "Key Decisions")
   - Repeat until no "Require User Decision" items remain

4. Once all decision-requiring questions are resolved:
   - Highlight any remaining **"Require Further Research"** items (these are addressed during the Prepare phase of implementation)
   - Explain that after approval, they can run `/PACT:orchestrate` to implement

**Do NOT exit plan mode** while "Require User Decision" items remain unresolved.

**Do NOT proceed to implementation** — await user approval or feedback.

---

## When to Recommend Alternative Commands

If during Phase 0 analysis you determine:

- **Task is trivial** (typo, config change, single-line fix) → Recommend `/PACT:comPACT` instead
- **Task is unclear** → Ask clarifying questions before proceeding with planning
- **Task requires immediate research first** → Recommend running preparation phase alone first

---

## Integration with /PACT:orchestrate

After the user approves the plan:

1. User runs `/PACT:orchestrate {same task}`
2. Orchestrator should check for existing plan in `docs/plans/`
3. If plan exists, use it as the implementation specification
4. Specialists receive relevant sections of the plan as context
