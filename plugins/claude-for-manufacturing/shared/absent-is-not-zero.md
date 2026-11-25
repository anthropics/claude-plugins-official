# Absent is not zero, and stale is not current

**Shared across the plugin.** The single most common way a manufacturing skill
produces a confident wrong answer.

The shape of it is always the same. A file did not land, a row did not match, a
field came back empty, or an export stopped running three weeks ago. The skill
reads that hole as a fact about the plant rather than a fact about the data. The
answer that comes out is clean, confident, and wrong in the direction that hides
the problem, which is the worst direction, because nothing looks like it needs
checking.

Two reasons this bites harder here than in most domains:

1. **A plant has no single database.** It has five to eight systems bought at
   different times by different departments, and the same physical thing carries
   a different identifier in each one. Joins fail constantly, and a failed join
   looks like an absence.
2. **Most of the data arrives as a file on a schedule.** Scheduled exports stop
   running silently. Nothing errors. The folder just stops getting newer, and
   every number downstream keeps being reported as if it were today's.

---

## The rule

**Before reporting any figure, ask what would make it look like this if the
plant were fine, and what would make it look like this if the data were broken.
If you cannot tell the two apart, say so instead of picking one.**

---

## Stale is not current

**Freshness is a headline, never a footnote.** Every skill that reads an export
states, up front, what each source's timestamp is and what window it covers. An
export that is weeks old and unnoticed is the normal failure, not the exotic one.

- **If last night's export did not land, say so at the top of the output.**
  Only a safety implication goes above it. A
  production report built on stale data is worse than no production report,
  because it gets believed and acted on.
- **Never silently reuse yesterday's file** in place of one that is missing.
- **Partial data is reported as partial.** When one line's or one system's
  export is missing, report on what is there and name what is not. Do not let a
  section quietly shrink.
- **Windows that do not overlap cannot be joined.** A production export covering
  1–31 August and an ERP pull covering 1 August–3 September will manufacture
  mismatches out of nothing. Check window overlap before anything else, because
  it explains most large mismatch counts.
- **A timestamp from the future is not fresh, it is untrusted.** A source
  whose created, modified or transaction dates fall after the run time has a
  clock that is ahead or data seeded wrong. That is a critical freshness
  finding: name the source and its latest such timestamp, and state no age or
  "as of" for it. A due or promised date in the future is a commitment, not
  this.
- **Export-sourced data is named as export-sourced.** When a system that could
  have been live is being read from a file instead, say which, so nobody assumes
  they are looking at this morning.

---

## Absent is not zero

1. **An empty section reads as good news.** A missing "open maintenance work
   orders" line reads as "no open maintenance," not as "we could not see it."
   Say which one it is, every time.
2. **No searchable history is not the absence of a problem.** When there are no
   prior records to check, report "no searchable history available." Silence
   reads as "no recurrence," which is a much stronger claim than the evidence
   supports.
3. **No prior history is not evidence of a one-off.** A new part or a new
   process has nothing to recur against. State that, rather than reporting a
   first occurrence as an isolated one.
4. **A constrained or paginated call describes its own slice, never the whole.**
   Totals come from an unconstrained source, or they are labelled as partial.
5. **A summary is a convenience, not a source.** When a payload offers both a
   summary and the rows it was computed from, total the rows.
6. **Zero and absent are different facts, and most systems conflate them.**
   Decide which is plausible. A part with genuinely zero production is possible;
   a field the customer never populated is far more common.
7. **A duplicate key is never resolved silently.** The same production work
   order appearing twice with different quantities is a finding. Surface both.
8. **Two counts that disagree by an order of magnitude are a finding, not a
   rounding error.** One of them is measuring something else. Say which was used
   and why.
9. **Never narrow scope to make a number look better.** When traceability is
   incomplete — no lot recorded, no operation stamped — the suspect scope gets
   wider, not narrower, and the output says why it had to widen.

---

## Units and custom fields

Two plant-specific versions of the same mistake:

- **Units differ and nothing announces it.** Each versus box of twelve, inches
  versus millimetres, pounds versus kilograms. Detect the unit-of-measure column
  and flag a mismatch rather than silently summing across it. A total computed
  across two units is not a total.
- **Customers add their own fields, and a missing one is not a failure.**
  NetSuite in particular is heavily customised per account. Never hard-fail on a
  custom field that is not present. Fall back, and report what could not be
  read.

---

## Time is a correctness problem, not a formatting one

Cross-system timestamp alignment is the highest-risk correctness issue in this
build, and it belongs here because a misaligned timestamp is a hole that looks
like a value.

- **Different systems record time differently.** Some are in local plant time,
  some in UTC, some are naive with no zone at all. Two systems can describe the
  same event an hour apart and neither is wrong about its own clock.
- **When the declared configuration and the observed data disagree, report it.**
  Do not pick. A real clock skew is a finding worth surfacing to the plant's IT.
- **Refuse to correlate across sources whose alignment cannot be established.**
  A spurious correlation presented confidently is worse than no correlation,
  because it closes an investigation.
- **A window that does not cover the event is not evidence about the event.** Do
  not reason from adjacent data as if it were the event.

---

## Saying it well

The plant person does not need the mechanism. They need to know which numbers to
trust and what to go fix.

> *"Production and the ERP agree on 412 of 447 work orders. The other 35 are all
> from 1–3 September, which the production export does not cover yet — so this is
> a window gap, not a data problem. Re-run after tonight's export."*

Not "35 mismatches found," which is true and useless.

> *"The inspection export last refreshed on 14 August, nineteen days ago. Every
> quality figure below is as of that date. Worth checking whether that scheduled
> job is still running."*

One sentence, and they know exactly how much to trust the number.

When something genuinely cannot be determined, say that and stop. **A named gap
is useful; a fabricated zero is worse than silence**, because it gets acted on —
and these outputs go to customers, auditors and quality managers.
