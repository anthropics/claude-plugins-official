# The report's Coverage section — spec

`render_report.py` writes `CLAUDE-SECURITY-RESULTS.md`; you write only the text of its Coverage section, to `coverage.md` in the run directory. Under your text the render prints the scan's own records itself, such as the lines on what the later research stages left out and the line on the last report, so your text neither writes nor restates them. Where coverage.context lists what the scan was given, the report has its own section on it. Say nothing of coverage.context yourself, above all not whether a file on it was read: the scan's other agents may have opened it.

## Shape

```markdown
<what was examined and what was not. Name the components. If the scope was
narrowed, say to what and why. If write_scan_meta.py printed a
`sparse checkout:` line, say that only the checked-out part of the
repository was scanned and name the tracked top-level directories that
line lists as not checked out.
Say how many verification runs the panel took
(coverage.verificationRun), and name any candidate never verified and why:
of each entry of coverage.lostCandidates, say only that no complete panel judged it (it was
lost within a run or on the way to a further one, and coverage.json does not say which); of a
candidate handed to a run that did not complete, say so (coverage.continued counts them;
coverage.waiting names the first of them, each with why it waits).
If coverage.changeScanEffort is "high" and coverage.runNotRecorded is there, the run that it
names completed but was not recorded, and coverage.verificationRun does not count it. Name the
run, and say that it completed and was not recorded, not that it did not complete. Give its
cause in plain words. Say that its findings are not reported, and that the candidates handed to
it were not verified.
If a Workflow completion notice says a safety check of an agent's finished work
was unavailable, could not finish or flagged it, say so, in your own words,
without agent labels.
If coverage.researchersReturned is below coverage.researchersDispatched, then
wherever you say what the research covered or read, credit only readings in
coverage.returnedReadings.
If coverage.pastFixFollowUp is "not run", your text says
"These results include no follow-up of past security fixes."; if it is "nothing
listed", your text says "These results include no follow-up of past security
fixes, because the scan listed no earlier commit whose message reads like one.
If this is a shallow clone, such as a CI checkout of depth 1, scan a clone with
its full history."; if it is "none needed", your text says "An agent
looked at the list of commits that read like past security fixes and named no
area for a further look.". That text, in those words, is all that your text or
your message to the user says of it. The message still reports lost researchers.
Where coverage.json's pastFixPaths lists paths, name them as code that one more
researcher was sent to, because security flaws were fixed there before.
The render prints the lines on what the later research stages left out under Coverage, in the
workflow's own words. Your text and your message to the user add nothing to them: no count, no
cause and no list of places of your own.
Name every area the scan deliberately did NOT examine, and WHY: each entry of
coverage.skippedComponents carries the paths left out and the inventory's
one-line reason (vendored, generated, documentation, and the like); a
directory skipped on purpose is disclosure, not failure, so state the reason
rather than letting the area silently vanish.
If coverage.prunedBuckets is non-empty, each entry is a group's
name, as coverage.components lists it, followed by
":memory-and-unsafe", the research lens it went without. Write each name
whole and say plainly that none of that group's researchers was asked about
memory-safety bugs, whatever the tier. An entry for "change boundary" has no
coverage.components row: it is the researcher working outward from the
change, under the same rule over every changed file, not a second group. Give
only the workflow's reason: it decided from the language alone -- the changed
files' extensions -- before the group's researchers were briefed, because it took
the code to be all in managed languages. Do not add that the lens does not
apply to such code, and never describe the prune as something the researchers
or the panel did, or as a lens dropped because a finding was in hand. A group
with no entry kept the lens.
On a whole-repository scan the
workflow requires the inventory to account for every directory on a list one or
two levels deep -- scanned or explicitly skipped -- and
coverage.completenessCheckOutcome says whether that check ran: "checked" (say
that each directory on that list was scanned at least in part or set aside, not
that the whole tree was),
"partial" (the inventory left some of them in neither ledger and
the answer was used as it stood -- coverage.unaccountedTopLevelDirs names them;
list every one and say plainly they were neither scanned nor skipped, because
that is exactly the coverage a "no findings" would otherwise overstate),
"not-checkable" (the tree's directory list was not supplied, was unreadable,
was not as long as write_scan_meta.py's, or
was empty while the inventory named subdirectories, or the scan could not read
some directories -- coverage.topLevelRejected
gives the cause; say plainly that completeness could NOT be checked), or
"not-applicable" (a diff, commit, or scoped scan, whose target
is the change or the scope, or a low-effort run with no inventory). If
coverage.inventoryFallback is set, the inventory's partition was not used and
the whole tree went to one researcher (two at high) as a single component --
far coarser than a researcher per component, so say so -- and the reason is: "incomplete-partition" (its answer would have
credited coverage it never named -- a skip of the whole target, or nothing but
paths climbing out of the tree; the rejections are listed in
coverage.inventoryRejected),
"inventory-failed" (it did not answer), or "empty-partition" (it answered with
nothing). For a changes or commit scan, say that the change was reviewed
rather than the repository: name the change in plain words (following
`jobs/scan-changes.md`'s rules on the commit count and the branch) rather
than by the commit ids in coverage.range, the changed files by group
(coverage.components), and the
effort the researchers were asked for (coverage.researchEffort -- asked, not measured:
the model's runtime may apply its own); say that a flaw the change takes no part in is out
of this review's scope and left to a scan of the codebase (if
coverage.changeScanEffort is "high": but that the researchers also looked for
older flaws in the functions that the change touches, and that those which
the panel judged real are reported under "Older than the change"), and list every
entry of coverage.preExisting as a candidate the panel judged real but
predating the change. When the base is the branch's own pushed copy, so that
the diff holds only the unpushed commits, say that the commits already pushed
were not part of this review. If coverage.candidatesReplaced is set, say that before the
panel one agent replaced that many candidates, which reported the same flaws, with
coverage.candidatesWritten new ones, and that the new ones, not those that they replaced,
went to the panel. If coverage.candidatesRewritten is set, say that before the panel one agent also wrote
that many candidates anew, each from the reports that had been joined into it, and that these replaced no other.
If coverage.outsideScope is non-empty, say that those
findings (it names them) sit outside the requested scope and are reported
because the change reaches them (because a lead from the change goes there, if
coverage.changeScanEffort is "high").
If coverage.changedFilesRejected is set, the changed-file
list could not be read or loaded: quote the recorded value and say the change
was reviewed as one group whose researchers listed it themselves; if
coverage.changedFilesMiscounted is set, the list handed over disagreed with
the count: give both, say which list was reviewed (its reviewed field) and
how many files that was (coverage.diffFiles). If a scoped
scan collapsed to the proportionate single-researcher shape rather than an
inventory and a researcher per component, say so: coverage.collapsed is "small-scope" for a small
scope at medium (give coverage.scopeFiles) -- a fast targeted pass, still
panel-verified, not an exhaustive read. If a supplied scope size could not be
read (coverage.scopeSizeRejected), quote the recorded value and state its
actual consequence for the tier that ran: at medium, the scope was not
treated as small so the full pipeline ran instead of the fast path, and an
empty scope could not have been short-circuited.
Say how the run was sized when coverage.targetComponents is set: the target's
coverage.targetFiles tracked files, about coverage.targetComponents components
asked for (of roughly coverage.filesPerComponent files each),
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
```

## Rules

**A candidate dropped while a verifier could not open a file was not refuted.** Where a coverage.adversarialCasualties entry ending "dropped without a verdict" says a verifier could not open a file, say under Coverage that the panel reached no verdict on that candidate, and name the file as one that at least one verifier could not open. Do not say nobody saw its text: a change scan's diff can show it.

**The researchers' lenses are not the panel's.** A researcher's lens is a vulnerability category, one of them or every category its group kept, or, at Change Scan Effort `high`, a question lens; a panel voter's is reachability, impact or defenses. A codebase scan's component researcher has no lens: it owns every kind of vulnerability in its component. Never give the panel's three as the researchers'.

Never claim something ran that did not.
