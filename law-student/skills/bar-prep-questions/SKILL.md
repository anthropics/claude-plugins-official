---
name: bar-prep-questions
description: >
  Bar prep questions — MBE or essay, targeted at your weak subjects and bar
  jurisdiction. Tracks misses and comes back to patterns. Use when the user
  says "bar prep", "MBE questions", "practice essay", or "test me for the
  bar".
argument-hint: "[subject, or --mbe / --essay / --session <n>]"
---

# /bar-prep-questions

1. Load `~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md` → bar jurisdiction, exam format (NextGen / traditional UBE / state-specific), weak subjects, prep course.
2. Also load `~/.claude/plugins/config/claude-for-legal/law-student/study-plan.yaml` if it exists — it tells you what subject is scheduled for today and what subtopics are still weak.
3. Apply the framework below.
4. **Exam-type gate (do not skip).** If exam format or jurisdiction isn't in the practice profile, ask before generating anything. The NextGen Bar Exam and the traditional UBE test materially different subjects — studying the wrong list is the one mistake that isn't recoverable. Point the student at the NCBE's jurisdiction page (<https://www.ncbex.org/>) to confirm their exam format and subject scope.
5. **Jurisdiction-rule gate.** If the student's jurisdiction has a state-specific component (CA, LA, NY Law Exam, FL state essay, VA, etc.) AND the subject is one where majority-vs-state rules diverge (Evidence, PR, Civ Pro, Criminal), ask whether this session is UBE/majority-rule, state-specific, or mixed. Do not silently default.
6. Generate questions **scoped to subjects tested on the student's exam**, weighted toward weak subjects. Label each question by rule body (`[UBE/majority]` or `[CA-specific]` / `[NY-specific]` / etc.) when running mixed.
7. When rules diverge between UBE/majority and the student's jurisdiction, explain the split explicitly in the answer — see `## Jurisdiction handling` below.
8. After each answer: explain why right/wrong. Track patterns in misses.
9. `--session <n>` runs a focused N-question session and writes results to `study-plan.yaml` under `session_history`.

---

## Real-matter check

If the question the student is asking sounds like it's about a REAL situation — their lease, their parking ticket, their family's business, their friend's arrest, a real dollar amount, a real deadline, a real party name — stop.

> "This sounds like a real situation, not a hypothetical. I can't give you legal advice, and you can't give it either — you're not a lawyer yet. If this is real, [the person] needs an actual lawyer: legal aid, your school's clinic, a lawyer referral service (your jurisdiction's bar association, law society, or legal aid body), or (if there's money) a private attorney. I'm happy to help you understand the general legal concepts involved, but that's study, not advice."

Watch for: real names, real addresses, real dates, specific dollar amounts, "my landlord/boss/parent/friend," "I got a ticket/letter/notice," deadlines measured in days. Any one of these is a trigger.

## Purpose

The bar exam tests a defined body of subjects. This skill drills you on them — weighted toward your weak spots.

## Exam type — ask first, do not assume

**The bar exam is in transition.** As of the July 2026 administration, the NextGen Bar Exam (developed by the NCBE) has launched in some jurisdictions, while others continue to administer the traditional Uniform Bar Exam (UBE). State-specific exams (California, Louisiana, Puerto Rico, etc.) are their own thing. The subject scope is materially different between the NextGen and the traditional UBE — **subjects no longer independently tested on the NextGen include Trusts & Estates, Family Law, Conflict of Laws, and Secured Transactions** (some underlying concepts may appear inside integrated "foundational concepts and skills" questions, but they are not standalone tested subjects the way they were on MEE).

Do not assume the subject list. Before generating any questions:

1. Load `~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md` and read the bar jurisdiction and bar date.
2. If the practice profile does not specify which exam format the student is sitting for (NextGen / traditional UBE / state-specific), **ask**:

   > Which bar exam are you sitting for?
   > 1. **NextGen Bar Exam** (NCBE, launched July 2026 in some jurisdictions)
   > 2. **Traditional Uniform Bar Exam (UBE)** (MBE + MEE + MPT)
   > 3. **State-specific exam** (California, Louisiana, Puerto Rico, Washington, etc. — tell me which)
   >
   > And which jurisdiction? The scope of what's tested depends on both.

3. **Point the student at the authoritative source.** Jurisdiction-by-jurisdiction exam format (and whether a given state has moved to NextGen) is on the NCBE's website at <https://www.ncbex.org/> under "Exams" → jurisdiction information. The NextGen subject outline lives at <https://www.ncbex.org/exams/nextgen>. The traditional UBE subjects (MBE and MEE) are at <https://www.ncbex.org/exams/mbe> and <https://www.ncbex.org/exams/mee>.

