# The eight mismatch classes

Load this when classifying join failures.

When two datasets are joined on a key, some rows find no partner. That is not a
nuisance to be counted — it is usually a real business problem in disguise. The
skill classifies every mismatch into one of the eight classes below and reports
each class separately, with counts **and example rows**.

**A count on its own is not a finding.** "312 mismatches" tells a plant person
nothing they can act on. "298 of them are one export covering three days the
other does not" tells them to re-run tomorrow.

---

## Check the date window first

**Class 7 is checked before any other class is reported.** A date-window
mismatch manufactures apparent mismatches across every key at once, and it
explains most large mismatch counts. Reporting format drift and orphan records
on top of an unnoticed window gap sends someone chasing problems that do not
exist.

Order of work: window overlap, then key shape, then genuine one-sided records.

---

## Class 1 — Orphan record

**What it is.** A record references a key that does not exist on the other side
at all. A production record reports output against production work order
`WO-88213`, and no such work order exists in NetSuite.

**What it means.** One of three things, and they are very different: somebody ran
an unauthorized job, a work order was deleted after the fact, or the two exports
are from different dates.

**Detection.** Key is well-formed and no normalization rung produces a match.

**Proposed fix.** None automatic — this is a question, not a formatting problem.
Report the orphans with their quantities and dates, and state which of the three
explanations the surrounding evidence supports. Check the date window before
concluding anything.

**On routings: routing with no matching part.** A routing whose part number no
normalization rung matches to the item master. Either the part was renamed,
retired, or never set up in the item master. Report it by that name, with its
operations; no automatic fix. It is never used to quote a part it merely looks
like.

---

## Class 2 — Format drift

**What it is.** `PN-4471-B` versus `4471B` versus `4471_B`. Same part, different
punctuation.

**What it means.** Nothing about the business. It is the most common class by
volume and the least interesting.

**Detection.** Normalization ladder rungs 1–3 produce a match.

**Proposed fix.** Apply the punctuation and case normalization, with the
normalization shown.

---

## Class 3 — Leading-zero loss

**What it is.** `00451` became `451` because a system exported to CSV and a
spreadsheet stripped the zeros on open.

**What it means.** A tooling artifact, extremely common, and not a data entry
problem.

**Detection.** Rung 4 — test whether a zero-padded variant of the short key
exists on the other side. Do not pad blindly; only claim the class when the
padded partner is actually present.

**Proposed fix.** Restore the padding to the source-of-truth width. Report the
width used.

---

## Class 4 — Revision suffix mismatch

**What it is.** `4471-B` versus `4471-B Rev 2`. The part is the same; the
revision is additional information carried on one side only.

**What it means.** One system tracks revision on the identifier and the other
does not.

**Detection.** Rung 5 — a match appears once the revision suffix is stripped.

**Proposed fix.** Strip and match, preserve the stripped revision in its own
column, and report that revision data existed on one side only. Never discard it.

**On routings: routing revision mismatch — no automatic fix.** A routing
written for revision 1, read against a drawing at revision 2, matches once the
suffix is stripped, and that match is exactly the mistake. A routing is the
operation list for one revision; a later revision may have tightened a
tolerance that adds an operation. Report it as a *routing revision mismatch*:
which revision the routing is for, which revision is being quoted or is
current, and what the drawing's revision history says changed where it is
available. The routing stays on the `routings` tab, marked `revision_mismatch`,
and `quote-build` shows it as superseded, never prices from it. A routing with
no revision at all is not a mismatch but it is not a match either: report it
as revision-unknown, never assumed current. `quote-build` may use it only with
that label on every line it touches.

---

## Class 5 — Case and whitespace

**What it is.** Trailing spaces and inconsistent capitalization, usually from a
manual export or a hand-maintained sheet.

**Detection.** Rungs 1–2 produce a match.

**Proposed fix.** Trim and case-fold for comparison.

---

## Class 6 — Genuine one-sided record

**What it is.** A part in the ERP that has never been produced. A machine in
the CMMS that appears in no production record. A supplier with no purchase orders
in the window.

**What it means.** Usually nothing wrong at all. An item master legitimately
contains parts that are not currently running.

**Detection.** Key is well-formed, no normalization produces a match, and the
absence is consistent with the record's own type and dates.

**Proposed fix.** None. **Report, do not alarm.** Distinguish this class clearly
from Class 1, because an orphan is a problem and a one-sided record generally is
not, and conflating them makes the whole report look like noise.

**Unless another source contradicts it.** A closed production work order with
no MES output is one-sided; the same work order cited on an NCR, on inspection
rows or by a lot was plainly run, and its parts were plainly made. Check for
that evidence before calling a record nothing wrong. Where it exists, the
record keeps class 6 and carries `contradicted_by`, naming the source and the
record (`quality_ncrs.csv NCR-2026-0141`). Consumers route it as an exception,
*"one-sided, contradicted by NCR-2026-0141"*, never to "Checked, nothing
wrong". Only evidence of the missing activity itself contradicts: downtime or
maintenance on a machine with no production does not.

---

## Class 7 — Date-window mismatch

**What it is.** The production export covers 1–31 August; the ERP pull covers
1 August to 3 September. Records in the non-overlapping days have no possible
partner.

**What it means.** A coverage problem, not a data problem.

**Detection.** Compare each source's coverage window before joining. Any
**activity** record whose date falls outside the intersection is this class,
not any other. Open commitments and reference history are not windowed the
same way, and are never this class for falling outside it: see
`join-keys.md`, *Date windows by entity*.

**Proposed fix.** Two options, and the user chooses: narrow the join to the
overlapping window, or wait for the next export and re-run. Report the
overlapping window explicitly either way, because every total below it is scoped
to that window.

**Check this first.** Per `../../../shared/absent-is-not-zero.md`, sources whose
windows do not overlap meaningfully are not joined at all.

---

## Class 8 — Duplicate key

**What it is.** The same production work order appearing twice with different
quantities. The same lot number on two different parts.

**What it means.** Either a genuine duplicate that needs deleting, a corrected
record that was appended rather than replaced, or two systems using the same
number space for different things.

**Detection.** Key appears more than once on a side where it should be unique.
**Unique means unique at the tab's grain**, per the contract: on
`production_output` that is production work order, shift and production day.
The same work order on two shifts is two legitimate rows, not a duplicate.
Count a duplicate by the rows that collide at the grain, from the query: if
WO-88201 has three rows, and two of them (509 and 480 good, both on
the 07:00 shift) are the duplicate; the 95 on the 23:00 shift is its own shift.
Say both: how many rows the key has, and how many collide.

**Proposed fix.** **None automatic, ever. Never silently pick one.** Surface both
rows with their full values and let the user say which is real. Summing them and
picking the larger are both wrong, and both are invisible once done.

---

## Reporting shape

Every class that fired gets its own block in the data quality report:

- The class name in plain language, not the class number
- How many records it affects, and how many records would join if the fix were applied
- Two or three real example rows, before and after
- The proposed correction, or an explicit statement that this class has no automatic fix
- What it means for the plant, in one line
