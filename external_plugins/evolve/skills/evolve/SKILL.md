---
name: evolve
description: Evolve novel algorithms through LLM-driven mutation, crossover, and selection
version: 1.0.0
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task, TodoWrite, WebSearch, WebFetch, AskUserQuestion, Skill
argument-hint: <problem description>
---

# /evolve - Evolutionary Algorithm Discovery

Evolve novel algorithms through LLM-driven mutation and selection with **true genetic recombination**. Runs adaptively—continuing while improvement is possible, stopping when plateaued.

This is the **master skill** that analyzes the request and delegates to specialized subskills.

---

## Available Modes

| Mode | Subskill | Optimizes | Use When |
|------|----------|-----------|----------|
| **perf** | `/evolve-perf` | Runtime speed (ops/sec, latency) | Faster algorithms, benchmarks |
| **size** | `/evolve-size` | Length (bytes, chars) | Code golf, minimal configs |
| **ml** | `/evolve-ml` | Model accuracy (F1, loss) | ML optimization (coming soon) |

---

## Usage

```bash
/evolve <problem description>
/evolve <problem description> --mode=<perf|size|ml>
/evolve --resume
```

---

## Mode Detection Instructions

You are the master `/evolve` skill. Your job is to understand the user's intent and delegate to the appropriate subskill.

### Step 1: Check for Explicit Override

If the request contains `--mode=perf`, `--mode=size`, or `--mode=ml`, use that mode directly. No further analysis needed.

### Step 2: Check for Resume

If the request is `--resume` or contains `--resume`:
1. Search for the most recent `.evolve/*/evolution.json` file
2. Read it to determine the mode from the `"mode"` field
3. Delegate to that subskill with `--resume`

### Step 3: Analyze the Request

Read the user's request carefully and determine what they want to optimize:

**Choose SIZE mode when the goal is to minimize length:**
- Making code shorter, smaller, more concise
- Code golf challenges
- Minimizing byte count or character count
- ARC-AGI tasks (these are code golf competitions)
- Reducing file size, config size, prompt length
- "Shortest", "smallest", "fewest bytes", "most concise"

**Choose PERF mode when the goal is to maximize speed:**
- Making code faster, quicker, more efficient
- Improving throughput, reducing latency
- Beating benchmarks, optimizing algorithms
- Runtime performance, ops/sec, iterations/sec
- "Faster", "optimize", "speed up", "high performance"

**Choose ML mode when the goal is to improve model metrics:**
- Improving accuracy, F1 score, precision, recall
- Reducing loss, error rate
- Model training, hyperparameter tuning
- Neural network architecture optimization
- Kaggle competitions, classification tasks

### Step 4: Consider Context (Optional)

If you're unsure, you may check the codebase for context clues:
- Files in `code-golf/` or `tasks/*.json` suggest SIZE mode
- Files like `benchmark.rs` or perf harnesses suggest PERF mode
- Files like `.h5`, `.pt`, `.pkl`, `model.py` suggest ML mode

### Step 5: Handle Ambiguity

If after analysis you genuinely cannot determine the mode, use AskUserQuestion:

```
Question: "What are we optimizing for?"
Options:
- "Fastest runtime (speed)" → perf
- "Smallest code (bytes)" → size
- "Best accuracy (ML)" → ml
```

### Step 6: Delegate

Once you've determined the mode:

1. Announce: `**Evolution mode: {mode}**` with brief reasoning
2. Invoke the subskill using the Skill tool:
   - `perf` → invoke `evolve-perf`
   - `size` → invoke `evolve-size`
   - `ml` → invoke `evolve-ml`
3. Pass the original request (minus --mode= if present) as args

---

## Examples with Reasoning

### Example 1: Clear SIZE intent
```
Request: "shortest Python solution for ARC task 0520fde7"
Reasoning: "shortest" + "ARC task" = clearly minimizing code length
Mode: size
Action: Skill(evolve-size, "shortest Python solution for ARC task 0520fde7")
```

### Example 2: Clear PERF intent
```
Request: "faster sorting algorithm to beat std::sort"
Reasoning: "faster" + "beat benchmark" = clearly optimizing speed
Mode: perf
Action: Skill(evolve-perf, "faster sorting algorithm to beat std::sort")
```

