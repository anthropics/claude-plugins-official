# Evolve Plugin

Evolve novel algorithms through LLM-driven mutation, crossover, and selection with **true genetic recombination**.

## Overview

The Evolve plugin brings evolutionary algorithm discovery to Claude Code. It maintains populations of solutions, performs semantic crossover between successful candidates, and adaptively continues while improvement is possible.

## Skills

| Skill | Description |
|-------|-------------|
| `/evolve` | Master skill that detects intent and delegates to subskills |
| `/evolve-perf` | Optimize for runtime performance (ops/sec, latency) |
| `/evolve-size` | Optimize for minimal size (bytes, characters) |
| `/evolve-ml` | Optimize for ML metrics (coming soon) |

## Quick Start

```bash
# Evolve a faster sorting algorithm
/evolve faster sorting algorithm to beat std::sort

# Evolve shortest code for a problem
/evolve shortest Python solution for this task

# Resume a previous evolution
/evolve --resume
```

## How It Works

1. **Bootstrap**: Discovers baselines and analyzes problem space
2. **Generation 1**: Explores diverse algorithm families in parallel
3. **Generation 2+**: Crossover between top performers + targeted mutations
4. **Adaptive stopping**: Continues while improving, stops on plateau
5. **Checkpointing**: Full state saved for resume capability

## Core Features

- **Population-based**: Maintains top 4 diverse solutions, not just the winner
- **Semantic crossover**: Combines innovations from multiple parents intelligently
- **Generalization testing**: VALID/HOLDOUT split prevents overfitting
- **Diversity maintenance**: Ensures algorithm family diversity in population
- **Statistical rigor**: Confidence intervals for timing benchmarks
- **Reproducibility**: Full determinism with logged seeds and versions

## Example Output

```
Evolution Complete!

Problem: bin packing heuristic
Generations: 12
Stop reason: plateau

Champion: 0.5720% excess waste
  vs baseline:    -16.2% improvement
  vs funsearch:   -8.4% improvement

Key Innovations:
  - Harmonic mean scoring (Gen 2)
  - Geometric balance term (Gen 5)
  - Adaptive coefficient scaling (Gen 8)
```

## Budget Options

| Budget | Meaning | Approx. Generations |
|--------|---------|---------------------|
| `10k` | 10,000 tokens | ~2-3 generations |
| `50k` | 50,000 tokens | ~10-12 generations |
| `100k` | 100,000 tokens | ~20-25 generations |
| `unlimited` | No limit | Until plateau |

## Requirements

- **Rust toolchain** (for performance mode): `rustup` with `cargo`
- **Python 3.10+** (for size mode and evaluation)

## Plugin Structure

```
evolve/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── evolve/
│   │   └── SKILL.md        # Master skill
│   ├── evolve-perf/
│   │   └── SKILL.md        # Performance optimization
│   ├── evolve-size/
│   │   └── SKILL.md        # Size optimization
│   └── evolve-ml/
│       └── SKILL.md        # ML optimization (stub)
└── README.md
```

## Evolution Artifacts Directory

All evolution artifacts are saved in `.evolve/<problem>/`:

```
.evolve/<problem>/
├── evolution.json       # Full state (for resume)
├── champion.json        # Best solution manifest
├── generations.jsonl    # Per-generation log
├── mutations/           # All tested mutations
└── rust/                # Benchmark code (perf mode)
```

## Showcases

The plugin has been used to evolve algorithms that beat state-of-the-art:

- **Bin packing**: Beat FunSearch by 8.4% on Weibull distribution
- **Code golf**: Achieved competitive results on ARC-AGI tasks
- **Sorting**: Evolved hybrid algorithms faster than std::sort

## License

MIT
