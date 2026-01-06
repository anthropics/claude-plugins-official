---
name: evolve-size
description: Size subskill for /evolve - optimizes for minimal code/text length
version: 1.0.0
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task, TodoWrite, WebSearch, WebFetch, AskUserQuestion
argument-hint: <problem description>
---

# /evolve-size - Size Optimization Subskill

This is the **size optimization subskill** for the `/evolve` command. It evolves solutions for **minimal length** (bytes, characters, tokens).

**Note**: This subskill is invoked by the master `/evolve` skill when size mode is detected. You can also invoke it directly with `/evolve-size`.

---

## Supported Domains

This subskill works across multiple domains, not just code:

| Domain | Measure | Correctness | Examples |
|--------|---------|-------------|----------|
| **Python** | bytes | Execute & test | ARC-AGI, code golf |
| **Rust** | bytes | Compile & test | Minimal implementations |
| **Go** | bytes | Compile & test | Minimal implementations |
| **Text/Markdown** | bytes/chars | LLM judges | Rule files, prompts, docs |
| **Regex** | chars | Test against examples | Pattern matching |
| **Config** | bytes | Functional test | .cursorrules, CLAUDE.md |

---

## Fitness Function

For all size optimization, smaller is better (while maintaining correctness):

```python
def size_fitness(candidate, domain, correctness_fn):
    """Universal size optimization fitness."""

    # 1. Measure size (domain-specific)
    if domain in ["python", "rust", "go"]:
        size = len(candidate.encode('utf-8'))  # bytes
    elif domain in ["text", "markdown"]:
        size = len(candidate.encode('utf-8'))  # bytes
    elif domain == "regex":
        size = len(candidate)  # characters

    # 2. Check correctness (domain-specific)
    is_correct, quality = correctness_fn(candidate)

    # 3. Combine: must be correct, then minimize size
    if not is_correct:
        return 0.001  # Penalty for incorrect

    # Higher fitness for smaller correct solutions
    # Quality can modulate (e.g., effectiveness 9/10 vs 6/10)
    return quality * (10000 / (size + 1))
```

### Scoring Formula

For code golf competitions (like ARC-AGI):
```python
score = 2500 - byte_count  # if correct
score = 0.001              # if incorrect
```

---

## Three-Stage Evolution Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  Size Optimization Pipeline                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ Stage 1:     │───▶│ Stage 2:     │───▶│ Stage 3:     │       │
│  │ Find Correct │    │ Apply Known  │    │ Discover New │       │
│  │ Solution     │    │ Tricks       │    │ Approaches   │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌──────────────────────────────────────────────────────┐       │
│  │              Trick Library (Persistent)               │       │
│  │  • Whitespace rules    • Operator substitutions      │       │
│  │  • Lambda conversions  • Comprehension patterns      │       │
│  │  • AST transformations • Algorithm templates         │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Stage 1: Find Correct Solution

Goal: Get ANY working solution. Don't worry about length yet.

```python
def stage1_find_solution(task, domain):
    """Generate initial correct solutions."""

    if domain == "python":
        prompt = f"""
        Solve this task. The solution must:
        1. Define a function: def solve(grid): ...
        2. Return the correct output for all examples

        Task examples:
        {task.train_examples}

        Return working Python code, correctness is the only goal.
        """
    elif domain == "text":
        prompt = f"""
        Write content that satisfies these requirements:
        {task.requirements}

        Focus on correctness first, not brevity.
        """

    # Generate 5-10 diverse solutions
    candidates = [llm.generate(prompt) for _ in range(10)]

    # Keep all that pass correctness tests
    return [c for c in candidates if evaluate(c, domain).correct]
```

---

## Stage 2: Apply Known Tricks

Goal: Systematically apply all known byte-saving transformations.

### Python Golf Tricks