> **Verify your jurisdiction's exam format and subject list against the NCBE's current outline before studying. This is the single most important thing you can get right** — studying the wrong subject list is the one mistake this skill can't undo for you. If your prep course (Barbri/Themis/Kaplan) and the NCBE outline disagree, go with the NCBE outline and tell your prep course.

Scope every question-generation session to the subjects actually tested on the student's exam. If the practice profile lists a weak subject that is not tested on their exam (e.g., Secured Transactions for a NextGen jurisdiction), flag it:

> You listed Secured Transactions as a weak essay subject, but the NextGen Bar Exam doesn't test it as a standalone subject. Do you want to (a) skip it, (b) drill the UCC Article 9 concepts that may appear inside integrated NextGen questions, or (c) drill it anyway because you're curious / auditing the area?

## Jurisdiction handling

The bar exam is not one exam. It is a family of exams. Rules that are "correct" on one are "wrong" on another. Getting this right matters more than almost anything else this skill does.

### Two things to distinguish

1. **Exam structure.** What does the student's jurisdiction administer?
   - **Pure UBE** jurisdictions: MBE + MEE + MPT, one set of rules, no state-specific content tested.
   - **UBE + state-specific component:** many UBE states require a separate state law component (e.g., NY Law Exam, DC Mandatory Course). These are pass/fail or supplementary, not graded into the UBE score.
   - **Non-UBE state-specific exams:** California runs its own exam (GBX + essays with California-specific subjects — Community Property, CA Civil Procedure/Evidence distinctions, CA Professional Responsibility — plus a Performance Test). Louisiana runs a civil-law exam that shares almost nothing with the UBE. Florida, Virginia, and several others keep state-specific essay days alongside or instead of the MEE.
   - **NextGen jurisdictions** (rolling out starting July 2026): integrated foundational concepts format, drops Trusts & Estates / Family Law / Conflict of Laws / Secured Transactions as standalone tested subjects.

   Before generating questions, confirm structure via the `## Exam type` gate above. Do not assume.

2. **Rule content — where majority rule, UBE default, and the student's jurisdiction's rule can diverge.** Common divergence areas:
   - **Criminal law:** common-law vs. MPC vs. state code (e.g., CA Penal Code on murder degrees, felony murder scope, consent defenses).
   - **Evidence:** FRE vs. state rules (CA Evidence Code diverges materially — hearsay exceptions, character, propensity in sex-offense cases, privileges).
   - **Civil procedure:** FRCP vs. state (CA Code of Civil Procedure — 170.6 peremptory challenges, demurrers vs. 12(b)(6), different discovery scope).
   - **Community property states** (CA, TX, AZ, NV, NM, WA, ID, LA, WI): tested on state-specific essays in CA; irrelevant on pure UBE.
   - **Professional responsibility:** MPRE tests ABA Model Rules; CA tests California Rules of Professional Conduct (which diverge on confidentiality, conflicts, fees).

### Rule when generating questions

For every question, internally classify by which body of rules applies:

- **General / federal / majority-rule questions** (MBE-style, federal courts, FRE, FRCP, constitutional, common-law core): the "correct answer" is the UBE/majority rule. State.
- **Jurisdiction-specific questions** (CA PR, CA Evidence, community property, LA civil code, NY Law Exam topics): the "correct answer" is the student's jurisdiction's rule. State that.

### Divergence tags — per-rule, not per-subject

**Tag divergences at the rule level, not the subject level.** "[CA does not materially diverge on this rule]" stamped on every question in a subject is noise — a student sees the same tag on every Contracts question and stops reading. Scope the tag to the specific rule being tested.

Rules to apply when emitting divergence tags:

- If the specific rule tested in a question has no material CA/NY/LA/etc. divergence, tag **at the rule level** within that question: `[CA does not diverge on UCC § 2-207 — this answer holds on the CA bar.]`
- If the specific rule tested has a material divergence, fire the `**Your jurisdiction (X) diverges:**` block per the format above. Do not use a subject-level tag when a rule-level divergence exists.
- Do NOT blanket-apply a subject-level tag like "[CA does not materially diverge on this subject]" across all questions in a subject. Contracts-as-a-subject has both divergent rules (CA statute of frauds specific carve-outs, CA-specific consumer contract rules) and non-divergent ones (UCC § 2-207, Restatement § 71 consideration), and stamping them all with the same tag hides the divergences that matter.
- If a question is CA-specific by construction (e.g., a CA Community Property question on a state-specific essay day), skip the tag — the CA-specific framing is already explicit.

