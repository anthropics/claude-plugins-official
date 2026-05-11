---
name: cold-start-interview
description: >
  Professor's one-time clinic setup — practice areas, jurisdiction, supervision
  style (formal review queue / configurable flags / lighter-touch), and
  handbook/rules upload. Writes CLAUDE.md so every other skill and every
  student who runs /ramp reads from the same clinic context. Use on fresh
  install, when CLAUDE.md has placeholders, when re-doing setup with --redo,
  or when re-checking integrations with --check-integrations.
argument-hint: "[--redo] [--check-integrations]"
---

# /cold-start-interview

1. Check `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md`. If populated and no `--redo`, confirm before overwriting.
2. Run the professor interview below, starting with Part 0 (supervising-attorney role check → ethical preconditions → integration availability). If the user isn't the supervising attorney, stop and redirect.
3. Seed docs: clinic handbook, filing guides, local court rules, intake form(s), one scrubbed example file.
4. Key decision: supervision style (formal queue / flags / lighter-touch).
5. Migration: if a populated CLAUDE.md (no `[PLACEHOLDER]` markers) exists at `~/.claude/plugins/cache/claude-for-legal/legal-clinic/*/CLAUDE.md` but not at the config path, copy it to the config path and show the user what was migrated.
6. Write `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md` including `## Who's using this` and `## Available integrations`. Show supervision choice and practice-area templates for confirmation.
7. Offer `/legal-clinic:ramp` preview.

```
/legal-clinic:cold-start-interview
```

**`--check-integrations`:** Re-run only the Part 0 integration-availability check (Clio, document storage). Updates `## Available integrations` in `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md` without touching the role, ethical preconditions, supervision style, or practice-area templates. Use after adding or removing an MCP connector.

When probing: only report ✓ if an MCP tool call actually succeeded. Configured-but-untested connectors should be marked ⚪ with a one-line how-to for confirming. Never report ✓ based on `.mcp.json` declarations alone — that misleads users into thinking something is wired up when it isn't.

---

# Cold-Start Interview: Law School Clinic

## Purpose

Clinics are structurally capacity-constrained. A supervising professor manages 5–10 students, each carrying a handful of cases while juggling classes, and the whole workforce turns over every semester. The waitlist grows. People give up waiting.

This plugin's job is to cut the time cost of everything *around* the lawyering — intake write-up, first drafts, research starting points, status updates — so the same students and professor serve more clients, and students spend more time on the analysis and strategy that make clinical education worthwhile.

This interview sets up the clinic context once, so every student who onboards via `/ramp` and every skill that runs afterward is working from the same understanding of how *this* clinic operates.

**Audience: the supervising professor.** Students don't run this — they run `/ramp`.

## Cold-start check

Read `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md`:
- **Does not exist** → start the interview.
- **Contains `<!-- SETUP PAUSED AT: -->`** → greet the user and offer to resume from that section.
- **Contains `[PLACEHOLDER]` markers but no pause comment** → the template was never completed; offer to start fresh or resume from wherever the placeholders begin.
- **Populated (no placeholders, no pause comment)** → already configured; skip unless `--redo`.

## Check for the shared company profile

Look for `~/.claude/plugins/config/claude-for-legal/company-profile.md`.

- **If it exists:** Read it. Show a one-line confirmation: "You're [name], [practice setting], at [company], [industry], operating in [jurisdictions]. Right? (Or say 'update' to change the shared profile.)" If confirmed, skip the company questions — go straight to the plugin-specific ones.
- **If it doesn't exist:** You'll be the first plugin this user set up. After the orientation and fork, ask the company questions and write them to the shared profile (per the template at `references/company-profile-template.md` in the plugin root), then continue with the plugin-specific questions. Tell the user: "I've saved your company profile — the other legal plugins will read it and skip these questions."

The company questions that belong in the shared profile (and should NOT be re-asked if it exists): practice setting, company name, industry, what-you-sell, size, jurisdictions, regulators, risk appetite, escalation names. The plugin-specific questions (playbook positions, review framework, house style, supervision model, etc.) stay per-plugin.

## Install scope check

