<!-- Audience: the Security Lead assembling a report from workflow findings, which writes CLAUDE-SECURITY-RESULTS.md as the delivery step of the scan job. Load this file only when a scan reaches delivery. -->

# CLAUDE-SECURITY-RESULTS.md — report spec

The markdown report is the one artifact written as prose rather than generated. It is what a human actually reads, so it is written for a specific reader: an engineer who owns this code, is busy, and will decide in about ninety seconds whether to act on each finding.

`render_report.py` generates the machine-readable companions from `findings.json` and `votes.json`. Do not hand-write the JSONL, the SARIF, or the stamp, and do not restate the JSONL here — this file is the part a person reads.

## Shape

```markdown
# Claude Security results

<one paragraph: what was scanned (path, revision, mode, scope), when, at what
effort, and the headline: how many findings at what severities, or that there
were none. Read `revision.dirty` in the run dir's scan-meta.json: on `true`,
say the repository's working tree held uncommitted changes or untracked files
-- which ones is not recorded, so never name or explain them; on `null`, say
the tree state could not be determined; otherwise say nothing of it.>

## Coverage

<what was examined and what was not. Name the components. If the scope was
narrowed, say to what and why. If write_scan_meta.py reported a sparse
checkout (`revision.not_checked_out_dirs` in the run dir's scan-meta.json
holds the list), say that only the checked-out part of the repository was
scanned and name those tracked top-level directories as not checked out.
Say how many verification runs the panel took
(coverage.verificationRun), and name any candidate never verified and why:
lost on the way to a further run (coverage.lostCandidates), or handed to a run
that did not complete.
If coverage.researchersReturned is below coverage.researchersDispatched:
- say how many researchers did not return and that their reading is missing
  from this scan;
- name each entry of coverage.lostResearchers by its reading, with its reason
  quoted;
- with more than 10 entries, group them by reason instead, each group with
  what its researchers were sent to read;
- describe why a researcher did not return only by its recorded reason;
- wherever the report says what the research covered or read, including the
  "What was verified" section, credit only readings in coverage.returnedReadings.
Name every area the scan deliberately did NOT examine, and WHY: each entry of
coverage.skippedComponents carries the paths left out and the componentizer's
one-line reason (vendored, generated, documentation, and the like); a
directory skipped on purpose is disclosure, not failure, so state the reason
rather than letting the area silently vanish.
If coverage.prunedBuckets is non-empty, each entry is a group's (or
component's) name, as coverage.components lists it, followed by
":memory-and-unsafe", the research lens it went without. Write each name
whole and say plainly that none of that group's researchers was asked about
memory-safety bugs, whatever the tier. An entry for "change boundary" has no
coverage.components row: it is the researcher working outward from the
change, under the same rule over every changed file, not a second group. Give
only the workflow's reason: it decided from the language alone -- the changed
files' extensions on a changes or commit scan, the inventory's language on a
codebase scan -- before the group's researchers were briefed, because it took
the code to be all in managed languages. Do not add that the lens does not
apply to such code, and never describe the prune as something the researchers
or the panel did, or as a lens dropped because a finding was in hand. A group
with no entry kept the lens.
On a whole-repository scan the
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
nothing). For a changes or commit scan, say that the change was reviewed
rather than the repository: name the change in plain words (following
`jobs/scan-changes.md`'s rules on the commit count and the branch) rather
than by the commit ids in coverage.range, the changed files by group
(coverage.components; coverage.diffFiles files of the coverage.changedFileCount
the helper counted, coverage.diffLines lines), and
how many researchers were dispatched and how many returned
(coverage.researchersDispatched, coverage.researchersReturned), and the
effort they were asked for (coverage.researchEffort -- asked, not measured:
the model's runtime may apply its own); say that a flaw the change takes no part in is out
of this review's scope and left to a scan of the codebase, and list every
entry of coverage.preExisting as a candidate the panel judged real but
predating the change. When the base is the branch's own pushed copy, so that
the diff holds only the unpushed commits, say that the commits already pushed
were not part of this review. If coverage.outsideScope is non-empty, say that those
findings (it names them) sit outside the requested scope and are reported
because the change reaches them. If coverage.changedFilesRejected is set, the changed-file
list could not be read or loaded: quote the recorded value and say the change
was reviewed as one group whose researchers listed it themselves; if
coverage.changedFilesMiscounted is set, the list handed over disagreed with
the count: give both, say which list was reviewed (its reviewed field) and
how many files that was (coverage.diffFiles). If a scoped
scan collapsed to the proportionate single-researcher shape rather than the
full component matrix, say so: coverage.collapsed is "small-scope" for a small
scope at medium (give coverage.scopeFiles) -- a fast targeted pass, still
panel-verified, not an exhaustive read. If a supplied scope size could not be
read (coverage.scopeSizeRejected), quote the recorded value and state its
actual consequence for the tier that ran: at medium, the scope was not
treated as small so the full pipeline ran instead of the fast path, and an
empty scope could not have been short-circuited.
Say how the run was sized when coverage.targetComponents is set: the target's
coverage.targetFiles tracked files, about coverage.targetComponents components
asked for (of roughly coverage.filesPerComponent files each, or larger when
the target holds more than coverage.componentCap components of that size),
at most coverage.componentCap kept. Then say what the researchers themselves report
not having read, as their account rather than as fact: coverage.research.components
lists, per component, the paths its researchers declared not reached and why --
summarize by directory with the reason, one line for a background tree (vendored
trees, and test and fixture trees under focus, left as background, are expected there
and are background, not gaps), and name individual files only up to a handful
per component. coverage.research.tree, when present, is that account checked
against the tracked files inside the components: how many were read to a
conclusion, how many lie under a declared not-reached path, and how many no
researcher accounted for at all (when coverage.research.capped is true an
account was truncated, so at least that many were read and at most that many
are unaccounted) -- list coverage.research.tree.unaccountedPaths (the first of them; the count
is the whole), because a component nobody finished reading would otherwise pass
for a clean one; files outside every component
(coverage.research.tree.outsideComponents) are the skipped and dropped areas
this section already names plus root files no component claims, not a
researcher's gap. When coverage.research is null or its tree absent, that
check did not run; say nothing of it, though any declared paths still stand.
This section is
what makes the rest of the report trustworthy: a reader who knows what you did
not look at can calibrate everything else.>

## Findings

The `F<n>` in each heading is that finding's `id` from `findings.json`, copied exactly — the findings arrive already in report order, so never renumber, reorder, or invent an id. A gap in the numbering is a candidate the panel did not keep under that id; call it rejected only when a complete panel refuted it, never when coverage.adversarialCasualties, coverage.preExisting or coverage.lostCandidates (the last by candidate id) names it.

### F1 — <title> (HIGH, confidence medium)

**Impact.** <what an attacker gets. Lead with this: it is what decides
priority.>

**Where.** `path/to/file.py:123` in `function_name` — <cwe_id, then
"(also <other_cwe_ids>)" when the finding carries further CWEs>

**Link to the change.** <a changes or commit scan only: the finding's
via_change, the changed line that takes part in the attack and how, named by
file:line and never quoted; omit the line for a scan of the codebase>

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
it -- do not bury it. If the status is "verified" and a researcher did not
return, say that "verified" does not cover the missing readings.>
```

