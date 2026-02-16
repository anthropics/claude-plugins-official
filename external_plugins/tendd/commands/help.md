---
description: "Explain the TenDD development pipeline"
---

# TenDD — Tenacity-Driven Development

Please explain the following to the user:

## What is TenDD?

TenDD (Tenacity-Driven Development) is a structured development pipeline where no stage advances until a separate reviewer explicitly approves. Like TDD but the T stands for Tenacity — quality is the exit condition, never fatigue.

## Available Commands

### /tendd:plan <description or path>

Tenacious planning cycle: bootstrap principles → create plan → DDD review → requirements extraction → cross-review.

**Usage:**
```
/tendd:plan "kanban-style issue tracking plugin"
/tendd:plan plans/2026-02-16_kanban-issue-tracker.md
```

**What it does:**
1. Bootstraps `PRINCIPLES.md` if missing (DDD + project-specific)
2. Creates (or reads) a high-level plan document
3. DDD/Architecture review loop — iterates until zero blockers
4. Extracts numbered requirements (MUST/SHOULD/MAY)
5. Cross-review loop — iterates until zero blockers
6. Commits approved plan + requirements

**Input is free-form.** Pass a feature description, a plan path, or anything in between.

**Team:** architect + reviewer + requirements expert (persistent, context-preserving).

---

### /tendd:dev <description or plan path>

Tenacious build cycle: architect → reviewer → builder with iterative review loops.

**Usage:**
```
/tendd:dev "kanban issue tracker"
/tendd:dev plans/2026-02-16_kanban-issue-tracker.md
```

**What it does:**
1. Bootstraps `PRINCIPLES.md` if missing
2. Interface design loop (architect + reviewer)
3. Implementation loop (builder + reviewer + tests + lint)
4. Conciseness rewrite loop (fresh builder + reviewer — relies on test coverage as safety net)
5. Verification (tests + lint hard gate)
6. Commits implementation

**Input is free-form.** Pass a description or a plan path. If you describe a feature, it searches `plans/` for matching plan and requirements files.

**Team:** architect + reviewer + builder (persistent, context-preserving). A fresh builder is spawned for the rewrite stage to get an outsider's perspective on conciseness — this only works because the test suite acts as the behavioral contract.

---

## Core Principles

1. **Never self-approve.** Architects don't review their own designs. Builders don't review their own code. Always spawn a separate reviewer.
2. **Never skip a review loop.** If the reviewer has findings, fix and re-review.
3. **Unbounded iterations.** The loop continues until quality is achieved — not until you're tired.
4. **Never weaken tests.** Fix the code, not the assertions.
5. **Surface blockers.** If stuck after 3+ iterations on the same issue, ask the user rather than papering over it.
6. **Persistent agents.** Team members stay alive across iterations to preserve context and avoid redundant token use.

## Agents

TenDD ships with 5 generic agent definitions:

| Agent | Role | Persists through |
|-------|------|-----------------|
| **architect** | Interfaces, protocols, type stubs. Bootstraps PRINCIPLES.md if missing. | Stages 0-1 |
| **reviewer** | BLOCKER/CONCERN/SUGGESTION findings. Never writes code. | All review stages |
| **builder** | Implementation + tests. | Stage 2 |
| **rewriter** | Fresh builder for conciseness. Tests are the safety net. | Stages 3-4 |
| **requirements** | Extracts testable requirements from plans. | Stages 3-4 (plan only) |

### Custom Agents

For best results, **create project-specific agents** at `.claude/agents/`:

```
.claude/agents/
├── architect.md      # Your domain's interface design conventions
├── reviewer.md       # Your project's review criteria, principles by number
├── builder.md        # Your test framework, lint tools, coding standards
└── requirements.md   # Your domain's requirement conventions
```

Project agents take priority over the plugin defaults. Customize them for:
- **Domain-specific review criteria** (e.g., DDD bounded contexts, compliance rules)
- **Tech stack** (e.g., Go uses `go test`, Rust uses `cargo test`, not `pytest`)
- **Project principles** (reference by number for precise reviewer feedback)
- **Niche specialties** (e.g., security auditor, performance reviewer, accessibility checker)

You can also add entirely new agent roles beyond the four defaults.

## The Name

TenDD = Tenacity-Driven Development. TDD where the T stands for tenacity — the relentless focus that doesn't let go until it's right.