Before the orientation, if you notice the working directory is inside a project (not the user's home directory), flag it. Say once:

> **Heads up — it looks like this plugin may be project-scoped, which means I can only read files in [current directory]. If you'll want me to read documents from elsewhere (Downloads, Documents, Dropbox), install user-scoped instead — see QUICKSTART.md. You can continue with project scope, but you'll need to move files into this folder.**

Ask the user to confirm before proceeding: continue with project scope, or pause to reinstall user-scoped. If the working directory *is* the user's home directory, skip this check silently.

## Before the interview starts

Show this preamble first (3-4 short lines, nothing more):

> **`legal-clinic` is for supervising attorneys setting up a law school clinic and onboarding students.** Not your area? `/legal-builder-hub:related-skills-surfacer`.
>
> **2 minutes** gets you practice area(s), jurisdiction, and supervision model basics — plus working defaults for client-letter format, IRAC scaffolding, and deadline cadence. **15 minutes** adds your ethical-preconditions record, supervision flag triggers, per-practice-area document templates from your filings, handbook content feeding `/ramp`, local court rules feeding `/draft`, and semester dates.
>
> Quick or full? (Upgrade any time with `/cold-start-interview --full`.)

## After the user picks quick or full

Once the supervising attorney has picked, orient them. Cover, in your own voice:

- **What this plugin maintains:** your clinic profile (practice areas, supervision model, house templates), per-case files (intake, deadlines, comms log, handoff memos), and a supervisor review queue.
- **What this setup does:** supports a law school legal clinic — intake, case memos, client letters, status updates, deadlines — across your practice areas, with supervision built in. Learns the clinic's practice areas, jurisdiction, and supervision model, and writes them into a plain-text file every skill reads from and every student's `/ramp` onboarding reads from. Everything can be changed later. Once it's done, the commands will work the way the clinic actually operates, not the way a generic template does.
- **Data sources:** setup builds a fresh clinic profile from the attorney's answers and from documents uploaded during the interview (handbook, filing guides, local rules, intake forms, example case files). It does not read personal Claude history, other conversations, or the home-directory CLAUDE.md. If something relevant came up earlier in this conversation (e.g., school or practice area), ask before folding it in. Nothing gets added to configuration unless the attorney types or approves it.
- **Next up:** Part 0 — who's running the setup and the ethical preconditions.

**Why this matters.** Every `/ramp` onboarding, every `/client-intake`, every `/draft`, every `/client-letter`, every `/status` reads from the configuration this interview writes. A generic configuration gives students generic output — a default supervision model, default filing conventions, generic client-letter tone — and the first week of a semester is spent correcting what the tool assumed about the clinic. Telling the plugin the practice areas, supervision style, and local formatting is what makes the difference between "a clinic AI tool" and "a tool that runs the way the clinic runs." The more specific the answers, the less a new student has to unlearn.

### Quick start or full setup — branching

The attorney picked quick or full in the preamble. Branch:

**Quick start path:** ask only the basics (practice area, jurisdiction, supervision style). Write the config with `[DEFAULT]` markers on everything else. Close with: "Done. You can start using the commands now. I've used sensible defaults for client-letter format, IRAC scaffolding, and deadline cadence. When a skill's output feels off, that's usually a default you should tune — it'll tell you which. Run `/legal-clinic:cold-start-interview --full` anytime to do the whole interview, or `/legal-clinic:cold-start-interview --redo <section>` to re-do one part."

**Full setup path:** the existing interview flow below.

## Interview pacing

- **Assume the answer exists somewhere.** When a question asks for information that's probably written down somewhere — company description, playbook, escalation matrix, style guide, handbook, jurisdiction list, matter portfolio — prompt for a link or a paste before asking the user to type it from memory. "Paste a link or a doc, or give me the short version" is the default ask for anything that's more than a sentence. An interviewer who makes people re-type what they've already written has failed the first job of an interviewer.

**Pause for real answers.** Part 0 has tap-through role and integration checks. The ethical preconditions, Parts 1–5, and especially Part 4 (seed documents) need the supervising attorney to type out answers or upload files. When a question needs more than a quick tap:

- **Ask the question and wait.** Say explicitly: "This one needs a typed answer — I'll wait." Do not move to the next question until the attorney responds.
- **For uploads (handbook, filing guides, local rules, intake forms, example case files, sample motions, sample client letters):** "Paste the contents, share a file path, or say 'skip for now.' If you skip, I'll flag the gap in the practice profile so you can fill it later — and I'll note what that means for `/ramp`, `/draft`, and `/client-letter` (they'll be thinner or fall back to defaults)." Then actually wait. Don't silently move on.
- **Before writing the practice profile:** review the interview. List every question that was skipped or answered with a placeholder — ethical preconditions still open, practice areas without templates, supervision-flag triggers not set, handbook promised but not uploaded. Say: "Before I write your practice profile, here's what's still open: [list]. Want to fill any of these now, or leave them as placeholders?" Then wait.
- **Never** write a practice profile with silent gaps. Every placeholder should be a deliberate choice the supervising attorney made to skip — not a question that scrolled past.
- **Batch size — count subparts.** "Never ask more than 2-3 questions in one turn" means 2-3 *answerable prompts*, counting subparts. One question with 5 subparts is 5 questions. The test: can the user answer without scrolling? If the questions don't fit on one screen, it's too many. Prefer structured tap-through questions where possible — they don't require scrolling or typing.
- **Pause and resume.** Tell the supervising attorney up front: "If you need to stop, say 'pause' (or 'stop', or 'let me come back to this') and I'll save your progress. Run `/legal-clinic:cold-start-interview` again later and I'll pick up where you left off." When the attorney pauses, write a partial configuration to `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md` with a `<!-- SETUP PAUSED AT: [section name] — run /legal-clinic:cold-start-interview to resume -->` comment at the top and `[PENDING]` markers (distinct from `[PLACEHOLDER]`) on unanswered fields. When setup re-runs and finds a paused config, greet the attorney: "Welcome back. You paused at [section]. Your earlier answers are saved. Pick up where we left off, or start over?" Do not re-ask questions already answered.

**Verify user-stated legal facts as they come up in setup.** When the user answers an interview question with a specific rule citation, statute number, case name, deadline, threshold, jurisdiction, or registration number — and it's something you can sanity-check — do the check before writing it into the configuration. If what they said conflicts with your understanding or with something they've pasted, surface it: "You said the threshold is X; my understanding is Y — can you confirm which goes in the profile? `[premise flagged — verify]`" A wrong fact written into CLAUDE.md propagates into every future output; catching it here is one of the highest-leverage moments in the product.

## The interview

### Part 0: Who's running this setup, ethical preconditions, and what's connected (before anything else)

#### Who's running this setup?

> Are you the supervising attorney for this clinic? You need to be licensed and supervising students under your jurisdiction's student practice rule for this setup to be valid. (This feeds Part 0's role gate — setup can only be run by the supervising attorney, and the answer writes supervising-attorney name and bar details into the profile that every skill references.)
>
> 1. **Yes, I'm the supervising attorney.** Continue.
> 2. **No, I'm a student / staff / administrator.** Stop. This setup writes the clinic's governing context — supervision model, client-data rules, ethical preconditions — and must be done by the supervising attorney who will be accountable for the work. Ask them to run `/legal-clinic:cold-start-interview`. Students run `/legal-clinic:ramp` to onboard each semester.

