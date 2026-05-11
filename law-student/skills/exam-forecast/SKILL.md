---
name: exam-forecast
description: >
  Analyze past exams from the same professor to surface patterns — subject
  weighting, recurring issue-spot traps, favored hypo types, policy-vs-doctrine
  mix — and forecast likely emphases for the upcoming exam. Use when the user
  says "what's on the exam", "analyze past exams", "predict the exam", or
  shares past exams.
argument-hint: "[class name, with past exams shared or paths to them]"
---

# /exam-forecast

1. Load `~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md` → class, professor, exam format, syllabus.
2. Apply the workflow below.
3. Intake past exams (PDF, paste, or paths). Confirm sample size.
4. Analyze each past exam: format, subject coverage, question style, fact-pattern density, recurring traps.
5. Cross-exam pattern analysis — what's stable, what varies.
6. Combine with current syllabus to produce forecast: subject weights, format, hobby horses, study emphasis.
7. Write `~/.claude/plugins/config/claude-for-legal/law-student/exam-forecasts/[class]/forecast-[YYYY-MM-DD].md`. Framed as weighting heuristic, not prediction.

---

## Purpose

Every professor's exam has fingerprints. The same hypo structures recur. The same traps come back. The same subject ratios repeat. Students who have prior exams study smarter; students who don't, study harder. This skill analyzes the prior exams you have and surfaces the patterns.

Not magic. A forecast, not a prediction. The skill cannot tell you what's on the exam — it can tell you what's been on past exams and what's likely to recur based on syllabus coverage.

## Confidence discipline

- Pattern analysis (what subjects appeared, how many questions per topic, how often policy vs. rule-application) — confident where the exams are clearly in front of me.
- Inference about likely emphasis on upcoming exam — `[UNCERTAIN]` is the default; these are forecasts, not certainties. Explicitly frame as "based on the [N] past exams you shared, [topic] appeared in [M]. Your upcoming exam may emphasize it, or the professor may rotate — use this as a weighting for review time, not a prediction."
- If only 1-2 past exams are available, say so explicitly — any pattern inferred from 1 exam is noise.
- If the professor is new (no past exams available), skill can't forecast. Say so; fall back to syllabus-based "these are the subjects covered" only.

## Load context

- `~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md` → current classes, exam formats, syllabus if captured
- User-provided past exams (PDF, pasted text, paths)
- Optional: syllabus for the current class (for "what's been covered to date")

**If the uploaded past exams have a professor's name, use it to match patterns** (same-professor exams are the highest-signal input). **If not, match on subject and structure.** Don't ask the user to type in the professor's name — use what's in the materials. If the user volunteers it in conversation that's fine; don't prompt for it.

## Workflow

### Step 1: Intake

- Which class are we forecasting for?
- How many past exams from this professor are available?
- Are they from the same course, or different courses by the same professor?
- Are any of them the take-home / open-book / different-format variants, vs. the typical format for your upcoming exam?
- Syllabus for your current class?

If fewer than 3 past exams: flag as thin sample. Pattern inference is weaker.
If exams are across different courses: some patterns transfer (question style, policy vs. doctrine ratio); subject-specific patterns don't.

### Step 2: Read each past exam

For each past exam:

- Format (number of questions, length, time limit, open/closed book)
- Subject coverage (which topics tested, in what proportion)
- Question style (issue-spotter, single-issue deep, policy essay, short-answer MBE-style, mix)
- Fact pattern density (fact-heavy hypos, sparse facts with doctrinal focus, or policy prompts with no facts)
- Recurring traps (e.g., professor always hides the jurisdictional issue in an otherwise-clean fact pattern; professor always asks about the exception rather than the rule)
- Policy vs. doctrine ratio
- Unusual structures (essays + MBE hybrid, moot court scenario, etc.)

### Step 3: Cross-exam pattern analysis

Roll up what's consistent across exams:

**Stable patterns (appeared in most/all past exams):**
- Subject weights (e.g., "consideration and modification account for 30% of exam points consistently")
- Question style (e.g., "always one long issue-spotter + two short-answer hypos")
- Professor hobby horses (e.g., "always tests third-party beneficiaries even when it's a minor topic in class")

