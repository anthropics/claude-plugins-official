---
name: receipts
description: Generate a personal Claude Code usage & impact report ("receipts") from this machine's local session transcripts — for justifying Claude Code usage/spend to a manager, self-review, or "what have I been using this for" check-ins. Mines ~/.claude/projects locally (no extra API calls beyond one final write-up), cross-references local git history, and writes a markdown report plus a self-contained HTML receipt to your home directory. Use when the user asks for "receipts", an "impact report", "usage report", wants to "show my Claude Code activity", "prove the value of Claude Code", or runs `/receipts`.
---

# /receipts — personal Claude Code impact report

Generates a markdown report of one developer's own Claude Code activity,
built entirely from local data:

- **Source data**: this machine's session transcripts at `~/.claude/projects/**/*.jsonl`
  (every session, every project, already on disk — nothing to set up).
- **Cost**: the mining step is a local Node script — file I/O + regex, zero
  API calls. The only model call is one final write-up over a small (~10-20KB)
  JSON summary, regardless of how much history was scanned.
- **Cross-reference**: local `git log` per repo (no network) to sanity-check
  commit activity against CC session activity.

## Step 1 — figure out the period

Parse `$ARGUMENTS`:
- "week" → 7, "month" → 30 (default if nothing given), "quarter" → 90, "year" → 365
- a bare number → that many days
- a repo name/substring (e.g. "for anthropic") → pass through as `--repo <substr>`

## Step 2 — run the miner

The script `mine-transcripts.mjs` ships alongside this SKILL.md, under
`scripts/`. Use its absolute path:

```bash
node <skill-dir>/scripts/mine-transcripts.mjs --days <N> [--repo <substr>] --html /tmp/cc-receipt.html
```

Use that fixed temp path — the real `since`/`until` are computed by the script
and only known once it has run, so don't try to put them in this filename.
Steps 4 and 5 name the final files, by which point the JSON has the dates.

This prints one JSON object to stdout **and** writes a self-contained, styled
HTML "receipt" to the `--html` path — built deterministically from the same
data (no extra model cost). **Do not** separately Read any `*.jsonl`
transcript files — the script has already extracted everything relevant.
Re-reading raw transcripts would burn a huge number of tokens for no benefit.

If `--days` is large (90+), the script can take 10-25s; for `--days 365` it
can take a minute or more since it reads every transcript file in the
window. That's fine — it's local CPU time, not API spend — but warn the user
up front for "year"-scale requests so a long pause isn't surprising.

The JSON shape:
```jsonc
{
  "generatedAt": "2026-06-08T17:04:22.000Z",  // when this run happened
  "userName": "Ada Lovelace" | null,  // from `git config --global user.name`, for personalizing the receipt
  "since": "2026-03-10", "until": "2026-06-08", "periodDays": 90,
  // How much was read to build this — provenance, not an achievement. Don't
  // put these in the report; they are not sessions and not files touched.
  "filesScanned": 189, "linesScanned": 36536,
  "totals": {
    "sessions": 199, "prompts": 918, "activeDays": 20, "calendarDays": 90,
    "filesTouched": 320, "linesTouched": 55126,
    "gitCommitCmds": 164, "prCreateCmds": 14,
    // gitCommitsByYou is de-duplicated by commit SHA across all repos (matters
    // for monorepo worktrees that share history). gitActiveDayOverlap is how
    // many of `activeDays` also had >=1 of those commits.
    "gitCommitsByYou": N | null, "gitActiveDayOverlap": N | null,
    // Relative cost weight per activity category — unitless (NOT dollars).
    // output tokens count ~5x input, cache writes ~1.25x, cache reads ~0.1x
    // (ratios from published per-token pricing, used only as relative
    // weights). Normalize to percentages for the report — see Step 3.
    // These five keys are the complete set — raw tool names are never emitted.
    "categoryCost": {
      "Writing & editing code": 1234.5, "Reading & research": 5678.9,
      "Running & verifying (shell)": 2345.6, "Delegated / automated work": 456.7,
      "Collaboration (Slack, email, docs, etc.)": 12.3
    }
  },
  // Top 12 repos by pctSpend, already ordered biggest-first. Everything else
  // — plus anything with no output and a negligible share of spend — rolls
  // into an "(other repos)" entry, whose activeDays and gitCommitsByYou are
  // unions (de-duplicated), not sums.
  "byRepo": {
    "<repo-name>": {
      "sessions": N, "prompts": N, "activeDays": N,
      "filesTouched": N, "linesTouched": N,
      "gitCommitCmds": N, "prCreateCmds": N,
      "gitCommitsByYou": N | null,        // commits by this git identity, this repo — NOT
                                           // de-duplicated against other repos (see sharedGitHistory)
      "gitActiveDayOverlap": N | null,    // days with both a CC session and a commit, this repo
      "sharedGitHistory": true | undefined // present+true if this repo shares a .git with
                                           // another repo in byRepo (worktrees) — its
                                           // gitCommitsByYou may double-count commits also
                                           // attributed to that other repo
      "pctSpend": 23.4   // this repo's share of total relative compute (see categoryCost
                          // above) — percentages across ALL repos, including ones rolled
                          // into "(other repos)", sum to ~100
    }
  }
}
```