```python
PYTHON_GOLF_TRICKS = [
    # Whitespace removal
    {"name": "remove_space_after_colon", "from": ": ", "to": ":"},
    {"name": "remove_space_in_tuple", "from": ", ", "to": ","},

    # Lambda conversion (saves ~4 bytes typically)
    {"name": "def_to_lambda",
     "pattern": r"def (\w+)\(([^)]*)\):\s*return (.+)",
     "replacement": r"\1=lambda \2:\3"},

    # Operator shortcuts (for 0/1 values)
    {"name": "and_to_mult", "from": " and ", "to": "*",
     "condition": "both_are_0_or_1"},
    {"name": "or_to_bitor", "from": " or ", "to": "|",
     "condition": "both_are_0_or_1"},
    {"name": "eq_zero_to_lt1", "from": "==0", "to": "<1",
     "condition": "value_is_non_negative"},
    {"name": "ne_zero_to_gt0", "from": "!=0", "to": ">0",
     "condition": "value_is_non_negative"},

    # Range shortcuts
    {"name": "range_tuple",
     "pattern": r"range\((\d)\)",
     "replacement": r"(\1*[0])",
     "note": "Only when index unused"},
    {"name": "range_to_tuple_explicit",
     "from": "range(3)", "to": "(0,1,2)"},

    # List tricks
    {"name": "list_map_to_star", "from": "list(map(", "to": "[*map("},
    {"name": "list_comp_identity",
     "pattern": r"\[x for x in (\w+)\]",
     "replacement": r"[*\1]"},

    # Variable shortcuts
    {"name": "use_row_directly",
     "pattern": r"for (\w) in range\(len\((\w+)\)\)",
     "replacement": r"for \1 in \2"},
]
```

### Markdown/Text Tricks

```python
TEXT_SIZE_TRICKS = [
    # Remove redundant formatting
    {"name": "single_newline", "from": "\n\n\n", "to": "\n\n"},
    {"name": "trim_trailing", "pattern": r" +\n", "replacement": "\n"},

    # Compress lists
    {"name": "compress_bullets",
     "pattern": r"- (.+)\n- (.+)\n- (.+)",
     "replacement": r"- \1\n- \2\n- \3"},  # Already optimal

    # Use shorter headers
    {"name": "h3_to_bold", "from": "### ", "to": "**", "suffix": "**"},

    # Abbreviate common phrases
    {"name": "abbrev_example", "from": "for example", "to": "e.g."},
    {"name": "abbrev_important", "from": "IMPORTANT:", "to": "!"},
]
```

### Trick Application Engine

```python
class TrickEngine:
    def __init__(self, domain):
        self.domain = domain
        self.tricks = self.load_tricks(domain)
        self.applied = []

    def apply_all(self, code):
        """Apply all applicable tricks, return best result."""
        best = code
        best_size = len(code.encode('utf-8'))

        for trick in self.tricks:
            try:
                result = self.apply_trick(code, trick)
                if result and self.verify_correctness(result):
                    size = len(result.encode('utf-8'))
                    if size < best_size:
                        best = result
                        best_size = size
                        self.applied.append(trick["name"])
            except:
                pass

        return best

    def apply_trick(self, code, trick):
        """Apply a single trick."""
        if "pattern" in trick:
            return re.sub(trick["pattern"], trick["replacement"], code)
        elif "from" in trick:
            return code.replace(trick["from"], trick["to"])
        return None
```

---

## Stage 3: Genetic Search

Goal: Discover fundamentally shorter algorithms through evolution.

### Mutation Operators

```python
class SizeMutationOperator:
    """Mutation operators for size optimization."""

    def mutate_compress(self, code):
        """Try to compress by removing/combining statements."""
        # LLM-guided compression
        prompt = f"""
        Make this code SHORTER while keeping it correct:

        {code}

        Techniques to try:
        - Combine nested loops into comprehensions
        - Use mathematical formulas instead of logic
        - Remove redundant variables
        - Use shorter built-in functions

        Return ONLY the shorter code.
        """
        return llm.generate(prompt)

    def mutate_algorithm_change(self, code, task):
        """Try a completely different approach."""
        prompt = f"""
        Current solution ({len(code)} bytes):
        {code}

        This solves the task but might be too long.
        Suggest a COMPLETELY DIFFERENT algorithm that might be shorter.

        Consider:
        - Mathematical formulas instead of iteration
        - Lookup tables instead of conditions
        - Direct array manipulation instead of loops

        Return ONLY the new code.
        """
        return llm.generate(prompt)

    def mutate_inline(self, code):
        """Inline single-use variables."""
        import ast
        tree = ast.parse(code)
        # Find single-use assignments and inline them
        # ...
        return ast.unparse(tree)
```

### Crossover Operators