**Variable patterns (appeared in some but not all):**
- Policy essays (e.g., "appeared in 2 of 4 past exams — usually when the semester covered a policy-heavy topic late")
- Open-book vs. closed-book differences
- Take-home vs. in-class differences

**Absent patterns worth noting:**
- Topics covered in class that have NEVER been tested in past exams — don't skip these, but don't weight them heavily either
- Topics tested in past exams that aren't in your current syllabus — probably not coming back

### Step 4: Forecast for the upcoming exam

**Header — required, first line of the forecast, both in-chat and in the saved file.** Per plugin config `## Outputs`, every study output carries the verbatim study-notes header. The forecast is a study output. Do not omit, rephrase, or relocate the header. The header is not a disclaimer the student can ask to drop; it is the output's identity and prevents the forecast from being mistaken for a predicted exam or for legal advice:

```
STUDY NOTES — NOT LEGAL ADVICE
```

Combine pattern analysis with current syllabus:

```markdown
STUDY NOTES — NOT LEGAL ADVICE

# Exam Forecast — [class / professor] — [date]

**Past exams analyzed:** [N]
**Sample confidence:** [thin (<3) / moderate (3-5) / strong (6+)]
**Caveats:** [e.g., "one of the past exams was an open-book final; your upcoming is closed-book. Pattern transfer is partial."]

---

## Subject weighting (historical)

| Topic | Past exam weight (avg) | In current syllabus? | Forecast weight |
|---|---|---|---|
| [topic 1] | [%] | [yes/partial/no] | [heavier / stable / lighter] |

## Question-style forecast

- **Format likely:** [X issue-spotters + Y short answers + Z policy, or similar]
- **Fact-pattern density:** [fact-heavy / sparse / mixed]
- **Call style:** [one broad call / multiple specific calls / bullet sub-parts]

## Professor hobby horses to watch

- [topic A] — appeared in [M of N] past exams. Weighted 3-5x its syllabus share.
- [topic B] — [pattern]
- [trap pattern] — e.g., "hides jurisdictional issue in otherwise-clean facts"

## Topics covered this semester but rarely tested

[list — don't skip, but don't over-weight]

## Study emphasis recommendation

Based on past exam patterns AND current syllabus coverage:

**Heavy:** [topics likely to anchor the exam — 40-50% of study time]
**Moderate:** [supporting topics — 30-40%]
**Sanity check:** [topics covered but historically under-represented — 10-20%, just in case]

## [UNCERTAIN — framing]

This forecast is derived from [N] past exams. Professors vary. Professors rotate. Topics that were emphasized in past years can be de-emphasized when the syllabus shifts. Treat this as a weighting heuristic for study time, not a prediction. The exam will include surprises.
```

### Step 5: Output location

Write to `~/.claude/plugins/config/claude-for-legal/law-student/exam-forecasts/[class]/forecast-[YYYY-MM-DD].md`. Versioned — if the student gets another past exam mid-semester, re-run and append.

## Integration

- **outline-builder:** forecast weights feed into outline depth decisions — weight depth on heavy topics
- **flashcards:** forecast-heavy topics get more cards generated
- **bar-prep-questions:** irrelevant for bar prep (that has its own forecast model); exam-forecast is for class-specific finals
- **irac-practice:** use forecast topics as the subject areas for IRAC practice hypos

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

## What this skill does not do

- **Predict specific questions.** Past exams show patterns; they don't show you tomorrow's prompt.
- **Work without past exams.** If you don't have prior exams from this professor, the skill can't forecast — it falls back to "here's what the syllabus covers, study that."
- **Replace studying everything on the syllabus.** Forecast is weighting, not elimination. Skipping a topic because it's historically under-represented is how students get burned.
- **Account for changes you don't know about.** If the professor has shifted focus this year (e.g., emphasized a new case in class lectures), the skill doesn't see that unless you tell it.
- **Work reliably with 1-2 past exams.** Thin sample. Flag as such.
