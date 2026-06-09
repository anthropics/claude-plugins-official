---
description: "Comprehensive PR review using specialized agents"
argument-hint: "[review-aspects]"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Task"]
---

# Comprehensive PR Review

Run a comprehensive pull request review using multiple specialized agents, each focusing on a different aspect of code quality.

**Review Aspects (optional):** "$ARGUMENTS"

## Review Workflow:

1. **Determine Review Scope**
   - Check git status to identify changed files
   - Parse arguments to see if user requested specific review aspects
   - Default: Run all applicable reviews

2. **Available Review Aspects:**

   - **comments** - Analyze code comment accuracy and maintainability
   - **tests** - Review test coverage quality and completeness
   - **errors** - Check error handling for silent failures
   - **types** - Analyze type design and invariants (if new types added)
   - **code** - General code review for project guidelines
   - **simplify** - Simplify code for clarity and maintainability
   - **all** - Run all applicable reviews (default)

3. **Identify Changed Files**
   - Run `git diff --name-only` to see modified files
   - Check if PR already exists: `gh pr view`
   - Identify file types and what reviews apply

4. **Determine Applicable Reviews**

   Based on changes:
   - **Always applicable**: code-reviewer (general quality)
   - **If test files changed**: pr-test-analyzer
   - **If comments/docs added**: comment-analyzer
   - **If error handling changed**: silent-failure-hunter
   - **If types added/modified**: type-design-analyzer
   - **After passing review**: code-simplifier (polish and refine)

5. **Launch Review Agents**

   **Sequential approach** (one at a time):
   - Easier to understand and act on
   - Each report is complete before next
   - Good for interactive review

   **Parallel approach** (user can request):
   - Launch all agents simultaneously
   - Faster for comprehensive review
   - Results come back together

