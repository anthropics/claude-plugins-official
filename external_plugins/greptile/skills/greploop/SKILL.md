---
name: greploop
description: >
  This skill should be used when the user wants to "optimize my PR", "get a perfect Greptile score",
  "fix all Greptile comments", "greploop", or iteratively improve a PR until Greptile gives 5/5
  confidence. Triggers Greptile review, fixes all actionable comments, pushes, re-triggers review,
  and repeats until the PR achieves a perfect score.
---

# Greploop

Iteratively fix a PR until Greptile gives a perfect review: 5/5 confidence, zero unresolved comments.

## Inputs

- **PR number** (optional): If not provided, detect the PR for the current branch.

## Instructions

### 1. Identify the PR

```bash
gh pr view --json number,headRefName -q '{number: .number, branch: .headRefName}'
```

Switch to the PR branch if not already on it.

### 2. Loop

Repeat the following cycle. **Max 5 iterations** to avoid runaway loops.

#### A. Trigger Greptile review

Push the latest changes (if any) and wait for Greptile's review check to appear:

```bash
git push
```

Then poll for the Greptile check to complete:

```bash
gh pr checks <PR_NUMBER> --watch
```

#### B. Fetch Greptile review results

Get the latest review from Greptile:

```bash
gh api repos/{owner}/{repo}/pulls/<PR_NUMBER>/reviews
```

Look for the most recent review from `greptile-apps[bot]` or `greptile-apps-staging[bot]`.

Parse the review body for:
- **Confidence score**: Greptile includes a score like `3/5` or `5/5` in its review summary.
- **Comment count**: Number of inline review comments.

Also fetch all unresolved inline comments:

```bash
gh api repos/{owner}/{repo}/pulls/<PR_NUMBER>/comments
```

Filter to comments from Greptile that are on the latest commit.

#### C. Check exit conditions

Stop the loop if **any** of these are true:
- Confidence score is **5/5**  AND there are **zero unresolved comments**
- Max iterations reached (report current state)

#### D. Fix actionable comments

For each unresolved Greptile comment:

1. Read the file and understand the comment in context.
2. Determine if it's actionable (code change needed) or informational.
3. If actionable, make the fix.
4. If informational or a false positive, note it but still resolve the thread.

#### E. Resolve threads

Fetch unresolved review threads and resolve all that have been addressed (see [GraphQL reference](references/graphql-queries.md)):

```bash
gh api graphql -f query='
query($cursor: String) {
  repository(owner: "OWNER", name: "REPO") {
    pullRequest(number: PR_NUMBER) {
      reviewThreads(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          comments(first: 1) {
            nodes { body path author { login } }
          }
        }
      }
    }
  }
}'
```

Resolve addressed threads:

```bash
gh api graphql -f query='
mutation {
  t1: resolveReviewThread(input: {threadId: "ID1"}) { thread { isResolved } }
  t2: resolveReviewThread(input: {threadId: "ID2"}) { thread { isResolved } }
}'
```

#### F. Commit and push

```bash
git add -A
git commit -m "address greptile review feedback (greploop iteration N)"
git push
```

Then go back to step **A**.

### 3. Report

After exiting the loop, summarize:

| Field | Value |
|-------|-------|
| Iterations | N |
| Final confidence | X/5 |
| Comments resolved | N |
| Remaining comments | N (if any) |

If the loop exited due to max iterations, list any remaining unresolved comments and suggest next steps.

## Output format

```
Greploop complete.
  Iterations:    2
  Confidence:    5/5
  Resolved:      7 comments
  Remaining:     0
```

If not fully resolved:

```
Greploop stopped after 5 iterations.
  Confidence:    4/5
  Resolved:      12 comments
  Remaining:     2

Remaining issues:
  - src/auth.ts:45 — "Consider rate limiting this endpoint"
  - src/db.ts:112 — "Missing index on user_id column"
```
