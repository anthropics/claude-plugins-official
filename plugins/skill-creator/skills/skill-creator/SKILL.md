---
name: skill-creator
description: Create new skills, improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, update or optimize an existing skill, run evals to test a skill, or benchmark skill performance with variance analysis.
---

# Skill Creator

A skill for creating new skills and iteratively improving them.

At a high level, the process of creating a skill goes like this:

- Decide what you want the skill to do and roughly how it should do it
- Write a draft of the skill
- Create a few test prompts and run claude-with-access-to-the-skill on them
- Evaluate the results
  - which can be through automated evals, but also it's totally fine and good for them to be evaluated by the human by hand and that's often the only way
- Rewrite the skill based on feedback from the evaluation
- Repeat until you're satisfied
- Expand the test set and try again at larger scale

Your job when using this skill is to figure out where the user is in this process and then jump in and help them progress through these stages. So for instance, maybe they're like "I want to make a skill for X". You can help narrow down what they mean, write a draft, write the test cases, figure out how they want to evaluate, run all the prompts, and repeat.

On the other hand, maybe they already have a draft of the skill. In this case you can go straight to the eval/iterate part of the loop.

Of course, you should always be flexible and if the user is like "I don't need to run a bunch of evaluations, just vibe with me", you can do that instead.

Cool? Cool.

## Building Blocks

The skill-creator operates on composable building blocks. Each has well-defined inputs and outputs.

| Building Block | Input | Output | Agent |
|-----------|-------|--------|-------|
| **Eval Run** | skill + eval prompt + files | transcript, outputs, metrics | `agents/executor.md` |
| **Grade Expectations** | outputs + expectations | pass/fail per expectation | `agents/grader.md` |
| **Blind Compare** | output A, output B, eval prompt | winner + reasoning | `agents/comparator.md` |
| **Post-hoc Analysis** | winner + skills + transcripts | improvement suggestions | `agents/analyzer.md` |

### Eval Run

Executes a skill on an eval prompt and produces measurable outputs.

- **Input**: Skill path, eval prompt, input files
- **Output**: `transcript.md`, `outputs/`, `metrics.json`
- **Metrics captured**: Tool calls, execution steps, output size, errors

### Grade Expectations

Evaluates whether outputs meet defined expectations.

- **Input**: Expectations list, transcript, outputs directory
- **Output**: `grading.json` with pass/fail per expectation plus evidence
- **Purpose**: Objective measurement of skill performance

### Blind Compare

Compares two outputs without knowing which skill produced them.

- **Input**: Output A path, Output B path, eval prompt, expectations (optional)
- **Output**: Winner (A/B/TIE), reasoning, quality scores
- **Purpose**: Unbiased comparison between skill versions

### Post-hoc Analysis

After blind comparison, analyzes WHY the winner won.

- **Input**: Winner identity, both skills, both transcripts, comparison result
- **Output**: Winner strengths, loser weaknesses, improvement suggestions
- **Purpose**: Generate actionable improvements for next iteration

---

## Environment Capabilities

Check whether you can spawn subagents — independent agents that execute tasks
in parallel. If you can, you'll delegate work to executor, grader, comparator,
and analyzer agents. If not, you'll do all work inline, sequentially.

This affects which modes are available and how they execute. The core
workflows are the same — only the execution strategy changes.

---

## Mode Workflows

Building blocks combine into higher-level workflows for each mode:

| Mode | Purpose | Workflow |
|------|---------|----------|
| **Eval** | Test skill performance | Executor → Grader → Results |
| **Improve** | Iteratively optimize skill | Executor → Grader → Comparator → Analyzer → Apply |
| **Create** | Interactive skill development | Interview → Research → Draft → Run → Refine |
| **Benchmark** | Standardized performance measurement (requires subagents) | 3x runs per configuration → Aggregate → Analyze |

See `references/mode-diagrams.md` for detailed visual workflow diagrams.

---

## Task Tracking

Use tasks to track progress on multi-step workflows.

### Task Lifecycle

Each eval run becomes a task with stage progression:

```
pending → planning → implementing → reviewing → verifying → completed
          (prep)     (executor)     (grader)    (validate)
```

### Creating Tasks

When running evals, create a task per eval run:

