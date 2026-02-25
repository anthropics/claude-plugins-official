---
description: "Comprehensive PR review using specialized agents"
argument-hint: "[review-aspects]"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Task"]
---

# Comprehensive PR Review

Run a comprehensive pull request review using multiple specialized agents, each focusing on a different aspect of code quality.

**Review Aspects (optional):** "$ARGUMENTS"

## Review Workflow:

### Step 1: Determine Review Context and Gather All Data (CRITICAL)

**You MUST complete this entire step before launching any agents. Do NOT delegate data fetching to agents.**

First, detect whether you are reviewing a PR or local changes. Run this command **alone** (not in parallel with other commands):

```bash
gh pr view --json number,title,body,headRefName,baseRefName,files 2>/dev/null
```

- **If the command succeeds**: You are in **PR mode**. Store the PR number, title, body, base branch, and file list.
- **If the command fails (exit code 1)**: This is expected — you are in **local mode**, reviewing uncommitted local changes.

Then, **after** determining the mode, fetch the diff and changed file list:

- **PR mode**: Run `gh pr diff <number>` and `gh pr diff <number> --name-only`
- **Local mode**: Run `git diff` (for unstaged) and/or `git diff --cached` (for staged), plus `git diff --name-only` and/or `git diff --cached --name-only`

Finally, use the Read tool to read the full contents of each changed file.

Store all of this data — you will pass it to agents in the next steps.

### Step 2: Parse Arguments and Determine Applicable Reviews

**Available Review Aspects:**

- **comments** - Analyze code comment accuracy and maintainability (agent: comment-analyzer)
- **tests** - Review test coverage quality and completeness (agent: pr-test-analyzer)
- **errors** - Check error handling for silent failures (agent: silent-failure-hunter)
- **types** - Analyze type design and invariants (agent: type-design-analyzer)
- **code** - General code review for project guidelines (agent: code-reviewer)
- **simplify** - Simplify code for clarity and maintainability (agent: code-simplifier)
- **all** - Run all applicable reviews (default)

If the user specified aspects, only run those. Otherwise determine applicability based on the changes:

- **Always run**: code-reviewer (general quality)
- **If test files changed**: pr-test-analyzer
- **If comments/docs added or modified**: comment-analyzer
- **If error handling code changed** (try/catch, error callbacks, Result types): silent-failure-hunter
- **If types/interfaces/classes added or modified**: type-design-analyzer
- **After other reviews pass**: code-simplifier (polish and refine)

### Step 3: Launch Review Agents With Pre-fetched Context

**IMPORTANT: When launching each agent via the Task tool, include the diff and relevant file contents directly in the agent's prompt.** This prevents agents from redundantly fetching the same data.

Structure each agent's Task prompt like this:

```
Review the following changes for [aspect].

## Changed Files
<list of changed file paths>

## Diff
<the full diff output, or the relevant portion for this agent>

## File Contents
<full contents of each changed file relevant to this agent's review>

## PR Context (if in PR mode)
Title: <pr title>
Description: <pr body>
```

**Parallelism rules:**
- Launch all applicable review agents in parallel since data is pre-fetched and agents will not duplicate work.
- The code-simplifier is the only exception — it should always run last, after other reviews complete.

### Step 4: Aggregate Results

After all agents complete, provide a unified summary:

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

**All reviews (explicit):**
```
/pr-review-toolkit:review-pr all
# Runs all applicable reviews in parallel
```

## Agent Descriptions:

**code-reviewer**:
- Checks CLAUDE.md compliance
- Detects bugs and issues
- Reviews general code quality

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

**code-simplifier**:
- Simplifies complex code
- Improves clarity and readability
- Applies project standards
- Preserves functionality

## Tips:

- **Run early**: Before creating PR, not after
- **Focus on changes**: Agents analyze the diff you provide, not the whole repo
- **Address critical first**: Fix high-priority issues before lower priority
- **Re-run after fixes**: Verify issues are resolved
- **Use specific reviews**: Target specific aspects when you know the concern
