---
name: build-guide
description: >
  Help a clinic supervisor author a practice-area guide that configures how
  student-facing skills behave — intake questions, pedagogy posture (assist /
  guide / teach), review gates, cross-plugin checks, and local rules. Use when
  a supervising attorney wants to build or revise a per-practice-area guide,
  tune how the clinic skills behave for their clinic type, or set their
  teaching philosophy as plugin configuration.
argument-hint: "[optional: practice area — e.g., 'immigration', 'housing']"
---

# /build-guide

1. Load `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md` → role (must be Supervising attorney), practice areas, jurisdiction.
2. Use the workflow below.
3. If the user is not the supervising attorney, stop and redirect (students run `/legal-clinic:ramp`).
4. Walk through: practice area → intake questions → pedagogy posture → review gates → cross-plugin checks → local rules.
5. Write `~/.claude/plugins/config/claude-for-legal/legal-clinic/guides/<practice-area>.md`. Create the `guides/` directory if needed.
6. Offer a test run — run `/legal-clinic:draft` under the configured posture so the supervisor sees what a student sees.

```
/legal-clinic:build-guide
```

Multiple guides are fine — one per practice area. Re-run this command to revise. Edit the guide file directly for quick changes.

---

# Build Guide: Supervisor-Authored Practice-Area Guide

## Purpose

The supervisor guide is the dial that turns student-facing skills from "get the work done" into "teach the student to do the work." Every student-facing skill in this plugin reads the guide before producing output: intake asks the questions the supervisor wants asked, drafting skills pick a pedagogy posture (assist / guide / teach), review gates route to the supervisor on the items the supervisor cares about, and cross-plugin checks wrap other-plugin skills in a supervision layer.

This skill helps a supervisor author that guide in 5-10 minutes per practice area. The guide is plain markdown at a well-known path — edit it by hand anytime.

**Audience: the supervising attorney.** Not students. Students run `/legal-clinic:ramp` and then the student-facing skills; they don't author guides.

## Work-product header

Every output from this skill is a supervisor-facing configuration artifact, not student work product. Do NOT prepend `[AI-ASSISTED DRAFT — requires student analysis and attorney review]` to the output of this skill — that label is for student outputs. The guide file this skill writes is a supervisor configuration document; it sits next to CLAUDE.md in the plugin config directory, not in a matter workspace.

## Key things your guide should address

Offer this as a checklist the supervisor can skip through or use as the table of contents for the interview:

- What does a student need to know before they touch a case? (Ethics rules, confidentiality, their scope of authority)
- What are the 3-5 most common mistakes students make in this practice area, and how should the skill catch them?
- When must the student stop and get your sign-off? (Filing, sending to a client, making a representation, advising on strategy)
- What's the reading level for client communications? (6th grade is the usual target for legal aid)
- What local rules, forms, or deadlines should every student know?
- When should the skill teach vs. do? (Per document type — you can set a default and override per type)

Walk through the checklist at the start of the interview so the supervisor knows what's coming and can flag which items they already have strong views on versus which they want to think through. Skip any item the supervisor waves off; note it in the guide as "not specified — skill uses defaults."

## Workflow

### Step 1: Check role

This is a supervisor skill. Read `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md` → `## Who's using this` → Role. If the role is not "Supervising attorney," say:

> This skill is for supervisors — it configures how the student-facing skills behave. If you're the supervisor, make sure your practice profile role is set to "Supervising attorney" in `/legal-clinic:cold-start-interview`. If you're a student, this isn't the right skill for you — run `/legal-clinic:ramp` to onboard, or ask your supervisor to author a guide for your clinic.

Stop if the role is not supervising attorney.

### Step 2: Which practice area?

> What clinic is this guide for? (Immigration / Housing / Family / Transactional / Criminal defense / Consumer / Other)

If the answer is "Other," ask for a short name — that name becomes the filename (lowercase, hyphenated: `immigration-removal-defense.md`, `transactional-nonprofit.md`, etc.).

Check the practice areas listed in `CLAUDE.md` → `## Clinic profile` → Practice areas. If the chosen practice area is not listed there, note it: "I'll write this guide, but your practice profile doesn't list [area] as one of your clinic's practice areas. That's fine — you can add it later with `/legal-clinic:cold-start-interview --redo` — but the student-facing skills won't route intakes to this area until the profile lists it."

