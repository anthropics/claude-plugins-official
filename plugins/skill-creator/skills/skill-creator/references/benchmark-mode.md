# Benchmark Mode Reference

**Requires subagents.** Benchmark mode relies on parallel execution of many independent runs. Without subagents, use Eval mode for individual eval testing instead.

Benchmark mode runs a standardized, opinionated evaluation of a skill. It answers: **"How well does this skill perform?"**

Unlike Eval mode (which runs individual evals), Benchmark mode:
- Runs **all evals** (or a user-specified subset)
- Runs each eval **3 times per configuration** (with_skill and without_skill) for variance
- Captures **metrics with variance**: pass_rate, time_seconds, tokens
- Uses the **most capable model** as analyzer to surface patterns and anomalies
- Produces **persistent, structured output** for cross-run analysis

## When to Use

- **Understanding performance**: "How does my skill perform?"
- **Cross-model comparison**: "How does this skill perform across different models?"
- **Regression detection**: Compare benchmark results over time
- **Skill validation**: Does the skill actually add value over no-skill baseline?

## Defaults

**Always include no-skill baseline.** Every benchmark runs both `with_skill` and `without_skill` configurations. This measures the value the skill adds - without a baseline, you can't know if the skill helps.

**Suggest models for comparison.** If the user wants to compare across models, suggest a couple of commonly available models in your environment. Don't hardcode model names - just recommend what's commonly used and available.

**Run on current model by default.** If the user doesn't specify, run on whatever model is currently active. For cross-model comparison, ask which models they'd like to test.

## Terminology

| Term | Definition |
|------|------------|
| **Run** | A single execution of a skill on an eval prompt |
| **Configuration** | The experimental condition: `with_skill` or `without_skill` |
| **RunResult** | Graded output of a run: expectations, metrics, notes |
| **Run Summary** | Statistical aggregates across runs: mean, stddev, min, max |
| **Notes** | Freeform observations from the analyzer |

## Workflow

```
1. Setup
   → Choose workspace location (ask user, suggest <skill>-workspace/)
   → Verify evals exist
   → Determine which evals to run (all by default, or user subset)

2. Execute runs (parallel where possible)
   → For each eval:
       → 3 runs with_skill configuration
       → 3 runs without_skill configuration
   → Each run captures: transcript, outputs, metrics
   → Coordinator extracts from Task result: total_tokens, tool_uses, duration_ms

3. Grade runs (parallel)
   → Spawn grader for each run
   → Produces: expectations with pass/fail, notes

4. Aggregate results
   → Calculate run_summary per configuration:
       → pass_rate: mean, stddev, min, max
       → time_seconds: mean, stddev, min, max
       → tokens: mean, stddev, min, max
   → Calculate delta between configurations

5. Analyze (most capable model)
   → Review all results
   → Surface patterns, anomalies, observations as freeform notes
   → Examples:
       - "Assertion X passes 100% in both configurations - may not differentiate skill value"
       - "Eval 3 shows high variance (50% ± 40%) - may be flaky"
       - "Skill adds 13s average time but improves pass rate by 50%"

6. Generate benchmark
   → benchmark.json - Structured data for analysis
   → benchmark.md - Human-readable summary
```

## Spawning Executors

Run executor subagents in the background for parallelism. When each agent completes, capture the execution metrics (tokens consumed, tool calls, duration) from the completion notification.

For example, in Claude Code, background subagents deliver a `<task-notification>` with a `<usage>` block:

```xml
<!-- Example: Claude Code task notification format -->
<task-notification>
<task-id>...</task-id>
<status>completed</status>
<result>agent's actual text output</result>
<usage>total_tokens: 3700
tool_uses: 2
duration_ms: 32400</usage>
</task-notification>
```

Extract from each completed executor's metrics:
- **total_tokens** = total tokens consumed (input + output combined)
- **tool_uses** = number of tool calls made
- **duration_ms** / 1000 = execution time in seconds

The exact format of completion notifications varies by environment — look for token counts, tool call counts, and duration in whatever format your environment provides.

Record these per-run metrics alongside the grading results. The aggregate script can then compute mean/stddev/min/max across runs for each configuration.

## Scripts

Use these scripts at specific points in the workflow:

### After Grading (Step 4: Aggregate)

```bash
# Aggregate all grading.json files into benchmark summary
scripts/aggregate_benchmark.py <benchmark-dir> --skill-name <name> --skill-path <path>
```

This reads `grading.json` from each run directory and produces:
- `benchmark.json` - Structured results with run_summary statistics
- `benchmark.md` - Human-readable summary table

### Validation

```bash
# Validate benchmark output
scripts/validate_json.py <benchmark-dir>/benchmark.json

# Validate individual grading files
scripts/validate_json.py <run-dir>/grading.json --type grading
```

### Initialize Templates

```bash
# Create empty benchmark.json with correct structure (if not using aggregate script)
scripts/init_json.py benchmark <benchmark-dir>/benchmark.json
```

## Analyzer Instructions

The analyzer (always most capable) reviews all results and generates freeform notes. See `agents/analyzer.md` for the full prompt, but key responsibilities:

1. **Compare configurations**: Which performed better? By how much?
2. **Identify patterns**: Assertions that always pass/fail, high variance, etc.
3. **Surface anomalies**: Unexpected results, broken evals, regressions
4. **Provide context**: Why might these patterns exist?

The analyzer should NOT:
- Suggest improvements to the skill (that's Improve mode)
- Make subjective quality judgments beyond the data
- Speculate without evidence