### Example 3: Clear ML intent
```
Request: "improve accuracy on this classification task"
Reasoning: "accuracy" + "classification" = clearly optimizing model metrics
Mode: ml
Action: Skill(evolve-ml, "improve accuracy on this classification task")
```

### Example 4: Explicit override
```
Request: "--mode=size optimize this function"
Reasoning: Explicit --mode=size overrides any inference
Mode: size
Action: Skill(evolve-size, "optimize this function")
```

### Example 5: Needs clarification
```
Request: "optimize this algorithm"
Reasoning: "optimize" is ambiguous - could mean speed OR size
Action: AskUserQuestion to clarify
```

### Example 6: Resume
```
Request: "--resume"
Action: Find .evolve/*/evolution.json, read mode, delegate with --resume
```

---

## Core Features (All Modes)

1. **Population-based**: Maintains diverse solutions, not just the winner
2. **Semantic crossover**: Combines innovations from multiple parents
3. **Adaptive generations**: Continues while improving, stops on plateau
4. **Budget control**: User sets token/generation limits
5. **Checkpointing**: Resume evolution from where you left off
6. **Correctness first**: Invalid solutions get fitness 0

---

## Budget Options

| Budget | Meaning | Approx. Generations |
|--------|---------|---------------------|
| `10k` | 10,000 tokens | ~2-3 generations |
| `50k` | 50,000 tokens | ~10-12 generations |
| `100k` | 100,000 tokens | ~20-25 generations |
| `5gen` | 5 generations | Fixed count |
| `unlimited` | No limit | Until plateau |
| (none) | Default 50k | ~10-12 generations |

---

## Resume Previous Evolution

Run `/evolve --resume` to continue a previous evolution:

1. Finds the most recent `evolution.json`
2. Loads population and champion state
3. Continues from last generation
4. Preserves all history and lineage

---

## Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│  /evolve <request>                                          │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Mode Detection (LLM-based)                           │  │
│  │  • Check for explicit --mode= override                │  │
│  │  • Analyze request intent                             │  │
│  │  • Consider codebase context if needed                │  │
│  │  • Ask user if genuinely ambiguous                    │  │
│  └──────────────────┬────────────────────────────────────┘  │
│                     │                                       │
│         ┌───────────┼───────────┬───────────┐               │
│         ▼           ▼           ▼           ▼               │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│   │ size     │ │ perf     │ │ ml       │ │ resume   │      │
│   │ subskill │ │ subskill │ │ subskill │ │ (detect) │      │
│   └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│                                                             │
│  Each subskill runs the full evolution loop:                │
│  • Bootstrap → Baseline → Evolution → Finalize              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Subskill Responsibilities

### /evolve-perf (Performance)
- Optimizes runtime speed (ops/sec, latency, throughput)
- Supports any language (Rust, Python, Go, etc.)
- Uses statistical significance testing for timing benchmarks
- Focuses on algorithm families, SIMD, cache optimization
- See: `/evolve-perf` for full documentation

### /evolve-size (Size)
- Optimizes length (bytes, characters, tokens)
- Supports code (Python, Rust, Go) and text (markdown, prompts, configs)
- Uses trick library for systematic transformations
- Focuses on compression, golf tricks, minimal implementations
- See: `/evolve-size` for full documentation

### /evolve-ml (ML - Coming Soon)
- Will optimize model accuracy, loss, F1, etc.
- Will support hyperparameter tuning, architecture search
- See: `/evolve-ml` for planned features

---

## Directory Structure

All evolution modes use a consistent directory structure:

```
.evolve/<problem>/
├── evolution.json       # Full state (mode, population, history)
├── champion.json        # Best solution manifest
├── generations.jsonl    # Per-generation log (append-only)
├── mutations/           # All tested mutations
└── [mode-specific]/     # Mode-specific artifacts
    ├── rust/            # (perf) Rust benchmark code
    ├── solutions/       # (size) Working solutions by size
    └── models/          # (ml) Trained models
```

---

## Quick Reference

| Want to... | Command |
|------------|---------|
| Make code faster | `/evolve faster <algorithm>` |
| Make code shorter | `/evolve shortest <code>` |
| Minimize config file | `/evolve minimal <file type>` |
| Continue previous | `/evolve --resume` |
| Force specific mode | `/evolve --mode=<mode> <problem>` |