**No dollar figures, anywhere.** Any $-cost computed from local token counts
would be inferred, not measured, and won't match the dev's actual bill —
presenting it as a number invites exactly the "that can't be right" reaction
that undermines the rest of the report. `categoryCost` exists only to show
the *relative* split of compute across activity types (as percentages) — see
"Where the spend went" in Step 3. Never sum it into a total or attach a `$`.

## Step 3 — write the report (one model call, from the JSON only)

Write a markdown report with this structure:

### Header
If `userName` is set, lead with it (e.g. "# Ada Lovelace's Claude Code Receipt"
or similar — keep it natural, this is for them). Period covered (`since` –
`until`), active days vs calendar days (e.g. "active on 20 of 90 days"), total
sessions, total prompts.

### What you shipped
- Distinct files touched, approximate lines touched (label this **"lines
  touched (approx.)"** — it's the size of edited regions, not a net diff, so
  don't call it "lines of code written")
- `totals.gitCommitsByYou` as "git commits in projects you used Claude Code
  in this period" — **don't call these "commits made with Claude Code"**,
  they're just commits by this git identity in repos where CC was also
  active. Use `totals.gitActiveDayOverlap` to qualify it: "N of your M active
  days also had a git commit in one of these projects."
- **Sanity-check the commit count before you print it.** It comes from `git
  log --author=<the repo's configured email>`, which counts anything committed
  under that identity — including commits a machine made on the dev's behalf.
  A snapshot cron, an auto-formatter, a sync job or a release bot committing
  as the dev will pile up hundreds or thousands of commits that no manager
  would credit as work, and one such repo can dwarf every real commit in the
  report. Divide each repo's `gitCommitsByYou` by its `activeDays`: a rate
  that couldn't plausibly be hand-authored (say, dozens per day, or commits in
  a repo with almost no sessions) means automation. When you see one, say so
  in place of the number — name the repo, give the headline count excluding
  it, and let the dev confirm. **A visibly absurd commit count discredits the
  whole receipt**, which is the one thing this report cannot afford.
- `prCreateCmds` as "PRs opened via Claude Code" (only if > 0) — note this
  counts `gh pr create` invocations, not confirmed successful PR creations.

### By repo
A small table of the repos in `byRepo`, which the miner has already picked and
ordered — the top 12 by share of spend, biggest first. Keep that order; don't
re-sort. Columns: repo, sessions, active days,
files touched, lines touched, commits, and `pctSpend` as a "% Spend" column
(round to whole percent; show "<1%" rather than "0%" for small nonzero
values). Roll anything in `(other repos)` into a single "everything else" row
— sum its `pctSpend` into that row too, same as the other numeric columns.

