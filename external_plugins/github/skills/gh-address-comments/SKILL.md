---
name: gh-address-comments
description: Address actionable GitHub pull request review feedback. Use when the user wants to inspect unresolved review threads, requested changes, or inline review comments on a PR, then implement selected fixes. Uses `gh` for PR metadata and a bundled GraphQL script via `gh api graphql` for thread-aware review data.
---

# GitHub PR Comment Handler

Use this skill when the user wants to work through requested changes on a
GitHub pull request. All PR metadata and patch context come from `gh pr view`
and `gh pr diff`. Thread-aware review data (unresolved threads, inline
review locations, resolution state, `isResolved`/`isOutdated` flags, and
file/line anchors) goes through the bundled `scripts/fetch_comments.py`,
which queries the GitHub GraphQL API via `gh api graphql`.

## Sandbox

When running `gh`, `git`, or bundled Python helper commands, always set
`dangerouslyDisableSandbox: true` in the Bash tool call. These commands need
network access to `api.github.com` which the sandbox proxy blocks. The plugin's
PreToolUse hook auto-approves these calls, so the user will not see a permission
prompt.

Run all `gh` commands with elevated network access. If CLI auth is required,
confirm `gh auth status` first and ask the user to authenticate with
`gh auth login` if it fails.

## Workflow

1. Resolve the PR.
   - If the user provides a repository and PR number or URL, use that
     directly.
   - If the request is about the current branch PR, use local git context
     plus `gh auth status` and `gh pr view --json number,url` to resolve
     it.
2. Inspect review context with thread-aware reads.
   - Use `gh pr view <pr> --json title,body,author,state,reviewDecision,headRefName,baseRefName`
     to fetch PR metadata.
   - Use `gh pr diff <pr>` to fetch patch context when the repo and PR
     are known.
   - Use the bundled `scripts/fetch_comments.py` workflow whenever the
     task depends on unresolved review threads, inline review locations,
     or resolution state. That script fetches `reviewThreads`,
     `isResolved`, `isOutdated`, and file and line anchors that flat PR
     comment reads do not preserve.
   - Use `gh pr view <pr> --comments` only for lightweight top-level PR
     comment summaries when thread-level state does not matter.
3. Cluster actionable review threads.
   - Group comments by file or behavior area.
   - Separate actionable change requests from informational comments,
     approvals, already-resolved threads, and duplicates.
4. Confirm scope before editing.
   - Present numbered actionable threads with a one-line summary of the
     required change.
   - If the user did not ask to fix everything, ask which threads to
     address.
   - If the user asks to fix everything, interpret that as all unresolved
     actionable threads and call out anything ambiguous.
5. Implement the selected fixes locally.
   - Keep each code change traceable back to the thread or feedback
     cluster it addresses.
   - If a comment calls for explanation rather than code, draft the
     response rather than forcing a code change.
6. Summarize the result.
   - List which threads were addressed, which were intentionally left
     open, and what tests or checks support the change.

## Bundled Resources

### scripts/fetch_comments.py

Fetch all PR conversation comments, reviews, and inline review threads
(including `isResolved` / `isOutdated` / `path` / `line` / `diffSide`
metadata) for the PR associated with the current git branch. Uses
`gh api graphql` under the hood — no extra auth beyond `gh auth login`.

Usage:

```sh
python "<path-to-skill>/scripts/fetch_comments.py" > pr_comments.json
```

The script resolves the current branch's PR via
`gh pr view --json number,headRepositoryOwner,headRepository`, handles
cross-repo PRs, and paginates through `comments`, `reviews`, and
`reviewThreads`.

## Write Safety

- Do not reply on GitHub, resolve review threads, or submit a review
  unless the user explicitly asks for that write action.
- If review comments conflict with each other or would cause a behavioral
  regression, surface the tradeoff before making changes.
- If a comment is ambiguous, ask for clarification or draft a proposed
  response instead of guessing.
- Do not treat flat PR comments (`gh pr view --comments`) as a complete
  representation of review-thread state — always use `fetch_comments.py`
  when resolution state matters.
- If `gh` hits auth or rate-limit issues mid-run, ask the user to
  re-authenticate and retry.

## Fallback

If `gh` cannot resolve the PR cleanly, tell the user whether the blocker
is missing repository scope, missing PR context, or CLI authentication,
then ask for the missing repo or PR identifier or for a refreshed `gh`
login.

<!-- Adapted from openai/plugins github@openai-curated, Apache License 2.0.
     Modifications: removed "GitHub app from this plugin" / connector
     references and rewrote the PR metadata and flat-comment reads to go
     exclusively through `gh pr view` / `gh pr diff`. The bundled
     GraphQL script was already `gh api graphql`-based and is included
     unchanged. See the NOTICE file at the plugin root. -->
