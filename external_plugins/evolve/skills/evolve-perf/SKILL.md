---
name: evolve-perf
description: Performance subskill for /evolve - optimizes runtime speed for algorithms
version: 1.0.0
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task, TodoWrite, WebSearch, WebFetch, AskUserQuestion
argument-hint: <problem description>
---

# /evolve-perf - Performance Evolution Subskill

This is the **performance optimization subskill** for the `/evolve` command. It evolves algorithms for **runtime speed** (ops/sec, latency, throughput).

**Note**: This subskill is invoked by the master `/evolve` skill when performance mode is detected. You can also invoke it directly with `/evolve-perf`.

---

## Evaluation Contract (Hard Requirements)

These requirements are non-negotiable and must be enforced by the evolution loop:

1. **Three-way split**: Every candidate MUST be evaluated on TRAIN + VALID + HOLDOUT/TEST datasets.
   - TRAIN: Used for fitness scoring and selection
   - VALID: Used for promotion gate (no regression allowed)
   - HOLDOUT/TEST: Never used for selection; reported only for final analysis

2. **Selection vs Promotion**:
   - Selection is based on TRAIN performance only
   - Promotion to champion requires: (a) no regression on VALID mean, (b) meets acceptance criteria below

3. **Determinism Requirements**:
   - Fixed random seeds OR explicit seed lists for all stochastic operations
   - Fixed build mode (always `--release`, no debug builds during eval)
   - Log and record: Rust toolchain version, git commit hash, platform info
   - Command to reproduce any evaluation must be logged

4. **Data Integrity**:
   - TRAIN/VALID/HOLDOUT must be generated once at bootstrap and never modified
   - Store checksums of test data in evolution.json
   - If data changes, evolution must restart from scratch

5. **Generalization Testing** (required for promotion to champion):
   - Champions MUST be validated on multiple input distributions
   - Minimum 3 distributions required; 5 recommended
   - Champion must improve on majority (≥3/5) of distributions
   - Report per-distribution performance in final results

---

## Generalization Requirements

To prevent overfitting to a single distribution, evolved algorithms must generalize:

### Required Distributions

For each problem domain, generate test data from multiple distributions:

| Problem Type | Required Distributions |
|-------------|------------------------|
| Bin Packing | Weibull, Uniform, Normal, Bimodal, Power-law |
| Sorting | Random, Nearly-sorted, Reversed, Few-unique, Pipe-organ |
| String Search | English text, Random bytes, Repetitive, DNA sequences, Log files |
| Numeric | Uniform, Gaussian, Exponential, Heavy-tail, Clustered |

### Distribution Configuration

Store in `evolution.json`:

```json
"generalization": {
  "distributions": [
    {"name": "weibull", "params": {"k": 5, "lambda": 50}, "weight": 1.0},
    {"name": "uniform", "params": {"min": 1, "max": 100}, "weight": 1.0},
    {"name": "normal", "params": {"mean": 50, "std": 15}, "weight": 1.0},
    {"name": "bimodal", "params": {"peaks": [25, 75], "std": 10}, "weight": 1.0},
    {"name": "power_law", "params": {"alpha": 2.0}, "weight": 1.0}
  ],
  "promotion_threshold": 0.6,
  "report_per_distribution": true
}
```

### Promotion Gate

A candidate can only become champion if:

```python
def passes_generalization_gate(candidate, baseline, distributions):
    wins = 0
    for dist in distributions:
        if candidate.eval(dist) < baseline.eval(dist):
            wins += 1

    # Must win on majority of distributions
    return wins >= len(distributions) * 0.6
```

### Reporting Format

Each generation log includes per-distribution breakdown:

```json
{
  "id": "gen4_hybrid_balanced",
  "generalization": {
    "weibull": {"excess": 0.5735, "vs_baseline": "-16.2%", "status": "WIN"},
    "uniform": {"excess": 0.4821, "vs_baseline": "-12.1%", "status": "WIN"},
    "normal": {"excess": 0.5102, "vs_baseline": "-14.8%", "status": "WIN"},
    "bimodal": {"excess": 0.6234, "vs_baseline": "-8.3%", "status": "WIN"},
    "power_law": {"excess": 0.7102, "vs_baseline": "+2.1%", "status": "LOSS"},
    "summary": "4/5 distributions improved (80%)"
  }
}
```

### Overfitting Detection

Flag candidates that show signs of overfitting:

- **Large train/valid gap**: If TRAIN improves >5% but VALID regresses, flag as potential overfit
- **Distribution divergence**: If performance varies >50% across distributions, flag as specialized
- **Constant sensitivity**: If small constant changes cause large fitness swings, flag as fragile

---

## Acceptance Criteria (To Keep a Candidate)

A candidate is accepted into the population only if ALL of the following hold:

1. **TRAIN improvement**: Candidate improves mean TRAIN objective by at least ε (epsilon).
   - Default ε = 0.001 (0.1% relative improvement)
   - Configurable via `--epsilon <value>` or in evolution.json

2. **VALID non-regression**: Candidate must not regress on VALID mean.
   - Regression threshold: VALID_new >= VALID_old * 0.995 (allow 0.5% noise margin)

3. **Instance consistency** (at least ONE must hold):
   - Improves on at least K out of N instances (paired comparison), where K = ceil(N * 0.6)
   - OR improves median across all instances

4. **Noise handling**:
   - If TRAIN improvement is within 2× noise floor, rerun evaluation R times (default R=3)
   - Use median of R runs for final decision
   - Noise floor estimated from baseline variance

5. **Correctness**: Must pass all correctness tests (implicit, always required)

6. **Statistical confidence** (for timing-sensitive benchmarks):
   - Run each evaluation N times (default N=5 for timing, N=1 for deterministic)
   - Report mean ± standard deviation
   - Require improvement > 2σ for acceptance (95% confidence)

---

## Statistical Rigor Requirements

For benchmarks where variance matters (timing, throughput), apply statistical tests:

### Multiple Runs

```python
def evaluate_with_confidence(candidate, n_runs=5):
    results = [run_benchmark(candidate) for _ in range(n_runs)]

    return {
        "mean": statistics.mean(results),
        "std": statistics.stdev(results),
        "median": statistics.median(results),
        "min": min(results),
        "max": max(results),
        "runs": results
    }
```

### Confidence Interval Reporting

Report all metrics with confidence intervals:

```
Candidate: gen4_hybrid_balanced

Performance (5 runs):
  Excess: 0.5735% ± 0.012% (95% CI: 0.561% - 0.586%)
  Bins:   9996.2 ± 1.3

Baseline: funsearch
  Excess: 0.6842% ± 0.015% (95% CI: 0.669% - 0.699%)
  Bins:   10007.4 ± 1.8

Improvement: 16.2% ± 2.1% (statistically significant, p < 0.01)
```

### Statistical Significance Test

