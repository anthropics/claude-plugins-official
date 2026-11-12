# The time interview and the offset self-check

**Cross-system timestamp alignment and shift-boundary definition are the highest
-risk correctness issues in this build.** This is the only place they get
established, which is why this file exists rather than three paragraphs in the
skill body.

Everything here lands in the `## Plant context` source clock table and the site
blocks, per `config-profile.md`.

---

## Why it is the highest risk

A misaligned timestamp is a hole that looks like a value. Nothing errors. The
data is present, well-formed and wrong by an hour, and every downstream
correlation inherits the error while looking perfectly reasonable.

Two concrete consequences already written into the plugin:

- **`root-cause-capa`** aligns sensor, inspection, production and maintenance
  data onto one timeline around an event. If the clocks are off, it produces a
  spurious correlation, presents it confidently, and closes an investigation on
  the wrong cause.
- **`daily-production-report`** computes availability against planned production
  time. If the shift boundary is wrong, every OEE figure is wrong, and OEE is the
  number everyone in operations knows by heart — so a wrong one destroys trust in
  the whole report.

---

## Part 1 — Per-source clocks

Ask this **per data source**, not once for the plant. Different systems record
time differently and a plant person will not have thought about it, so ask
concretely rather than abstractly.

For each source in the export folder and each live connector:

1. **What timezone are this system's timestamps in?** Offer the plant's local
   zone as the likely answer, but do not assume it. Historians and cloud systems
   are frequently UTC.
2. **Does the timestamp carry its zone, or is it bare?** A bare local time is
   "naive" and cannot be safely compared to anything until the zone is declared.
   The practical test: open one file and look at whether the timestamp has an
   offset or a zone suffix on it.

Record both per source. A naive source with a declared zone is workable; a naive
source with an undeclared zone is a blocking gap.

**Do not infer a zone from a system's default setting.** That is the zone the
account was created in, not necessarily where the data was recorded.

---

## Part 2 — Shift and day definition

Four questions, per site. These are the ones a supervisor answers instantly and
an engineer guesses wrong.

1. **What is the shift pattern?** Two 8s, three 8s, two 12s, 4-on-4-off, or
   something else. Get the actual clock start times, not just the count.
2. **When does the production day start?** Often the start of first shift, not
   midnight. This is the single most consequential answer here, because it
   decides which day every number belongs to.
3. **A shift that crosses midnight — which day does it belong to?** The day it
   started, or the day it ended. There is no universal convention and both are in
   use. Getting it wrong moves a whole shift of output to the wrong day, which
   makes the day look bad and the next day look good.
4. **What counts as planned production time?** Scheduled shift hours, minus what
   — planned maintenance windows, breaks, scheduled changeovers? This is the
   denominator of OEE availability, so its definition decides whether 62% is a
   maintenance problem or a definitional artifact.

Where the plant runs more than one site, ask per site. Do not carry one site's
answers to another silently; `config-profile.md` explains the inheritance rule.

---

## Part 3 — The offset self-check

**This is the point of the whole interview.** A declared configuration is a
claim. This step tests it against the data.

The procedure:

1. **Find one event recorded in two systems.** A production work order with a
   completion timestamp in the ERP and in the MES export. A downtime event in
   both the maintenance record and the historian window. A shipment in the ERP and
   the planning export.
2. **Convert both timestamps into a single zone** using the declarations from
   Part 1.
3. **Compare them.** They should agree to within the systems' own recording
   granularity.
4. **Report the observed skew**, whether or not it is zero. A zero result is a
   confirmed configuration, which is worth saying out loud.

### Reading the result

| Observed | What it means | What to do |
|---|---|---|
| Zero, or within recording granularity | The declared config is consistent with the data | Record it as checked, with the date |
| A whole-hour offset | A timezone declaration is wrong, or a naive source was assigned the wrong zone | Re-ask Part 1 for the source in question |
| A whole-hour offset that matches a DST transition | A source is recording standard time year-round, or converting inconsistently | Record the skew and flag it; this one recurs twice a year |
| Minutes, not hours | Genuine clock drift on a machine or server | Report it to the plant's IT. This is a real finding |
| Cannot be tested — no shared event | The config is declared but unverified | Record as unverified and put it on the gaps list |

### When the user insists the config is right

**Report the skew; do not override it.** The observed data is evidence and the
declaration is a claim. A real clock drift is worth surfacing to their IT, and
overriding the measurement to match the assertion throws away the only signal
there is.

Say it plainly and without argument:

> *"Your MES export reads one hour ahead of NetSuite on the same work order
> completion. I've recorded both declarations as you gave them and flagged the
> skew, so anything that correlates these two sources will say the alignment is
> unverified. Worth having IT check the MES server clock."*

---

## What blocks and what defers

Consistent with the skill's rule that setup never blocks:

- **Deferrable:** an untested offset, a missing planned-production-time
  definition, a second site's shift pattern. All go on the gaps list with the
  affected skills named.
- **Effectively blocking downstream, not here:** a naive source with no declared
  zone. Setup completes, but per `../../../shared/absent-is-not-zero.md` any skill
  asked to correlate that source refuses and reports the alignment gap instead of
  producing a correlation nobody can trust.

The distinction matters. Onboarding does not stop. The skill that would produce a
wrong answer does.
