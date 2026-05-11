---
name: draft
description: >
  First draft of a common clinic document — practice-area templates (asylum
  applications, eviction answers, protective order petitions, demand letters),
  jurisdiction-aware formatting, explicitly a starting point requiring student
  analysis and attorney review. Use when a student needs a first draft of a
  motion, letter, petition, declaration, or other clinic document.
argument-hint: "[document type — e.g., 'eviction-answer', 'asylum-declaration', 'demand-letter']"
---

# /draft

1. Load `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md` → practice-area templates, jurisdiction, local rules, supervision style.
2. Use the workflow below.
3. Match doc type to template. Gather facts from case notes — flag missing, never guess.
4. Apply jurisdiction formatting. Draft with `[FACT NEEDED]`, `[VERIFY]`, `[UNCERTAIN]` flags inline.
5. Output with prominent AI-assisted label, student review checklist, supervision routing.

```
/legal-clinic:draft eviction-answer
```

```
/legal-clinic:draft asylum-declaration
```

---

# Draft: First-Draft Document Generation

## Purpose

Students spend enormous time on first drafts of documents where the educational value is in the analysis and strategy, not in formatting a caption or writing "Dear Judge." This skill produces the first draft from case notes and practice-area templates so the student's time goes to the thinking.

**Every draft is explicitly a starting point.** Not final work product. The student analyzes, revises, and the professor reviews before anything goes anywhere.

## Load context

`~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md` → practice areas, practice-area templates, jurisdiction (state + local court + any local rules ingested), supervision style.

Case notes or intake summary for the facts.

## Pedagogy check

Read the supervisor guide for this practice area at `~/.claude/plugins/config/claude-for-legal/legal-clinic/guides/<practice-area>.md`. Check the `pedagogy_posture` setting:

- **`guide` (default):** Produce the structure and the checklist. Ask the student to draft each section. Give feedback on their draft (register, reading level, required elements, what they missed). Offer to fill a section only when the student has tried once.
- **`assist`:** Produce the work product. Flag items for student review. The student edits and learns by reviewing.
- **`teach`:** Don't produce the work product. Ask the student to draft it. Give feedback. Ask leading questions when they're stuck. Only show a model paragraph after two attempts, and only the section they're stuck on. Track what they got right and wrong so the supervisor can see progress.

If no guide exists, use `guide`. If the guide exists but doesn't set a posture, use `guide`.

Whatever the posture, the output always includes: "**Pedagogy mode: [assist/guide/teach]** — set by your supervisor's guide. This means I [description of what the student did vs what the skill did]."

**Jurisdiction assumption.** The draft assumes the state, court, and local rules set in CLAUDE.md. Caption format, service requirements, page limits, filing windows, and substantive rules vary materially across jurisdictions and even between courts in the same state. If the matter is in a different court or a different state, confirm with your supervisor before relying on any format, deadline, or argument in the draft.

## Workflow

### Step 1: Which document?

Match the request to the clinic's template set (from `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md`). Common set by practice area:

| Practice area | Documents |
|---|---|
| **Immigration** | I-589 asylum application narrative, client declaration, motion to change venue, motion to continue, FOIA request, country conditions summary |
| **Housing** | Eviction answer, demand letter (repairs/deposit), motion to stay execution, discovery requests |
| **Family** | Protective order petition, custody declaration, motion to modify, financial affidavit |
| **Consumer** | Debt validation letter, FDCPA demand letter, answer to collection complaint, motion to vacate default |
| **General litigation** | Motion template, notice of appearance, certificate of service |

If the requested document isn't in the template set: "The clinic's templates don't include [X]. I can attempt a draft from general principles, but flag this heavily — it hasn't been tuned for your practice area or jurisdiction. Better to ask [Professor] if there's an existing template."

### Step 2: Gather the facts

Read the intake summary or case notes. For each fact the document needs: do we have it?

| Document needs | Have? | Source |
|---|---|---|
| [fact] | ✓ / ✗ | [intake / client doc / need to get] |