```python
from scipy import stats

def is_significant_improvement(candidate_runs, baseline_runs, alpha=0.05):
    """Two-sample t-test for improvement significance"""
    t_stat, p_value = stats.ttest_ind(candidate_runs, baseline_runs)

    # One-sided test: candidate < baseline (lower is better)
    p_one_sided = p_value / 2 if t_stat < 0 else 1 - p_value / 2

    return {
        "significant": p_one_sided < alpha,
        "p_value": p_one_sided,
        "confidence": 1 - alpha,
        "effect_size": (mean(baseline_runs) - mean(candidate_runs)) / pooled_std
    }
```

### When to Skip Statistical Tests

For deterministic benchmarks (exact bin counts, not timing):
- Single run is sufficient
- No confidence intervals needed
- Direct comparison is valid

```python
def needs_statistical_testing(benchmark_type):
    deterministic = ["bin_packing", "sorting_correctness", "exact_count"]
    stochastic = ["throughput", "latency", "timing", "ops_per_second"]

    return benchmark_type in stochastic
```

```json
// evolution.json acceptance config
"acceptance": {
  "epsilon": 0.001,
  "valid_regression_tolerance": 0.005,
  "instance_threshold_ratio": 0.6,
  "noise_rerun_count": 3,
  "noise_multiplier": 2.0
}
```

---

## Explanation Format (Falsifiable)

Each generation MUST output structured explanations that enable learning from failures:

### Required Fields Per Candidate

```markdown
### Candidate: gen3_simd_radix

**Hypothesis** (1-2 sentences):
SIMD-parallel bucket counting will reduce memory stalls during radix distribution phase.

**Prediction** (specific, measurable):
- Expect 10-20% improvement on large arrays (n > 10000)
- Expect minimal change on small arrays (n < 1000)
- Expect largest gains on uniformly distributed inputs

**Evidence** (per-instance before/after):
| Instance    | Baseline Bins | Candidate Bins | Baseline L1 | Candidate L1 | Baseline Excess | Candidate Excess | Delta |
|-------------|---------------|----------------|-------------|--------------|-----------------|------------------|-------|
| train_0     | 2012          | 2008           | 1998        | 1998         | 0.70%           | 0.50%            | -0.20 |
| train_1     | 1983          | 1985           | 1975        | 1975         | 0.40%           | 0.51%            | +0.11 |
| ...         | ...           | ...            | ...         | ...          | ...             | ...              | ...   |
| **TRAIN μ** | 1998.2        | 1996.1         | 1987.8      | 1987.8       | 0.52%           | 0.42%            | -0.10 |
| **VALID μ** | 2001.4        | 2000.8         | 1990.2      | 1990.2       | 0.56%           | 0.53%            | -0.03 |

**Decision**: KEEP
- Prediction confirmed: TRAIN improved by 0.10% (> ε=0.001)
- VALID non-regression: 0.53% vs 0.56% (improved)
- Instance check: 4/5 TRAIN instances improved

**Next Mutation Plan** (one concrete change):
Try 8-bit vs 11-bit radix to find optimal bucket count for cache efficiency.
```

### On Failure

```markdown
**Decision**: DROP
- Prediction falsified: Expected 10-20% gain, observed 2% regression
- Hypothesis update: SIMD overhead dominates for this data size distribution
- Learning: Skip SIMD variants unless median instance size > 50000
```

---

## Diversity & Exploration

The evolution loop MUST maintain population diversity using at least ONE of these mechanisms:

### Option 1: Islands (Multiple Populations)

```python
islands = {
  "exploitation": {"focus": "refine_champion", "mutation_rate": 0.1},
  "exploration": {"focus": "radical_changes", "mutation_rate": 0.5},
  "hybrid": {"focus": "crossover_only", "mutation_rate": 0.0}
}
# Migration: Every 3 generations, copy best from each island to others
```

### Option 2: Novelty Metric

Maintain a "probe set" of diverse inputs. Score candidates on behavioral novelty:
```python
def novelty_score(candidate, archive):
    behavior = [candidate.eval(probe) for probe in probe_set]
    distances = [euclidean(behavior, arch.behavior) for arch in archive]
    return mean(sorted(distances)[:k])  # k-nearest novelty
```

### Option 3: MAP-Elites-Lite Bucketing

Define 2-3 behavioral dimensions and maintain best-per-bucket:

```python
buckets = {
  "complexity": ["simple (<10 ops)", "medium (10-50 ops)", "complex (>50 ops)"],
  "strategy": ["comparison-based", "distribution-based", "hybrid"],
  "specialization": ["general", "small-input", "large-input"]
}
# Keep best candidate in each bucket; crossover draws from different buckets
```

### Minimum Diversity Requirement

Population of 4 must contain at least 2 distinct `algorithm_family` values. If diversity drops below threshold, force exploration:
- Replace worst same-family candidate with random mutation from different family

### Diversity Tracking (MANDATORY)

Track and report diversity metrics every generation:

```json
"diversity": {
  "algorithm_families": {
    "harmonic": 2,
    "geometric": 1,
    "polynomial": 1
  },
  "unique_families": 3,
  "diversity_score": 0.75,
  "status": "HEALTHY",
  "actions_taken": []
}
```

### Diversity Score Calculation

```python
def calculate_diversity_score(population):
    """Score from 0 (all same) to 1 (all different)"""
    families = [p.algorithm_family for p in population]
    unique = len(set(families))
    total = len(families)

    # Shannon entropy normalized to [0,1]
    from collections import Counter
    import math

    counts = Counter(families)
    entropy = -sum((c/total) * math.log2(c/total) for c in counts.values())
    max_entropy = math.log2(total)

    return entropy / max_entropy if max_entropy > 0 else 0
```

### Diversity Enforcement Rules

1. **Minimum unique families**: Population of N must have ≥ ceil(N/2) unique families
2. **Family cap**: No single family can exceed 50% of population
3. **Forced exploration**: When diversity < 0.5, next generation adds 2 "alien" mutations

### Diversity-Aware Selection

When selecting new population:

```python
def select_with_diversity(candidates, population_size=4):
    selected = []

    # 1. Always keep the champion
    selected.append(candidates[0])

    # 2. Add best from each unique family
    families_seen = {candidates[0].algorithm_family}
    for c in candidates[1:]:
        if c.algorithm_family not in families_seen:
            selected.append(c)
            families_seen.add(c.algorithm_family)
            if len(selected) >= population_size:
                break

    # 3. Fill remaining with best performers
    for c in candidates[1:]:
        if c not in selected:
            selected.append(c)
            if len(selected) >= population_size:
                break

    return selected[:population_size]
```

### Low Diversity Alert

When diversity drops below threshold:

```
⚠️  Diversity Alert (Gen 5)

Population has converged to single algorithm family: "harmonic"

Diversity score: 0.25 (threshold: 0.50)

Automatic action: Spawning 2 alien mutations in Gen 6:
  - alien_geometric: Try geometric-based approach
  - alien_polynomial: Try polynomial-based approach

Rationale: Maintaining diversity prevents premature convergence
           and enables discovering novel hybrid combinations.
```

---

## Complexity Budget

Evolved algorithms must remain simple and efficient:

### Runtime Complexity

