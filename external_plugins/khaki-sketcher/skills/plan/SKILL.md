---
name: plan
description: Cross-validated planning with Codex analysis + Gemini design review. Use for complex features before implementation.
---

# Plan

Cross-validated planning: Codex analyzes → Gemini reviews → Codex re-reviews → Consolidated plan.

## Usage

```
/ksk:plan <feature description, task, or goal>
```

## Phase 1: Codex Deep Analysis

Gather project context (files, dependencies, architecture), then call Codex:

```bash
codex exec "Create a comprehensive implementation plan with maximum depth.

## Task
<task description>

## Project Context
<key files, module boundaries, dependency graph, current architecture>

## Analyze
1. Architecture Impact
   - Which modules/components are affected?
   - Dependency chain: what depends on what?
   - Coupling/cohesion impact of proposed changes

2. Implementation Strategy
   - Phased plan (least dependent first)
   - Each phase independently testable
   - Migration strategy if restructuring

3. Risk Assessment
   - What could break?
   - Edge cases and failure modes
   - Rollback strategy per phase

4. Effort Estimation
   - Complexity per phase (low/medium/high)
   - Files to create vs modify
   - Test surface per phase

## Output Format (IMPORTANT)
1. Summary (key decisions + phase count) — this is ALL Sonnet reads
2. Detailed Plan → save to .ksk/artifact/plan-codex-<ts>.md
3. Risk Matrix (likelihood x impact)
4. Open Questions (what needs user input?)" --full-auto 2>/dev/null
```

Save result to `.ksk/artifact/plan-codex-<ts>.md`. Sonnet reads ONLY the summary.

### Fallback (Codex unavailable)

```bash
gemini -p "Create a comprehensive implementation plan.

## Task
<task description>

## Context
<same context>

## Output Format (IMPORTANT)
1. Summary (key decisions + phase count)
2. Detailed Plan → save to .ksk/artifact/plan-<ts>.md" -y --output-format text 2>/dev/null
```

## Phase 2: Gemini Design & UX Analysis

If the task involves any UI, user interaction, or visual changes:

```bash
gemini -p "Analyze this planned feature from UX and design perspective.

## Task
<task description>

## Project Context
<UI components, user flows, current design system>

## Analyze
1. User Flow
   - Entry point → actions → goal → exit
   - How does this change existing flows?
   - Information hierarchy: what draws attention?

2. Design Decisions
   - Component patterns needed
   - Responsive behavior
   - Interaction states (loading, error, empty, success)

3. Accessibility
   - WCAG 2.1 AA compliance
   - Keyboard navigation
   - Screen reader considerations

4. Polish
   - Animation/transition needs
   - Edge case UI states
   - Mobile considerations

## Output Format (IMPORTANT)
1. Summary (key UX decisions) — this is ALL Sonnet reads
2. Detailed Analysis → save to .ksk/artifact/plan-gemini-<ts>.md
3. Design tokens if applicable (colors, spacing, typography)
4. UX Risks (confusing patterns, cognitive load)" -y --output-format text 2>/dev/null
```

Save result to `.ksk/artifact/plan-gemini-<ts>.md`. Sonnet reads ONLY the summary.

Skip this phase if task is purely backend/logic with no UI impact.

## Phase 3: Cross-Validation

Each model reviews the other's plan:

### Codex reviews Gemini's plan:

```bash
codex exec "Review this UX/design plan for technical feasibility.

## UX Plan
<paste Gemini's summary>

## Review
1. Technical feasibility: can this be implemented with current stack?
2. Performance impact: will proposed UX patterns cause performance issues?
3. Implementation complexity: are proposed interactions realistic?
4. Conflicts: does UX plan conflict with architectural plan?

## Output Format (IMPORTANT)
1. Summary (conflicts found + suggestions) — this is ALL Sonnet reads
2. Details → save to .ksk/artifact/plan-crossval-codex-<ts>.md" --full-auto 2>/dev/null
```

### Gemini reviews Codex's plan:

```bash
gemini -p "Review this implementation plan for UX impact.

## Implementation Plan
<paste Codex's summary>

## Review
1. UX blind spots: does the technical plan miss user-facing concerns?
2. Accessibility gaps: are there accessibility issues in the proposed approach?
3. User experience: will phased implementation create temporary UX degradation?
4. Suggestions: how to improve the plan from user perspective?

## Output Format (IMPORTANT)
1. Summary (blind spots + suggestions) — this is ALL Sonnet reads
2. Details → save to .ksk/artifact/plan-crossval-gemini-<ts>.md" -y --output-format text 2>/dev/null
```

## Phase 4: Consolidation — Sonnet

Based on all analyses, create the final consolidated plan:

```markdown
# Implementation Plan: <task>

## Summary
<1-2 sentence overview>

## Architecture (from Codex)
<key decisions, affected modules>

## UX/Design (from Gemini)
<key UX decisions, if applicable>

## Cross-Validation Notes
<Codex concerns about Gemini's plan>
<Gemini concerns about Codex's plan>
<How conflicts were resolved>

## Implementation Phases
### Phase 1: <name>
- Files: <list>
- Changes: <description>
- Test: <how to verify>
- Risk: <low/medium/high>

### Phase N: ...

## Open Questions
<items needing user decision>

## Artifacts
- Codex analysis: .ksk/artifact/plan-codex-<ts>.md
- Gemini analysis: .ksk/artifact/plan-gemini-<ts>.md (if UI)
- Cross-validation: .ksk/artifact/plan-crossval-*.md
```

Save to `.ksk/artifact/plan-<ts>.md` and present to user for review.

## Error Handling
- CLI returns empty or error → try fallback CLI
- Both CLIs unavailable → Sonnet creates plan directly, note lack of external analysis
- Rate limited → proceed with available model only
- Cross-validation fails → proceed with single model's plan, note limitation

## After Plan Approval

User approves → proceed with implementation:
- Use `/ksk:run` or appropriate skill
- Sonnet reads plan artifact as implementation guide
- Each phase completed → verify against plan

Task: {{ARGUMENTS}}