```python
TaskCreate(
    subject="Eval 0, run 1 (with_skill)",
    description="Execute skill eval 0 with skill and grade expectations",
    activeForm="Preparing eval 0"
)
```

### Updating Stages

Progress through stages as work completes:

```python
TaskUpdate(task, status="planning")     # Prepare files, stage inputs
TaskUpdate(task, status="implementing") # Spawn executor subagent
TaskUpdate(task, status="reviewing")    # Spawn grader subagent
TaskUpdate(task, status="verifying")    # Validate outputs exist
TaskUpdate(task, status="completed")    # Done
```

### Comparison Tasks

For blind comparisons (after all runs complete):

```python
TaskCreate(
    subject="Compare skill-v1 vs skill-v2"
)
# planning = gather outputs
# implementing = spawn blind comparators
# reviewing = tally votes, handle ties
# verifying = if tied, run more comparisons or use efficiency
# completed = declare winner
```

---

## Architecture

The **coordinator** (this skill):

1. Asks the user what they want to do and which skill to work on
2. Determines workspace location (ask if not obvious)
3. Creates workspace and tasks for tracking progress
4. Delegates work to subagents when available, otherwise executes inline
5. Tracks the **best version** (not necessarily the latest)
6. Reports results with evidence and metrics

### Agent Types

| Agent | Role | Reference |
|-------|------|-----------|
| **Executor** | Run skill on a task, produce transcript + outputs + metrics | `agents/executor.md` |
| **Grader** | Evaluate expectations against transcript and outputs | `agents/grader.md` |
| **Comparator** | Blind A/B comparison between two outputs | `agents/comparator.md` |
| **Analyzer** | Post-hoc analysis of comparison results | `agents/analyzer.md` |

## Communicating with the user

The skill creator is liable to be used by people across a wide range of familiarity with coding jargon. If you haven't heard (and how could you, it's only very recently that it started), there's a trend now where the power of Claude is inspiring plumbers to open up their terminals, parents and grandparents to google "how to install npm". On the other hand, the bulk of users are probably fairly computer-literate.

So please pay attention to context cues to understand how to phrase your communication! In the default case, just to give you some idea:

- "evaluation" and "benchmark" are borderline, but OK
- for "JSON" and "assertion" you want to see serious cues from the user that they know what those things are before using them without explaining them

It's OK to briefly explain terms if you're in doubt, and feel free to clarify terms with a short definition if you're unsure if the user will get it.

---

## Creating a skill

### Capture Intent

Start by understanding the user's intent. The current conversation might already contain a workflow the user wants to capture (e.g., they say "turn this into a skill"). If so, extract answers from the conversation history first — the tools used, the sequence of steps, corrections the user made, input/output formats observed. The user may need to fill the gaps, and should confirm before proceeding to the next step.

1. What should this skill enable Claude to do?
2. When should this skill trigger? (what user phrases/contexts)
3. What's the expected output format?
4. Should we set up test cases to verify the skill works? Skills with objectively verifiable outputs (file transforms, data extraction, code generation, fixed workflow steps) benefit from test cases. Skills with subjective outputs (writing style, art) often don't need them. Suggest the appropriate default based on the skill type, but let the user decide.

### Interview and Research

Proactively ask questions about edge cases, input/output formats, example files, success criteria, and dependencies.

Check available MCPs - if useful for research (searching docs, finding similar skills, looking up best practices), research in parallel via subagents if available, otherwise inline. Come prepared with context to reduce burden on the user.

### Initialize

Run the initialization script:

```bash
scripts/init_skill.py <skill-name> --path <output-directory>
```

This creates:
- SKILL.md template with frontmatter
- scripts/, references/, assets/ directories
- Example files to customize or delete

### Fill SKILL.md Frontmatter

Based on interview, fill:

- **name**: Skill identifier
- **description**: When to trigger, what it does. This is the primary triggering mechanism - include both what the skill does AND specific contexts for when to use it. All "when to use" info goes here, not in the body. Note: currently Claude has a tendency to "undertrigger" skills -- to not use them when they'd be useful. To combat this, please make the skill descriptions a little bit "pushy". So for instance, instead of "How to build a simple fast dashboard to display internal Anthropic data.", you might write "How to build a simple fast dashboard to display internal Anthropic data. Make sure to use this skill whenever the user mentions dashboards, data visualization, internal metrics, or wants to display any kind of company data, even if they don't explicitly ask for a 'dashboard.'"
- **compatibility**: Required tools, dependencies (optional, rarely needed)