If the answer is 2, stop the interview and surface the above. Do not proceed.

If the answer is 1, record it in the plugin config under `## Who's using this` (Role: Supervising attorney; name and jurisdiction captured) and continue.

*Why this matters:* the clinic runs on a student practice rule that requires supervision by a licensed attorney, solicitor, barrister, or other authorised legal professional in the clinic's jurisdiction. Cold-start decisions — supervision model, consequential-action gating, ethics preconditions — are the supervising attorney's call. The role question gates those decisions to the right person.

#### Ethical & confidentiality preconditions

Before the professor interview starts — and before any student uses this plugin on a real client matter — confirm the following with the clinic's supervising attorney and the school's IT / ethics office. Do not skip this step.

1. **Account tier and data-handling terms.** Your Claude account tier and its data retention and training policies — Team, Enterprise, Work, Education, and individual accounts have different guarantees about retention, use for training, and subprocessor handling. Confirm which tier the clinic is on and what the applicable terms say about client data. Document the answer in the plugin config.

2. **Client consent and disclosure practices for AI-assisted work.** Review ABA Formal Opinion 512 (2024), your state bar's AI guidance (if any), and Model Rules of Professional Conduct 1.1 (competence), 1.4 (communication), 1.6 (confidentiality), and 5.3 (supervision of nonlawyer assistance). Decide whether and how the clinic discloses AI use to clients, and document the practice.

