# The pattern checks — computed, never eyeballed

**Every check on this page is calculated in code, and the skill interprets the
computed result.**

This is not a stylistic preference. A statement that a process "was drifting,"
asserted from having looked at a data file, is exactly the claim a quality
manager will test first, and it is the fastest available way to lose their
trust. They have a control chart. If yours disagrees with theirs and you cannot
show the arithmetic, you are finished in that room.

So: compute the control limits, compute the group comparisons, run the run
rules, and then say in plain language what came out.

---

## 1. SPC drift on the relevant characteristic

Plot the measured characteristic across the run and the runs preceding it,
against computed control limits.

**The point of SPC is to catch the process that is fully in spec and clearly
heading out.** A run where every part passed but the last forty measurements sat
above the centreline and trending is a different finding from a single bad part,
and no individual inspection would ever flag it.

Apply the standard run rules rather than only checking for out-of-limit points:
a run of consecutive points on one side of the centre, a sustained trend, points
beyond two sigma. Say which rule triggered.

**Print the chart's numbers, every time.** Centreline, UCL, LCL, the basis
(individuals or X-bar, n points, which runs), and the run rule with its result
are five required rows in the figures block. They are printed when nothing
drifted: "UCL 0.00207, no point beyond, no run rule fired" is the evidence that
the check ran. A response that says "drift was checked" and shows no limit has
not shown its work.

**Control limits are not specification limits.** Confusing the two is the most
common error in this area, and it goes both ways: a process can be inside spec
and out of control, or in control and producing scrap. Report against both and
label which is which.

Needs measured values. Where the NCR carries `is_subjective: true` or no
measurements, **skip this check and say why** rather than substituting a
qualitative impression for it.

---

## 2. Clustering

Do the failures group by something? Compute the comparison; do not eyeball a
table.

| Group by | What it would point at |
|---|---|
| Material lot | The supplier. This is the signal that routes into Chain 5 |
| Shift | Training, staffing, a handover, or an environmental swing overnight |
| Operator | Training or a work-instruction gap. Handle with care — see below |
| Machine or cell | Equipment condition, tooling, or a setup |
| Position relative to a tool change | Tool wear, which usually also shows as a trend rather than a cluster |

**State the base rate alongside the cluster.** Eleven of fourteen failures on
night shift means nothing if night shift ran eighty percent of the parts. This
is the single most common way a clustering claim turns out to be nothing, and
computing it takes one extra division.

**Report small numbers as small numbers.** Three failures split two-to-one
across shifts is not a pattern, and saying so plainly is more useful than
dressing it up.

**On operator clustering specifically:** name the pattern, not the person's
competence. "The operator misread the print" is a symptom. "Two revisions of the
print were in circulation and the shop copy was not controlled" is a root cause,
and it is the same evidence read properly. An investigation that terminates on a
named individual has almost always stopped one question early.

---

## 3. Correlation with a maintenance event

Was the machine serviced, adjusted or repaired shortly before the failures
began? A repair is a change, and a change is a candidate cause — including
because it may have been done wrong.

This check depends on aligned timestamps, so it is gated on
`time-alignment.md` verifying. Where alignment fails, this check does not run
and the output says so.

---

## 4. Recurrence

The NCR already carries a recurrence finding from its history search at
creation. Read it forward rather than re-deriving it, and weight it heavily.

`recurrence_prior_capa_failed` is the highest-signal input available here. It
says a previous investigation reached a conclusion, somebody implemented a fix,
and the problem came back anyway — which means either the earlier root cause was
wrong, or the corrective action never really happened. Both are worth stating,
and the earlier 8D is worth reading before proposing a new one.

Where recurrence is `no_searchable_history`, that is **not** a first occurrence
and must never be written as one.

---

## Reporting what did not trigger

A check that ran and found nothing is evidence, and it belongs in the appendix.

"Failures did not cluster by shift or by operator" is what makes the lot
clustering meaningful. Report the checks that came back clean alongside the ones
that did not, and report separately any check that **could not run** — those are
three different states and collapsing them misleads.