### Skill Writing Guide

#### Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/    - Executable code for deterministic/repetitive tasks
    ├── references/ - Docs loaded into context as needed
    └── assets/     - Files used in output (templates, icons, fonts)
```

**What NOT to include**: README.md, INSTALLATION_GUIDE.md, CHANGELOG.md, or any auxiliary documentation. Skills are for AI agents, not human onboarding.

#### Progressive Disclosure

Skills use a three-level loading system:
1. **Metadata** (name + description) - Always in context (~100 words)
2. **SKILL.md body** - In context whenever skill triggers (<500 lines ideal)
3. **Bundled resources** - As needed (unlimited, scripts can execute without loading)

These word counts are approximate and you can feel free to go longer if needed.

**Key patterns:**
- Keep SKILL.md under 500 lines; if you're approaching this limit, add an additional layer of hierarchy along with clear pointers about where the model using the skill should go next to follow up.
- Reference files clearly from SKILL.md with guidance on when to read them
- For large reference files (>300 lines), include a table of contents

**Domain organization**: When a skill supports multiple domains/frameworks, organize by variant:
```
cloud-deploy/
├── SKILL.md (workflow + selection)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```
Claude reads only the relevant reference file.

#### Principle of Lack of Surprise

This goes without saying, but skills must not contain malware, exploit code, or any content that could compromise system security. A skill's contents should not surprise the user in their intent if described. Don't go along with requests to create misleading skills or skills designed to facilitate unauthorized access, data exfiltration, or other malicious activities. Things like a "roleplay as an XYZ" are OK though.

#### Writing Patterns

Prefer using the imperative form in instructions.

**Defining output formats** - You can do it like this:
```markdown
## Report structure
ALWAYS use this exact template:
# [Title]
## Executive summary
## Key findings
## Recommendations
```

**Examples pattern** - It's useful to include examples. You can format them like this (but if "Input" and "Output" are in the examples you might want to deviate a little):
```markdown
## Commit message format
**Example 1:**
Input: Added user authentication with JWT tokens
Output: feat(auth): implement JWT-based authentication
```

### Immediate Feedback Loop

**Always have something cooking.** Every time user adds an example or input:

1. **Immediately start running it** - don't wait for full specification
2. **Show outputs in workspace** - tell user: "The output is at X, take a look"
3. **First runs in main agent loop** - not subagent, so user sees the transcript
4. **Seeing what Claude does** helps user understand and refine requirements

### Writing Style

Try to explain to the model why things are important in lieu of heavy-handed musty MUSTs. Use theory of mind and try to make the skill general and not super-narrow to specific examples. Start by writing a draft and then look at it with fresh eyes and improve it.

### Test Cases

After writing the skill draft, come up with 2-3 realistic test prompts — the kind of thing a real user would actually say. Share them with the user: [you don't have to use this exact language] "Here are a few test cases I'd like to try. Do these look right, or do you want to add more?" Then run them.

If the user wants evals, create `evals/evals.json` with this structure:

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt",
      "expected_output": "Description of expected result",
      "files": [],
      "assertions": [
        "The output includes X",
        "The skill correctly handles Y"
      ]
    }
  ]
}
```

You can initialize with `scripts/init_json.py evals evals/evals.json` and validate with `scripts/validate_json.py evals/evals.json`. See `references/schemas.md` for the full schema.

### Transition to Automated Iteration

Once gradable criteria are defined (expectations, success metrics), Claude can:

- More aggressively suggest improvements
- Run tests automatically (via subagents in the background if available, otherwise sequentially)
- Present results: "I tried X, it improved pass rate by Y%"

### Package and Present (only if `present_files` tool is available)

Check whether you have access to the `present_files` tool. If you don't, skip this step. If you do, package the skill and present the .skill file to the user:

```bash
scripts/package_skill.py <path/to/skill-folder>
```

After packaging, direct the user to the resulting `.skill` file path so they can install it.

---

## Improving a skill

