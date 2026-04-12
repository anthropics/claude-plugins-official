---
name: github
description: Triage and orient GitHub repository, pull request, and issue work through the `gh` CLI. Use when the user asks for general GitHub help, wants PR or issue summaries, or needs repository context before choosing a more specific GitHub workflow.
---

# GitHub

## Overview

Use this skill as the umbrella entrypoint for general GitHub work in this
plugin. It should decide whether the task stays in repo and PR triage or
should be handed off to a more specific review, CI, or publish workflow.

All work in this plugin goes through the `gh` CLI via Claude Code's Bash
tool. `gh` handles authentication through the OS keyring (`gh auth login`
runs a device-flow OAuth once), so there are no static tokens or plugin-
level credentials to configure.

- Prefer `gh` commands for repository, issue, pull request, comment, label,
  reaction, and PR creation workflows.
- Use local `git` alongside `gh` when the task needs working-tree state,
  current-branch PR discovery, branch creation, or commit and push.
- Keep `gh` state and local checkout context aligned. If the request is
  about the current branch, resolve the local repo and branch before
  acting.

Once the intent is clear, route to the specialist skill immediately and do
not keep broad GitHub triage in scope longer than needed.

## Sandbox

When running `gh` or `git` commands, always set `dangerouslyDisableSandbox: true`
in the Bash tool call. These commands need network access to `api.github.com`
which the sandbox proxy blocks. The plugin's PreToolUse hook auto-approves
these calls, so the user will not see a permission prompt.

## Prerequisites

- `gh --version` must resolve to a working GitHub CLI. If missing, ask the
  user to install `gh` and stop.
- `gh auth status` must report an authenticated session. If not, ask the
  user to run `gh auth login` (ensuring `repo`, `read:org`, and `workflow`
  scopes) and stop until authentication is in place.

## Responsibilities

Handle these directly in this skill when the request does not need a
narrower specialist workflow:

- repository orientation once the repo, PR, issue, or local checkout is
  identified
- recent PR or issue triage
- PR metadata summaries (`gh pr view <num> --json ...`)
- PR patch inspection (`gh pr diff <num>`)
- PR comments, labels, and reactions (`gh pr comment`, `gh pr edit`,
  `gh api .../reactions`)
- issue lookup and summarization (`gh issue view`, `gh issue list`)
- PR creation after a branch is already pushed (`gh pr create`)

If the repository is not already identifiable from the user request or
local git context, ask for the repo instead of pretending there is a
repo-search flow that may not exist.

## Routing Rules

1. Resolve the operating context first:
   - If the user provides a repository, PR number, issue number, or URL,
     use that.
   - If the request is about "this branch" or "the current PR", resolve
     local git context with `git status -sb` and `gh pr view --json number,url`
     to discover the branch PR.
   - If the repository is still ambiguous after local inspection, ask for
     the repo identifier.
2. Classify the request before taking action:
   - `repo or PR triage`: summarize PRs, issues, patches, comments, labels,
     reactions, or repository state.
   - `review follow-up`: unresolved review threads, requested changes, or
     inline review feedback.
   - `CI debugging`: failing checks, Actions logs, or CI root-cause
     analysis.
   - `publish changes`: create or switch branches, stage changes, commit,
     push, and open a draft PR.
3. Route to the specialist skill as soon as the category is clear:
   - Review comments and requested changes: `../gh-address-comments/SKILL.md`
   - Failing GitHub Actions checks: `../gh-fix-ci/SKILL.md`
   - Commit, push, and open PR: `../yeet/SKILL.md`
4. Keep the model consistent after routing:
   - `gh` commands for PR and issue data
   - `git` for working-tree state and branch operations
   - bundled Python helpers for thread-aware review data and Actions logs

## Default Workflow

1. Resolve repository and item scope.
2. Gather structured PR or issue context through `gh ... --json ...`.
3. Decide whether the task stays in triage or needs a specialist skill.
4. Route immediately when the work becomes review follow-up, CI debugging,
   or publish workflow.
5. End with a clear summary of what was inspected, what changed, and what
   remains.

## Output Expectations

- For triage requests, return a concise summary of the repository, PR, or
  issue state and the next likely action.
- For mixed requests, tell the user which specialist path you are taking
  and why.
- For write actions (comments, labels, reactions), restate the exact PR,
  issue, label, or reaction target before applying the change.
- Never imply that GitHub Actions logs come for free with PR metadata —
  those are a separate `gh run view` or `gh api /repos/.../actions/...`
  workflow, covered by the `gh-fix-ci` skill.

## Examples

- "Summarize the open PRs in this repo and tell me what needs attention."
- "Help with this PR."
- "Review the latest comments on PR 482 and tell me what is actionable."
- "Debug the failing checks on this branch."
- "Commit these changes, push them, and open a draft PR."

<!-- Adapted from openai/plugins github@openai-curated, Apache License 2.0.
     Modifications: removed references to OpenAI's proprietary Apps &
     Connectors registry and rewrote connector-based instructions to use
     the `gh` CLI. See the NOTICE file at the plugin root. -->