```python
class SizeCrossoverOperator:
    """Combine techniques from multiple solutions."""

    def crossover_tricks(self, parent_a, parent_b):
        """Apply tricks from one parent to another's algorithm."""
        # Take the shorter algorithm structure
        if len(parent_a.code) < len(parent_b.code):
            base, donor = parent_a, parent_b
        else:
            base, donor = parent_b, parent_a

        # Apply donor's tricks to base
        code = base.code
        for trick in donor.tricks_applied:
            if trick not in base.tricks_applied:
                code = self.trick_engine.apply_trick(code, trick)

        return code

    def crossover_llm(self, parent_a, parent_b):
        """Use LLM to intelligently combine approaches."""
        prompt = f"""
        Combine the shortest elements from these two solutions:

        Solution A ({len(parent_a.code)} bytes):
        {parent_a.code}

        Solution B ({len(parent_b.code)} bytes):
        {parent_b.code}

        Create the SHORTEST possible correct solution by:
        - Using the more compact structure
        - Applying the best tricks from each
        - Finding new combinations

        Return ONLY the combined code.
        """
        return llm.generate(prompt)
```

### Population Selection

```python
def select_population(candidates, pop_size=8):
    """Select diverse, short solutions."""

    # Filter to correct only
    correct = [c for c in candidates if c.correct]
    if not correct:
        return candidates[:pop_size]

    # Sort by size (ascending - smaller is better)
    correct.sort(key=lambda c: c.byte_count)

    selected = []

    # Always keep the champion (shortest)
    selected.append(correct[0])

    # Add diverse algorithm families
    families_seen = {correct[0].algorithm_family}
    for c in correct[1:]:
        if c.algorithm_family not in families_seen:
            selected.append(c)
            families_seen.add(c.algorithm_family)
        if len(selected) >= pop_size:
            break

    # Fill with next shortest
    for c in correct:
        if c not in selected:
            selected.append(c)
        if len(selected) >= pop_size:
            break

    return selected[:pop_size]
```

---

## Non-Code Size Optimization

For markdown, config files, prompts, and other text:

### Correctness via LLM Judging

```python
def evaluate_text_solution(candidate, requirements):
    """Evaluate a text solution using LLM as judge."""

    byte_count = len(candidate.encode('utf-8'))

    # Judge effectiveness
    judgment_prompt = f"""
    Evaluate this content against the requirements:

    REQUIREMENTS:
    {requirements}

    CONTENT:
    {candidate}

    Rate on these dimensions (0-10 each):
    1. Completeness: Does it cover all required topics?
    2. Clarity: Is it unambiguous and easy to follow?
    3. Effectiveness: Would it achieve the stated goal?

    Return JSON: {{"scores": [X, Y, Z], "avg": N, "passes": true/false}}
    """

    result = llm.evaluate(judgment_prompt)

    if not result["passes"]:
        return {"fitness": 0.001, "correct": False, "bytes": byte_count}

    effectiveness = result["avg"]
    fitness = effectiveness * (10000 / (byte_count + 1))

    return {"fitness": fitness, "correct": True, "bytes": byte_count,
            "effectiveness": effectiveness}
```

### Example: Git Commit Rules

```
Evolving: shortest markdown rule for effective git commits

Gen 1: (2,847 bytes) - Full conventional commits spec
       Effectiveness: 9/10

Gen 3: (1,204 bytes) - Condensed rules, fewer examples
       Effectiveness: 8/10

Gen 5: (634 bytes) - Core rules only
       Effectiveness: 8/10

Gen 7: (412 bytes) - Too terse, unclear on edge cases
       Effectiveness: 6/10

Gen 9: (523 bytes) - Balance of brevity and clarity
       Effectiveness: 9/10

Champion: (523 bytes, effectiveness: 9/10)
- 82% smaller than Gen 1
- Same effectiveness
```

---

## Directory Structure

```
.evolve/<problem>/
├── solutions/           # Working solutions by size
│   ├── 80_baseline.py
│   ├── 65_gen3.py
│   └── 57_champion.py
├── mutations/           # All tested mutations with results
│   └── task_evolution.md
├── tricks/              # Discovered tricks
│   └── discovered.json
├── evolution.json       # Full state for resume
└── champion.json        # Best solution manifest
```

### evolution.json for Size Mode