When user asks to improve a skill, ask:
1. **Which skill?** - Identify the skill to improve
2. **How much time?** - How long can Claude spend iterating?
3. **What's the goal?** - Target quality level, specific issues to fix, or general improvement

Claude should then autonomously iterate using the building blocks (run, grade, compare, analyze) to drive the skill toward the goal within the time budget.

Some advice on writing style when improving a skill:

1. Try to generalize from the feedback, rather than fixing specific examples one by one. The big picture thing that's happening here is that we're trying to create "skills" that can be used a million times (maybe literally, maybe even more who knows) across many different prompts. Here you and the user are iterating on only a few examples over and over again because it helps move faster. The user knows these examples in and out and it's quick for them to assess new outputs. But if the skill you and the user are codeveloping works only for those examples, it's useless. Rather than put in fiddley overfitty changes, or oppressively constrictive MUSTs, if there's some stubborn issue, you might try branching out and using different metaphors, or recommending different patterns of working. It's relatively cheap to try and maybe you'll land on something great.

2. Keep the prompt lean; remove things that aren't pulling their weight. Make sure to read the transcripts, not just the final outputs -- if it looks like the skill is making the model waste a bunch of time doing things that are unproductive, you can try getting rid of the parts of the skill that are making it do that and seeing what happens.

3. Last but not least, try hard to explain the **why** behind everything you're asking the model to do. Today's LLMs are *smart*. They have good theory of mind and when given a good harness and go beyond rote instructions and really make things happen. Even if the feedback from the user is terse or frustrated, try to actually understand the task and why the user is writing what they wrote, and what they actually wrote, and then try to transmit this understanding into the instructions. If you find yourself writing ALWAYS or NEVER in all caps, or using super rigid structures, that's a yellow flag - try to reframe and explain the reasoning so that the model understands why the thing you're asking for is important. That's a more humane, powerful, and effective approach.

This task is pretty important (we are trying to create billions a year in economic value here!) and your thinking time is not the blocker; take your time and really mull things over. I'd suggest writing a draft skill and then looking at it anew and making improvements. Really try to get into the head of the user and understand what they want and need. Best of luck.

### Setup Phase

0. **Read output schemas**:

   ```bash
   Read references/schemas.md  # JSON structures for grading, history, comparison, analysis
   ```

   This ensures you understand the structure of outputs you'll produce and validate.

1. **Choose workspace location**:

   **Ask the user** where to put the workspace. Suggest `<skill-name>-workspace/` as a sibling to the skill directory, but let the user choose. If the workspace ends up inside a git repo, suggest adding it to `.gitignore`.

2. **Copy skill to v0**:
   ```bash
   scripts/copy_skill.py <skill-path> <skill-name>-workspace/v0 --iteration 0
   ```

3. **Verify or create evals**:
   - Check for existing `evals/evals.json`
   - If missing, ask user for 2-3 example tasks and create evals
   - Use `scripts/init_json.py evals` to create with correct structure

4. **Create tasks** for baseline:

   ```python
   for run in range(3):
       TaskCreate(
           subject=f"Eval baseline, run {run+1}"
       )
   ```

5. **Initialize history.json**:

   ```bash
   scripts/init_json.py history <workspace>/history.json
   ```

   Then edit to fill in skill_name. See `references/schemas.md` for full structure.

### Iteration Loop

For each iteration (0, 1, 2, ...):

#### Step 1: Execute (3 Parallel Runs)

Spawn 3 executor subagents in parallel (or run sequentially without subagents — see "Without subagents" below). Update task to `implementing` stage.

Spawn a subagent for each run with these instructions:

```
Read agents/executor.md at: <skill-creator-path>/agents/executor.md

Execute this task:
- Skill path: workspace/v<N>/skill/
- Task: <eval prompt from evals.json>
- Test files: <eval files if any>
- Save transcript to: workspace/v<N>/runs/run-<R>/transcript.md
- Save outputs to: workspace/v<N>/runs/run-<R>/outputs/
```

#### Step 2: Grade Assertions

Spawn grader subagents (or grade inline — see "Without subagents" below). Update task to `reviewing` stage.

**Purpose**: Grading produces structured pass/fail results for tracking pass rates over iterations. The grader also extracts claims and reads user_notes to surface issues that expectations might miss.

