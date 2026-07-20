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
doc or a review, and a self-contained HTML receipt to open or attach. The
receipt has an **Export CSV** button for the by-project table, and prints to a
clean PDF.

## What it reports

- **What you shipped** — files and lines touched, commits carrying that work,
  PRs opened.
- **By project** — sessions, active days, and each project's share of your
  total compute.
- **Framing for a manager** — how to present the above without overclaiming.

## What counts

The report's universe is **work you did with Claude Code**, mapped to the
project you did it on. Two consequences worth knowing before you read a number:

**Claude Code's own machinery isn't your work.** The agent's scratchpad, its
per-session tool output, and `~/.claude` are excluded. On a real 30-day corpus
that removed 82% of the raw "lines touched" figure — files Claude wrote to talk
to itself, which no one shipped.

**A project is where work landed, not where your shell was.** Sessions are
attributed to the projects their file operations touched (reads included —
reading a repo to answer a question is work in that repo), resolved to the git
root, or to the containing directory when it isn't a repo. Work outside a repo
still counts; it's named for its directory. Subagents share their parent's
session, so their work lands on the same project — there's no "delegated"
category, because delegation is a mechanism, not a kind of work.

Sessions that touched no files and didn't run in a repo — web searches, Slack
reads, dashboard queries — land in **Research & investigation (no project)**.
That row is often the biggest one. It's real work that genuinely has no home on
disk, and naming it beats inventing a project for it.

## Design notes

**No dollar figures, anywhere.** A cost computed from local token counts is
inferred, not measured, and won't match your actual bill. Presenting one
invites the "that can't be right" reaction that discredits everything else in
the report. Spend appears only as relative percentages.

**No invented "hours saved."** There's no baseline in local data to compute a
counterfactual from, and a fabricated multiplier undermines the real numbers
sitting next to it. The report deliberately leaves room for you to add
concrete wins by hand — those land better than any aggregate anyway.

**No breakdown of spend by activity.** "38% of your compute went to reading
code" is the chart everyone wants and the data can't support. A turn's cost is
~90% context handling, half of it re-reading what earlier turns added, so
charging it to whichever tool fired that turn is a modeling choice rather than
a measurement — and the choice decides the answer. On one real month, three
equally defensible weightings put web search at 11%, 28% or 51%. Spend appears
once, per project, where it divides a real quantity by a real fact and the
ranking holds whichever weighting you pick.

**Careful claims.** Commits are counted only when they were authored under the
identity git uses in that repo *and* their changed files include something
Claude Code touched. Both tests have to pass, which is what keeps a snapshot
cron out — it commits under your name but never touches the files Claude
edited — while still counting the commit you made by hand after Claude wrote
the code. The gap it leaves: a repo configured with a *shared* identity (a
release bot's, say) makes that bot "you" for that repo, so a bot commit
touching a file Claude also edited would count. Rare, and the alternative —
reading only your global identity — silently zeroes the commit count for
anyone using git's standard `includeIf` work/personal split, which is far more
common.

Lines are "touched", not "written". Sessions, active days and commits are all
marked as columns that don't sum: a session spanning two projects is genuinely
in both, and worktrees of one repo share commits.

## Privacy

Mining is a local Node script — file I/O and `git`, no network calls.

It reads `~/.claude/projects/**/*.jsonl` — your own session history, already on
disk, all projects, for the window you ask for. To find out which of the
directories in there are repos, it runs `git rev-parse` in **every** directory
any session mentioned (on one real month, 152 of them), and in the ones that
are repos it also reads `user.email` and runs `git log`. All read-only, all
local.

The only thing that reaches the model is a small JSON summary: your name from
`git config user.name`, aggregate counts, and project names. Your email is read
but never emitted — it's used locally to match commit authorship. No code, no
conversation content, and no tool or MCP server names — the report has no
per-tool breakdown at all, so the list of services you've connected never
leaves the script.

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