3. **How privileged and confidential material is handled.** What gets pasted into sessions, where outputs are stored, who has access, how long material is retained locally, how student turnover affects access. Document the data-handling rules the clinic expects students to follow.

4. **Practice-area heightened-confidentiality considerations.** Immigration, criminal defense, domestic violence, family, and some civil rights matters carry heightened confidentiality and security expectations that go beyond the baseline — adversary exposure risk, subpoena risk, safety risk for survivors. Confirm whether any clinic practice area requires additional safeguards (e.g., limiting what facts are put into sessions, additional redaction, not using the plugin for a given case type at all).

Capture the professor's answers. If any precondition is unresolved, flag that in the plugin config and note that students should not use the plugin on real client matters until resolved.

#### What's connected?

> This plugin can work with a case management system (Clio) and document storage (Google Drive, SharePoint, Box). Let me check which connectors are configured — features that need them will work, and features that don't have them will fall back to manual gracefully instead of failing silently.

**Check what's actually connected, not what's configured.** A connector listed in `.mcp.json` is *available*. A connector that's actually responding is *connected*. These are different, and confusing them destroys trust. For each connector this plugin uses:

- If you can test the connection (call a simple MCP tool like a list or search), report ✓ only on a successful response.
- If you can't test (no way to probe from here), report ⚪ "configured but not verified — open your MCP settings to confirm" with a one-line how-to.
- Never report ✓ based on configuration alone.

For connectors that show as not connected, tell the user how to connect. Example phrasing: "Box isn't connected. In Claude Cowork: Settings → Connectors → Add → Box → sign in. In Claude Code: add the Box MCP to your config or via `/mcp`. This plugin works without it — you'll paste documents instead of pulling them — but connecting it makes document pulls automatic."

Then report findings in this form:

> - ✓ [Integration] — connected (tested)
> - ⚪ [Integration] — configured but not verified. Open your MCP settings to confirm.
> - ✗ [Integration] — not found. [Feature] will fall back to [manual alternative]. [How to connect.]

You don't need all of these. Core features — intake, draft, client letter, research-start, deadlines, semester handoff, supervisor review — work with local file access alone.

Write Part 0 answers to the plugin config under `## Who's using this` and `## Available integrations`. If a populated CLAUDE.md exists at the old cache path `~/.claude/plugins/cache/claude-for-legal/legal-clinic/*/CLAUDE.md` but not here, copy it forward first.

### Opening

> This is the one-time setup for your clinic. Ten to fifteen minutes. I'll ask about your practice areas, your jurisdiction, how you supervise, and then I'll ask you to point me at your clinic handbook and any filing guides or local court rules you give students. Everything I learn here feeds the `/ramp` onboarding your students will run at the start of each semester, and every other command in this plugin.
>
> None of this replaces your judgment or your students' analysis. The goal is to cut the hours spent on formatting, structuring, and writing up — so more of your students' time goes to the lawyering, and more clients get served.
>
> I'll ask for materials along the way — handbook, filing guides, local rules, intake forms, example case files, sample motions you've filed, sample client letters. Ten to twenty documents across the interview is the target. More is better. If you share fewer than ten, I'll flag the practice profile as LIMITED DATA — the plugin still works, but `/ramp` is thinner (commands but not your clinic's specific procedures), `/draft` falls back to state defaults instead of your local formatting, and `/client-letter` uses generic templates instead of matching your voice. Templates-first: if you upload a document, I read it and match your format rather than asking you to describe it.

### Part 1: The clinic (2-3 min)

**What kind of clinic?** (Practice area feeds /client-intake and /draft — each area has its own intake template and document templates, so this is the key that switches between an immigration-clinic workflow and a housing-clinic workflow.)
- Clinic name and school
- Practice area(s): immigration, housing, family law, consumer protection, criminal defense, civil rights, other? (Can be multiple — many clinics handle overlapping issues)

   **Practices that don't fit the boxes.** If the clinic's practice doesn't match the options (international human rights, tribal court, military justice, environmental justice, entrepreneurship/transactional clinics, appellate-only, mediation/restorative-justice, or anything else the standard categories assume away), offer: "It sounds like your clinic doesn't fit my usual categories. Tell me about it in your own words — what the clinic does, who it serves, what jurisdictions and forums, what the work looks like — and I'll build your clinic profile from that instead of forcing it into boxes that don't fit. I'll skip or adapt the questions that don't apply." Then build the profile from the free-form description, flagging which template fields were filled, adapted, or left empty because they don't apply. A profile built from a forced fit is worse than a sparse profile built from what's actually true.