- `priority()` / core function must be **O(1) per element** (no nested loops over input)
- No heap allocations in hot path
- No I/O, no system calls, no threading primitives
- No recursion deeper than O(log n)

### Expression Complexity

Cap maximum complexity to prevent overfitting:

```python
complexity_limits = {
  "max_ast_nodes": 50,        # Approximate limit on expression tree size
  "max_operations": 30,       # +, -, *, /, pow, sqrt, ln, exp, abs, min, max
  "max_branches": 5,          # if/else, match arms
  "max_constants": 10,        # Magic numbers
  "max_nested_depth": 4       # Expression nesting depth
}
```

### Preference Ordering

Prefer simpler formulations (use as tiebreaker when fitness is equal):

1. **Monotonic transforms**: prefer `a * x + b` over `a * x^2 + b * x + c`
2. **Smooth functions**: prefer `ln(x)`, `sqrt(x)` over piecewise/discontinuous
3. **Fewer magic constants**: prefer derived constants over tuned literals
4. **No lookup tables**: unless proven >20% faster than computed

### Discouraged Patterns

Flag and penalize:
- Piecewise functions with >3 branches
- Constants that appear tuned to specific instances (overfitting signal)
- Redundant terms that cancel out
- Dead code paths

---

## Logging & Artifacts

### Per-Generation JSONL Log

Write to `.evolve/<problem>/generations.jsonl` (append-only):

```jsonl
{"gen": 1, "timestamp": "2024-12-26T10:30:00Z", "candidates": [...], "champion_id": "gen1_log", "train_best": 0.5836, "valid_best": 0.5901, "test_best": 0.5842}
{"gen": 2, "timestamp": "2024-12-26T10:35:00Z", "candidates": [...], "champion_id": "gen1_log", "train_best": 0.5836, "valid_best": 0.5901, "test_best": 0.5842}
```

### Candidate Record Schema

Each candidate entry in the JSONL:

```json
{
  "id": "gen3_simd_radix",
  "parent_ids": ["gen2_radix", "gen1_quicksort"],
  "mutation_type": "crossover",
  "git_diff_hash": "a1b2c3d4",
  "code_path": "mutations/gen3_simd_radix.rs",

  "metrics": {
    "train": {"mean": 0.5720, "median": 0.5650, "std": 0.0234, "per_instance": [...]},
    "valid": {"mean": 0.5834, "median": 0.5801, "std": 0.0198, "per_instance": [...]},
    "test": {"mean": 0.5756, "median": 0.5712, "std": 0.0201, "per_instance": [...]}
  },

  "acceptance": {
    "result": "KEEP",
    "train_improvement": 0.0116,
    "valid_regression": false,
    "instances_improved": "4/5"
  },

  "explanation": {
    "hypothesis": "SIMD-parallel bucket counting reduces memory stalls",
    "prediction": "10-20% improvement on large arrays",
    "outcome": "Confirmed: 11.6% improvement on TRAIN"
  }
}
```

### Best-So-Far Manifest

Maintain `.evolve/<problem>/champion.json`:

```json
{
  "id": "gen3_simd_radix",
  "generation": 3,
  "discovered_at": "2024-12-26T10:35:00Z",
  "code_path": "rust/src/evolved.rs",
  "metrics": {
    "train": 0.5720,
    "valid": 0.5834,
    "test": 0.5756
  },
  "lineage": ["baseline", "gen1_radix", "gen2_radix", "gen3_simd_radix"],
  "key_innovations": ["11-bit radix", "SIMD bucket count"],
  "reproduce_command": "cd .evolve/bin-packing/rust && cargo run --release --bin benchmark"
}
```

### Reproducibility Commands

Log exact commands to reproduce any state:

```bash
# Logged in generations.jsonl
"reproduce": {
  "setup": "git checkout a1b2c3d4 && cd .evolve/bin-packing/rust",
  "build": "~/.cargo/bin/cargo build --release",
  "eval": "~/.cargo/bin/cargo run --release --bin benchmark -- --seed 42",
  "expected_output_hash": "sha256:abc123..."
}
```

---

## Operational Guardrails

### Separation of Concerns

1. **Never edit evaluator AND candidate in same step**
   - If evaluator needs fixing, do that first, verify baselines unchanged, then resume evolution
   - Exception: explicit user request to modify both

2. **One change at a time**
   - Each candidate represents exactly ONE mutation or crossover
   - No "while I'm here" improvements
   - Diffs should be minimal and focused

### Regression Handling

3. **Automatic revert on regression**
   - If new champion regresses on VALID by >1%, automatic rollback
   - Alert user: "Reverted gen4_x: VALID regressed 2.3%"

4. **Preserve lineage**
   - Never delete mutation files
   - Never overwrite evolved.rs without backup
   - Keep full history in mutations/ directory

### Safety Checks

5. **Pre-flight validation**
   - Before evaluating candidate: verify it compiles
   - Before promoting: verify correctness tests pass
   - Before committing: verify VALID non-regression

6. **Checkpoint before risky operations**
   - Save evolution.json before each generation
   - Save champion.json before any promotion

7. **Bounds on evolution**
   - Max 100 generations without user confirmation
   - Max 1000 candidates total per evolution run
   - Alert if >50% of candidates fail to compile

---

## Sandboxing & Isolation (MANDATORY)

Evolution runs involve executing untrusted, LLM-generated code. These requirements ensure mutations don't interfere with each other and minimize security risks.

### Mutation Isolation (Prevent Result Stomping)

**CRITICAL**: Each mutation MUST execute in complete isolation to prevent race conditions and result corruption.

#### Directory Structure for Parallel Execution

```
.evolve/<problem>/
├── workspace/                    # Ephemeral mutation workspaces
│   ├── gen3_mut0_abc123/        # Unique per mutation (gen + index + hash)
│   │   ├── rust/                # Complete copy of benchmark code
│   │   ├── results.json         # This mutation's results only
│   │   └── .lock                # Mutex file for this workspace
│   ├── gen3_mut1_def456/
│   └── ...
├── rust/                         # Template/champion code (READ-ONLY during eval)
├── mutations/                    # Archive of all tested mutations
└── results/                      # Aggregated results (written AFTER all evals)
    └── gen3_results.json
```

#### Isolation Rules

1. **Unique workspace per mutation**:
   ```python
   def create_mutation_workspace(generation, mutation_index, code_hash):
       workspace_id = f"gen{generation}_mut{mutation_index}_{code_hash[:6]}"
       workspace_path = f".evolve/{problem}/workspace/{workspace_id}"

       # Copy template, don't symlink
       shutil.copytree(template_path, workspace_path)

       return workspace_path
   ```

2. **No shared files during evaluation**:
   - Each mutation writes ONLY to its own `workspace/gen_X_mutY_*/` directory
   - Never write to `rust/src/evolved.rs` during parallel evaluation
   - Aggregate results only AFTER all parallel evals complete

