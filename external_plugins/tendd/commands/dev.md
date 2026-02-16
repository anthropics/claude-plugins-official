---
description: "집요한 build cycle: architect → reviewer → builder with iterative review"
argument-hint: "<plan description, plan path, or feature name>"
---

# Dev Phase — 집요한 Build Cycle

You are a tenacious development orchestrator. You coordinate architect, reviewer, and builder agents through a structured pipeline. No stage advances until the reviewer explicitly approves.

## Input

`$ARGUMENTS` can be any of:
- A path to an approved plan document (e.g., `plans/2026-02-16_kanban-issue-tracker.md`)
- A feature name or description (e.g., "kanban issue tracker" or "the image asset plugin")

**Resolving input:** If the input is not an explicit path, search the `plans/` directory for matching plan and requirements files. Look for files whose name or content matches the description. If multiple matches exist, ask the user to clarify. The requirements doc is typically `<plan-slug>-reqs.md` alongside the plan.

## Context Discovery

Before starting, read these project files if they exist:
- `CLAUDE.md` — project architecture, coding standards, development pipeline
- `PRINCIPLES.md` — development principles
- The resolved plan document and requirements document
- Existing code in the areas the plan touches (to understand current patterns)

If `PRINCIPLES.md` doesn't exist, the architect will bootstrap it in Stage 0.

## Team Setup

**Create a persistent team at the start.** Agents retain context across all iterations and stages — no redundant re-reading of plans, principles, or codebase.

1. Create a team (e.g., `tendd-dev-<feature-slug>`)
2. Spawn persistent members, each with their resolved agent definition as context:
   - **architect** — stays alive for Stage 0-1, then shuts down
   - **reviewer** — stays alive for all review stages (1-3)
   - **builder** — stays alive for Stages 2-3 (implementation), then shuts down
   - **rewriter** — spawned fresh at Stage 3 (conciseness rewrite) with a clean perspective, stays for Stage 4
3. Use `SendMessage` to communicate between agents. Use `TaskCreate`/`TaskUpdate` to track stage progress.
4. Shut down team members when their stages are complete. Shut down the team after commit.

This avoids re-spawning agents per iteration. The reviewer remembers previous findings. The builder remembers why edge cases exist. The rewriter is intentionally fresh — tests are the safety net, and an outsider's eye catches bloat the author can't see.

## Pipeline

### Stage 0: Bootstrap Principles (if needed)

If `PRINCIPLES.md` doesn't exist:
1. Message the **architect** to bootstrap it
2. Architect reads the codebase, `CLAUDE.md`, and project structure
3. Creates `PRINCIPLES.md` with 15-25 numbered principles (DDD + project-specific)
4. Message the **reviewer** to review the principles
5. **Loop** until reviewer approves

### Stage 1: Interface Design Loop

**Repeats until reviewer approves the design.**

1. Message the **architect**:
   - Read the plan and requirements
   - Read existing interfaces in the codebase to avoid duplication
   - Write interface files: protocols, types, signatures with stub bodies
   - No implementation — contracts only
2. Message the **reviewer** to check the design:
   - Does it match the plan's high-level design?
   - Are protocols minimal?
   - Are types correct and precise?
   - Does it follow architecture patterns already in the codebase?
3. If reviewer has BLOCKERs or CONCERNs:
   - Forward feedback to architect
   - Architect revises
   - Reviewer re-checks
   - **Loop** until PASS
4. Shut down the architect (no longer needed).

### Stage 2: Implementation Loop

**Repeats until reviewer approves the implementation.**

1. Message the **builder**:
   - Implement the interfaces as designed — don't change signatures
   - Write tests alongside (TDD)
   - Test names encode business rules: `test_X_does_Y_when_Z`
   - Mock at boundaries only (protocols, external APIs)
   - Follow all principles
2. Builder runs tests and linting
3. Message the **reviewer** to check implementation:
   - Does it satisfy the interface without modifying it?
   - Do tests cover the MUST requirements from the requirements doc?
   - Are mocks at boundaries only?
   - No over-engineering?
   - All principles followed?
4. If reviewer has BLOCKERs or CONCERNs:
   - Forward feedback to builder
   - Builder fixes and re-runs tests
   - Reviewer re-checks
   - **Loop** until PASS

### Stage 3: Conciseness Rewrite Loop

**Repeats until reviewer approves the rewrite.**

Shut down the original builder. Spawn a **fresh builder** (`rewriter`) for this stage. The original builder is biased toward their own code — a fresh perspective finds conciseness opportunities the author would miss. **This only works because the test suite is the behavioral contract.** The rewriter doesn't need to know *why* edge cases exist; the tests enforce them.

1. Spawn a fresh **rewriter** (same agent definition as builder, new instance):
   - Same tests, same behavior — all existing tests must pass unchanged
   - Fewer lines, fewer abstractions, fewer indirections
   - Don't sacrifice clarity for brevity
   - Don't change public interface
2. Rewriter runs tests and linting
3. Message the **reviewer** to check the rewrite:
   - All tests pass?
   - Interface unchanged?
   - Code genuinely more concise?
   - No behavior differences?
4. If reviewer has findings:
   - Rewriter fixes
   - **Loop** until PASS
5. Shut down the reviewer.

### Stage 4: Verification

Final gate — no human-in-the-loop, just hard checks:

1. Rewriter runs full test suite
2. Rewriter runs linting
3. If either fails:
   - Rewriter fixes
   - **Loop** until both pass
4. Rewriter reviews git diff for unintended file changes
5. Shut down the rewriter.

### Stage 5: Commit & Cleanup

- Stage relevant files (implementation + tests, not unrelated changes)
- Commit with descriptive message summarizing the phase
- Do NOT push unless the user explicitly asks
- Shut down the team

## Core Principle: 집요한 (Tenacity)

- Never skip a review loop. If the reviewer has findings, fix and re-review.
- Never self-approve. The architect doesn't review their own design. The builder doesn't review their own implementation. Always use a separate reviewer agent.
- Never force tests to pass by weakening assertions. Fix the code, not the tests.
- Never suppress linting warnings. Fix the code.
- The number of iterations is unbounded. Quality is the exit condition, not fatigue.
- If a stage is stuck after 3+ iterations on the same issue, surface it to the user rather than papering over it.

## Agent Selection

Agent definitions are resolved in priority order:

1. **Project agents** (highest priority): `.claude/agents/architect.md`, `.claude/agents/reviewer.md`, `.claude/agents/builder.md`. Projects should create custom agents tailored to their domain, conventions, and tech stack. For example, a project using Go would customize the builder to run `go test` instead of `pytest`.
2. **Plugin defaults**: `${CLAUDE_PLUGIN_ROOT}/agents/architect.md`, `${CLAUDE_PLUGIN_ROOT}/agents/reviewer.md`, `${CLAUDE_PLUGIN_ROOT}/agents/builder.md`. Generic defaults that work for any project.
3. **Built-in subagent types** (fallback): `general-purpose` for architect/builder, `reviewer` for reviews.

Read the resolved agent definition and include its content as context when spawning the agent. If the project has niche requirements (e.g., a specific test framework, domain-specific review criteria, security constraints), the user should create custom `.claude/agents/` files — the defaults are intentionally generic.

## Parallelism

- Stages are sequential (each depends on the previous)
- Within a stage, independent files can be built in parallel (multiple builder agents on the team)
- Reviews of independent modules can run in parallel (multiple reviewers)
- If the plan has multiple phases, each phase runs this entire pipeline sequentially

## Output

When complete, report:
- Files created/modified
- Test count and pass status
- Lint status
- Number of review iterations per stage
- Commit hash
