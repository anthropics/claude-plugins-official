# Mode Workflow Diagrams

Visual representations of how each mode orchestrates building blocks.

## Quality Assessment (Eval Mode)

Measures how well a skill performs on its evals.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Executor   │────▶│   Grader    │────▶│  Aggregate  │
│  (N runs)   │     │  (N runs)   │     │   Results   │
└─────────────┘     └─────────────┘     └─────────────┘
      │                   │                    │
      ▼                   ▼                    ▼
 transcript.md       grading.json         summary.json
 user_notes.md       claims[]
 metrics.json        user_notes_summary
```

Use for: Testing skill performance, validating skill value.

## Skill Improvement (Improve Mode)

Iteratively improves a skill through blind comparison.

```
┌─────────────────────────────────────────────────────────────────┐
│                        ITERATION LOOP                           │
│                                                                 │
│  ┌─────────┐   ┌─────────┐   ┌────────────┐   ┌──────────┐      │
│  │Executor │──▶│ Grader  │──▶│ Comparator │──▶│ Analyzer │      │
│  │(3 runs) │   │(3 runs) │   │  (blind)   │   │(post-hoc)│      │
│  └─────────┘   └─────────┘   └────────────┘   └──────────┘      │
│       │             │              │                │           │
│       │             │              │                ▼           │
│       │             │              │         suggestions        │
│       │             │              ▼                │           │
│       │             │         winner A/B            │           │
│       │             ▼                               │           │
│       │        pass_rate                            │           │
│       ▼                                             ▼           │
│  transcript                              ┌──────────────────┐   │
│  user_notes                              │ Apply to v(N+1)  │   │
│                                          └────────┬─────────┘   │
│                                                   │             │
└───────────────────────────────────────────────────┼─────────────┘
                                                    │
                                              (repeat until
                                               goal or timeout)
```

Use for: Optimizing skill performance, iterating on skill instructions.

## A/B Testing (with vs without skill)

Compares skill-enabled vs no-skill performance.

```
┌─────────────────┐
│ Executor        │──┐
│ (with skill)    │  │     ┌────────────┐     ┌─────────┐
└─────────────────┘  ├────▶│ Comparator │────▶│ Report  │
┌─────────────────┐  │     │  (blind)   │     │ winner  │
│ Executor        │──┘     └────────────┘     └─────────┘
│ (without skill) │              │
└─────────────────┘              ▼
                            rubric scores
                            expectation results
```

Use for: Proving skill adds value, measuring skill impact.

## Skill Creation (Create Mode)

Interactive skill development with user feedback.

```
┌───────────────────────────────────────────────────────────────┐
│                    USER FEEDBACK LOOP                         │
│                                                               │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌──────────┐ │
│  │ Interview │──▶│  Research │──▶│   Draft   │──▶│   Run    │ │
│  │   User    │   │ via MCPs  │   │  SKILL.md │   │ Example  │ │
│  └───────────┘   └───────────┘   └───────────┘   └──────────┘ │
│       ▲                                               │       │
│       │                                               ▼       │
│       │                                          user sees    │
│       │                                          transcript   │
│       │                                               │       │
│       └───────────────────────────────────────────────┘       │
│                         refine                                │
└───────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    (once criteria defined,
                     transition to Improve)
```

Use for: Creating new skills with tight user feedback.

## Skill Benchmark (Benchmark Mode)

Standardized performance measurement with variance analysis.

```
┌──────────────────────────────────────────────────────────────────────┐
│                         FOR EACH EVAL                                │
│                                                                      │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────┐│
│  │        WITH SKILL (3x)          │  │      WITHOUT SKILL (3x)     ││
│  │  ┌─────────┐ ┌─────────┐        │  │  ┌─────────┐ ┌─────────┐    ││
│  │  │Executor │ │ Grader  │ ───┐   │  │  │Executor │ │ Grader  │───┐││
│  │  │ run 1   │→│ run 1   │    │   │  │  │ run 1   │→│ run 1   │   │││
│  │  └─────────┘ └─────────┘    │   │  │  └─────────┘ └─────────┘   │││
│  │  ┌─────────┐ ┌─────────┐    │   │  │  ┌─────────┐ ┌─────────┐   │││
│  │  │Executor │ │ Grader  │ ───┼───│──│──│Executor │ │ Grader  │───┼││
│  │  │ run 2   │→│ run 2   │    │   │  │  │ run 2   │→│ run 2   │   │││
│  │  └─────────┘ └─────────┘    │   │  │  └─────────┘ └─────────┘   │││
│  │  ┌─────────┐ ┌─────────┐    │   │  │  ┌─────────┐ ┌─────────┐   │││
│  │  │Executor │ │ Grader  │ ───┘   │  │  │Executor │ │ Grader  │───┘││
│  │  │ run 3   │→│ run 3   │        │  │  │ run 3   │→│ run 3   │    ││
│  │  └─────────┘ └─────────┘        │  │  └─────────┘ └─────────┘    ││
│  └─────────────────────────────────┘  └─────────────────────────────┘│
│                              │                    │                  │
│                              └────────┬───────────┘                  │
│                                       ▼                              │
│                              ┌─────────────────┐                     │
│                              │    Analyzer     │                     │
│                              │  (most capable) │                     │
│                              └────────┬────────┘                     │
│                                       │                              │
└───────────────────────────────────────┼──────────────────────────────┘
                                        ▼
                              ┌─────────────────┐
                              │  benchmark.json │
                              │  benchmark.md   │
                              └─────────────────┘
```

Captures per-run: pass_rate, time_seconds, tokens, tool_calls, notes
Aggregates: mean, stddev, min, max for each metric across configurations
Analyzer surfaces: patterns, anomalies, and freeform observations

Use for: Understanding skill performance, comparing across models, tracking regressions.

---

## Inline Workflows (Without Subagents)

When subagents aren't available, the same building blocks execute sequentially in the main loop.

### Eval Mode (Inline)

```
┌───────────────────────────────────────────────────────┐
│                  MAIN LOOP                            │
│                                                       │
│  Read executor.md → Execute eval → Save outputs       │
│         │                                             │
│         ▼                                             │
│  Read grader.md → Grade expectations → Save grading   │
│         │                                             │
│         ▼                                             │
│  Display results                                      │
└───────────────────────────────────────────────────────┘
```

### Improve Mode (Inline)

```
┌───────────────────────────────────────────────────────┐
│                  ITERATION LOOP                       │
│                                                       │
│  Read executor.md → Execute (1 run) → Save outputs    │
│         │                                             │
│         ▼                                             │
│  Read grader.md → Grade expectations → Save grading   │
│         │                                             │
│         ▼                                             │
│  Compare with previous best (inline, not blind)       │
│         │                                             │
│         ▼                                             │
│  Analyze differences → Apply improvements to v(N+1)   │
│         │                                             │
│         (repeat until goal or timeout)                │
└───────────────────────────────────────────────────────┘
```

Benchmark mode requires subagents and has no inline equivalent.
