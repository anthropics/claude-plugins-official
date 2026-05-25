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

4. **Migration Timestamp Preflight (deterministic check, always run)**

   If the PR adds any timestamped migration files, verify their timestamps land **after** the latest migration on `origin/main`. Out-of-order timestamps are a common merge hazard: the new migration's prefix is older than a migration already on main, so it can be skipped, applied out of order, or rejected depending on the tool (Supabase, Rails, Knex, Prisma, Flyway, golang-migrate, sqlx, Liquibase, etc).

   Steps:

   1. Refresh main: `git fetch origin main`
   2. Find migrations added in the PR. Common patterns:
      - `supabase/migrations/YYYYMMDDHHMMSS_*.sql`
      - `db/migrate/YYYYMMDDHHMMSS_*.rb` (Rails)
      - `migrations/YYYYMMDDHHMMSS_*.{sql,js,ts}` (Knex, golang-migrate, sqlx)
      - `prisma/migrations/YYYYMMDDHHMMSS_*/migration.sql`
      - `db/migrations/V<version>__*.sql` (Flyway)
      - `liquibase/changelog/*` with date-based identifiers

      ```bash
      git diff --name-only --diff-filter=A origin/main...HEAD | \
        grep -E '(supabase/migrations|db/migrate|prisma/migrations|^migrations/)'
      ```
   3. For each migration directory that has additions, find the highest existing timestamp on `origin/main`:
      ```bash
      git ls-tree -r --name-only origin/main -- <migration-dir>/ | \
        grep -oE '[0-9]{14}' | sort | tail -1
      ```
   4. Extract the timestamp prefix from each newly added migration and compare. **Fail the preflight** if any added migration's timestamp is `<=` the latest timestamp on `origin/main` for the same directory.
   5. Report findings as a **Critical Issue** in the final summary. Suggested remediation: rename the migration file (and any internal references, e.g. Prisma's directory name) to a fresh timestamp `> max(origin/main)`. For Rails, `bin/rails db:migrate:status` reveals out-of-order migrations; renaming and re-staging is the canonical fix.

   Examples of what to flag:
   - Added `supabase/migrations/20260101120000_add_x.sql` while `origin/main` already has `20260315090000_*.sql` → out of order.
   - Two added migrations on the branch share a prefix or sit between existing main timestamps.

   This is a **blocking** finding: surface it before agent-based reviews so the author can fix the rename in the same pass.

5. **Determine Applicable Reviews**

   Based on changes:
   - **Always applicable**: code-reviewer (general quality)
   - **If test files changed**: pr-test-analyzer
   - **If comments/docs added**: comment-analyzer
   - **If error handling changed**: silent-failure-hunter
   - **If types added/modified**: type-design-analyzer
   - **After passing review**: code-simplifier (polish and refine)

6. **Launch Review Agents**

   **Sequential approach** (one at a time):
   - Easier to understand and act on
   - Each report is complete before next
   - Good for interactive review

   **Parallel approach** (user can request):
   - Launch all agents simultaneously
   - Faster for comprehensive review
   - Results come back together

7. **Aggregate Results**

   After agents complete, summarize:
   - **Critical Issues** (must fix before merge)
   - **Important Issues** (should fix)
   - **Suggestions** (nice to have)
   - **Positive Observations** (what's good)

8. **Provide Action Plan**

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

## Notes:

- Agents run autonomously and return detailed reports
- Each agent focuses on its specialty for deep analysis
- Results are actionable with specific file:line references
- Agents use appropriate models for their complexity
- All agents available in `/agents` list