For the commits column, per repo:
- If `gitCommitsByYou` is non-null, show it. If `sharedGitHistory` is true on
  that repo, add a footnote that this repo shares commit history with another
  repo in the table (worktrees of the same checkout) so the per-repo numbers
  may overlap — the report-wide total (`totals.gitCommitsByYou`) is already
  de-duplicated by commit SHA, so don't re-sum the per-repo column into a new
  total.
- If `gitCommitsByYou` is null but `gitCommitCmds > 0`, show `~N` (from
  `gitCommitCmds`) with a footnote that git history wasn't available to verify
  (e.g. no git identity configured in that repo) so this is based on `git
  commit` commands run, not confirmed commits.
- Otherwise show `–`.

### Where the spend went
`totals.categoryCost` is already bucketed into five human categories (Writing
& editing code, Reading & research, Running & verifying (shell), Delegated /
automated work, Collaboration) — the miner groups tool calls on purpose and
never emits raw tool names, so this field is the only view of them you get.
There is no separate "thinking" bucket: a turn with no tool calls folds into
the activity it was wrapping up.

Normalize the values to percentages of their sum and show one line per
category with a non-zero share, largest first. This is a *relative* split of
compute by activity type — weighted so that output-heavy turns (writing code,
long responses) count more than read-heavy/cached turns, which is closer to
where the underlying compute actually went than a raw tool-call count would
be. **Do not convert this to a dollar figure** — show percentages only. Don't
title this section around "time" — the report is about justifying spend, just
not in dollar terms.

### Framing for a manager
2-3 sentences, in the dev's own voice, suggesting how to present this:
- Lead with shipped output (files/commits/PRs), not activity volume — activity
  counts are evidence of engagement, not impact on their own.
- Note that this report is self-reported and built from local data on one
  machine. If the dev's organization publishes its own verified engineering
  metrics, cite those for the headline numbers and use this report as the
  personal, immediate-feedback complement.
- Prompt the dev to add one or two concrete wins by hand (a specific
  incident, migration, or feature this period) — qualitative "this took 20
  minutes instead of a day" stories land better than any aggregate stat.

**Do not** invent "hours saved" or dollar-value-created numbers — there's no
reliable baseline to compute them from local data, and a fabricated multiplier
undermines the credibility of the rest of the report.

## Step 4 — save the markdown

Write the report to `~/claude-code-receipts-<since>-to-<until>.md`, taking
`<since>` and `<until>` from the JSON — not from your own date arithmetic.

## Step 5 — save the HTML receipt locally

Copy `/tmp/cc-receipt.html` (from Step 2) to
`~/claude-code-receipts-<since>-to-<until>.html`, same dates as Step 4. It is
self-contained (no external resources), so the user can open it straight from
disk — `open ~/claude-code-receipts-...html` on macOS, `xdg-open` on Linux.

Then list the project names that appear in `byRepo` in one line — "this
receipt names: X, Y, Z". These are repo directory names, reproduced verbatim
in the report, and may include internal codenames, client names, or
unannounced projects. The user is about to send this to a manager or paste it
into a review doc, so they should know what is in it before it travels. Don't
block on this — just surface it. If something shouldn't be there, they can
re-run Step 2 with `--repo` to scope to one project, or edit the HTML by hand.

**Do not publish the receipt anywhere by default.** It stays on the user's
disk unless they explicitly ask for a hosted or shareable version. If they do
ask, and the `Artifact` tool is available in the environment, call it on the
HTML file with `favicon: "🧾"` and a label like
`"receipt-<since>-to-<until>"` — but only on request, after they have seen the
project-name list above.

## Step 6 — wrap up

Tell the user where both outputs live: the `.md` for pasting into docs or
chat, the `.html` for a polished view to open or attach. Confirm what did and
didn't leave the machine — the mining step is pure local file and `git`
parsing with no network calls, and the only thing sent to the model is the
small JSON summary used to write the markdown: their name, aggregate counts
and repo names, with no code, no conversation content, and no tool or MCP
server names.