If a guide already exists at `~/.claude/plugins/config/claude-for-legal/legal-clinic/guides/<practice-area>.md`, offer: "A guide for [area] already exists at [path]. Do you want to (a) revise it section-by-section, (b) start fresh and overwrite, or (c) see what's there first?"

### Step 3: Intake questions

> What should students ask a new client for this clinic type? I'll start with a generic intake for [practice area] — tell me what to add, remove, or change. What red flags should students look for? What makes a case a good fit for your clinic vs. a referral out?

Show the generic intake defaults for the practice area — use the same defaults that `client-intake` uses (Immigration: status, entry, prior applications, country conditions, family, criminal history, timeline urgency; Housing: housing type, what happened, lease, habitability, timeline; Family: relationship, issue, children, safety, orders, hearings; Consumer: debt type, contacts, documentation, filings, deadlines). For practice areas outside those four, ask the supervisor to describe the intake from scratch.

Capture: questions to add, questions to remove, questions to rephrase, red flags (a list), good-fit criteria (what makes this a case the clinic takes vs. refers out).

### Step 4: Pedagogy posture

> How much should the skills do vs. how much should the student do?
>
> - **Guide (default):** The skill produces structure; students fill in substance; the skill gives feedback. Balanced — most clinics start here.
> - **Assist:** The skill produces work product; students review and learn by editing. Fastest, least pedagogical. Good for high-volume clinics or when deadlines are tight.
> - **Teach:** The skill doesn't produce work product — students draft, the skill gives Socratic feedback and only shows models after two attempts. Slowest, most pedagogical. Good for seminar-style clinics or when learning is the primary goal.
>
> You can set this per document type (e.g., teach for client letters, assist for file memos).

Capture the default posture for the practice area, and any per-document overrides. Per-document settings the skills read:

- `pedagogy_posture_default: assist | guide | teach`
- `pedagogy_posture_client_letter: [override]`
- `pedagogy_posture_memo: [override]`
- `pedagogy_posture_draft: [override]`

If the supervisor names a document type the skills don't currently have, record the intended posture in a `pedagogy_posture_other:` block with a note — future skills can read it.

### Step 5: Review gates

> Which work product needs your review before it goes to a client? Which can students send directly? Default: everything client-facing needs review.

Present the options as a table the supervisor fills in:

| Work product | Gate |
|---|---|
| Intake summary | [student writes; supervisor reviews at case rounds / supervisor reviews before client sees / student keeps] |
| Memo (internal) | [supervisor reviews / student keeps] |
| Client letter (appointment / doc request / brief status) | [supervisor reviews / student sends directly] |
| Client letter (substantive advice / bad news) | [always supervisor — cannot override] |
| Draft filing (court / agency) | [always supervisor — cannot override] |
| Status update to court | [always supervisor — cannot override] |
| Research-start roadmap | [student works from it directly] |

Some gates are non-negotiable: client letters that give substantive advice, court filings, and status to courts always route through the supervisor per the clinic's supervision structure. Flag those as fixed; the configurable gates are the routine ones.

### Step 6: Cross-plugin checks

> Do you want students to use skills from other plugins (defined-terms checks, doc consistency, section references, research verification)? I can wrap them in supervision — the student runs the check, the output flags uncertainty for your review, nothing goes out without your sign-off.

Offer concrete examples tied to practice area:

- **Transactional clinic:** `commercial-legal:review` (NDA triage, vendor review) wrapped so the student runs the review, the output is flagged for supervisor review before going to the client.
- **Immigration clinic:** `litigation-legal:chronology` for building a timeline from client documents, flagged for supervisor review before it feeds a filing.
- **Housing clinic:** `litigation-legal:subpoena-triage` when the client brings in a subpoena, wrapped so the student drafts the response plan but the supervisor signs off.
- **Any clinic:** `privacy-legal:triage` if the student is handling any matter where personal data is shared outside the clinic.

If the supervisor names a cross-plugin skill they want, record: skill name, when students should use it, what supervision wrapper applies (always reviewer, only when flagged, never without supervisor).

### Step 7: Local rules and jurisdiction

> What court(s) does your clinic practice in? Any local rules or forms students need to use?

Check `CLAUDE.md` → `## Jurisdiction` — the state and primary court are already set at cold-start. This step is for practice-area-specific local rules and forms (e.g., "Housing Court standing order on summary process answers," "USCIS filing address for the local field office," "Family Court self-help center forms and where to find them"). Offer to capture a short list of pointers the student-facing skills should use when drafting or advising.