**Set the grader up for success**: The grader needs to actually inspect the outputs, not just read the transcript. If the outputs aren't plain text, tell the grader how to read them — check the skill for inspection tools it already uses and pass those as hints in the grader prompt.

Spawn a subagent with these instructions:

```
Read agents/grader.md at: <skill-creator-path>/agents/grader.md

Grade these expectations:
- Assertions: <list from evals.json>
- Transcript: workspace/v<N>/runs/run-<R>/transcript.md
- Outputs: workspace/v<N>/runs/run-<R>/outputs/
- Save grading to: workspace/v<N>/runs/run-<R>/grading.json

To inspect output files:
<include inspection hints from the skill, e.g.:>
<"Use python -m markitdown <file> to extract text content">
```

**Review grading.json**: Check `user_notes_summary` for uncertainties and workarounds flagged by the executor. Also check `eval_feedback` — if the grader flagged lax assertions or missing coverage, update `evals.json` before continuing. Improving evals mid-loop is fine and often necessary; you can't meaningfully improve a skill if the evals don't measure anything real.

**Eval quality loop**: If `eval_feedback` has suggestions, tighten the assertions and rerun the evals. Keep iterating as long as the grader keeps finding issues. Once `eval_feedback` says the evals look solid (or has no suggestions), move on to skill improvement. Consult the user about what you're doing, but don't block on approval for each round — just keep making progress.

When picking which eval to use for the quality loop, prefer one where the skill partially succeeds — some expectations pass, some fail. An eval where everything fails gives the grader nothing to critique (there are no false positives to catch). The feedback is most useful when some expectations pass and the grader can assess whether those passes reflect genuine quality or surface-level compliance.

#### Step 3: Blind Compare (If N > 0)

For iterations after baseline, use blind comparison:

**Purpose**: While grading tracks expectation pass rates, the comparator judges **holistic output quality** using a rubric. Two outputs might both pass all expectations, but one could still be clearly better. The comparator uses expectations as secondary evidence, not the primary decision factor.

**Blind A/B Protocol:**
1. Randomly assign: 50% chance v<N> is A, 50% chance v<N> is B
2. Record the assignment in `workspace/grading/v<N>-vs-best/assignment.json`
3. Comparator sees only "Output A" and "Output B" - never version names

Spawn a subagent with these instructions:

```
Read agents/comparator.md at: <skill-creator-path>/agents/comparator.md

Blind comparison:
- Eval prompt: <the task that was executed>
- Output A: <path to one version's output>
- Output B: <path to other version's output>
- Assertions: <list from evals.json>

You do NOT know which is old vs new. Judge purely on quality.
```

**Determine winner by majority vote:**
- If 2+ comparators prefer A: A wins
- If 2+ comparators prefer B: B wins
- Otherwise: TIE

#### Step 4: Post-hoc Analysis

After blind comparison, analyze results. Spawn a subagent with these instructions:

```
Read agents/analyzer.md at: <skill-creator-path>/agents/analyzer.md

Analyze:
- Winner: <A or B>
- Winner skill: workspace/<winner-version>/skill/
- Winner transcript: workspace/<winner-version>/runs/run-1/transcript.md
- Loser skill: workspace/<loser-version>/skill/
- Loser transcript: workspace/<loser-version>/runs/run-1/transcript.md
- Comparison result: <from comparator>
```

#### Step 5: Update State

Update task to `completed` stage. Record results:

```python
if new_version wins majority:
    current_best = new_version
    # Update history.json

history.iterations.append({
    "version": "v<N>",
    "parent": "<previous best>",
    "expectation_pass_rate": 0.85,
    "grading_result": "won" | "lost" | "tie",
    "is_current_best": bool
})
```

#### Step 6: Create New Version (If Continuing)

1. Copy current best to new version:
   ```bash
   scripts/copy_skill.py workspace/<current_best>/skill workspace/v<N+1> \
       --parent <current_best> \
       --iteration <N+1>
   ```

2. Apply improvements from analyzer suggestions

3. Create new tasks for next iteration

