# Law Student Plugin

Learning mode, not answer mode. Socratic drilling that asks YOU questions and pushes back on sloppy reasoning. Case briefing, outline building, flashcards, IRAC grading, cold-call prep, writing feedback that never rewrites for you, and exam forecasting from past professor exams. Calibrated to you — your classes, your bar jurisdiction, whether you want to be drilled or scaffolded.

**Every output is a study scaffold, not a model answer. The plugin structures your thinking, drills you Socratically, and flags what you got wrong. It doesn't write the outline, the brief, or the essay for you — that would defeat the purpose. Citations in study materials are tagged for verification.**

## Who this is for

Law students. 1L through bar prep.

## First run: cold-start

This one's about you, not an org. Your classes, your bar jurisdiction, your learning style — drill-me vs. explain-to-me. Bring materials: past outlines, graded essays, old exams (especially same-professor), MBE sets, syllabi, papers. Ten to twenty items is the target; below that the practice profile is flagged `LIMITED DATA` and downstream skills will be thinner until more is added.

```
/law-student:cold-start-interview
```

## Skills

Every skill is invoked as `/law-student:<skill-name>`.

| Skill | Does |
|---|---|
| `/law-student:cold-start-interview` | About-you interview + materials intake — classes, bar, learning style, materials |
| `/law-student:socratic-drill [subject]` | Socratic drilling — it asks, you answer, it pushes back. Does not give the answer. |
| `/law-student:case-brief [case]` | Case brief in your preferred format |
| `/law-student:outline-builder [subject]` | Build or extend an outline in your format from class materials |
| `/law-student:bar-prep-questions [subject]` | Bar prep questions, MBE or essay — jurisdiction-aware (UBE / NextGen / state-specific), flags majority/UBE vs. your state's rule |
| `/law-student:flashcards [subject]` | Generate or drill flashcards; Leitner-style buckets; per-subject markdown; `--session <n>` mode |
| `/law-student:study-plan` | Build or update a long-term study plan — phases, subjects by weakness, adaptive daily schedule from session history |
| `/law-student:session <subject> <n>` | Focused N-question session on a subject; updates the plan with results |
| `/law-student:irac-practice` | Grade your IRAC essay — structure, issues, rules, analysis. Tracks patterns across sessions. Never rewrites. |
| `/law-student:cold-call-prep [case]` | Prep for cold-call — predict professor questions and drill them |
| `/law-student:legal-writing [path-or-paste]` | Structural feedback on any draft — never rewrites, ever |
| `/law-student:exam-forecast [class]` | Analyze past exams from same professor; forecast upcoming |

## What "learning mode" means

Several skills here (socratic-drill, case-brief in drill-me mode, cold-call-prep, irac-practice, legal-writing) are deliberately built to *not* give you the answer or write the thing for you. The point is that you learn by doing. If you want an answer or a draft, use a different tool. This plugin is for the struggle.

**legal-writing is the strictest.** It reads your draft and tells you what's weak, but does not rewrite. Asking it to rewrite will return a polite refusal plus an offer of more specific structural feedback. This is a feature.

**outline-builder and case-brief follow the same rule in a softer form.** Outline builder scaffolds — topic tree, sub-topic slots, case placeholders — and asks Socratic questions as you fill the rules from your own notes and casebook. It won't generate a populated outline from a syllabus alone. Case brief works the same way in every mode (drill-me and explain-to-me both): the skill gives the template and pushes back on what you wrote; it doesn't brief the case for you. If you paste the case text, it can extract the court's own language into the slots — that's pointing at the source, not writing for you.

## Academic integrity

Before using this plugin on any graded work — take-home exams, graded writing assignments, journal notes, papers — check your school's honor code and your professor's syllabus policy on AI tools. Many schools prohibit or restrict AI use on graded work, and the rules vary by course and professor. This plugin is designed for study and practice; using it where your school prohibits it is an honor code violation, and the consequences are yours, not the tool's. When in doubt, ask your professor in writing.

