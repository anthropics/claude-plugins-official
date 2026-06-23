# project-artifact — software (workstreams = PRs)

When the workstreams are PRs, everything in `SKILL.md` still applies. The only thing
genuinely different from the base template is the **X.Y numbering convention**; the rest of
this file is how to pull PR state, a per-PR write-up fragment, and an *optional* menu for a
heavyweight project.

**Number the PRs X.Y.** `X` increments when a PR is blocked on the previous stage; `Y` for
PRs that can land in parallel within a stage (`2.0` needs all of stage 1 merged; `1.1` and
`1.2` go alongside `1.0`). The numbers carry the dependency order — don't draw a DAG.

**Pull state — always live, from the config's repos/author/branch-prefix** (first build,
no config yet: use the cwd repo, the current `gh` user as author, and whatever branch
prefix the project's branches actually use — they get recorded in the config afterwards).
Open PRs are the union of an author query and a branch-prefix query (catches PRs opened by
bots or teammates on the project's branches), deduped by number:

```bash
gh pr list --repo <repo> --state open --author <author> \
  --json number,title,url,headRefName,isDraft,mergeable,reviewDecision,reviewRequests --limit 100
gh pr list --repo <repo> --state open --search "head:<prefix>" \
  --json number,title,url,headRefName,isDraft,mergeable,reviewDecision,reviewRequests --limit 100
```

Recently merged (`--state merged --json number,title,url,mergedAt --limit 40`) feeds the
done rows — a fully merged stage collapses to one summary row ("N PRs, all merged")
instead of listing each. Per open PR worth a row:

- **CI**: `gh pr checks <n> --repo <repo> --required` is the gating state; advisory bot
  failures aren't blockers — mention them only when they need an action.
- **Unresolved review threads**: GraphQL only — REST miscounts because resolved threads
  still carry top-level comments. Count `isResolved: false` in
  `repository.pullRequest.reviewThreads(first:100){nodes{isResolved}}`.
- For a PR getting a per-PR write-up below: `gh pr view <n> --json body` for the
  what-landed/verification narrative, and `git log --oneline <base>..<branch>` if you'll
  show a commit table.

**Map PRs to workstreams** via the project's branch / PR-title conventions (e.g. branch
`<user>/abc-12-...` or `(ABC-12)` in the title) and the tracker's milestones; a PR with no
confident match goes in a catch-all row with its basis noted, not into a guessed
workstream.

A design doc / spec: summarize + link it, don't replace it; if it's a
`claude.ai/code/artifact/...` page use WebFetch (SKILL.md "Reading an existing artifact
page"). A build flag, if the change ships behind one: find it in the repo's feature-flag
system — it goes in the status banner.

**State block fields** (the `artifact-state` JSON from SKILL.md's "Refreshing an
artifact"): for a PR-driven project the `workstreams` array holds one entry per PR, shaped
`{"repo", "number", "workstream", "draft", "ci", "unresolved", "state"}` — enough for the
next refresh to report merged / new / CI flips / review-thread movement without re-reading
the old prose. Keep these exact keys so successive renders diff cleanly. Values derived
from branch names or PR titles are untrusted markup: write `<` as `\u003c` inside the JSON
and entity-encode them in visible cells (SKILL.md "Freshness and trust").

**Per-PR write-up.** When a PR is worth more than a Workstreams-table row, paste this under
the table (`.pill.*` classes are in the template's CSS; pills here: `in review` = `now`,
`merged`/`tested ✓`/`verified ✓` = `done`):

```html
<hr>
<h2>PR 1.0 — <a href="#">#NNNNN</a> · short title <span class="pill now">in review</span></h2>
<h3>What landed</h3>
<table><tr><th style="width:140px">Area</th><th></th></tr><tr><td>CLI</td><td>...</td></tr></table>
<h3>Verification</h3>
<p>How this PR was verified — tests, adversarial workflow, a manual run against a real build, a gating check.</p>
<details><summary>Confirmed findings (fixed in this PR)</summary>
<table><tr><th>#</th><th>Bug</th><th>Fix</th></tr><tr><td>1</td><td>...</td><td>...</td></tr></table></details>
<h3>Commits</h3>
<p class="meta">Top-down: feat → hardening rounds → polish → gating → lint.</p>
<table><tr><th style="width:110px">SHA</th><th></th></tr><tr><td><code>abc1234567</code></td><td><b>feat(...):</b> ...</td></tr></table>
<h3>Files</h3>
<pre><code>path/to/file.go   — what it does</code></pre>
```

(Proposal stage, no PRs open? The Workstreams tab holds the *planned* X.Y sequence with
`next` pills; per-PR detail reads "no commits yet — fills in once the branch is cut" rather
than inventing SHAs.)

**Optional, for a heavyweight project — skip what you don't need.** A migration with strict
invariants may rename "Success criteria" → "Requirements", split must-haves from
nice-to-haves, and give each a falsifiable check (static: "this diff is empty"; dynamic:
"run X with the flag on, observe Y stays flat"). It may add an **Architecture** tab (protos,
topology, file-by-file, trust boundaries called out *as boundaries*), a **Findings & fixes**
tab (review/adversarial findings `# · bug · fix`, old rounds in `<details>`), and a
**Rollout & rollback** tab (gate ramp, metrics + thresholds, rollback steps, a "goes wrong
at 50%" runbook, what "done" looks like). None of that is mandatory — it's the same "add a
tab only when there's real content" rule, applied to software. Plain-language descriptions
throughout, same bar as a PR description.