4. Continue loop or stop if:
   - **Time budget exhausted**: Track elapsed time, stop when approaching limit
   - **Goal achieved**: Target quality level or pass rate reached
   - **Diminishing returns**: No significant improvement in last 2 iterations
   - **User requests stop**: Check for user input between iterations

### Final Report

When iterations complete:

1. **Best Version**: Which version performed best (not necessarily the last)
2. **Score Progression**: Assertion pass rates across iterations
3. **Key Improvements**: What changes had the most impact
4. **Recommendation**: Whether to adopt the improved skill

Copy best skill back to main location:
```bash
cp -r workspace/<best_version>/skill/* ./
```

Check whether you have access to the `present_files` tool. If you do, package and present the improved skill, and direct the user to the resulting `.skill` file path so they can install it:
```bash
scripts/package_skill.py <path/to/skill-folder>
```
(If you don't have the `present_files` tool, don't run `package_skill.py`)

### Without Subagents

Without subagents, Improve mode still works but with reduced rigor:

- **Single run per iteration** (not 3) — variance analysis isn't possible with one run
- **Inline execution**: Read `agents/executor.md` and follow the procedure directly in your main loop. Then read `agents/grader.md` and follow it directly to grade the results.
- **No blind comparison**: You can't meaningfully blind yourself since you have full context. Instead, compare outputs by re-reading both versions' results and analyzing the differences directly.
- **No separate analyzer**: Do the analysis inline after comparing — identify what improved, what regressed, and what to try next.
- **Keep everything else**: Version tracking, copy-iterate-grade loop, history.json, stopping criteria all work the same.
- **Acknowledge reduced rigor**: Without independent agents, grading is less rigorous — the same context that executed the task also grades it. Results are directional, not definitive.

---

## Eval Mode

Run individual evals to test skill performance and grade expectations.

**IMPORTANT**: Before running evals, read the full documentation:
```
Read references/eval-mode.md      # Complete Eval workflow
Read references/schemas.md        # JSON output structures
```

Use Eval mode when:
- Testing a specific eval case
- Comparing with/without skill on a single task
- Quick validation during development

The workflow: Setup → Check Dependencies → Prepare → Execute → Grade → Display Results

Without subagents, execute and grade sequentially in the main loop. Read the agent reference files (`agents/executor.md`, `agents/grader.md`) and follow the procedures directly.

---

## Benchmark Mode

Run standardized performance measurement with variance analysis.

**Requires subagents.** Benchmark mode relies on parallel execution of many runs to produce statistically meaningful results. Without subagents, use Eval mode for individual eval testing instead.

**IMPORTANT**: Before running benchmarks, read the full documentation:
```
Read references/benchmark-mode.md # Complete Benchmark workflow
Read references/schemas.md        # JSON output structures
```

Use Benchmark mode when:
- "How does my skill perform?" - Understanding overall performance
- "Compare Sonnet vs Haiku" - Cross-model comparison
- "Has performance regressed?" - Tracking changes over time
- "Does the skill add value?" - Validating skill impact

Key differences from Eval:
- Runs **all evals** (not just one)
- Runs each **3 times per configuration** for variance
- Always includes **no-skill baseline**
- Uses **most capable model** for analysis

---

## Workspace Structure

Workspaces are created as sibling directories to the skill being worked on.

