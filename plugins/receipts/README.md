# Receipts

Generate a personal Claude Code impact report — "receipts" — from your own
session transcripts, for the conversation where someone asks what all this
Claude Code usage is actually buying.

```
/receipts            # last 30 days (default)
/receipts week       # last 7 days
/receipts quarter    # last 90 days
/receipts 14         # last 14 days
/receipts for myrepo # scope to one project
```

You get two files in your home directory: a markdown report to paste into a
doc or a review, and a self-contained HTML receipt to open or attach.

## What it reports

- **What you shipped** — files and lines touched, commits in the projects you
  used Claude Code in, PRs opened.
- **By repo** — sessions, active days, and each project's share of your total
  compute.
- **Where the spend went** — a relative split across writing code, reading and
  research, running and verifying, delegated work, and collaboration.
- **Framing for a manager** — how to present the above without overclaiming.

## Design notes

**No dollar figures, anywhere.** A cost computed from local token counts is
inferred, not measured, and won't match your actual bill. Presenting one
invites the "that can't be right" reaction that discredits everything else in
the report. Spend appears only as relative percentages.

**No invented "hours saved."** There's no baseline in local data to compute a
counterfactual from, and a fabricated multiplier undermines the real numbers
sitting next to it. The report deliberately leaves room for you to add
concrete wins by hand — those land better than any aggregate anyway.

**Careful claims.** Commit counts are labeled as commits in projects where
Claude Code was active, not commits made *by* Claude Code. Lines are "touched",
not "written". Worktrees sharing a `.git` are de-duplicated by commit SHA and
footnoted where they may still overlap.

## Privacy

Mining is a local Node script — file I/O and `git log`, no network calls. It
reads only `~/.claude/projects/**/*.jsonl`, which is your own session history
already on disk, and shells out to `git` in the repos that appear there to
cross-reference commits.

The only thing that reaches the model is a small JSON summary: your name from
`git config`, aggregate counts, and repo directory names. No code, no
conversation content, and no tool or MCP server names — tool calls are grouped
into five activity categories during mining, so the list of services you've
connected never leaves the script.

The report is written to your disk and published nowhere unless you explicitly
ask for a shareable version. Because repo names appear verbatim, the skill
lists them before you send the report anywhere.

## Relationship to `session-report`

Both plugins read the same transcripts, and that's about where the similarity
ends.

[`session-report`](../session-report) is a tuning tool. It asks *where am I
wasting tokens* — cache hit rates, disproportionate projects, expensive
prompts — and its output is a list of optimizations. The audience is you, and
the goal is to drive usage down.

`receipts` is a justification tool. It asks *was this worth it* — what shipped,
in which repos, against what spend — and cross-references local git history to
tie usage to output. The audience is your manager, and the goal is to defend
the spend rather than trim it.

Install `session-report` to make your usage cheaper. Install `receipts` to
explain why it was worth paying for.