Short rule: the tag lives inside the question (at the rule being tested), not outside it (at the subject level).

### Rule when the rules diverge

When a question's answer differs between the majority/UBE rule and the student's jurisdiction's rule, the explanation must say so explicitly:

```markdown
**Correct: C**

**Why C (UBE/majority rule):** [rule + application]

**Your jurisdiction (CA) diverges:** Under [California Evidence Code § X / CRPC Rule Y / CA Penal Code § Z], the rule is [jurisdiction-specific rule]. Under that rule, the answer would be [A/B/C/D].

**On the bar exam:** On the MBE and MEE portions, the default answer is the UBE/majority rule unless the question tells you to apply state law. On a state-specific essay day (e.g., California's essay subjects, NY Law Exam, Florida state essay), the default is your jurisdiction's rule. Check the call of the question.

**Rule to remember:** [one-line takeaway flagging the split]
```

If the student sits for a state-specific exam day (CA, LA, FL state essay, VA, NY Law Exam, etc.), weight some sessions toward state-specific content. Ask:

> You're sitting for California. Do you want this session to be (a) MBE-style federal/majority rule, (b) California-specific essay subjects (Community Property, CA Evidence, CA PR, CA Civ Pro), or (c) mixed?

Never silently default to one. If the student says "mixed" or doesn't answer, generate a mix and label each question `[MBE / UBE default]` or `[CA-specific]` so they know which body of rules governs.

### When unsure of the jurisdiction's rule

The skill does not know every state's idiosyncrasies with confidence. If the student's jurisdiction has a known divergence but the skill is not confident on the specific current rule, flag it: `[UNCERTAIN: CA's exact rule here — verify against CA-specific prep materials (e.g., BarMax CA, Themis CA supplement, the California Bar's released essay graded answers)]`. Do not invent. The cost of a wrong California rule stated confidently is higher than the cost of flagging uncertainty.

## Confidence discipline

Every question generated states a rule. A wrong rule stated confidently is worse than no question. The rule for this skill:

- **Confident:** rule is black-letter in the subject; write the question normally.
- **Uncertain:** rule varies by jurisdiction, is a minority rule, or I'm not sure I've got it exactly right — flag inline with `[UNCERTAIN: specific reason]` and tell the student to verify against their prep course materials before relying on the question.
- **Don't know:** don't invent a question. Say "I don't have a reliable rule for this area; skip or use your prep course." Do not fabricate.

Every MBE question answer explanation carries the same rule: if the "why C is correct" rule isn't one the skill is confident on, flag `[VERIFY: rule — confirm against Barbri/Themis/Kaplan outline]`. Use liberally.

## Load context

`~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md` → bar jurisdiction, exam format (NextGen / traditional UBE / state-specific), weak subjects, prep course. If exam format isn't specified, run the "Exam type" gate above before continuing. If jurisdiction is specified, apply the `## Jurisdiction handling` rules — label questions by which rule body governs, and flag divergences explicitly.

Also load `~/.claude/plugins/config/claude-for-legal/law-student/study-plan.yaml` if it exists (written by the `study-plan` skill). If the plan has a session scheduled for today or specifies weak subjects to weight, honor it.

## Session mode

`--session <n>` runs a focused N-question session on a specific subject, tracks performance, and writes session results back to `~/.claude/plugins/config/claude-for-legal/law-student/study-plan.yaml` under `session_history` so the study plan adapts.

Trigger phrasing the student might use: "let's do 5 questions on Contracts", "run me 10 Evidence questions", "/law-student:session Evidence 10".

**Session flow:**

1. Confirm subject, N, and MBE-vs-essay (or mixed). If the student's jurisdiction has a state-specific component and the subject is one where rules diverge (Evidence, PR, Civ Pro, Criminal), ask whether to run UBE/majority rule, state-specific rule, or mixed.
2. Generate N questions. Weight by subtopics the student has missed before (read `session_history`).
3. Present them one at a time. After each, show correct answer + why each wrong answer is wrong, with jurisdiction handling per the rules above.
4. At session end, report:

