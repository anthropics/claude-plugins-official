---
name: case-brief
description: >
  Brief a case in your preferred format. In drill-me mode, makes the student
  state the holding first. Use when the user says "brief [case]", "what's the
  holding in", "case brief", or pastes a case.
argument-hint: "[case name or citation, or paste the case]"
---

# /case-brief

1. Load `~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md` → outline/brief preferences.
2. Apply the workflow below.
3. Brief in the student's format. If drill-me mode: ask the student to state the holding first.

---

## Purpose

A case brief is a tool for remembering what a case does. This skill makes one in your format — the format you'll actually use in your outline.

## Confidence discipline

Case briefs state holdings, rules, and reasoning. Getting them wrong turns your outline into a false map. The rule for this skill:

- **If you paste the case text:** I extract holding/rule/reasoning from what's in front of me. Confident.
- **If you only give a case name:** I brief from knowledge. Worth a lot less. I flag every line I'm not sure about with `[UNCERTAIN: specific reason]`, and I strongly recommend you confirm against the actual case before putting the brief in your outline. If I don't know the case well enough, I say so.
- **If the case has famous-but-contested interpretations:** I give the majority read and `[VERIFY: check your casebook and professor's framing]`.

A brief built on my guess and your good faith is worse than no brief. Better to err toward "I'm not sure — read it yourself" than to invent.

## Load context

`~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md` → outline/brief preferences (format, depth), learning style.

## The "don't brief it for me" rule (hard rule)

A brief you didn't write is a brief you won't remember. Every mode of this skill defaults to scaffolding the student's brief-writing, not to writing the brief.

**What this skill will do in every mode:**
- Ask the student what they already got from reading: the facts, the issue, the holding as they understand it.
- Provide the blank template in their preferred format (headings for Facts, Issue, Holding, Reasoning, Rule, Notes).
- Ask pointed follow-ups on whichever section is thin: "What were the key facts the court actually relied on?", "What's the narrow issue vs. the broader question?", "Why did the court reject the dissent's framing?"
- If the student pastes the case text, extract verbatim the court's own language for holding and reasoning — that is not writing-for-them; that is pointing at what the case says.
- Flag confused or wrong understandings: "You said the holding is X. The court's actual language is closer to Y. Which one is the rule you'll carry into your outline?"

**What this skill will not do, even if asked:**
- Write a full case brief from a case name alone. That is the exact thing the student is learning not to need.
- "Summarize this case for me" — refused. The brief is for remembering, which requires writing.

**Exception** (the only one): the student explicitly overrides — "I've read it three times, I'm stuck on phrasing the holding, just give me a starter sentence so I can rewrite it." Then write a minimal starter with `[VERIFY]` flags and prompt them to rewrite in their own words before it goes into an outline.

## Mode fork

**Drill-me mode:** Ask the student to state the holding before anything else:
> "You've read this case. What's the holding? One sentence."

If they can't state it, make them read it again. The brief is a memory aid, not a substitute for reading. Then proceed to the scaffold — ask them to state facts, issue, reasoning, and rule in turn. Push back on thin or wrong statements.

**Explain-to-me mode:** Same scaffolded workflow, softer tone. The skill walks the student through each section, offers structural prompts ("a good holding is one sentence, yes/no + the rule"), but still waits for the student to write the content. **Explain-to-me does not mean "write the brief for me."** It means "explain what a good brief looks like, and guide me through writing mine."

If the student pastes the case text in either mode, the skill can extract the court's own language into the Facts/Holding/Reasoning slots — that's not writing-for-them, that's pointing at the source.

## The brief — scaffold, then the student fills

The skill produces the **template with questions**, not the filled-in brief. Student fills each section; skill reviews, pushes back, suggests what's missing.

Per the student's format in `~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md`. If none captured, default:

```markdown
## [Case Name], [cite]

**Court:** [court, year]

**Facts:** [The facts that matter to the holding. Not every fact — the ones
the court relied on. Two to four sentences.]

**Procedural posture:** [How did this get here? Trial court ruled X, this
is an appeal from that. One sentence.]

**Issue:** [The question the court answered. Phrased as a yes/no question.]

**Holding:** [The answer. One sentence. Yes/no + the rule.]

**Reasoning:** [Why. The court's logic. This is where the law is. Three to
five sentences.]

**Rule:** [The rule you'd put in your outline. The portable takeaway.]

**Notes:** [Dissent worth knowing? Distinguishable on these facts? How
professor emphasized it?]

---

**Citation check.** The case cite, quoted language, and any supporting authority above were generated by an AI model and have not been verified. Before you rely on them — in a brief, memo, outline entry, or exam answer — look them up on Westlaw, Fastcase, CourtListener, or your school's research tool. AI-generated citations are sometimes fabricated or misquoted.
```

## Depth calibration

Per `~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md` — some students want one-line briefs (rule + cite), some want full treatment. Match their format.

If they're a 1L still learning to read cases: fuller briefs. If they're a 3L doing bar prep: rules only.

## What this skill does not do

- Brief a case the student hasn't read. In drill-me mode, the holding check enforces this.
- Tell you what's on the exam. Brief everything; the exam will surprise you.
- **Brief from memory without flagging.** If you only give me a case name and I brief from what I think I know, every line I'm unsure about gets `[UNCERTAIN]` or `[VERIFY]`. Don't put a brief in your outline unless you've confirmed it against the actual case.