```
parent-directory/
├── skill-name/                      # The skill
│   ├── SKILL.md
│   ├── evals/
│   │   ├── evals.json
│   │   └── files/
│   └── scripts/
│
└── skill-name-workspace/            # Workspace (sibling directory)
    │
    │── [Eval mode]
    ├── eval-0/
    │   ├── with_skill/
    │   │   ├── inputs/              # Staged input files
    │   │   ├── outputs/             # Skill outputs
    │   │   │   ├── transcript.md
    │   │   │   ├── user_notes.md    # Executor uncertainties
    │   │   │   ├── metrics.json
    │   │   │   └── [output files]
    │   │   ├── grading.json         # Assertions + claims + user_notes_summary
    │   │   └── timing.json          # Wall clock timing
    │   └── without_skill/
    │       └── ...
    ├── comparison.json              # Blind comparison (A/B testing)
    ├── summary.json                 # Aggregate metrics
    │
    │── [Improve mode]
    ├── history.json                 # Score progression across versions
    ├── v0/
    │   ├── META.yaml                # Version metadata
    │   ├── skill/                   # Copy of skill at this version
    │   └── runs/
    │       ├── run-1/
    │       │   ├── transcript.md
    │       │   ├── user_notes.md
    │       │   ├── outputs/
    │       │   └── grading.json
    │       ├── run-2/
    │       └── run-3/
    ├── v1/
    │   ├── META.yaml
    │   ├── skill/
    │   ├── improvements/
    │   │   └── suggestions.md       # From analyzer
    │   └── runs/
    └── grading/
        └── v1-vs-v0/
            ├── assignment.json      # Which version is A vs B
            ├── comparison-1.json    # Blind comparison results
            ├── comparison-2.json
            ├── comparison-3.json
            └── analysis.json        # Post-hoc analysis
    │
    │── [Benchmark mode]
    └── benchmarks/
        └── 2026-01-15T10-30-00/      # Timestamp-named directory
            ├── benchmark.json        # Structured results (see schema)
            ├── benchmark.md          # Human-readable summary
            └── runs/
                ├── eval-1/
                │   ├── with_skill/
                │   │   ├── run-1/
                │   │   │   ├── transcript.md
                │   │   │   ├── user_notes.md
                │   │   │   ├── outputs/
                │   │   │   └── grading.json
                │   │   ├── run-2/
                │   │   └── run-3/
                │   └── without_skill/
                │       ├── run-1/
                │       ├── run-2/
                │       └── run-3/
                └── eval-2/
                    └── ...
```

**Key files:**
- `transcript.md` - Execution log from executor
- `user_notes.md` - Uncertainties and workarounds flagged by executor
- `metrics.json` - Tool calls, output size, step count
- `grading.json` - Assertion pass/fail, notes, user_notes summary
- `timing.json` - Wall clock duration
- `comparison-N.json` - Blind rubric-based comparison
- `analysis.json` - Post-hoc analysis with improvement suggestions
- `history.json` - Version progression with pass rates and winners
- `benchmark.json` - Structured benchmark results with runs, run_summary, notes
- `benchmark.md` - Human-readable benchmark summary

---

## Coordinator Responsibilities

The coordinator must:

1. **Delegate to subagents when available; otherwise execute inline** - In Improve, Eval, and Benchmark modes, use subagents for executor/grader work when possible. Without subagents, read the agent reference files and follow the procedures directly.
2. **Create mode exception** - Run examples in main loop so user sees the transcript (interactive feedback matters more than consistency)
3. **Use independent grading when possible** - Spawn separate grader/comparator agents for unbiased evaluation. Without subagents, grade inline but acknowledge the limitation.
4. **Track progress with tasks** - Create tasks, update stages, mark complete
5. **Track best version** - The best performer, not the latest iteration
6. **Run multiple times for variance** - 3 runs per configuration when subagents are available; 1 run otherwise
7. **Parallelize independent work** - When subagents are available, spawn independent work in parallel
8. **Report results clearly** - Display pass/fail with evidence and metrics
9. **Review user_notes** - Check executor's user_notes.md for issues that passed expectations might miss
10. **Capture execution metrics** - In Benchmark mode, record tokens/time/tool_calls from each execution
11. **Use most capable model for analysis** - Benchmark analyzer should use the smartest available model

---

## Delegating Work

There are two patterns for delegating work to building blocks:

**With subagents**: Spawn an independent agent with the reference file instructions. Include the reference file path in the prompt so the subagent knows its role. When tasks are independent (like 3 runs of the same version), spawn all subagents in the same turn for parallelism.

**Without subagents**: Read the agent reference file (e.g., `agents/executor.md`) and follow the procedure directly in your main loop. Execute each step sequentially — the procedures are designed to work both as subagent instructions and as inline procedures.

---

# Conclusion

Just pasting in the overall workflow again for reference:

- Decide what you want the skill to do and roughly how it should do it
- Write a draft of the skill
- Create a few test prompts and run claude-with-access-to-the-skill on them
- Evaluate the results
  - which can be through automated evals, but also it's totally fine and good for them to be evaluated by the human by hand and that's often the only way
- Rewrite the skill based on feedback from the evaluation
- Repeat until you're satisfied
- Expand the test set and try again at larger scale

Good luck!