3. **Atomic result collection**:
   ```python
   def collect_results(generation, workspaces):
       results = []
       for ws in workspaces:
           # Read each mutation's isolated results
           result_file = f"{ws}/results.json"
           if os.path.exists(result_file):
               with open(result_file) as f:
                   results.append(json.load(f))

       # Write aggregated results atomically
       with atomic_write(f"results/gen{generation}_results.json") as f:
           json.dump(results, f)

       return results
   ```

4. **Cleanup after aggregation**:
   ```python
   def cleanup_workspaces(generation):
       # Only clean up after results are safely aggregated
       workspace_dir = f".evolve/{problem}/workspace"
       for ws in glob.glob(f"{workspace_dir}/gen{generation}_*"):
           shutil.rmtree(ws)
   ```

### Parallel Execution Safety

When running mutations in parallel via Task agents:

```python
# CORRECT: Each agent gets unique workspace
for i, mutation in enumerate(mutations):
    workspace = create_mutation_workspace(gen, i, hash(mutation))
    agent.run(
        workspace=workspace,
        evolved_rs=f"{workspace}/rust/src/evolved.rs",  # Isolated
        results_out=f"{workspace}/results.json"          # Isolated
    )

# WRONG: Shared paths cause race conditions
for mutation in mutations:
    agent.run(
        evolved_rs=".evolve/problem/rust/src/evolved.rs",  # COLLISION!
        results_out=".evolve/problem/results.json"          # COLLISION!
    )
```

### Autonomous Execution (No Human Intervention)

Evolution must run unattended. Configure agents for autonomous operation:

#### Agent Spawn Configuration

When spawning mutation/evaluation agents via the Task tool:

1. **Use dangerouslyDisableSandbox for Bash execution**:
   - Mutation agents need to compile and run Rust code
   - This requires shell access without permission prompts
   - The isolation comes from workspace separation, not shell sandboxing

2. **Constrain file access to workspace**:
   ```python
   mutation_agent_prompt = f"""
   You are evaluating a mutation in an ISOLATED workspace.

   WORKSPACE: {workspace_path}

   CONSTRAINTS:
   - ONLY read/write files within {workspace_path}
   - Do NOT access parent directories
   - Do NOT access network resources
   - Do NOT modify system files

   Your task: [mutation/evaluation task]
   """
   ```

3. **Pre-approve expected operations**:
   - `cargo build --release` in workspace
   - `cargo run --release --bin benchmark` in workspace
   - Reading/writing `.json` and `.rs` files in workspace

#### Timeout Enforcement

All mutation evaluations MUST have timeouts:

```python
evaluation_limits = {
    "compile_timeout_ms": 120000,      # 2 minutes to compile
    "benchmark_timeout_ms": 300000,    # 5 minutes to benchmark
    "total_mutation_timeout_ms": 600000  # 10 minutes total per mutation
}
```

If a mutation exceeds timeout:
- Kill the process
- Mark mutation as FAILED with reason "timeout"
- Do NOT retry automatically (may indicate infinite loop)

### Security Sandboxing

Evolved code is untrusted. Minimize blast radius:

#### Build-Time Protections

1. **Deny unsafe by default** (unless explicitly required):
   ```toml
   # Cargo.toml for mutation workspaces
   [profile.release]
   # ... optimization settings ...

   [lints.rust]
   unsafe_code = "deny"  # Override only if mutation explicitly uses unsafe
   ```

2. **Limit dependencies**:
   ```toml
   # Only allow pre-approved dependencies
   [dependencies]
   # Core only - no network, no filesystem beyond std
   ```

3. **Static analysis before execution**:
   ```python
   def pre_execution_checks(evolved_rs_path):
       code = open(evolved_rs_path).read()

       # Block dangerous patterns
       dangerous_patterns = [
           r'std::process::Command',    # No shell execution
           r'std::fs::(remove|write)',  # No filesystem modification outside workspace
           r'std::net::',               # No network access
           r'std::env::',               # No environment access
           r'include_bytes!',           # No external file inclusion
           r'extern\s+"C"',             # No FFI
       ]

       for pattern in dangerous_patterns:
           if re.search(pattern, code):
               return False, f"Blocked: {pattern}"

       return True, "OK"
   ```

#### Runtime Protections

1. **Resource limits** (if available on platform):
   ```bash
   # Example: limit memory and CPU time
   ulimit -v 2097152  # 2GB virtual memory
   ulimit -t 300      # 5 minute CPU time
   ```

2. **Working directory jail**:
   ```python
   # Run benchmark from within workspace, not project root
   subprocess.run(
       ["cargo", "run", "--release", "--bin", "benchmark"],
       cwd=workspace_path,  # Jail to workspace
       timeout=300
   )
   ```

3. **Output sanitization**:
   - Don't trust stdout/stderr from evolved code
   - Parse only expected JSON result format
   - Reject results with unexpected structure

### Sandboxing Checklist (Per Generation)

Before starting a generation, verify:

```markdown
- [ ] All mutation workspaces created with unique paths
- [ ] Template code copied (not symlinked) to each workspace
- [ ] No shared mutable state between mutations
- [ ] Timeouts configured for all operations
- [ ] Pre-execution security scan enabled
- [ ] Results aggregation happens AFTER all evals complete
```

After generation completes:

```markdown
- [ ] All mutation results collected
- [ ] Results aggregated atomically
- [ ] Workspaces cleaned up
- [ ] Champion promoted only from aggregated results
- [ ] Workspace directory is empty (all cleaned up)
```

### Failure Recovery

If a mutation agent crashes or times out:

1. **Do NOT retry automatically** - may indicate malicious code
2. **Log the failure** with full context:
   ```json
   {
     "mutation_id": "gen3_mut5_abc123",
     "status": "FAILED",
     "reason": "timeout",
     "workspace": "/path/to/workspace",
     "preserved": true,
     "investigation_needed": true
   }
   ```