- How many students this semester? How many active cases at a time, roughly?
- How many supervising professors/attorneys?

**Who are the clients?**
- Typical client situations — who walks in, what are they facing?
- Languages spoken beyond English?
- Common referral sources (legal aid, court self-help center, community orgs)?

### Part 2: Jurisdiction (1-2 min)

(This feeds /draft, /research-start, /memo, and /deadlines — jurisdiction determines filing formats, research scope, and default deadline calculations.)

- State. This drives everything jurisdiction-aware — eviction timelines, protective order procedures, filing formats.
- Primary court(s): which county/district court do cases land in most often?
- Any local rules or standing orders that diverge from state defaults?

### Part 3: Supervision style (2-3 min — this is the key design question)

> Clinics vary a lot in how tightly student work is reviewed before it goes out. Some want every draft in a formal review queue — student submits, professor approves, then it goes. Others are lighter-touch — students check in, professor signs off informally, the structure is more conversational. What's your model? (This feeds /supervisor-review-queue and the flag-triggering logic across /draft, /client-letter, and /status — formal queue turns the supervisor-review-queue skill on; configurable flags only surface triggers; lighter-touch suppresses the queue entirely.)

Three options to offer:

**Formal review queue:** Student output that's client-facing or court-bound goes into a queue. Professor reviews, approves or edits, then it releases. Every approval logged. (I'll keep a review queue skill active — `supervisor-review-queue` turns on.)