Missing required facts → don't guess. Mark them: `[FACT NEEDED: client's entry date — get from I-94 or ask client]`.

### Step 3: Apply jurisdiction

Per `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md` jurisdiction:

- **Caption format:** state and local court rules. If local rules were ingested at cold-start, use them. If not, use state default and flag: `[VERIFY CAPTION: local rules not loaded — confirm format against [Court]'s current rules]`
- **Service requirements:** who gets served, how, by when per the court's rules
- **Local quirks:** page limits, font requirements, standing orders. Apply what's ingested; flag what isn't.

### Step 4: Draft

Use the practice-area template. Fill what can be filled from facts. Leave placeholders explicit — never fill with plausible-sounding invention.

**Everywhere the draft makes a legal assertion:** that assertion is a hypothesis the student verifies, not a conclusion the draft guarantees. Mark accordingly.

### Step 5: Flag uncertainty

Three kinds of flags, in-line:

- `[FACT NEEDED: ...]` — the document needs a fact the case notes don't have
- `[VERIFY: ...]` — a legal or factual assertion that needs checking before this is filed
- `[UNCERTAIN: ...]` — the skill is genuinely unsure and says so rather than guessing

### Step 6: Supervision routing

Filing a document with a court or agency is a consequential action. The gate is the supervision workflow in `## Supervision style` in `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md`, reinforced by the Part 0 role check that confirms a licensed supervising attorney owns the clinic setup. Court filings always route through supervision before filing, regardless of the supervision-style choice.

Per `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md` supervision style:
- **Formal queue:** draft goes to queue, student sees "queued for [Professor]"
- **Configurable flags:** if this document type is a flag trigger (court filings usually are), output includes "CHECK WITH [PROFESSOR] BEFORE FILING"
- **Lighter-touch:** standard safeguard label, no additional gate — but court filings still go to the professor before filing per the clinic's existing supervision structure

## Output

```markdown
═══════════════════════════════════════════════════════════════════════
  AI-ASSISTED DRAFT — REQUIRES STUDENT ANALYSIS AND ATTORNEY REVIEW
  This is a starting point, not final work product.
  Every [VERIFY] and [FACT NEEDED] flag must be resolved before filing.
═══════════════════════════════════════════════════════════════════════

[The document — in the practice-area template format, jurisdiction-aware,
with flags inline]

═══════════════════════════════════════════════════════════════════════

## Student review checklist

Before showing this to [Professor]:

- [ ] Read the whole thing. Does it say what you want it to say?
- [ ] Every fact: is it accurate per the client's actual documents, not just the intake notes?
- [ ] Every [VERIFY] flag: resolved with research or struck
- [ ] Every [FACT NEEDED] flag: filled with verified information or the section removed
- [ ] Legal theory: is this the right argument? Are there better ones? (That's your analysis, not the draft's.)
- [ ] Jurisdiction: caption, service, format correct per current local rules
- [ ] [Supervision step per CLAUDE.md style]

## What this draft does NOT do

- It does not decide strategy. The draft follows the most common approach for
  this document type — you decide if that's right for this client.
- It does not verify its own legal assertions. Every legal conclusion above is
  a hypothesis until you research it.
- It does not file itself. [Professor] reviews, you file per clinic procedure.

---

**Before this leaves the clinic.** This is a student draft for supervising-attorney review, not a final letter, filing, or form. Filing it with a court or agency, or sending it to a client or opposing party, has legal consequences for the client. A licensed supervising attorney reviews, edits, and signs off before it leaves the clinic. Strip the AI-assisted draft header only after that sign-off. Do not send or file this draft without supervisor approval.

*ABA Formal Opinion 512 (2024): generative AI use requires competence,
supervision, and verification. This draft is designed to be supervised and
verified — it is not designed to be trusted without that.*
```

## What this skill does NOT do

- **Produce final work product.** First draft only. Student revises, professor reviews.
- **Guess at missing facts.** Flags them for the student to get.
- **Decide the legal theory.** Uses the common approach; the student decides if it's the right one for this case.
- **Replace jurisdiction-specific research.** Applies ingested local rules; flags where rules weren't ingested or might have changed.