```json
{
  "mode": "size",
  "domain": "python",
  "problem": "ARC task 0520fde7",
  "created": "2024-12-26T10:30:00Z",

  "baseline": {
    "bytes": 80,
    "code": "def solve(g):\\n return[[2*(g[r][c]&g[r][c+4])for c in range(3)]for r in range(3)]"
  },

  "champion": {
    "id": "gen2_lambda_tuple",
    "bytes": 57,
    "score": 2443,
    "code": "solve=lambda g:[[2*r[c]*r[c+4]for c in(0,1,2)]for r in g]",
    "generation_discovered": 2,
    "tricks_applied": ["def_to_lambda", "range_to_tuple", "row_iteration"]
  },

  "population": [
    {
      "id": "gen2_lambda_tuple",
      "bytes": 57,
      "algorithm_family": "list_comprehension",
      "tricks_applied": ["def_to_lambda", "range_to_tuple", "row_iteration"]
    },
    {
      "id": "gen2_zip_variant",
      "bytes": 57,
      "algorithm_family": "zip_based",
      "tricks_applied": ["def_to_lambda", "zip_slicing"]
    }
  ],

  "history": [
    {"gen": 0, "best_bytes": 80, "best_id": "baseline"},
    {"gen": 1, "best_bytes": 65, "best_id": "gen1_lambda"},
    {"gen": 2, "best_bytes": 57, "best_id": "gen2_lambda_tuple"}
  ],

  "tricks_discovered": [
    {
      "name": "row_iteration",
      "source_task": "0520fde7",
      "description": "Iterate over rows directly instead of indices",
      "before": "for r in range(len(g))",
      "after": "for r in g",
      "savings": 8
    }
  ],

  "stopping": {
    "plateau_count": 2,
    "plateau_threshold": 3,
    "target_bytes": null
  }
}
```

---

## Usage

```bash
# Explicit invocation
/evolve-size <problem description>

# Examples
/evolve-size shortest Python solution for ARC task 0520fde7
/evolve-size minimize bytes for this function
/evolve-size shortest markdown rule for git commits
/evolve-size most concise regex for email validation
/evolve-size minimal .cursorrules for TypeScript

# With options
/evolve-size --target=50 task 0520fde7    # Stop at 50 bytes
/evolve-size --domain=python task X       # Explicit domain
/evolve-size --resume                     # Continue previous
```

---

## Output Format

```
┌─────────────────────────────────────────────────────────────┐
│  Size Evolution: Task 0520fde7                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Stage 1: Find Solution                                     │
│    ✓ Found 8 correct solutions (73-142 bytes)               │
│                                                             │
│  Stage 2: Apply Tricks                                      │
│    ├─ def_to_lambda: 142→136 bytes (-6)                     │
│    ├─ whitespace: 136→134 bytes (-2)                        │
│    ├─ var_rename: 134→128 bytes (-6)                        │
│    └─ range_to_tuple: 128→124 bytes (-4)                    │
│    Best after tricks: 73 bytes                              │
│                                                             │
│  Stage 3: Genetic Search (12 generations)                   │
│    Gen 1:  73 bytes (baseline)                              │
│    Gen 4:  68 bytes (discovered: row_iteration)             │
│    Gen 7:  62 bytes (discovered: mult_for_and)              │
│    Gen 12: 57 bytes (plateau)                               │
│                                                             │
│  Result: 57 bytes (score: 2443)                             │
│  Improvement: 23 bytes (28.8% reduction)                    │
│                                                             │
│  Tricks Applied:                                            │
│    • def_to_lambda: "solve=lambda g:" vs "def solve(g):"    │
│    • row_iteration: "for r in g" vs "for r in range(len(g))"│
│    • mult_for_and: "a*b" vs "a&b" for 0/1 values            │
│                                                             │
│  Champion saved to: solutions/0520fde7.py                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Evaluation Contract

1. **Correctness First**: A solution that's wrong is worthless regardless of size
2. **Train/Valid Split**: Test on held-out examples to prevent overfitting
3. **Deterministic Evaluation**: Same solution = same byte count (no randomness)
4. **Byte Accuracy**: Use `len(code.encode('utf-8'))` for consistent measurement

### Correctness Testing

For code domains:
```python
def test_correctness(code, domain, task):
    if domain == "python":
        # Execute and test
        exec(code, namespace := {})
        solve = namespace.get("solve")
        for example in task.examples:
            result = solve(example.input)
            if result != example.output:
                return False, "Wrong output"
        return True, 1.0
```

For text domains:
```python
def test_correctness(text, domain, requirements):
    if domain in ["text", "markdown"]:
        # LLM judges
        return llm_judge(text, requirements)
    elif domain == "regex":
        # Test against examples
        return regex_test(text, requirements.positive, requirements.negative)