### Step 8: Write the guide

Write to `~/.claude/plugins/config/claude-for-legal/legal-clinic/guides/<practice-area>.md`. Create the `guides/` directory if it doesn't exist. Use this structure:

```markdown
# Practice-area guide: [Practice area]

*Authored by the supervising attorney via `/legal-clinic:build-guide`. Student-facing skills read this before producing output. Edit directly anytime.*

**Last updated:** [date]
**Authored by:** [supervising attorney name from CLAUDE.md]

---

## Intake

**Questions to ask** (supplement/replace the generic defaults):
- [question 1]
- [question 2]
- ...

**Red flags** (surface these in the intake summary if present):
- [flag 1]
- [flag 2]

**Good-fit criteria** (cases this clinic takes):
- [criterion 1]
- [criterion 2]

**Refer-out criteria** (cases this clinic does not take):
- [criterion 1]
- [criterion 2]

---

## Pedagogy posture

`pedagogy_posture_default: [assist | guide | teach]`

Per-document overrides (optional):
- `pedagogy_posture_client_letter: [assist | guide | teach]`
- `pedagogy_posture_memo: [assist | guide | teach]`
- `pedagogy_posture_draft: [assist | guide | teach]`

**Rationale:** [one or two sentences from the supervisor on why this posture — helps next semester's supervising attorney understand the choice]

---

## Review gates

| Work product | Gate |
|---|---|
| Intake summary | [gate] |
| Memo (internal) | [gate] |
| Client letter — routine | [gate] |
| Client letter — substantive | supervisor (fixed) |
| Draft filing | supervisor (fixed) |
| Court-facing status | supervisor (fixed) |
| Research roadmap | [gate] |

---

## Cross-plugin checks

| Skill | When students use it | Supervision wrapper |
|---|---|---|
| [plugin:skill] | [situation] | [wrapper] |

---

## Local rules and jurisdiction

**Court(s):** [from CLAUDE.md or additional courts for this practice area]
**Practice-area-specific local rules and forms:**
- [pointer 1]
- [pointer 2]
```

Fill every section from the supervisor's answers. Leave a section empty only if the supervisor said so — do not invent content.

Then tell the supervisor:

> Your guide is at `~/.claude/plugins/config/claude-for-legal/legal-clinic/guides/<practice-area>.md`. Every student who uses the clinic plugin for [practice area] will have skills that follow it. Edit the file directly to change anything, or re-run `/legal-clinic:build-guide` to revise a section. You can have multiple guides — one per practice area.

### Step 9: Offer a test run

> Want to see how the pedagogy posture changes the experience? I'll run `/legal-clinic:draft` with a sample client letter under [posture] — you'll see what the student sees.

If the supervisor says yes, simulate the drafting skill reading the guide they just wrote and producing output under the configured posture. Walk through one full cycle so the supervisor sees exactly what a student would see.

## Output

The skill's "output" is the file written at `~/.claude/plugins/config/claude-for-legal/legal-clinic/guides/<practice-area>.md`. The conversation with the supervisor is the interview; the written guide is the artifact.

After writing, show a brief confirmation:

> **Guide written.** `[practice-area]` is now configured:
>
> - Intake: [N] custom questions, [N] red flags, [N] refer-out criteria
> - Pedagogy: [posture default], with overrides for [list if any]
> - Review gates: [summary of what routes to supervisor vs. student]
> - Cross-plugin: [N] skills wired in
>
> Students will see these changes the next time they run a clinic command for this practice area. Edit `[path]` anytime to change anything, or re-run `/legal-clinic:build-guide` to revise.

## What this skill does NOT do

- **Configure the plugin globally.** The guide is per-practice-area. For plugin-wide config (supervision style, jurisdiction, practice areas), that's `/legal-clinic:cold-start-interview`.
- **Author student work product.** This is supervisor-facing configuration, not a draft for a client.
- **Override the supervision style from cold-start.** The supervision model (formal queue / configurable flags / lighter-touch) is set at setup. Review gates in the guide refine that model for this practice area; they don't replace it.
- **Make a student skill skip the AI-assisted header, the confidence flags, or the verification prompts.** Those are shared-guardrail baselines. The guide changes posture, not guardrails.
