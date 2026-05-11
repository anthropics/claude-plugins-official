---
name: study-plan
description: >
  Build or update a long-term bar prep (or exam prep) study plan — phases,
  subjects weighted by weakness, daily session schedule, adaptive to session
  history in study-plan.yaml. Use when the user says "build a study plan",
  "plan my bar prep", "schedule my studying", or "how should I study for [X]".
argument-hint: "[--build | --update | --status | --cram]"
---

# /study-plan

1. Load `~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md` → bar jurisdiction, exam format, bar date, weak subjects, target study hours/day, prep course.
2. Load `~/.claude/plugins/config/claude-for-legal/law-student/study-plan.yaml` if it exists.
3. Apply the framework below.
4. Route by flag:
   - `--build` (default if no plan exists): walk the inputs gate (exam, subjects, hours/week, days off, methods). Build the phase structure + daily schedule for the first two weeks. Write `study-plan.yaml`.
   - `--update` (default if plan exists): re-read `session_history`, adjust subject priorities and weekly_hours, fill in the next stretch of daily schedule.
   - `--status`: what's scheduled today / this week, score trend, subjects slipping, next scheduled session per subject.
   - `--cram`: force cram mode — 80/20 high-yield prioritization, daily MBE volume, taper last 2-3 days.
5. Before writing: summarize the plan in prose and confirm with the student. Adjust based on their answer.
6. Always sanity-check hours/week against the student's stated life constraints. Over-ambitious plans fail.

---

## Purpose

Sitting down to study and not knowing what to study is how weeks disappear. This skill builds a plan — weeks to exam, sessions per day, subjects per week, session types — and then adapts as the student actually does the sessions. It is a living plan, not a calendar export.

It also gives downstream skills (bar-prep, flashcards, drill, irac) a shared schedule to honor, so the student isn't asked "what do you want to study today" every time they open a session.

## Confidence discipline

A plan is opinion, not doctrine. The skill states clearly what's an estimate:

- **Time-per-topic estimates** are general guidance (based on typical Barbri/Themis/Kaplan weightings). Flag them as estimates — the student's real pace will differ.
- **Subject weightings** are derived from the student's own reported weak subjects and session history. Confident.
- **High-yield-topic prioritization in cram mode** is based on multi-year bar exam release patterns (MBE/MEE subject frequency). Flag any "this is definitely on the exam" claim as `[UNCERTAIN — past frequency is not a prediction]`.

## Load context

`~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md`:
- Bar jurisdiction, exam format, bar date
- Current classes (for non-bar use)
- Weak subjects (MBE, essay)
- Prep course
- Target study hours/day

`~/.claude/plugins/config/claude-for-legal/law-student/study-plan.yaml` if it exists — extend, don't overwrite.

## Workflow

### Step 1: What are we planning for

> What are we building a plan for?
>
> 1. **Bar exam** (you have a bar date in mind)
> 2. **A specific law school exam or set of finals**
> 3. **General semester study cadence** (outlining, reading, drilling across all classes)

For (1) bar: read bar date from practice profile, confirm. If no bar date captured, ask.
For (2) law school exam: ask which class, what date, what format.
For (3) semester: ask for the term-end date as the anchor.

### Step 2: Inputs — one at a time, wait for each

**Ask and wait.** Do not bulk all questions into one prompt and move on.

- **Exam date:** confirmed? (If bar: ask for jurisdiction if not in practice profile — study content depends on it.)
- **Subjects to cover:** for bar, read from NCBE subject outline for the exam format (NextGen / traditional UBE / state-specific). For a class, the syllabus. Confirm with student — "any subject I should add or drop?"
- **Strongest subjects:** least priority. Still reviewed, not drilled heavily.
- **Weakest subjects:** most priority. Get more sessions.
- **Hours per week available:** realistic, not aspirational. "I can do 20 hours" is different from "I will do 20 hours for 8 weeks." Ask what they can actually sustain.
- **Life-context sanity check — force it.** After the student gives a number, ask (one question at a time — do not skip):

  > You said [N] hours per week. Before I build this, tell me what else is in your week — job (hours/week), family (kids, caregiving), commute, workout, therapy, clinic, anything meaningful. The plan should fit your life, not the other way around. A plan you can't follow is worse than a lighter plan you can.

  Wait for the answer. Then sanity-check the stated hours against their reported load:

  > That's ~[X] hours/day across [N] study days, on top of [job + family + commute + other]. In my experience that's [realistic / tight / unsustainable]. Want to adjust the hours/week target before I build, or keep them and see how week 1 goes?

  Do not skip this step even if the practice profile's target hours number was already captured at cold-start. The profile captures what the student said; the life-context check captures whether it's sustainable. If the check produces a lower number, use the lower number for the plan and note the adjustment in the `confidence_flags` block.

  If the student declines to share life context ("just build it"), respect that — but add a `confidence_flags` entry: "Life-context check declined; plan assumes [N] hours/week is sustainable. Revisit at end of week 2 if adherence is below [X]%."