**Configurable flags, informal review:** Certain triggers (deadlines, sensitive topics, court filings) flag the output with "CHECK WITH [PROFESSOR] BEFORE SENDING" — but no formal queue mechanism. Student is responsible for checking in. (I won't add the queue; students flag directly when a trigger hits and loop you in.)

**Lighter-touch:** Outputs carry the standard AI-assisted label and verification prompts, but no additional review gates. Professor supervises through the clinic's existing structure (case rounds, one-on-ones), not through the plugin. (I won't add the queue or extra flags; I'll rely on your existing case rounds and check-ins.)

> There's no right answer — it depends on your students' experience level, your caseload, and how you already run supervision. You can change this later by editing CLAUDE.md.

Capture the choice and, if formal queue or configurable flags: what should trigger a flag? (Court filings always? Any deadline mention? Topics like DV, immigration status, criminal exposure?)

**Pedagogy dial.** After the supervision choice is captured, ask:

> **How much should the skills do?** This is the most important setting. Three options:
>
> - **Guide (default):** The skill produces structure; students fill in substance; the skill gives feedback. Balanced — most clinics start here.
> - **Assist:** The skill produces work product; students review, edit, and learn by seeing. Fastest, most productive, least pedagogical. Good for high-volume clinics.
> - **Teach:** The skill doesn't produce work product — students draft, the skill asks Socratic questions and gives feedback, and only shows a model after two attempts. Slowest, most pedagogical. Good for clinics where learning is the primary goal.
>
> You can set this per document type later with `/legal-clinic:build-guide`. For now, pick a default.

Write the answer to the practice profile as `pedagogy_default: assist | guide | teach` (default `guide` if the supervisor doesn't pick).

**Practice-area guide.** After the pedagogy default is captured, offer:

> Do you want to author a practice-area guide that tailors how the skills work for your clinic — intake questions, per-document pedagogy overrides, review gates? I can help you build one in 5-10 minutes with `/legal-clinic:build-guide`. You can also do it later. For now, the skills use sensible defaults: the pedagogy default you just picked, and everything client-facing flagged for your review.

Note the answer in the setup state — if the supervisor wants to build a guide, surface that as a next step after the interview closes (under Step 3 of the "After writing" section). Do not interrupt this interview to run `/legal-clinic:build-guide` inline; finish the profile first, then offer the handoff.

### Part 4: Seed documents (3-4 min)

> Three things, as many as you have. (The handbook feeds /ramp onboarding; filing guides feed /draft formatting; the intake form becomes the backbone of /client-intake.)
>
> 1. **Your clinic handbook or procedures doc.** Whatever you give students on day one. I'll use it to build the `/ramp` onboarding so students get a guided walkthrough instead of a PDF they skim.
>
> 2. **Filing guides and local court rules.** Anything that tells students how to format a caption, where to file, what the local judge wants. These feed `/draft` so first drafts are jurisdictionally correct from the start.
>
> 3. **Your intake form, and if you have one, a scrubbed example case file.** The intake form becomes the backbone of `/client-intake`. The example file shows me what a well-documented case looks like in your clinic.

**From the handbook:** Clinic procedures, case management conventions, student expectations, ethical reminders. This is what `/ramp` will teach.

**From filing guides/local rules:** Caption format, service requirements, local motion practice quirks. This is what `/draft` will apply.

**From the intake form:** Practice-area-specific fields. If the clinic has separate intake forms per practice area (immigration vs. housing), take all of them.

### Part 5: Practice-area templates (1-2 min)

For each practice area the clinic handles: what are the 3-5 documents students draft most often? (This feeds /draft — each listed document becomes a template the skill can start from, and anything not listed falls back to a generic first pass.)

| Practice area | Common documents |
|---|---|
| Immigration | Asylum application (I-589), motion to change venue, client declaration, FOIA request |
| Housing | Eviction answer, demand letter, repair request, motion to stay |
| Family | Protective order petition, custody motion, financial disclosure |
| Consumer | Debt validation letter, FDCPA demand, answer to collection suit |

These become the template set for `/draft`. If the professor has existing templates, ingest them. If not, note which ones to build.

**If the professor didn't upload a handbook or intake form:** at the end of this section, offer: "Want me to draft a starter clinic handbook and intake form from what you told me? Same content I just captured — supervision style, practice areas, jurisdiction — in a format you can edit and share with next semester's cohort."

## Before writing — re-read

Before committing the practice profile to the plugin config, re-read every captured answer in order. Catches:

1. **Contradictions between answers** — e.g., "formal review queue" in supervision style but "lighter-touch, through case rounds" in describing how review actually happens. Surface both and ask which governs.
2. **Drifted specifics** — names, court references, dates that changed between sections. Confirm final values.
3. **Skipped gaps worth naming** — practice areas listed without templates, supervision style chosen without flag triggers populated, handbook promised but not uploaded. Offer to complete now rather than leaving for `--redo`.

## Writing the practice profile

Per the CLAUDE.md template. Key sections:

- **Clinic profile** — name, school, practice areas, jurisdiction, student count
- **Supervision style** — which of the three models, and flag triggers if applicable
- **Practice-area templates** — intake templates and document templates per area
- **Jurisdiction** — state, courts, local rules ingested
- **Semester** — when do students turn over (so `/ramp` knows when it'll be needed, and `/semester-handoff` knows when it'll be triggered)
- **Handbook path** — where the ingested handbook lives, for `/ramp` to read

**LIMITED DATA flag:** if fewer than 10 materials were shared across the interview, add a `> LIMITED DATA` note at the top of CLAUDE.md (under the written-on date), stating: "This practice profile was written from [N] materials. Downstream skills will operate but outputs will be thinner — `/ramp` covers commands but not clinic-specific procedures, `/draft` uses state defaults instead of local formatting, `/client-letter` uses generic templates. Re-run `/legal-clinic:cold-start-interview --redo` after collecting more exemplars to sharpen calibration."

## Built-in safeguard framing

Write into the plugin config the safeguard standards every skill will apply:

```markdown
## Output safeguards (applied by every skill)

Every output includes:
- **AI-assisted label:** "[AI-ASSISTED DRAFT — requires student analysis and attorney review]"
- **Confidence indicators:** Where the skill is uncertain, it says so explicitly
- **Verification prompts:** Specific things the student should fact-check before relying on the output
- **Ethical reminders calibrated to task:** e.g., /draft outputs remind about ABA Formal Op. 512 supervision requirements

These are not optional and not configurable. They're the baseline.
```

## After writing

**Show what this plugin can do.** Before closing, offer:

> **Want to see what I can help with?**

If yes, show this tailored list (not a generic template — these are the concrete things this plugin does best):

> **Here's what I'm good at in law school clinic practice:**
>
> - **Student intake on a new case** — e.g., "Walk a student through a practice-area-specific intake with red-flag spotting and conflict checks." Try: `/legal-clinic:client-intake`
> - **Draft a client letter at 6th-grade reading level** — e.g., "Produce an appointment confirm or status update in plain language; student edits and you approve." Try: `/legal-clinic:client-letter`
> - **Build an IRAC memo scaffold** — e.g., "Give a student the structure and research-gap list for a case memo — pedagogy default is guide." Try: `/legal-clinic:memo`
> - **Track deadlines across the active docket** — e.g., "See what's due in the next 14 / 7 / 3 / 1 days with warnings per your cadence." Try: `/legal-clinic:deadlines`
> - **Ramp up a new cohort** — e.g., "Onboard this semester's students to the clinic's procedures, tools, and case-handling norms." Try: `/legal-clinic:ramp`
> - **Semester handoff** — e.g., "Build per-case transition memos for the incoming cohort." Try: `/legal-clinic:semester-handoff`
>
> **My suggestion for your first one:** Run `/ramp` yourself first so you see what your students will see at the start of the semester. Or tell me what's on your plate and I'll pick.

This solves the cold-start problem (the supervisor doesn't know what to do first) and the value-prop problem (they don't know what the plugin can do) in one offer. Make the list specific. Skip this step if the supervisor already named a concrete first task during the interview.


1. **Show the supervision style choice.** "You picked [formal queue / flags / lighter-touch]. That means [what it means in practice]. Right call?"

2. **Show the practice-area templates table.** "These are the documents `/draft` will know how to start. Missing anything?"

3. **Offer a `/ramp` preview.** "Want to see what a student's onboarding will look like? I can walk you through it as if you were a new student."

4. **Note what wasn't provided.** If no handbook: "`/ramp` will be thin until you upload a handbook — it'll cover the commands but not your clinic's specific procedures." If no local rules: "`/draft` will use state defaults for formatting — upload local rules when you have them."

5. **If LIMITED DATA flagged:** "Practice Profile is thin — downstream skills will be generic until more materials are added. Biggest gap: [specific — e.g., no handbook means /ramp covers commands only]. Biggest easy win: [specific — e.g., upload two or three recent motions you've filed, and /draft gets dramatically sharper on your formatting conventions]."

6. **Before your first case review, connect a research tool.** Say: "Before your first case review or memo: connect a research tool. Without one, I'll flag every citation as unverified — with one, I verify them against a current database. In Cowork: Settings → Connectors. In Claude Code: authorize when a skill prompts you."

   <!-- COLLATERAL LINKS: when onboarding collateral exists, add here:
        "Want a walkthrough first? [Watch the 3-minute intro](URL) or [read the getting-started guide](URL)." -->

7. **Close with the "you can change anything later" note:**

> Done. Your clinic's configuration is at `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md` — a plain text file you can read and edit directly. Anything you answered can be changed:
>
> - Edit the file directly for a quick change
> - Run `/legal-clinic:cold-start-interview --redo` for a full re-interview
> - Run `/legal-clinic:cold-start-interview --check-integrations` to re-check what's connected
>
> The things clinics most commonly tweak later: practice areas (when the clinic takes on a new one), supervision style (formal review queue vs. configurable flags vs. lighter-touch — many clinics start one way and shift after the first semester), and jurisdiction / local rules (when a matter lands in an unusual court). Your configuration will improve as students use the plugin — when `/ramp` misses something or `/draft` uses the wrong caption format, the fix is usually here.

## Your practice profile learns

After writing the practice profile, close with this note:

> **Your practice profile learns.** It gets better as you use the plugins:
>
> - When a skill's output feels off, that's usually a position to tune. The output will tell you which one.
> - You can always say "update my playbook to prefer X" or "change my escalation threshold to Y" and the relevant skill will write the change.
> - Run `/cold-start-interview --redo <section>` to re-interview one part, or edit the config file directly.
>
> Ten minutes of setup gets you a working profile. A month of use gets you one that reads like you wrote it yourself.

## What this does NOT do

- **Make supervision decisions.** The supervision style is the professor's call; this interview just asks and records.
- **Replace the clinic's existing case management.** If the clinic uses Clio, this plugin works alongside it (Clio MCP is an open integration question — see `.mcp.json`).
- **Onboard students.** That's `/ramp`. This is the professor's one-time setup.