The learning-mode skills here (socratic-drill, irac-practice, legal-writing, cold-call-prep) are deliberately designed to not give you the answer or write the thing for you — that's the pedagogy. It's also the design assumption behind treating some permitted uses (unassisted-looking practice drilling) differently from prohibited ones (ghostwriting a graded memo). Don't work around the guardrails.

## Confidence markers

Content-generating skills flag their confidence inline. A rule statement or card without a marker is something the skill is confident on (but still not a substitute for your own source-checking before an exam). Markers used across the plugin:

- `[VERIFY: claim — check source]` — stated as likely correct, but you should confirm against your outline, casebook, prep course, or the primary source before relying on it. Used liberally in bar-prep-questions, case-brief, flashcards, legal-writing, irac-practice.
- `[UNCERTAIN: specific reason]` — the skill is not confident on this specific call (minority rule, debatable issue-spot, jurisdiction the skill doesn't know well). Make your own judgment; check the source.
- `[GAP — fill from class notes]` — outline-builder marker for a topic where the skill has no reliable source and won't invent a rule. You fill it from your notes.
- `[NEEDS CASES — rule stated but no illustrating case]` — outline-builder marker where the rule is there but the case illustration is missing.
- `[CHECK CLASS NOTES — professor may have emphasized something here]` — outline-builder marker for areas where professor-specific emphasis matters and the skill can't know it.
- `[EXCEPTION UNCLEAR — casebook mentions an exception, find the rule]` — outline-builder marker for a known exception with unresolved detail.
- `[UNCERTAIN — framing]` — exam-forecast marker noting that a forecast is a weighting for study time, not a prediction.

Trust the flags more than the absence of flags — an unflagged rule is something the skill is confident on, but exam prep still demands source-checking.

## Connectors and citation verification

**Connect a research tool first — the citation guardrails depend on it.** Without one, every cite is tagged `[verify]` and the reviewer note above each deliverable records that sources weren't verified. The plugin works either way; it just does more of the verification for you when a research tool is connected.

The legal research connectors in this plugin aren't just data sources — they're the difference between a verified citation and a citation you have to check. A citation retrieved through **CourtListener** (U.S. court opinions, PACER dockets, citation verification) or **Descrybe** (primary-law search, citation treatment, quoted-language verification) is tagged with its source and can be traced back. A citation from the model's knowledge or from web search is tagged `[verify]` or `[verify-pinpoint]` and should be checked against a primary source before anyone relies on it. The plugin tiers its citations so your verification time goes where it matters.

## Storage

Your practice profile is stored at `~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md` and survives plugin updates. Everything else is in your working directory:

```
law-student/
├── flashcards/
│   └── [subject]/cards.md             # per-subject flashcard decks
├── irac-sessions/
│   └── [student]/
│       ├── [date]-[topic].md          # individual session feedback
│       └── tracker.md                 # cross-session pattern tracking
├── writing-feedback/
│   └── [student]/
│       ├── [date]-[assignment].md     # individual session feedback
│       └── tracker.md                 # cross-session pattern tracking
└── exam-forecasts/
    └── [class]/
        └── forecast-[YYYY-MM-DD].md   # versioned forecasts
```

## Testing & QA


## How it learns

Your study profile at `~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md` isn't static — it improves as you use the plugin. Skills tell you when an output used a default you should tune. You can re-run setup, edit the file directly, or tell a skill to record a new position.

## Notes

- Drill-me vs. explain-to-me is set at cold-start; switch per session.
- Case briefs and outlines use YOUR format. If you have existing outlines, point cold-start at them.
- Bar prep targets your weak subjects from ~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md. It will keep coming back to them.
- Every content-generating skill flags when it's uncertain. Trust the flags more than the absence of flags — an unflagged rule is something I'm confident on; check your source anyway before an exam.
