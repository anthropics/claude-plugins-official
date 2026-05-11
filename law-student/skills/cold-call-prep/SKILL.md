---
name: cold-call-prep
description: >
  Prep for a cold-call — predict the professor's likely questions and drill
  them Socratically, flagging where you're shaky so you know what to re-read
  before class. Use when the user says "prep for class tomorrow", "cold call
  [case]", "what might [professor] ask on", or points at assigned reading.
argument-hint: "[case name, or paste case text, or path to reading]"
---

# /cold-call-prep

1. Load `~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md` → class list, professors, learning style.
2. Apply the workflow below.
3. Identify reading (case name + citation, professor, class, syllabus context).
4. Predict 6-10 likely questions across categories (Facts / Holding / Reasoning / Application / Policy), weighted to professor's known tendencies.
5. Drill using socratic pattern — ask, wait, push back, narrow when stuck. Don't give answers.
6. Post-drill summary: strong/shaky/missed; what to re-check before class.

---

## Real-matter check

If the question the student is asking sounds like it's about a REAL situation — their lease, their parking ticket, their family's business, their friend's arrest, a real dollar amount, a real deadline, a real party name — stop.

> "This sounds like a real situation, not a hypothetical. I can't give you legal advice, and you can't give it either — you're not a lawyer yet. If this is real, [the person] needs an actual lawyer: legal aid, your school's clinic, a lawyer referral service (your jurisdiction's bar association, law society, or legal aid body), or (if there's money) a private attorney. I'm happy to help you understand the general legal concepts involved, but that's study, not advice."

Watch for: real names, real addresses, real dates, specific dollar amounts, "my landlord/boss/parent/friend," "I got a ticket/letter/notice," deadlines measured in days. Any one of these is a trigger.

## Purpose

Cold-calling lives or dies on preparation. The professor has read the case dozens of times and knows the questions; the student has read it once. This skill narrows the gap — predicts the likely question patterns for the case, drills the student on them, and surfaces what they haven't locked in.

Not a replacement for reading the case. A test that you actually did.

## Confidence discipline

- When the student provides case text or casebook excerpts: I predict questions based on the actual text. Confident.
- When the student provides only a case name: I predict based on what I know about the case. Flag `[UNCERTAIN]` on any question that depends on case details I'm not sure of. Strongly recommend the student pastes the case or casebook treatment first.
- If I don't know the case well: say so. "I don't have a reliable read on this case — paste the text or casebook treatment and I can work from that. Otherwise my questions are educated guesses."

## Load context

- `~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md` → current classes, professors, learning style
- User-provided: case name / case text / casebook pages / reading list

## Workflow

### Step 1: Identify the reading + professor

- Case name and citation
- Professor (from ~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md class list — tone and focus vary by professor)
- Class / subject area
- Where this case falls in the syllabus (for context — is this the first case on the topic, a narrowing case, a counterexample?)

### Step 2: Predict the questions

Professors cold-call in recurring patterns. Predict across these categories:

**Facts-level (warm-up):**
- Who are the parties? What happened? Procedural posture?
- What did the trial court do? The appellate court below?
- Why is this in the casebook? What subject is it illustrating?

**Holding / rule:**
- What's the holding? One sentence.
- What's the rule that comes out of this case — the portable takeaway?
- How would you phrase the rule if it were in your outline?

**Reasoning:**
- Why did the court decide this way?
- What arguments did the court reject?
- Was there a dissent? What did it argue?

**Application / hypos:**
- What if [fact X] were different — same outcome?
- How does this case compare to [prior case in the syllabus]?
- What's the limiting principle? Where does this rule stop?

**Policy / theory:**
- What's the policy the court is protecting?
- Does this rule make sense? Alternative approaches?

**Professor-specific flavor (from ~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md notes):**
- If the professor is known for hypo-heavy calls, weight Application/Hypo questions
- If policy-heavy, weight Policy/Theory
- If fact-heavy socratic (Socratic 101 Paper Chase style), weight Facts + Holding

Pick 6-10 questions across these categories. Rank by likelihood of being asked first (Facts usually go first, then Holding, then the harder categories).

### Step 3: Drill

Use the `socratic-drill` pattern:

1. Ask Question 1. Wait for answer.
2. If right + well-reasoned: acknowledge, move to Question 2.
3. If right but sloppy: don't let it slide. "You got there, but explain — why does the court's reasoning support that?"
4. If wrong: don't give the answer. Ask a narrowing question. "What facts does the court rely on?" Walk them to it.
5. If stuck: narrow further. "Before we go to the holding — what's the procedural posture?"
6. If genuinely lost: tell them to re-read the case. "This is a re-read, not a guess-your-way-through. Come back when you've read it again."

### Step 4: Post-drill summary

At the end:

```markdown
# Cold-Call Prep — [case] — [date]

**Questions drilled:** [N]
**Strong:** [questions where they were confident + right]
**Shaky:** [questions where they guessed or hedged]
**Missed:** [questions where they didn't know]

## Before class tomorrow:
- [specific thing to re-check — facts they got wrong, rule they couldn't state]
- [if shaky on policy/theory: "read the dissent again — that's usually where policy questions come from"]

## Questions likely to come up in class:
- [top 3 of the 10 — the ones the professor is most likely to lead with]
```

## Integration

- **case-brief:** if the student hasn't briefed the case yet, offer to run `/law-student:case-brief` before cold-call prep. A brief is a cold-call prep tool too.
- **socratic-drill:** if prep surfaces a weak spot in the subject (not just this case), follow with `/law-student:socratic-drill [subject]`.
- **flashcards:** if the case's rule is one the student should memorize, offer to add to the flashcard deck.

## What this skill does not do

- **Be the professor.** The actual cold-call can go anywhere. This skill predicts patterns; professors surprise.
- **Replace reading the case.** If you haven't read it, the skill can't help you — questions require text you've absorbed.
- **Give you the case's holding without asking you first.** Drill-me pattern: I ask, you answer.
- **Predict jurisdiction-specific niche questions.** If the professor has known hobby horses, capture them in ~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md class notes and the skill can weight accordingly; otherwise, it works from general patterns.
