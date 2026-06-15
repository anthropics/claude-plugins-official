---
name: project-analyzer
description: Deep 8-dimension analysis framework for open-source projects and software architectures. Use this skill whenever you need to analyze, understand, or document any software project — whether reviewing a new repo, preparing for a technical interview, writing architecture docs, or evaluating a system design. Trigger on: "analyze this project", "understand this architecture", "deep dive into this repo", "review the system design", "how does X work architecturally", or any request involving project comprehension beyond surface-level code reading. The 8 dimensions transform shallow code tours into living architectural analysis with Why, Fallback, Closed Loop, Competitive Landscape, and Quantification — the gap between describing what exists vs explaining why it matters.
---

# Project Analyzer — 8-Dimension Deep Analysis Framework

Most project analysis is a static specimen — precise but lifeless. It lists components, traces calls, enumerates configs. But great analysis is alive: it has **Why** (design intent), **Fallback** (what happens when things break), **Closed Loop** (how the system evolves), **Competitive Landscape** (where it stands in the market), **Quantification** (precise numbers from code), and a **time arrow** (how it changes over time).

This skill gives you a repeatable framework to produce that living analysis.

## The 8 Dimensions

| Dimension | Core Question | What It Produces |
|-----------|--------------|-----------------|
| Progressive Disclosure | Can readers get what they need at their level? | L0/L1/L2 layered docs |
| Architecture Decision Records | Why was it designed this way? | ADR table with alternatives |
| Scenario Walkthrough | Can the architecture actually run? | 3-scenario numerical trace |
| Degradation & Fallback | What happens when it breaks? | Fallback chain table |
| Competitive Landscape | Where does this stand vs alternatives? | Comparison table |
| Quantification | Are there real numbers? | Threshold/priority tables from code |
| Closed Loop | Does the system evolve over time? | Feedback loop diagram |
| Longitudinal Narrative | What happens long-term? | Day 1/30/90 evolution table |

### Dimension 1: Progressive Disclosure

Don't dump everything into one document. Structure analysis in three reading levels:

| Level | Content | Time | Audience |
|-------|---------|------|----------|
| L0 | One-sentence definition + core architecture diagram | 5 min | Decision-makers, newcomers |
| L1 | Component relationships, core mechanisms, config parameters | 30 min | Architects |
| L2 | Terminology, delegation mechanisms, code-path mapping | 2h+ | Developers |

**Why this matters**: Readers have different depth needs. A CTO needs L0 in 5 minutes; a new team member needs L1; the implementer needs L2. Mixing all levels forces everyone to read everything.

### Dimension 2: Architecture Decision Records (ADR)

For every key design choice, answer three questions:

1. **What was chosen?** — the current design
2. **What was rejected?** — at least one alternative
3. **Why this over that?** — the trade-off reasoning

Format as a table:

```
| Decision | Choice | Rejected Alternative | Why |
|-----------|--------|---------------------|-----|
| Composition vs Inheritance | Composition (delegate) | Inherit and override | Delegate preserves single responsibility; inheritance forces child to carry parent's entire contract |
```

**Why this matters**: Code only shows what was designed, not why. Without ADR, readers guess intent — and usually guess wrong. ADR turns description into explanation.

### Dimension 3: Scenario Walkthrough

After drawing any architecture diagram, trace 2-3 concrete scenarios with real numbers:

| Scenario | Input | Expected Path |
|----------|-------|--------------|
| A — Normal | Small input (e.g., 3000 tokens, 5 iterations) | Straight-through, no special processing |
| B — Stress | Large input (e.g., 150K tokens, 50 iterations) | Triggers processing chain at thresholds |
| C — Failure | Extreme input (e.g., 280K tokens, 200 iterations) | Exhausts all normal paths, activates fallbacks |

Write the trace as a decision tree showing what each threshold check produces.

**Why this matters**: A diagram that can't be walked through with real values is just decoration. Scenario traces prove the architecture works — or reveal where it breaks.

### Dimension 4: Degradation & Fallback

For every mechanism, trace the full fallback chain — not just "it retries", but what happens when retry also fails:

```
| Mechanism | Normal Path | Fallback | Ultimate Backstop |
|-----------|------------|----------|-----------------|
| Context Compression | L0→L1 compression | L1→L2 merge | Aggressive keep-recent → Hard truncation |
| API Call | Direct call | Retry 3x | Cached stale response → Graceful error message |
```

**Why this matters**: Code only shows happy paths. Error handling is scattered across catch blocks. Consolidating fallback chains reveals gaps — mechanisms without a backstop are risk points.

### Dimension 5: Competitive Landscape

Every project analysis should include a positioning section:

```
| Dimension | This Project | Competitor A | Competitor B |
|-----------|-------------|-------------|-------------|
| Core Paradigm | ... | ... | ... |
| Flexibility | ... | ... | ... |
| Determinism | ... | ... | ... |
```

Three dimensions suffice. Be fair — list competitor advantages too.

**Why this matters**: Understanding a system in isolation is like understanding a word without knowing the language. Positioning reveals what makes this system different and why that difference matters.

### Dimension 6: Quantification

Replace every vague descriptor with a number extracted from code:

| Vague | Precise |
|----------|-----------|
| "multi-level compression" | "5-level compression: thresholds at 60K, 100K, 160K, 230K" |
| "higher priority rails execute first" | "SkillUseRail(100) -> SubagentRail(95) -> Interrupt(90) -> Default(50)" |
| "compression triggers on overflow" | "Token > 60000 triggers MessageSummaryOffloader" |

If you can't find the number in code, mark it **(needs confirmation)** — never fabricate.

**Why this matters**: "Big" and "small" are opinions; numbers are facts. Quantification turns impressions into evidence and lets readers reproduce your reasoning.

### Dimension 7: Closed Loop

After mapping component relationships, identify feedback loops — paths where output feeds back as input, causing the system to evolve:

```
Execution -> Observation -> Pattern Detection -> Distillation -> Registration
     ^                                                         |
     +---------- Next execution uses distilled patterns --------+
```

A closed loop means the system gets better with use. Without loops, it's static — same quality forever.

**Why this matters**: Static architectures are dead snapshots. Real systems have feedback arrows that make them adaptive. If you can't find any loops, the system can't self-improve — that's a design limitation worth noting.

### Dimension 8: Longitudinal Narrative

Describe how the system changes over time using a Day 1/30/90 frame:

| Time | System State | What Mechanism Drives It |
|------|-------------|--------------------------|
| Day 1 | Cold start — every action needs full reasoning | No accumulated patterns |
| Day 30 | Repeated patterns detected and cached | Feedback loops begin producing reusable knowledge |
| Day 90 | Stable routines distilled, only novel cases need reasoning | Self-optimization loops mature |

**Why this matters**: A single time-slice tells you what the system is today. Longitudinal narrative tells you what it becomes — and whether its design supports that trajectory.

## Agent-Assisted Analysis Workflow

Agent tools amplify human judgment — they handle extraction in minutes, but the interpretive dimensions (Why, Fallback, Positioning, Closed Loop) require human reasoning.

### Phase 1: Agent Extraction (automated)

```
1. CodeGraph/Grep: map project structure, inheritance chains, call graphs
2. Scan all Config/settings classes -> extract thresholds, defaults, priorities
3. Scan all except/catch/retry/fallback blocks -> find degradation logic
4. Scan all TODO/FIXME/HACK -> mark unresolved risk points
```

### Phase 2: Human Judgment (you decide)

```
1. Looking at inheritance chains -> ask "why this layering?"
2. Looking at threshold tables -> ask "what do these numbers mean in practice?"
3. Looking at fallback chains -> ask "do these cover all failure modes?"
4. Where Agent found NO fallback -> mark as risk point
```

### Phase 3: Agent + Human (hybrid)

```
1. Agent searches competitor architecture docs -> provides comparison material
2. You make the positioning judgment
3. Agent generates scenario walkthroughs from thresholds
4. You verify the walkthroughs are realistic
```

### Phase 4: Pure Human (insight layer)