```markdown
## Session: [Subject], [N] questions

**Score:** [X]/[N] ([percentage])
**Missed:** [list — subtopic + what went wrong]
**Weak subtopics:** [the 2-3 subtopics where misses clustered]
**Strong subtopics:** [where the student nailed it]

**Pattern vs. prior sessions:** [if session_history has prior sessions on this subject: "Hearsay exceptions missed in 3 of last 4 sessions — this is stuck. Route to /law-student:socratic-drill." Or: "Improvement from 40% to 70% on Evidence. Still shaky on character evidence."]

**Study plan update:** Weak subtopics added to priority list. Next scheduled [Subject] session: [date from study-plan.yaml].
```

5. Append session results to `study-plan.yaml` under `session_history`:

```yaml
session_history:
  - date: 2026-05-08
    subject: Evidence
    type: bar-prep-mbe
    n_questions: 10
    score: 6
    weak_subtopics: [hearsay-exceptions, character-evidence]
    jurisdiction_mode: mixed  # or ube / state-specific
```

If no `study-plan.yaml` exists, write session history to `~/.claude/plugins/config/claude-for-legal/law-student/session-history.yaml` instead so future sessions can still weight appropriately.

## MBE mode

> **Note on "MBE" terminology.** The traditional UBE uses the MBE (Multistate Bar Examination) for the multiple-choice portion. The NextGen Bar Exam replaces the MBE with its own integrated multiple-choice + short-answer question sets. If the student is sitting for the NextGen, generate NextGen-style questions (integrated foundational concepts across subjects, some shorter scenarios with selected-response answers) rather than classic MBE questions, and say so. Use the student's NCBE-listed subject outline as the subject universe.

### Generate questions

Classic MBE format (traditional UBE): fact pattern + call + four answer choices, one correct.
NextGen format: refer the student to released NextGen sample questions on the NCBE site for the current authoritative format and mimic that structure.

Subject distribution: weight toward weak subjects **within the subjects actually tested on the student's exam**. If `~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md` says weak on Evidence and Civ Pro, 60% of questions come from those.

Difficulty: bar-level. Not law school issue-spotter difficulty (which is higher). Bar questions are about knowing the black-letter rule and applying it cleanly.

### After each answer

Show correct answer + why each wrong answer is wrong.

```markdown
**Correct: C**

**Why C:** [the rule + application]

**Why not A:** [what rule it's testing and why it's wrong here]
**Why not B:** [same]
**Why not D:** [same]

**Rule to remember:** [the one-line takeaway]

---

**Citation check.** Rules and any cases cited in the explanation were generated by an AI model and have not been verified. Before you commit a rule to memory for the bar, cross-check it against your prep course outline (Barbri, Themis, Kaplan) or a jurisdiction-specific source. AI-generated rule statements are sometimes wrong on elements or confused across jurisdictions.
```

### Track patterns

Keep a running tally: which subjects, which sub-topics, which wrong-answer traps. After a session:

> "You missed 3 of 5 Evidence questions, all on hearsay exceptions. That's a pattern. Let's drill hearsay specifically."

## Essay mode

### Generate a prompt

Bar essay format for the student's exam and jurisdiction.
- **Traditional UBE states:** MEE format.
- **NextGen jurisdictions:** NextGen integrated performance task / short-answer format (per current NCBE released samples).
- **State-specific exams:** that state's essay format (California, Louisiana, etc.).

Subject per weak areas or user choice — **constrained to subjects tested on the student's exam.**

### Grade

After the student writes:

- Issue spotting: what did they spot, what did they miss
- Rule statements: accurate? Complete?
- Analysis: did they apply the rule to the facts, or just restate both?
- Organization: IRAC/CRAC or equivalent? Readable?

Bar grading is about competence, not brilliance. A complete, organized, accurate answer passes. A brilliant but incomplete answer doesn't.

```markdown
## Essay feedback

**Issues spotted:** [X] of [Y]
**Missed:** [list — these are points left on the table]

**Rule statements:** [Accurate / close / wrong — for each issue]

**Analysis:** [Did they actually apply, or just list rule + facts?]

**Organization:** [Clear or muddled]

**If this were graded:** [Pass / borderline / not yet — with what to fix]
```

## Schedule integration

If the student has a study schedule: weight questions toward what's on the schedule for this week. Fresh material gets drilled.

## What this skill does not do

- Replace a bar prep course. Barbri/Themis/Kaplan have the full curriculum. This is supplemental drilling.
- Predict the bar exam. Nobody can. Study everything.
- Pass the bar for you. Obviously.
- **State rules it isn't confident on without flagging.** If I'm not sure the rule is right, you will see `[UNCERTAIN]` or `[VERIFY]` — check the cited rule against your prep course before relying on the question. A wrong rule I state confidently is a worse study session than one I skip.
