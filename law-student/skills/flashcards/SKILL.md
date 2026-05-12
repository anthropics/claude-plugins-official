---
name: flashcards
description: >
  Generate or drill flashcards for black-letter memorization — Leitner-style
  buckets, per-subject markdown storage, drill mode with self-assessment. Use
  when the user says "drill flashcards", "make flashcards from", "quiz me on
  cards", or wants to memorize rules.
argument-hint: "[subject] [--generate | --drill | --review | --stats | --session <n>]"
---

# /flashcards

1. Load `~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md` → current classes, weak subjects, outline locations.
2. Apply the framework below.
3. Route by flag:
   - `--generate`: build cards from source (outline path, notes, casebook) per card-writing rules. Write to `~/.claude/plugins/config/claude-for-legal/law-student/flashcards/[subject]/cards.md`.
   - `--drill` (default): prioritize due cards + new; show Q, wait for answer, show A, take self-assessment, update buckets + next review.
   - `--review`: browse deck by bucket.
   - `--stats`: progress snapshot; flag stuck cards for verbal drill.
   - `--session <n>`: focused N-card session, prioritized by prior misses + due cards; appends results to `study-plan.yaml` → `session_history`.
4. Apply confidence discipline: flag every card generated from knowledge-without-source with `[VERIFY]`.

---

## Real-matter check

If the question the student is asking sounds like it's about a REAL situation — their lease, their parking ticket, their family's business, their friend's arrest, a real dollar amount, a real deadline, a real party name — stop.

> "This sounds like a real situation, not a hypothetical. I can't give you legal advice, and you can't give it either — you're not a lawyer yet. If this is real, [the person] needs an actual lawyer: legal aid, your school's clinic, a lawyer referral service (your jurisdiction's bar association, law society, or legal aid body), or (if there's money) a private attorney. I'm happy to help you understand the general legal concepts involved, but that's study, not advice."

Watch for: real names, real addresses, real dates, specific dollar amounts, "my landlord/boss/parent/friend," "I got a ticket/letter/notice," deadlines measured in days. Any one of these is a trigger.

## Purpose

Outlines are for synthesis; flashcards are for memorization. The bar exam and most law school exams reward fast rule recall. This skill generates cards from your outline (or notes or casebook excerpts), drills them with light spacing, and tracks what's stuck and what hasn't.

**Not a full SRS system.** Simple Leitner-style buckets. Good enough to study, light enough to maintain. If you want Anki, use Anki; this is for when you're in chat and want a quick drill.

## Confidence discipline

Same rule as the other content-generating skills:

- If generating cards from a source you provide (outline, notes, casebook excerpt), the card's Q and A come from that source. Confident.
- If generating cards from my knowledge without a source, I flag every card that states a rule I'm not fully confident on with `[VERIFY: rule — confirm against source]`. You should check before committing to the card as a learning target.
- If I don't know an area well, I generate fewer cards rather than inventing. Better to have 8 good cards than 20 where 5 are wrong.

## Load context

- `~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md` → current classes, weak subjects, existing outlines
- `~/.claude/plugins/config/claude-for-legal/law-student/flashcards/[subject]/cards.md` if it exists (incremental build)
- User-provided source (outline path, notes, casebook excerpt) if given

## Modes

Flag: `--generate | --drill | --review | --stats | --session <n>` (default: prompt)

### `--session <n>` — focused N-card session

For when the student says "let's do 5 cards on Contracts" or runs `/law-student:session Contracts 5 --flashcards`.

- Load `~/.claude/plugins/config/claude-for-legal/law-student/study-plan.yaml` if it exists and read `session_history` for this subject.
- Prioritize: cards previously marked wrong > due cards > new cards.
- Run N cards one at a time per the `--drill` flow.
- At session end, append results to `study-plan.yaml` → `session_history`:

```yaml
session_history:
  - date: 2026-05-08
    subject: Contracts
    type: flashcards
    n_cards: 5
    right: 3
    partial: 1
    wrong: 1
    stuck_topics: [parol-evidence-rule]
```

- If no `study-plan.yaml`, write to `~/.claude/plugins/config/claude-for-legal/law-student/session-history.yaml` instead.

### `--generate` — create cards

**Inputs:**
- Subject (class name or topic)
- Source (outline path, notes, or "use my existing outline from ~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md")
- Optional: card count target (default 10-20 per session)

**Card structure:**

```markdown
### Card [N]
**Q:** [question — one concept, one card]
**A:** [answer — the rule, one or two sentences]
**Source:** [outline section, casebook page, class note date]
**Bucket:** new
**Last reviewed:** —
**Next review:** [today's date]
**Notes:** [optional — distinctions, exceptions, traps]
```

**Card-writing rules:**
1. **One concept per card.** "Elements of negligence" becomes 4 cards, not 1.
2. **Front is a question, not a topic.** "Negligence duty" bad. "What are the four elements of negligence?" good.
3. **Back is a rule, not a paragraph.** If the answer needs a paragraph, split into multiple cards.
4. **Cite the source** so you can re-check during drill.

**Citation check.** When cards are generated from my knowledge rather than a source you pasted, the rule and any case/statute cited on the back were generated by an AI model and have not been verified. Before you memorize a card, confirm it against your outline, casebook, or a research tool (Westlaw, Fastcase, CourtListener). A wrong card drilled to mastery is worse than no card.

### `--drill` — study session

**Prioritization:**
1. Cards where `next_review <= today` AND bucket != mastered
2. New cards not yet attempted
3. If no cards due and no new cards: ask if user wants review of mastered cards (for decay prevention)

**Drill flow per card:**
1. Show Q. Wait for answer.
2. User answers (or types "skip" / "don't know")
3. Show A.
4. User self-assesses: `right` / `partial` / `wrong` / `don't know`
5. Update bucket + next review per the table below:

| Self-assessment | Bucket change | Next review |
|---|---|---|
| right | up one (new → learning → review → mastered) | +1d new, +3d learning, +7d review, +21d mastered |
| partial | same bucket | +1d |
| wrong | down one (review → learning; learning → new; new stays new) | today +4h |
| don't know | down one | today +4h |

### `--review` — browse deck

Show all cards in a subject. Grouped by bucket. Useful for scanning what's in the deck and manually adjusting card content.

### `--stats` — progress snapshot

Per subject: total cards, bucket distribution, due today, reviewed this week. Highlight any cards that have bounced down to `new` more than twice — those are the stuck concepts worth drilling verbally via `/law-student:socratic-drill`.

## Integration with other skills

- **outline-builder:** after building or extending an outline, offer to generate flashcards from the new material
- **socratic-drill:** if a card has been wrong 2+ times, route it to `/law-student:socratic-drill` for verbal working-through — flashcards aren't enough for concepts you don't actually understand
- **bar-prep-questions:** bar prep subjects with poor flashcard stats weight higher in MBE drilling

## Storage

```
flashcards/
└── [subject]/
    └── cards.md
```

One file per subject. Cards are markdown. Bucket/review metadata is inline per card. Not optimal for very large decks (>500) but fine for typical law school deck sizes.

## What this skill does not do

- **Replace Anki.** If you already have a flashcard habit, keep it. This is for when you're in chat and want to drill without switching apps.
- **Invent cards to hit a count target.** If I can only generate 8 confident cards from your source, you get 8. Padding with `[VERIFY]`-heavy guesses is worse than a smaller deck.
- **Enforce study discipline.** Missed review days compound; the skill just shows what's due. You decide whether to drill.
- **Teach you the rule.** Cards are for drilling what you've already studied. If a card is consistently wrong, the problem is upstream — use `/law-student:socratic-drill` or re-read the source.
