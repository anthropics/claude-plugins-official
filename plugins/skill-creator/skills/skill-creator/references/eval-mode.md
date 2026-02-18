# Eval Mode Reference

Eval mode runs skill evals and grades expectations. Enables measuring skill performance, comparing with/without skill, and validating that skills add value.

## Purpose

Evals serve to:
1. **Set a floor** - Prove the skill helps Claude do something it couldn't by default
2. **Raise the ceiling** - Enable iterating on skills to improve performance
3. **Measure holistically** - Capture metrics beyond pass/fail (time, tokens)
4. **Understand cross-model behavior** - Test skills across different models

## Eval Workflow

```
0. Choose Workspace Location
   → Ask user where to put workspace, suggest sensible default

1. Check Dependencies
   → Scan skill for dependencies, confirm availability with user

2. Prepare (scripts/prepare_eval.py)
   → Create task, copies skill, stages files

3. Execute (agents/executor.md)
   → Update task to implementing, spawn executor sub-agent
   → Executor reads skill, runs prompt, saves transcript

4. Grade (agents/grader.md)
   → Update task to reviewing, spawn grader sub-agent
   → Grader reads transcript + outputs, evaluates expectations

5. Complete task, display results
   → Pass/fail per expectation, overall pass rate, metrics
```

## Step 0: Setup

**Before running any evals, read the output schemas:**

```bash
# Read to understand the JSON structures you'll produce
Read references/schemas.md
```

This ensures you know the expected structure for:
- `grading.json` - What the grader produces
- `metrics.json` - What the executor produces
- `timing.json` - Wall clock timing format

**Choose workspace location:**

1. **Suggest default**: `<skill-name>-workspace/` as a sibling to the skill directory
2. **Ask the user** using AskUserQuestion — if the workspace is inside a git repo, suggest adding it to `.gitignore`
3. **Create the workspace directory** once confirmed

## Step 1: Check Dependencies

Before running evals, scan the skill for dependencies:

1. Read SKILL.md (including `compatibility` frontmatter field)
2. Check referenced scripts for required tools
3. Present to user and confirm availability

## Step 2: Prepare and Create Task

Run prepare script and create task:

```bash
scripts/prepare_eval.py <skill-path> <eval-id> --output-dir <workspace>/eval-<id>/
```

```python
task = TaskCreate(
    subject=f"Eval {eval_id}"
)
TaskUpdate(task, status="planning")
```

## Step 3: Execute

Update task to `implementing` and run the executor:

```bash
echo "{\"executor_start\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > <run-dir>/timing.json
```

**With subagents**: Spawn an executor subagent with these instructions:

```
Read agents/executor.md at: <skill-creator-path>/agents/executor.md

Execute this eval:
- Skill path: <workspace>/skill/
- Prompt: <eval prompt from eval_metadata.json>
- Input files: <workspace>/eval-<id>/inputs/
- Save transcript to: <workspace>/eval-<id>/transcript.md
- Save outputs to: <workspace>/eval-<id>/outputs/
```

**Without subagents**: Read `agents/executor.md` and follow the procedure directly — execute the eval, save the transcript, and produce outputs inline.

After execution completes, update timing.json with executor_end and duration.

## Step 4: Grade

Update task to `reviewing` and run the grader:

**With subagents**: Spawn a grader subagent with these instructions:

```
Read agents/grader.md at: <skill-creator-path>/agents/grader.md

Grade these expectations:
- Assertions: <list from eval_metadata.json>
- Transcript: <workspace>/eval-<id>/transcript.md
- Outputs: <workspace>/eval-<id>/outputs/
- Save grading to: <workspace>/eval-<id>/grading.json
```

**Without subagents**: Read `agents/grader.md` and follow the procedure directly — evaluate expectations against the transcript and outputs, then save grading.json.

After grading completes, finalize timing.json.

## Step 5: Display Results

Update task to `completed`. Display:
- Pass/fail status for each expectation with evidence
- Overall pass rate
- Execution metrics from grading.json
- Wall clock time from timing.json
- **User notes summary**: Uncertainties, workarounds, and suggestions from the executor (may reveal issues even when expectations pass)

## Comparison Workflow

To compare skill-enabled vs no-skill performance:

```
1. Prepare both runs (with --no-skill flag for baseline)
2. Execute both (parallel executors)
3. Grade both (parallel graders)
4. Blind Compare outputs
5. Report winner with analysis
```