- **Preferred study methods:** multi-select. MBE practice / essays / flashcards / outlining / drilling / re-reading. Weight the schedule toward the methods they say they'll actually do.
- **Days off per week:** rest days matter. Plans that schedule 7/7 days fail in week 3.

### Step 2.5: Supplement vs. replace (prep-course users)

If `~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md` → `Prep course` is **Barbri**, **Themis**, **Kaplan**, or any other structured prep course (i.e., NOT `self` or `N/A`), the student already has a prep-course calendar. This skill's plan must choose one of two roles — it cannot run a full parallel curriculum alongside the prep course without burning the student out.

Ask, one question, wait:

> Your profile says you're on [Barbri / Themis / Kaplan]. They publish a day-by-day calendar with every subject and task scheduled. Two ways this plan can work — pick one:
>
> 1. **Supplement.** The prep course is your primary curriculum. This plan fills gaps: extra MBE drilling on your weak subjects, targeted essay practice, flashcard loops on the topics you're missing. I won't rebuild the prep-course calendar; I'll layer on top of it.
> 2. **Replace.** You're not following the prep-course calendar (maybe because its pacing doesn't work for your life). I'll build the whole plan — subjects, hours, phases, schedule — and you drop the prep-course calendar.
>
> Don't pick both. Running two full curricula against each other is how students blow up in week 4.

Wait for the answer. Record it in the yaml as `prep_course_mode: supplement | replace`.

If **supplement**: the plan's daily schedule is lighter — it only adds weak-subject drilling and targeted practice, does not duplicate prep-course coverage. Flag in `confidence_flags`: "Supplement mode — this plan assumes you're on track with [prep course] for primary coverage. If you fall behind on the prep course, tell me and we'll re-plan."

If **replace**: build the full plan as specified below.

If the student's prep course is `self` or `N/A`, skip this step — there's nothing to supplement.

### Step 3: Build the schedule

Calculate weeks-to-exam from today's date. Then:

**Normal mode (4+ weeks out):**
- Split weeks into phases:
  - **Learning phase** (first ~60% of time): one subject per ~3-5 days, mixing outlining/reading with flashcards and a few MBE/essay questions on fresh material.
  - **Drilling phase** (next ~30%): more MBE volume, more essay practice, simulated conditions, all subjects in rotation.
  - **Review phase** (last ~10%): focused on weakest subtopics from session_history, full practice exams, light review of strong areas.
- Weight subjects by weakness: weak subjects get ~2x the hours of strong subjects.
- Schedule day-by-day: which subject, which method, how long. Leave slack for the student's actual life.

**Cram mode (< 4 weeks out):**
- Flag it: "You're less than four weeks out. This is cram mode — the plan prioritizes high-yield topics over full coverage. You will leave gaps. That's the tradeoff at this point."
- 80/20 prioritization: the MBE subjects that historically appear most (Civ Pro, Evidence, Con Law, Contracts) get the lion's share. Narrower subjects get minimum viable coverage.
- Daily schedule: MBE blocks every day (volume matters now), essay practice every other day, one simulated exam per week.
- Sleep and taper the last 2-3 days. Do not schedule hard drilling the day before the exam. This is real — students who cram through the night before score worse.

### Step 4: Write it

Write to `~/.claude/plugins/config/claude-for-legal/law-student/study-plan.yaml`:

```yaml
plan_type: bar  # or law-school-exam or semester
exam_date: 2026-07-28
jurisdiction: CA
exam_format: state-specific  # or NextGen / UBE
created: 2026-05-08
last_updated: 2026-05-08
weeks_to_exam: 12
hours_per_week: 25
days_per_week: 6
mode: normal  # or cram
phases:
  - name: learning
    start: 2026-05-08
    end: 2026-06-20
    focus: outlining, flashcards, introductory MBE
  - name: drilling
    start: 2026-06-21
    end: 2026-07-18
    focus: MBE volume, essay practice, simulated conditions
  - name: review
    start: 2026-07-19
    end: 2026-07-27
    focus: weak-subtopic review, full practice exams
subjects:
  evidence:
    priority: high  # weak
    weekly_hours: 5
    methods: [mbe, flashcards, essay]
  con-law:
    priority: medium
    weekly_hours: 3
    methods: [mbe, outline-review]
  # etc.
schedule:
  - date: 2026-05-08
    day: Thursday
    sessions:
      - subject: Evidence
        method: outline-review
        duration_min: 90
      - subject: Evidence
        method: mbe
        duration_min: 60
        n_questions: 25
  - date: 2026-05-09
    day: Friday
    sessions:
      - subject: Contracts
        method: flashcards
        duration_min: 45
      - subject: Contracts
        method: essay
        duration_min: 60
  # etc.
session_history: []  # appended by bar-prep, flashcards, drill, irac as sessions complete
```

### Step 5: Confirm with the student

**Header — required on every in-chat presentation and on any separate prose-format plan document written alongside the YAML.** The first line of the summary (and the first line of any `study-plan.md` companion file) must be the verbatim header from plugin config `## Outputs`:

```
STUDY NOTES — NOT LEGAL ADVICE
```

The header does not go inside the YAML itself (it's a data file), but it belongs on the prose summary you show the student and on any human-readable plan document you save next to the YAML. This is not a disclaimer afterthought — it is the output's identity. Do not omit, rephrase, or relocate it.

Summarize the plan in prose (not raw YAML) before saving, with the header on top:

> STUDY NOTES — NOT LEGAL ADVICE
>
> Here's what I built. [X] weeks to the [exam]. [Y] hours/week across [Z] days. Weak subjects (Evidence, Contracts) get 2x the hours. Three phases: learning through [date], drilling through [date], review the last [N] days. I've scheduled the first two weeks day-by-day. Beyond that it's allocated by week — I'll fill in the daily schedule as you complete sessions, so the plan adapts to where you actually are.
>
> Does this feel right? Too ambitious? Too light? Missing a subject?

Adjust based on the answer. Then write.

## Adapting the plan

After each session (via bar-prep-questions, flashcards, drill, irac), the corresponding skill appends to `session_history`:

```yaml
session_history:
  - date: 2026-05-08
    subject: Evidence
    type: bar-prep-mbe
    n_questions: 10
    score: 6
    weak_subtopics: [hearsay-exceptions, character-evidence]
```

On the next `/law-student:study-plan --update` run (or when any skill detects the plan is stale):
- Subjects with consistently low scores get promoted in `priority` and `weekly_hours`.
- Weak subtopics within a subject get flagged for the next scheduled session on that subject.
- If the student is falling behind (scheduled sessions not appearing in history), adjust: either compress coverage or note the gap and ask.
- If the student is ahead, open up time for deeper weak-subject drilling.

## Modes

`--build` (default) — fresh plan
`--update` — re-read session_history and adjust weightings, fill in upcoming daily schedule
`--status` — what's on deck today / this week, what's the score trend, what's slipping
`--cram` — force cram mode even if more than 4 weeks out (user override)

## Integration

- `/law-student:session <subject> <n>` writes results to this plan's `session_history`.
- `/law-student:bar-prep-questions` reads the plan to know which subject is scheduled for today.
- `/law-student:flashcards` can `--session <n>` and results land in the plan.
- `/law-student:socratic-drill` and `/law-student:irac-practice` session completions also append.

## What this skill does not do

- **Guarantee you pass.** The plan is a scaffold. The work is on you.
- **Predict the exam.** Cram mode uses historical subject frequency; high-yield ≠ guaranteed-tested.
- **Replace your prep course schedule.** If you're on Barbri/Themis/Kaplan, this plan can supplement — don't run two full curricula against each other. Use one as primary.
- **Schedule your life.** Hours available is what you tell me. If you overstate, the plan will break in week 2. Be honest.