6. **Aggregate Results**

   After agents complete, summarize:
   - **Critical Issues** (must fix before merge)
   - **Important Issues** (should fix)
   - **Suggestions** (nice to have)
   - **Positive Observations** (what's good)

   **Interpreting cross-agent convergence (parallel runs):**

   When multiple agents run in parallel, *convergence* is a signal worth weighing explicitly:

   - **Unanimous flag** (all or nearly all agents flag the same line/issue): structural concern. The issue is inherent to the code shape, not a perspective. Treat as Important/Critical even if each individual agent rated it lower. Prioritize in the action plan.
   - **Majority flag** (more than half): still structural, usually worth fixing.
   - **Unique flag** (one agent): perspective-specific. Could be a real issue within that agent's specialty (e.g., only type-design-analyzer notices a type invariant); could also be stylistic. Triage individually — don't automatically down-rank, but don't treat as load-bearing either.

   Call out unanimous flags explicitly in the summary with something like:
   > "Flagged by all 4 agents: [issue]. Structural concern — highest priority."

   This gives the reviewer clear signal about which findings to act on first, independent of how each agent rated the issue in its individual report.

7. **Provide Action Plan**

   Organize findings:
   ```markdown
   # PR Review Summary

   ## Critical Issues (X found)
   - [agent-name]: Issue description [file:line]

   ## Important Issues (X found)
   - [agent-name]: Issue description [file:line]

   ## Suggestions (X found)
   - [agent-name]: Suggestion [file:line]

   ## Strengths
   - What's well-done in this PR

   ## Recommended Action
   1. Fix critical issues first
   2. Address important issues
   3. Consider suggestions
   4. Re-run review after fixes
   ```

## Usage Examples:

**Full review (default):**
```
/pr-review-toolkit:review-pr
```

**Specific aspects:**
```
/pr-review-toolkit:review-pr tests errors
# Reviews only test coverage and error handling

/pr-review-toolkit:review-pr comments
# Reviews only code comments

/pr-review-toolkit:review-pr simplify
# Simplifies code after passing review
```

**Parallel review:**
```
/pr-review-toolkit:review-pr all parallel
# Launches all agents in parallel
```

## Agent Descriptions:

**comment-analyzer**:
- Verifies comment accuracy vs code
- Identifies comment rot
- Checks documentation completeness

**pr-test-analyzer**:
- Reviews behavioral test coverage
- Identifies critical gaps
- Evaluates test quality

**silent-failure-hunter**:
- Finds silent failures
- Reviews catch blocks
- Checks error logging

**type-design-analyzer**:
- Analyzes type encapsulation
- Reviews invariant expression
- Rates type design quality

**code-reviewer**:
- Checks CLAUDE.md compliance
- Detects bugs and issues
- Reviews general code quality

**code-simplifier**:
- Simplifies complex code
- Improves clarity and readability
- Applies project standards
- Preserves functionality

## Tips:

- **Run early**: Before creating PR, not after
- **Focus on changes**: Agents analyze git diff by default
- **Address critical first**: Fix high-priority issues before lower priority
- **Re-run after fixes**: Verify issues are resolved
- **Use specific reviews**: Target specific aspects when you know the concern

## Workflow Integration:

**Before committing:**
```
1. Write code
2. Run: /pr-review-toolkit:review-pr code errors
3. Fix any critical issues
4. Commit
```

**Before creating PR:**
```
1. Stage all changes
2. Run: /pr-review-toolkit:review-pr all
3. Address all critical and important issues
4. Run specific reviews again to verify
5. Create PR
```

**After PR feedback:**
```
1. Make requested changes
2. Run targeted reviews based on feedback
3. Verify issues are resolved
4. Push updates
```

## Posting Inline Comments to GitHub

### `position`, not `line`

`POST /repos/{owner}/{repo}/pulls/{pull_number}/reviews` requires **`position`**: the line's integer offset in the unified diff. GitHub accepts `line` + `side` without error but returns `line: null`; the parameters anchor nothing. They belong to `POST /pulls/{n}/comments`, not this endpoint.

### Computing diff positions

Count every line in the unified diff (`@@` headers, `+`, `-`, context); `+++ b/` resets to 0.

```python
import re, subprocess

diff = subprocess.check_output(['git', 'diff', 'main...HEAD']).decode()
position = 0
current_file = None
new_line = 0
positions = {}

for raw in diff.splitlines():
    if raw.startswith('diff --git'):
        current_file = None
    elif raw.startswith('+++ b/'):
        current_file = raw[6:]
        position = 0
    elif raw.startswith('@@'):
        m = re.search(r'\+(\d+)', raw)
        if m:
            new_line = int(m.group(1)) - 1
        position += 1
    elif current_file and raw.startswith('+'):
        new_line += 1; position += 1
        positions[(current_file, new_line)] = position
    elif current_file and raw.startswith('-'):
        position += 1
    elif current_file and raw.startswith(' '):
        new_line += 1; position += 1
        positions[(current_file, new_line)] = position

# positions.get(('src/foo.ts', 42))
```

### Posting the review

Build the body with `json.dump`; `printf`/heredoc escaping corrupts any body with backticks or quotes.

```python
import json

review = {
  'event': 'REQUEST_CHANGES',
  'body': 'Summary.',
  'comments': [
    {'path': 'src/foo.ts', 'position': 8, 'body': 'Comment with `backticks`.'},
  ]
}
with open('/tmp/review.json', 'w') as f:
    json.dump(review, f)
```

```bash
gh api repos/{owner}/{repo}/pulls/{number}/reviews \
  --method POST \
  --input /tmp/review.json \
  --jq '[.id, .state]'
```

### Don't debug against the live PR

COMMENTED reviews are permanent: the API and UI offer no way to remove them. On the first unexpected result, read the docs before retrying. Use a throwaway PR for API experimentation.

### zsh: use `>|` for temp files in loops

In zsh, `noclobber` blocks `>` from overwriting existing files. Use `>|` in loops that write the same path.

## Notes:

- Results include file:line references
- All agents available in `/agents`