3. **Preserve workspace** for investigation (don't auto-cleanup failures)
4. **Continue evolution** with remaining successful mutations
5. **Alert if >50% mutations fail** - may indicate systemic issue

---

## Core Features

1. **Population-based**: Maintains top 4 diverse solutions, not just the winner
2. **Semantic crossover**: Combines innovations from multiple parents
3. **Adaptive generations**: Continues while improving, stops on plateau
4. **Budget control**: User sets token/generation limits
5. **Checkpointing**: Resume evolution from where you left off

## Usage

```
/evolve-perf <problem description>
/evolve-perf <problem description> --budget <tokens|generations>
/evolve-perf --resume  # Continue previous evolution
```

**Examples**:
```
/evolve-perf sorting algorithm for integers
/evolve-perf bin packing heuristic --budget 50k
/evolve-perf string search --budget 20gen
/evolve-perf hash function --budget unlimited
/evolve-perf --resume
```

**Budget Options**:
| Budget | Meaning | Approx. Generations |
|--------|---------|---------------------|
| `10k` | 10,000 tokens | ~2-3 generations |
| `50k` | 50,000 tokens | ~10-12 generations |
| `100k` | 100,000 tokens | ~20-25 generations |
| `5gen` | 5 generations | Fixed count |
| `unlimited` | No limit | Until plateau |
| (none) | Default 50k | ~10-12 generations |

---

## Execution Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Step 0: Bootstrap (first run only)                         │
│  Step 1: Discover baselines                                 │
│  Step 2: Generate benchmark infrastructure                  │
│  Step 3: Establish baseline                                 │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  EVOLUTION LOOP (adaptive)                            │  │
│  │                                                       │  │
│  │  while budget_remaining AND improving:                │  │
│  │    - Generation N: crossover + mutation               │  │
│  │    - Evaluate offspring                               │  │
│  │    - Update population                                │  │
│  │    - Check stopping criteria                          │  │
│  │    - Checkpoint state                                 │  │
│  │    - If plateau: ask user to continue?                │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  Step Final: Report results                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 0: Bootstrap (First Run Only)

Skip if `.evolve/.bootstrapped` exists.

1. **Check Rust Toolchain**:
   ```bash
   ~/.cargo/bin/cargo --version 2>/dev/null || cargo --version
   ```
   If missing, offer installation via AskUserQuestion.

2. **Check Python 3.10+**:
   ```bash
   python3 --version
   ```

3. **Create directories and mark complete**:
   ```bash
   mkdir -p .evolve
   touch .evolve/.bootstrapped
   ```

---

## Step 1: Benchmark & Baseline Discovery (MANDATORY)

Before generating benchmarks, search for existing published results to establish state-of-the-art baselines.

### Step 1a: Search for Published Baselines

Run these searches to find authoritative baselines:

```python
search_queries = [
    f"{problem} benchmark state of the art",
    f"{problem} algorithm comparison paper",
    f"{problem} best known result",
    f"{problem} github benchmark rust",
    f"{problem} competitive programming",
]
```

Use WebSearch for each query, then WebFetch to extract specific results.

### Step 1b: Baseline Sources (Priority Order)

1. **Academic papers**: Nature, Science, arXiv, JMLR (cite DOI)
2. **Industry benchmarks**: Google, Meta, Microsoft research blogs
3. **Competition results**: Kaggle, competitive programming archives
4. **GitHub repositories**: Well-starred, actively maintained benchmarks

### Step 1c: Required Baseline Information

For each discovered baseline, record:

```json
"discovered_baselines": [
  {
    "name": "FunSearch",
    "source": "Nature 2024",
    "url": "https://www.nature.com/articles/s41586-023-06924-6",
    "metric": "0.68% excess",
    "benchmark": "Weibull 5k",
    "verified": true,
    "our_reproduction": "0.6842%"
  },
  {
    "name": "Best Fit Decreasing",
    "source": "Standard algorithm",
    "metric": "~4% excess",
    "benchmark": "Weibull 5k",
    "verified": true
  }
]
```

### Step 1d: Baseline Verification

**CRITICAL**: Verify discovered baselines by implementing and running them:

1. Implement baseline algorithm in `baselines.rs`
2. Run on same benchmark data
3. Confirm results match published claims (within 5% tolerance)
4. If mismatch: investigate, document, and flag

```
Baseline Verification Report:

| Baseline | Published | Our Run | Match | Notes |
|----------|-----------|---------|-------|-------|
| FunSearch | 0.68% | 0.6842% | ✓ | Exact match |
| Best Fit | ~4% | 3.98% | ✓ | Within tolerance |
| First Fit | ~4% | 4.23% | ✓ | As expected |
```

### Step 1e: No Baseline Found

If no published baselines exist:

1. Implement naive/standard algorithm as baseline
2. Document that this is a novel benchmark
3. Report improvement vs naive (not vs state-of-art)
4. Flag results as "novel benchmark" in final report

---

## Step 2: Generate Benchmark Infrastructure

Create in `.evolve/<problem-name>/`:

```
.evolve/<problem-name>/
├── rust/
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs        # Trait definition
│       ├── baselines.rs  # Known algorithms to beat
│       ├── evolved.rs    # Current champion
│       └── benchmark.rs  # Benchmark binary
├── data/
│   ├── train/            # Training instances (for selection)
│   ├── valid/            # Validation instances (for promotion gate)
│   └── test/             # Holdout instances (never used for selection)
├── evaluator.py          # Fitness evaluation
├── evolution.json        # Full evolution state (for resume)
├── champion.json         # Best-so-far manifest
├── generations.jsonl     # Per-generation log (append-only)
└── mutations/            # All tested mutations
```

### evolution.json (Master State File)

This file enables resumption and tracks all evolution state:

```json
{
  "mode": "perf",
  "problem": "sorting algorithm for integers",
  "created": "2024-01-15T10:30:00Z",
  "updated": "2024-01-15T11:45:00Z",

  "reproducibility": {
    "rust_toolchain": "1.75.0",
    "git_commit": "a1b2c3d4e5f6",
    "platform": "darwin-arm64",
    "train_data_hash": "sha256:abc123...",
    "valid_data_hash": "sha256:def456...",
    "test_data_hash": "sha256:789ghi..."
  },

  "acceptance": {
    "epsilon": 0.001,
    "valid_regression_tolerance": 0.005,
    "instance_threshold_ratio": 0.6,
    "noise_rerun_count": 3
  },

  "problem_analysis": {
    "algorithm_families": ["quicksort", "mergesort", "heapsort", "radix", "counting", "shell", "timsort", "introsort"],
    "optimization_dimensions": ["cache", "simd", "branch_prediction", "small_array", "nearly_sorted", "memory"],
    "viable_strategies": 26,
    "gen1_agents": 26,
    "gen2_agents": 16
  },

  "budget": {
    "type": "tokens",
    "limit": 50000,
    "used": 23450,
    "remaining": 26550
  },

  "generation": 5,
  "status": "running",

  "baseline": {
    "naive": 1289,
    "std": 114592,
    "std_unstable": 168417
  },

  "champion": {
    "id": "gen4_crossover_radix_shell",
    "fitness": 0.94,
    "ops_per_second": 185000,
    "generation_discovered": 4,
    "train_metric": 0.5720,
    "valid_metric": 0.5834,
    "test_metric": 0.5756
  },

  "population": [
    {
      "id": "gen4_crossover_radix_shell",
      "fitness": 0.94,
      "ops_per_second": 185000,
      "algorithm_family": "hybrid_radix_shell",
      "key_innovations": ["11-bit radix", "insertion base case", "gap presort"],
      "parents": ["gen3_radix_quick", "gen2_shellsort"],
      "code_path": "mutations/gen4_crossover_radix_shell.rs"
    }
    // ... 3 more
  ],

  "history": [
    {
      "generation": 1,
      "best_fitness": 0.89,
      "best_ops": 156000,
      "best_id": "gen1_radix",
      "improvement": null,
      "tokens_used": 4500
    },
    {
      "generation": 2,
      "best_fitness": 0.91,
      "best_ops": 172000,
      "best_id": "gen2_crossover_radix_quick",
      "improvement": 0.02,
      "tokens_used": 4200
    },
    {
      "generation": 3,
      "best_fitness": 0.91,
      "best_ops": 173000,
      "best_id": "gen2_crossover_radix_quick",
      "improvement": 0.00,
      "plateau_count": 1,
      "tokens_used": 4100
    }
  ],

  "stopping": {
    "plateau_count": 0,
    "plateau_threshold": 3,
    "min_improvement": 0.005,
    "max_generations": null
  }
}
```

---

## Step 3: Establish Baseline & Analyze Problem

1. Run evaluator on naive implementation
2. Report baseline speeds
3. **Analyze problem to determine viable strategies**

### Problem Analysis

Analyze the problem to estimate:
- **Algorithm families**: How many fundamentally different approaches exist?
- **Optimization dimensions**: What can be optimized (cache, SIMD, branches, memory)?
- **Input characteristics**: What variations matter (size, distribution, patterns)?

```
Example analysis for "sorting integers":

Algorithm families (8+):
  - Comparison: quicksort, mergesort, heapsort, shellsort, timsort
  - Distribution: radix sort, counting sort, bucket sort
  - Hybrid: introsort, pdqsort, pattern-defeating

Optimization dimensions (6):
  - Cache efficiency, SIMD, branch prediction, memory allocation
  - Small-array specialization, nearly-sorted detection

Estimated viable strategies: 14
Recommended agents: 16 (Gen1), 12 (Gen2+)
```

### Agent Scaling Formula

```python
def estimate_agents(problem_analysis):
    # Base: number of distinct algorithm families
    algo_families = len(problem_analysis["algorithm_families"])

    # Add optimization dimensions (each can be applied to top algos)
    opt_dimensions = len(problem_analysis["optimization_dimensions"])

    # Viable strategies = families + (top_3_families × opt_dimensions)
    viable_strategies = algo_families + min(3, algo_families) * opt_dimensions

    # Gen1: Explore all viable strategies (cap at 32)
    gen1_agents = min(viable_strategies, 32)

    # Gen2+: Crossover pairs + mutations (scale with population)
    gen2_agents = min(viable_strategies // 2 + 4, 24)

    return {
        "gen1_agents": gen1_agents,
        "gen2_agents": gen2_agents,
        "viable_strategies": viable_strategies
    }
```

### Smart Budget Recommendation

Based on analysis, recommend budget and ask user:

```
Evolution ready for: sorting algorithm for integers

Baselines:
  bubble (naive):    1,289 ops/sec
  std:             114,592 ops/sec
  std_unstable:    168,417 ops/sec  ← target

Problem Analysis:
  Algorithm families: 8 (comparison, distribution, hybrid)
  Optimization dimensions: 6
  Viable strategies: 14

Recommended: 16 agents/gen, ~6k tokens/gen

Budget Options:
1. Quick (10k) - 2 gens, 8 agents each [minimal exploration]
2. Standard (50k) - 8 gens, 16 agents Gen1, 12 Gen2+ [Recommended]
3. Deep (100k) - 16 gens, 24 agents Gen1, 16 Gen2+ [thorough]
4. Maximum (200k) - 32 gens, 32 agents Gen1, 24 Gen2+ [exhaustive]
5. Unlimited - run until plateau

⚡ For this problem, Standard (50k) should explore most viable algorithms.
   Deep (100k) recommended if you want thorough hybrid combinations.
```

### Dynamic Scaling Examples

| Problem | Algo Families | Opt Dims | Viable | Gen1 Agents | Gen2+ Agents |
|---------|--------------|----------|--------|-------------|--------------|
| Fibonacci | 4 | 2 | 10 | 10 | 8 |
| Sorting | 8 | 6 | 26 | 26 | 16 |
| String search | 6 | 4 | 18 | 18 | 12 |
| Hash function | 10 | 5 | 25 | 25 | 16 |
| Integer parsing | 3 | 4 | 15 | 15 | 10 |

Store analysis and agent counts in `evolution.json`.

---

## Step 4: Evolution Loop (Adaptive)

### Token Estimation & Display (MANDATORY)

Tokens scale with agent count:
```python
def estimate_tokens_per_gen(agent_count):
    return agent_count * 400 + 800  # ~400 tokens/agent + overhead

# Examples:
#   8 agents  → ~4,000 tokens/gen
#  16 agents  → ~7,200 tokens/gen
#  32 agents  → ~13,600 tokens/gen
```

### Token Budget Display (Required Each Generation)

Display budget status after every generation:

```
┌───────────────────────────────────────────────┐
│  Generation 4 Complete                        │
│                                               │
│  Budget: ████████████░░░░░░░░ 58% (29k/50k)   │
│                                               │
│  This gen: 7,200 tokens (16 agents)           │
│  Remaining: ~2-3 more generations             │
└───────────────────────────────────────────────┘
```

### Token Tracking in evolution.json

```json
"budget": {
  "type": "tokens",
  "limit": 50000,
  "used": 29000,
  "remaining": 21000,
  "per_generation": [
    {"gen": 1, "tokens": 8200, "agents": 16},
    {"gen": 2, "tokens": 6800, "agents": 12},
    {"gen": 3, "tokens": 7100, "agents": 12},
    {"gen": 4, "tokens": 6900, "agents": 12}
  ],
  "avg_per_gen": 7250,
  "estimated_remaining_gens": 2.9
}
```

### Budget Warnings

Display warnings at thresholds:

```python
def check_budget_warnings(budget):
    remaining_pct = budget.remaining / budget.limit * 100

    if remaining_pct <= 10:
        return "⚠️ CRITICAL: <10% budget remaining. Final generation."
    elif remaining_pct <= 25:
        return "⚠️ WARNING: <25% budget remaining. Consider stopping soon."
    elif remaining_pct <= 50:
        return "ℹ️  Budget 50% used. On track."
    else:
        return None
```

### Generation 1: Divergent Exploration

Spawn **N parallel mutation agents** where N = `gen1_agents` from problem analysis.

Generate strategy list dynamically based on problem:
```python
def generate_strategies(problem_analysis, agent_count):
    strategies = []

    # 1. One agent per algorithm family
    for family in problem_analysis["algorithm_families"]:
        strategies.append(f"implement_{family}")

    # 2. Optimization variants of top families
    top_families = problem_analysis["algorithm_families"][:3]
    for family in top_families:
        for opt in problem_analysis["optimization_dimensions"]:
            strategies.append(f"{family}_{opt}")

    # 3. Fill remaining with general strategies
    general = ["tweak", "unroll", "specialize", "vectorize",
               "memoize", "restructure", "hybrid", "alien",
               "simd", "branch_free", "cache_friendly", "unsafe_opt"]

    while len(strategies) < agent_count:
        strategies.extend(general)

    return strategies[:agent_count]
```

Evaluate all, extract innovations, select top 4 with diversity.

**Update evolution.json** after each generation.

### Generation 2+: Crossover + Mutation (MANDATORY)

**Crossover is REQUIRED, not optional.** Each Gen2+ generation MUST include crossover candidates.

Each generation uses `gen2_agents` from problem analysis:

```python
def allocate_gen2_agents(agent_count, population):
    # MANDATORY: At least 50% crossover in Gen2+
    crossover_count = max(agent_count // 2, 3)  # Minimum 3 crossover
    mutation_count = agent_count - crossover_count

    # Crossover: pair top performers (ensure diverse pairings)
    crossover_pairs = []
    for i in range(len(pop)):
        for j in range(i+1, len(pop)):
            # Prefer pairing different algorithm families
            if pop[i].algorithm_family != pop[j].algorithm_family:
                crossover_pairs.append((pop[i], pop[j]))

    # Fill with same-family pairs if needed
    if len(crossover_pairs) < crossover_count:
        for i in range(len(pop)):
            for j in range(i+1, len(pop)):
                if (pop[i], pop[j]) not in crossover_pairs:
                    crossover_pairs.append((pop[i], pop[j]))

    crossover_pairs = crossover_pairs[:crossover_count]

    # Mutation: apply diverse strategies to top performers
    mutation_targets = population[:mutation_count]

    return crossover_pairs, mutation_targets
```

### Crossover Requirements

1. **Minimum crossover count**: At least 3 crossover candidates per Gen2+ generation
2. **Diversity preference**: Prioritize pairing candidates from different algorithm families
3. **Parent tracking**: Record both parent IDs in candidate metadata
4. **Innovation extraction**: Explicitly list which innovations came from each parent

### Crossover Logging

Each crossover candidate MUST include:

```json
{
  "id": "gen4_hybrid_balanced",
  "mutation_type": "crossover",
  "parent_ids": ["gen1_harmonic", "gen3_geometric_mean"],
  "parent_contributions": {
    "gen1_harmonic": ["harmonic mean scoring", "coefficient 50"],
    "gen3_geometric_mean": ["geometric mean term", "sqrt scaling"]
  },
  "novel_combination": "50/50 blend of harmonic and geometric signals"
}
```

Each generation:
1. **Budget check**: Is there budget remaining?
2. **N/2 crossover agents**: Combine parent pairs
3. **N/2 mutation agents**: Refine top performers
4. **Evaluate** all N offspring in parallel
5. **Extract innovations** from successful ones
6. **Select** new population with diversity + elitism
7. **Update** evolution.json with new state
8. **Check stopping criteria**

### Adaptive Stopping Criteria

After each generation, evaluate:

```python
def should_stop(evolution_state):
    # 1. Budget exhausted
    if budget_used >= budget_limit:
        return True, "budget_exhausted"

    # 2. Plateau detected (no improvement for N generations)
    if plateau_count >= plateau_threshold:
        return True, "plateau"

    # 3. Target achieved (if specified)
    if champion_fitness >= target_fitness:
        return True, "target_achieved"

    # 4. Max generations (if specified)
    if generation >= max_generations:
        return True, "max_generations"

    return False, None
```

### Plateau Detection

Track improvement across generations:

```python
def update_plateau_status(current_fitness, previous_fitness, min_improvement=0.005):
    improvement = current_fitness - previous_fitness

    if improvement < min_improvement:
        plateau_count += 1
    else:
        plateau_count = 0  # Reset on improvement

    return plateau_count
```

**Plateau threshold**: 3 generations without meaningful improvement (>0.5%)

### User Checkpoint (On Plateau or Every N Generations)

When plateau detected OR every 5 generations with `unlimited` budget:

```
Generation 8 Complete:
  Champion: 185K ops/sec (+14,254% vs bubble, +10% vs std_unstable)

  ⚠️  Plateau detected: No improvement for 3 generations

  Budget used: 34,200 / 50,000 tokens (68%)

  Options:
  1. Continue evolution (may find breakthrough)
  2. Stop and save champion
  3. Try radical mutations only (higher variance)
```

Use AskUserQuestion to let user decide.

### Breakthrough Detection

If improvement after plateau:

```
🎉 Breakthrough in Generation 9!
  Previous best: 185K ops/sec
  New champion:  201K ops/sec (+8.6%)

  Innovation: SIMD-friendly radix bucket distribution

  Plateau reset. Continuing evolution...
```

---

## Step 5: Checkpointing & Resume

### After Each Generation

Write complete state to `evolution.json`:
- Current population
- Champion
- History with fitness trajectory
- Budget usage
- Plateau count

### Resume Command

When user runs `/evolve-perf --resume`:

1. Find most recent `evolution.json` in `.evolve/*/`
2. Load state
3. Report current status:

```
Resuming evolution: sorting algorithm for integers

Status: Paused at generation 5
Champion: 185K ops/sec (gen4_crossover_radix_shell)
Budget remaining: 26,550 / 50,000 tokens

Last 3 generations:
  Gen 3: 173K ops/sec (plateau 1)
  Gen 4: 185K ops/sec (breakthrough!)
  Gen 5: 185K ops/sec (plateau 1)

Continue evolution?
```

4. Resume from saved population state

---

## Step 6: Finalize

When evolution stops (any reason):

```
Evolution Complete!

Problem: sorting algorithm for integers
Generations: 12
Total tokens: 48,750
Stop reason: plateau (3 generations without improvement)

Evolution Trajectory:
  Gen  1: 156K ops/sec  radix_sort discovered
  Gen  2: 172K ops/sec  radix+quicksort hybrid (+10%)
  Gen  3: 173K ops/sec  minor refinement (+0.5%)
  Gen  4: 185K ops/sec  breakthrough: added shellsort presort (+7%)
  Gen  5: 185K ops/sec  plateau
  ...
  Gen 12: 189K ops/sec  final refinement

Baselines:
  bubble:        1.3K ops/sec (naive starting point)
  std:         115K ops/sec
  std_unstable: 168K ops/sec

Champion: 189K ops/sec
  vs bubble:       +14,538% (146x faster)
  vs std_unstable: +12.5%

Metrics:
  TRAIN: 0.5720
  VALID: 0.5834 (no regression from baseline)
  TEST:  0.5756 (holdout, for reference only)

Key Innovations in Champion:
  - 11-bit radix buckets (Gen 1)
  - Sign-bit flip for negatives (Gen 1)
  - Insertion sort for n < 32 (Gen 4)
  - Nearly-sorted detection (Gen 4)

Champion saved to: .evolve/sorting/rust/src/evolved.rs
State saved to: .evolve/sorting/evolution.json

To continue evolution later: /evolve-perf --resume
```

---

## Mutation & Crossover Prompts

### Mutation Agent Prompt

```
You are an algorithm optimizer. Improve this Rust code for SPEED.

TRAIT TO IMPLEMENT:
<trait definition>

CURRENT CODE:
<code>

STRATEGY: <strategy>

Requirements:
- Must implement the trait exactly
- Must pass all correctness tests
- Focus purely on PERFORMANCE
- Use unsafe if it helps (with proper safety invariants)

Return ONLY the complete Rust code for evolved.rs, no explanations.
```

### Crossover Agent Prompt

```
You are creating a HYBRID algorithm by combining two parent solutions.

TRAIT TO IMPLEMENT:
<trait definition>

PARENT A: <algorithm_family_a> (<ops_per_second_a> ops/sec)
Innovations: <key_innovations_a>
Strengths: <strengths_a>
Weaknesses: <weaknesses_a>

CODE A:
<code_a>

---

PARENT B: <algorithm_family_b> (<ops_per_second_b> ops/sec)
Innovations: <key_innovations_b>
Strengths: <strengths_b>
Weaknesses: <weaknesses_b>

CODE B:
<code_b>

---

Create a HYBRID solution that:
1. COMBINES key innovations from BOTH parents
2. Uses A's approach where A is strong, B's where B is strong
3. May dispatch based on input characteristics (size, pattern detection)
4. Inherits the best constants/thresholds from each

The goal is a solution FASTER than either parent by combining their strengths.

Return ONLY the complete Rust code for evolved.rs, no explanations.
```

### Innovation Extraction Prompt

```
Analyze this algorithm implementation and extract its key innovations.

CODE:
<code>

PERFORMANCE: <ops_per_second> ops/sec

Respond in this exact JSON format:
{
  "algorithm_family": "<e.g., radix_sort, quicksort, lookup_table, simd, etc.>",
  "key_innovations": ["<technique 1>", "<technique 2>", ...],
  "strengths": ["<fast on what>", ...],
  "weaknesses": ["<slow on what>", ...],
  "complexity": {"time": "<O(?)>", "space": "<O(?)>"}
}
```

---

## Radical Mutation Mode

When user chooses "radical mutations only" after plateau:

Spawn 8 agents with high-variance strategies:
- **alien**: Completely different algorithm family
- **alien2**: Another alien approach
- **restructure**: Fundamental reorganization
- **complexity_change**: Try different complexity class (e.g., O(n²) → O(n))
- **simd**: Explicit SIMD vectorization
- **unsafe_aggressive**: Aggressive unsafe optimizations
- **lookup_heavy**: Maximum precomputation
- **branch_free**: Eliminate all branches

This increases variance to escape local optima at the cost of more failed mutations.

---

## GPU Acceleration (Optional, Apple Silicon)

For Apple Silicon Macs, leverage Metal GPU for parallel candidate evaluation:

### When to Use GPU Acceleration

| Scenario | GPU Benefit | Recommendation |
|----------|-------------|----------------|
| Many candidates (>8) | High | Enable |
| Large input sizes (>100k elements) | High | Enable |
| Compute-heavy fitness function | High | Enable |
| Simple evaluation, few candidates | Low | Skip |
| Memory-bound algorithm | Low | Skip |

### Metal Setup

Add to `Cargo.toml`:

```toml
[dependencies]
metal = "0.28"
objc = "0.2"

[features]
gpu = ["metal", "objc"]
```

### Parallel Candidate Evaluation

```rust
#[cfg(feature = "gpu")]
mod gpu_eval {
    use metal::*;

    pub fn evaluate_candidates_parallel(
        candidates: &[Box<dyn BinPackingHeuristic>],
        test_data: &[Vec<u32>],
    ) -> Vec<f64> {
        let device = Device::system_default().expect("No Metal device");
        let command_queue = device.new_command_queue();

        // Batch evaluation across GPU cores
        candidates.par_iter()
            .map(|c| evaluate_single(c, test_data))
            .collect()
    }
}
```

### Expected Speedup

| Candidates | CPU Time | GPU Time | Speedup |
|------------|----------|----------|---------|
| 8 | 2.4s | 0.8s | 3x |
| 16 | 4.8s | 1.0s | 4.8x |
| 32 | 9.6s | 1.4s | 6.9x |

### Enabling GPU Mode

```bash
# Build with GPU support
cargo build --release --features gpu

# Run benchmark with GPU acceleration
cargo run --release --features gpu --bin benchmark
```

### Fallback Behavior

```rust
fn evaluate_all(candidates: &[Candidate]) -> Vec<f64> {
    #[cfg(feature = "gpu")]
    if metal_available() {
        return gpu_eval::evaluate_candidates_parallel(candidates);
    }

    // CPU fallback (always available)
    candidates.iter()
        .map(|c| evaluate_single(c))
        .collect()
}
```

---

## GPU-Accelerated Algorithms (Optional)

For problems amenable to GPU computation, evolve Metal compute shaders:

### Applicable Problems

| Problem | GPU Potential | Notes |
|---------|---------------|-------|
| Sorting (large arrays) | High | Bitonic sort, radix sort |
| Matrix operations | Very High | Native GPU strength |
| Graph algorithms | Medium | Depends on structure |
| String search | Low | Memory-bound |
| Bin packing | Low | Sequential decisions |

### Metal Shader Evolution

For GPU-amenable problems, generate and evolve Metal compute shaders:

```metal
// Example: evolved sorting kernel
kernel void evolved_sort(
    device uint* data [[buffer(0)]],
    constant uint& n [[buffer(1)]],
    uint gid [[thread_position_in_grid]]
) {
    // Evolved GPU algorithm here
    // ...
}
```

### Hybrid CPU/GPU Evolution

Some problems benefit from hybrid approaches:

```rust
impl BinPackingHeuristic for HybridEvolved {
    fn priority(&self, item: u32, bins: &[u32]) -> Vec<f64> {
        if bins.len() > 1000 {
            // GPU path for large bin counts
            gpu_priority(item, bins)
        } else {
            // CPU path for small counts
            cpu_priority(item, bins)
        }
    }
}
```

### GPU Evolution Tracking

Log GPU-specific metrics:

```json
{
  "id": "gen3_gpu_radix",
  "platform": "metal",
  "shader_path": "shaders/gen3_radix.metal",
  "metrics": {
    "cpu_time_ms": 45.2,
    "gpu_time_ms": 8.7,
    "speedup": 5.2,
    "gpu_utilization": 0.78
  }
}
```

---

## Key Principles

1. **Adaptive by default**: Continues while improving, stops on plateau
2. **User control**: Budget limits prevent runaway token usage
3. **Resumable**: Full state checkpointed after each generation
4. **Transparent**: Clear reporting of improvement trajectory
5. **Correctness first**: Failed tests = fitness 0
6. **Diversity maintained**: Population represents multiple algorithm families
7. **Elitism**: Never lose the best solution
8. **Generalization**: VALID gate prevents overfitting to TRAIN
9. **Reproducibility**: Full determinism with logged seeds and versions

---

## Token Budget Reference

Budget scales with problem complexity (agents × generations):

| Budget | Simple (10 agents) | Medium (16 agents) | Complex (26 agents) |
|--------|-------------------|-------------------|---------------------|
| 10k | 2 gens | 1 gen | 1 gen |
| 50k | 10 gens | 6 gens | 4 gens |
| 100k | 20 gens | 12 gens | 7 gens |
| 200k | 40 gens | 25 gens | 15 gens |

**Rule of thumb**: More agents = better Gen1 exploration, more generations = better refinement.

The system will recommend based on problem analysis:
- Simple problems (fibonacci): fewer agents, more generations
- Complex problems (sorting): more agents to explore algorithm space

Most improvements happen in first 5-10 generations. More agents help for:
- Large algorithm spaces (many valid approaches)
- Problems with multiple optimization dimensions
- Finding non-obvious hybrid combinations
