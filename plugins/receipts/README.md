# Receipts

Generate a personal Claude Code impact report — "receipts" — from your own
session transcripts, for the conversation where someone asks what all this
Claude Code usage is actually buying.

<img src="assets/sample-receipt.png" width="400"
  alt="A printed-receipt-styled report headed 'Claude Code — usage receipt, Morgan Lunt', covering 2026-06-21 to 2026-07-20, active on 28 of 30 days. It lists 40 sessions, 64 prompts, 14 files touched, 3,120 lines touched, 12 commits carrying that work and 7 PRs opened, headlined as 19 commits and PRs shipped. A by-project table gives 'Research and investigation (no project)' 53% of spend with no files touched, then acme-api 29%, acme-web 10%, billing-service 5%, infra-terraform 3%, and a plain ~/notes directory 1%. Footnotes explain which columns do not sum, and an Export CSV button sits above a barcode.">

*Sample output — the projects and numbers are invented. It's rendered from a
synthetic corpus, not from anyone's real usage.*

## Install

```
/plugin install receipts@claude-plugins-official
```

## Use

```
/receipts            # last 30 days (default)
/receipts week       # last 7 days
/receipts quarter    # last 90 days
/receipts 14         # last 14 days
/receipts for myrepo # scope to one project
```

Two files land in your home directory: a markdown report to paste into a doc or
a review, and a self-contained HTML receipt to open or attach. The receipt has
an **Export CSV** button and prints to a clean PDF. Nothing is published
anywhere.

Takes a few seconds — about 1s for a week, 5s for a year.

## What you get

- **What you shipped** — files and lines touched, commits carrying that work,
  PRs opened.
- **By project** — sessions, active days, and each project's share of your
  usage. Work outside a repo is named for its directory; sessions that touched
  no files at all (web searches, chat tools, dashboards) show as
  *Research & investigation (no project)*, which for a lot of people is the
  biggest row.
- **Framing for a manager** — how to present the above without overclaiming.

A few things the report deliberately won't tell you: no dollar figures, no
"hours saved", and no breakdown of spend by activity. Each of those would be a
guess dressed up as a measurement, and one bad number discredits the rest of
the page. What's left is meant to survive someone pushing back on it.

## Privacy

Everything is read locally — file I/O and read-only `git`, no network calls.

It reads `~/.claude/projects/**/*.jsonl`, your own session history, already on
disk. To work out which of the directories mentioned there are git repos, it
runs `git rev-parse` in each of them, and in the ones that are, reads
`user.email` and runs `git log`.

The only thing that reaches the model is a small summary: your name from
`git config`, aggregate counts, and project names. No code, no conversation
content, and no tool or MCP server names — so the list of services you've
connected never leaves your machine. Your email is used locally to match commit
authorship and is never sent.

Project names appear verbatim in the report, so the skill reads them back to
you before you send it anywhere. Use `/receipts for <project>` to scope it down.

## Which plugin do I want?

[`session-report`](../session-report) reads the same transcripts to answer
*where am I wasting tokens* — cache hit rates, expensive prompts — and hands
you a list of optimizations. Install it to make your usage cheaper.

`receipts` answers *was this worth it* — what shipped, in which projects,
against what spend. Install it to explain why the usage was worth paying for.