```

---

## Key Principles

1. **Byte count is king**: For correct solutions, smaller always wins
2. **Correctness is binary**: Either it works or it doesn't
3. **Tricks compound**: Multiple small savings add up
4. **Algorithm matters**: Sometimes a different approach is fundamentally shorter
5. **Cross-task learning**: Tricks discovered on one task often apply to others
6. **Domain-aware**: Different domains need different optimization strategies

---

## Trick Library Location

Tricks are stored in `.evolve/size/tricks.json` and persist across evolution runs:

```json
{
  "tricks": [
    {
      "id": "def_to_lambda",
      "domain": "python",
      "pattern": "def (\\w+)\\((.*)\\):\\s*return (.+)",
      "replacement": "$1=lambda $2:$3",
      "avg_savings": 4,
      "times_applied": 47,
      "success_rate": 0.92
    }
  ],
  "discovered": [
    {
      "id": "task_0520fde7_row_iter",
      "domain": "python",
      "source_task": "0520fde7",
      "description": "Direct row iteration",
      "before": "for r in range(len(g))",
      "after": "for r in g",
      "savings": 8,
      "generalized": true,
      "applicable_to": ["grid_iteration", "list_iteration"]
    }
  ]
}
```

---

## Task Documentation (REQUIRED)

After evolution completes, you MUST create/update the task's README.md with detailed generation-by-generation documentation.

### README.md Template

```markdown
# Task {task_id}: {short_description}

## Problem

{Brief description of what the task does with input/output example}

## Solution Stats

- **Bytes**: {final_bytes}
- **Score**: {2500 - final_bytes} points
- **Status**: Passing all tests

---

## Evolution Journey

### Generation-by-Generation Progress

| Gen | Bytes | Change | Code Snippet | Insight |
|-----|-------|--------|--------------|---------|
| 0 | {baseline} | Baseline | `{key_part_of_code}` | Initial working solution |
| 1 | {gen1} | -{delta} | `{changed_part}` | {what_changed_and_why} |
| 2 | {gen2} | -{delta} | `{changed_part}` | {what_changed_and_why} |
| ... | ... | ... | ... | ... |
| N | {final} | **Champion** | `{final_key_part}` | {final_insight} |

### Key Breakthroughs

{Describe the 1-3 most impactful changes that led to byte savings}

---

## Algorithm

{Numbered steps explaining how the solution works}

## Key Golf Tricks Used

- {trick_1}: `before` → `after` (saves N bytes)
- {trick_2}: `before` → `after` (saves N bytes)
- ...

## Champion Solution ({final_bytes} bytes)

\`\`\`python
{full_solution_code}
\`\`\`
```

### Documentation Requirements

1. **Generation Table**: MUST include every generation where bytes changed, showing:
   - The byte count
   - What specifically changed in the code
   - Why it saved bytes

2. **Code Snippets**: Show the actual code that changed, not just descriptions

3. **Tricks Section**: Document each golf trick with before/after examples

4. **Save Intermediate Solutions**: During evolution, save each generation's code to `{task_id}/gen{N}.py` for reference

### Example Generation Table

| Gen | Bytes | Change | Code Snippet | Insight |
|-----|-------|--------|--------------|---------|
| 0 | 280 | Baseline | `s=[(i,j)for i in range(H)...]` | Edge detection flood fill |
| 1 | 262 | -18 | `g=[o:=[0]*w,*[[0,*r,0]for r in G],o]` | Padding approach |
| 2 | 241 | -21 | `g[a][b]=1;s+=(a+1,b),...` | Walrus + tuple extend |
| 3 | 238 | -3 | `[4,0,0,3][c]` | Marker=1 simplifies lookup |
| 4 | 223 | -15 | `def f(a,b):...f(a+1,b)` | Recursive flood fill |
| 5 | 219 | -4 | `a>~0` | ~0 trick for bounds check |

---

## Resume Capability

When running `/evolve-size --resume`:

1. Load `evolution.json` from last run
2. Restore population state
3. Continue from last generation
4. Report current status:

```
Resuming size evolution: ARC task 0520fde7

Status: Paused at generation 8
Champion: 57 bytes (gen2_lambda_tuple)
Plateau count: 2/3

Last 3 generations:
  Gen 6: 57 bytes (no improvement)
  Gen 7: 57 bytes (no improvement)
  Gen 8: 57 bytes (no improvement)

Continue evolution?
```