```
1. Draw closed-loop diagrams with feedback arrows
2. Write ADR paragraphs explaining design intent
3. Sketch Day 1/30/90 longitudinal narrative
```

## Analysis Template

When analyzing a project, produce output in this structure:

```markdown
# {Project Name} Architecture Deep Analysis

## L0 Overview (5 minutes)
- One-sentence definition
- Core architecture diagram
- Key numbers (components, config thresholds, scale indicators)

## L1 Architecture Detail (30 minutes)
- Component relationships + inheritance chains
- Data flow + scenario walkthrough (3 scenarios with real values)
- Configuration parameters + thresholds extracted from code

## L2 Implementation Detail (deep dive)
- Code path mapping (class -> file -> function)
- Key interface/protocol definitions

## Architecture Decision Records
| Decision | Choice | Rejected Alternative | Why |

## Degradation & Fallback
| Mechanism | Normal Path | Fallback Chain | Ultimate Backstop |

## Competitive Landscape
| Dimension | This Project | Competitor A | Competitor B |

## Closed Loops
Diagram showing feedback arrows. Label each loop: what observes, what learns, what improves.

## Longitudinal Evolution
| Time | System State | Driving Mechanism |
| Day 1 | Cold start | - |
| Day 30 | Pattern accumulation | Which loops activate |
| Day 90 | Mature optimization | Self-improvement effects |

## Risk Points
- Components without fallback chains
- TODO/FIXME/HACK locations
- Single points of failure
```

## Quality Checklist

Before finalizing any analysis, verify:

1. **Numbers come from code** — every threshold traceable to source file; if not found, mark "(needs confirmation)"
2. **ADR has alternatives** — each decision lists at least one rejected option with reasoning
3. **Scenario walkthroughs use concrete values** — not "large data triggers compression" but "150K tokens triggers DialogueCompressor"
4. **Fallback chains reach a backstop** — every mechanism traces to an ultimate safety net, not just "retry" (what if retry fails?)
5. **Competitive comparison is fair** — list competitor strengths, not just your project's advantages
6. **Closed loops have feedback arrows** — without arrows it's a pipeline, not a loop
7. **Longitudinal narrative is grounded** — Day 1/30/90 predictions reference actual feedback mechanisms in the system

## What NOT to Do

| Anti-pattern | Why It Fails | Fix |
|-------------|-------------|-----|
| Single monolithic document | All readers forced to read everything | Progressive Disclosure: L0/L1/L2 |
| Describing design without explaining intent | Readers guess why, usually wrong | ADR: every choice has alternatives and reasoning |
| Architecture diagram with no trace | Looks pretty but unverified | Scenario Walkthrough: trace real values through the diagram |
| Only happy-path documentation | Real systems break; readers need to know what happens | Fallback chains traced to backstop |
| No competitor context | System understood in isolation | 3-dimension comparison table |
| Vague descriptors ("large", "many", "high") | Opinions, not facts | Quantify: extract numbers from code |
| Static component map without feedback | Snapshot, not a living system | Add feedback arrows -> closed loop diagram |
| Single time-slice description | Tells what it is, not what it becomes | Day 1/30/90 longitudinal narrative |

## 8-Dimension Quick Reference

| Dimension | Core Question | Output | Extraction Method |
|-----------|--------------|--------|------------------|
| Progressive Disclosure | Can readers self-select depth? | L0/L1/L2 docs | Manual structuring |
| ADR | Why this design? | Decision table | Inheritance + Config + TODO analysis |
| Scenario Walkthrough | Does it actually run? | 3-scenario numerical trace | Config thresholds + flow diagrams |
| Degradation & Fallback | What happens when it breaks? | Fallback chain table | except/retry/fallback scanning |
| Competitive Landscape | Where does it stand? | Comparison table | Web search + industry knowledge |
| Quantification | Are there real numbers? | Threshold/priority tables | Config class extraction from code |
| Closed Loop | Does it evolve? | Feedback loop diagram | evolution/feedback/score pattern search |
| Longitudinal Narrative | What happens long-term? | Day 1/30/90 table | Loop mechanism projection |
