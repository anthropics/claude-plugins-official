<!-- Audience: the Security Lead assembling a report from workflow findings, which writes CLAUDE-SECURITY-RESULTS.md as the delivery step of the scan job. Load this file only when a scan reaches delivery. -->

# CLAUDE-SECURITY-RESULTS.md — report spec

The markdown report is the one artifact written as prose rather than generated. It is what a human actually reads, so it is written for a specific reader: an engineer who owns this code, is busy, and will decide in about ninety seconds whether to act on each finding.

`render_report.py` generates the machine-readable companions from `findings.json` and `votes.json`. Do not hand-write the JSONL or the stamp, and do not restate the JSONL here — this file is the part a person reads.

## Shape

```markdown
# Claude Security results

<one paragraph: what was scanned (path, revision, mode, scope), when, at what
effort, and the headline: how many findings at what severities, or that there
were none.>

## Coverage

<what was examined and what was not. Name the components. If the scope was
narrowed, say to what and why. If a cap truncated anything -- unreviewed
candidates, a skipped oversized file -- say so here, plainly. Name every
area the scan deliberately did NOT examine, and WHY: each entry of
coverage.skippedComponents carries the paths left out and the componentizer's
one-line reason (vendored, generated, documentation, and the like); a
directory skipped on purpose is disclosure, not failure, so state the reason
rather than letting the area silently vanish. On a whole-repository scan the
workflow requires the inventory to account for every top-level directory --
scanned or explicitly skipped -- and coverage.completenessCheckOutcome says whether
that check ran: "checked" (say the whole tree is accounted for),
"partial" (the inventory left some top-level directories in neither ledger and
the answer was used as it stood -- coverage.unaccountedTopLevelDirs names them;
list every one and say plainly they were neither scanned nor skipped, because
that is exactly the coverage a "no findings" would otherwise overstate),
"not-checkable" (the tree's directory list was not supplied, was unreadable, or
was empty while the inventory named subdirectories -- coverage.topLevelRejected
says which; say plainly that completeness could NOT be checked, since that is
what turns "no findings" into "clean" rather than "not examined"), or
"not-applicable" (a diff, commit, or scoped scan, whose target
is the change or the scope, or a low-effort run with no inventory). If
coverage.inventoryFallback is set, the inventory's partition was not used and
the whole tree was read as one component instead of the matrix -- complete,
but coarser -- and the reason is: "incomplete-partition" (its answer would have
credited coverage it never named -- a skip of the whole target, or nothing but
paths climbing out of the tree; the rejections are listed in
coverage.inventoryRejected),
"inventory-failed" (it did not answer), or "empty-partition" (it answered with
nothing). If the run
collapsed to the proportionate single-researcher shape rather than the full
component matrix, say so: coverage.collapsed is "small-diff" for a small diff
at medium (give the file and line counts, coverage.diffFiles / coverage.diffLines)
or "small-scope" for a small scope at medium (give coverage.scopeFiles) -- a
fast targeted pass, still panel-verified, not an exhaustive read. If a
supplied size could not be read (coverage.diffSizeRejected or
coverage.scopeSizeRejected), say which count -- for a diff: file, line, or
both -- quote the recorded value, and state its actual consequence for the
tier that ran: at medium, the target was not treated as small so the full
pipeline ran instead of the fast path; and, when a file count was the
unreadable one, an empty range or scope could not have been short-circuited.
This section is
what makes the rest of the report trustworthy: a reader who knows what you did
not look at can calibrate everything else.>

## Findings

The `F<n>` in each heading is that finding's `id` from `findings.json`, copied exactly — the findings arrive already numbered in report order, so never renumber, reorder, or invent an id.

### F1 — <title> (HIGH, confidence medium)

**Impact.** <what an attacker gets. Lead with this: it is what decides
priority.>

**Where.** `path/to/file.py:123` in `function_name`

**What.** <the vulnerability, in two or three sentences. Name the untrusted
source, the dangerous operation, and why nothing in between stops it.>

**Exploit scenario.** <a concrete walk-through. Not "an attacker could inject
SQL" -- what they send, what happens, what they get.>

**Preconditions.** <bullets: what must be true. Authentication? A non-default
config? Victim interaction? An empty list means none, which is worth saying.>

**Fix.** <what to change, in outcome terms. The root cause at the sink, not a
patch at one caller.>

**Verification.** <n>/3 lens verifiers confirmed.

### F2 — ...

## What was verified

<one paragraph: the pipeline that produced these findings, the votes each
survived, and the stamp's verification.status. If the status is anything other
than "verified", explain what it means in plain language and what to do about
it -- do not bury it.>
```

## Rules

**Severity is impact, not confidence.** HIGH means system control or broad cross-user data exposure. MEDIUM means real harm with limits. LOW means defense in depth. Uncertainty belongs in `confidence` — a word, `low`, `medium`, or `high` — which the panel's vote clamps: a finding two of three voters confirmed cannot claim `high`, and `render_report.py` will lower it if you try; only a unanimous panel earns `high`.

**Order by severity, then by confidence.** The reader stops partway down; put what matters at the top.

**Every finding cites a real `file:line`.** A finding pointing at the wrong line costs the reader more than a missed finding, because they lose trust in the rest of the report while chasing it.

**No control characters.** Only `\n` and `\t`. The report is read in a terminal, where an escape sequence can rewrite what a human sees. If a byte like that genuinely appears in the scanned source, describe it rather than reproducing it.

**No hedging, no padding.** Do not soften a real finding to be polite about the code, and do not inflate a nit to look thorough. "No findings" is a complete report, and writing it well — what you covered, what you did not — is more valuable than a page of maybes.

**Never claim something ran that did not.** Nothing in a scan executes the repository's code: no tests were run, no exploit was fired, no proof-of-concept was validated. Every finding is derived from reading. Say so rather than implying a demonstration.

## Example of the bar

Not this:

> The code may be vulnerable to SQL injection. Consider using parameterized
> queries as a best practice.

This:

> **Impact.** Any unauthenticated caller of `GET /users?name=` can read every
> row of the `users` table, including password hashes and email addresses.
>
> **Where.** `api/app.py:3` in `get_user`
>
> **What.** `name` arrives from the query string in `handlers.py:41` and is
> interpolated into the SQL string with `%`. No escaping or validation runs on
> the path between them; the `validate_name` call in `handlers.py:38` checks
> length only.
>
> **Exploit scenario.** `GET /users?name=' OR '1'='1` makes the WHERE clause
> tautological and returns the full table in the JSON response.