## Rules

**Severity is exploitability and impact, not confidence.** CRITICAL means severe impact with nothing in the attacker's way. HIGH means severe impact behind one real hurdle. MEDIUM means bounded impact, or serious impact behind several conditions. LOW means limited impact and demanding exploitation. The severity in `findings.json` is final: where the panel's confirming voters rated a finding lower than its researchers did, the workflow already lowered it, and coverage.severityLowered names each such finding with both ratings — say so in its **Verification.** line and do not restore the reported one. Uncertainty belongs in `confidence` — a word, `low`, `medium`, or `high` — which the panel's vote clamps: only a unanimous panel earns `high`, and the workflow has already lowered any other `high`; `render_report.py` lowers it if you raise it.

**Order by severity, then by confidence.** The reader stops partway down; put what matters at the top.

**More than twenty findings are written in batches.** One call holding every finding can exceed the model's output limit, and a Write cut off there is refused whole. So the first Write holds the opening paragraph, Coverage, the first twenty findings and What was verified, and each further twenty go in with Edit, inserted above the `## What was verified` heading.

**Every finding cites a real `file:line`.** A finding pointing at the wrong line costs the reader more than a missed finding, because they lose trust in the rest of the report while chasing it.

**A hard-coded credential finding gets no "Link to the change" line.** That is any finding carrying CWE-798, CWE-259, CWE-321 or CWE-671, in `cwe_id` or in `other_cwe_ids`: the changed line it would name is the credential, and the JSONL and SARIF already withhold that link.

**No control characters.** Only `\n` and `\t`. The report is read in a terminal, where an escape sequence can rewrite what a human sees. If a byte like that genuinely appears in the scanned source, describe it rather than reproducing it.

**No hedging, no padding.** Do not soften a real finding to be polite about the code, and do not inflate a nit to look thorough. "No findings" is a complete report, and writing it well — what you covered, what you did not — is more valuable than a page of maybes.

**The researchers' lenses are not the panel's.** A researcher's lens is a vulnerability category, one of them or every category its group kept; a panel voter's is reachability, impact or defenses. Never give the panel's three as the researchers'.

**Never claim something ran that did not.** Nothing in a scan executes the repository's code: no tests were run, no exploit was fired, no proof-of-concept was validated. Every finding is derived from reading. Say so rather than implying a demonstration.

## Example of the bar

Not this:

> The code may be vulnerable to SQL injection. Consider using parameterized
> queries as a best practice.

This:

> **Impact.** Any unauthenticated caller of `GET /users?name=` can read every
> row of the `users` table, including password hashes and email addresses.
>
> **Where.** `api/app.py:3` in `get_user` — CWE-89
>
> **What.** `name` arrives from the query string in `handlers.py:41` and is
> interpolated into the SQL string with `%`. No escaping or validation runs on
> the path between them; the `validate_name` call in `handlers.py:38` checks
> length only.
>
> **Exploit scenario.** `GET /users?name=' OR '1'='1` makes the WHERE clause
> tautological and returns the full table in the JSON response.
