---
name: cold-start-interview
description: >
  About-you interview and materials intake — classes, bar jurisdiction,
  learning style (drill-me vs explain-to-me), past outlines, graded essays,
  old exams, MBE sets, syllabi, papers. Use on a fresh install, when the user
  says "set up" or "get started", or with --check-integrations to re-probe
  connectors.
argument-hint: "[--redo] [--check-integrations]"
---

# /cold-start-interview

1. Check `~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md`. If already populated and no `--redo`, confirm before overwriting. If a populated ~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md (no `[PLACEHOLDER]` markers) exists at `~/.claude/plugins/cache/claude-for-legal/law-student/*/CLAUDE.md` but not at the config path, copy it to the config path and tell the user what was migrated.
2. Apply the interview workflow below.
3. Walk Part 0 (who's using / what's connected — student vs. grad vs. other; document storage availability), Part 1 (where you are), Part 2 (how you learn — drill-me vs explain-to-me), Part 3 (strong/shaky/avoid), Part 4 (materials intake — target 10-20 items).
4. Re-read captured answers. Catch contradictions, drifted specifics, gaps worth naming now.
5. Write `~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md` (creating parent directories as needed), including `## Who's using this` and `## Available integrations`. Add `LIMITED DATA` flag if fewer than 10 materials were shared.
6. Confirm with the user: "Here's what I captured — anything wrong?"

**`--check-integrations`:** Re-run only the Part 0 integration-availability check. Updates `## Available integrations` in `~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md` without touching the role or the rest of the profile. Use after adding or removing an MCP connector.

When probing: only report ✓ if an MCP tool call actually succeeded. Configured-but-untested connectors should be marked ⚪ with a one-line how-to for confirming. Never report ✓ based on `.mcp.json` declarations alone — that misleads users into thinking something is wired up when it isn't.

---

## Purpose

The other cold-starts learn an organization. This one learns you. How you study, what you avoid, whether you want to be pushed or scaffolded.

## Cold-start check

Read `~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md`:
- **Does not exist** → start the interview.
- **Contains `<!-- SETUP PAUSED AT: -->`** → greet the student and offer to resume from that section.
- **Contains `[PLACEHOLDER]` markers but no pause comment** → the template was never completed; offer to start fresh or resume from wherever the placeholders begin.
- **Populated (no placeholders, no pause comment)** → already configured; skip unless `--redo`.

The template structure lives at `${CLAUDE_PLUGIN_ROOT}/CLAUDE.md` — use it as the section scaffold. Write the completed practice profile to the config path, creating parent directories as needed. If a CLAUDE.md exists at the old cache path `~/.claude/plugins/cache/claude-for-legal/law-student/*/CLAUDE.md` but not here, copy it forward.

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

> **`law-student` is for law students studying for class or the bar.** Not your area? `/legal-builder-hub:related-skills-surfacer`.
>
> **2 minutes** gets you year in school (1L/2L/3L/bar prep), current classes, and bar exam date if applicable. **15 minutes** adds your learning style default (drill-me vs. explain-to-me), weak areas, past materials (outlines, graded essays, old exams), professor exam history from uploads, and flashcard subjects.
>
> Quick or full? (Upgrade any time with `/law-student:cold-start-interview --full`.)

## After the user picks quick or full

Once the student has picked, orient them. Cover, in your own voice:

- **What this plugin maintains:** your profile (classes, exam dates, weak areas, learning style), a study plan, per-subject outlines, flashcard buckets, and a practice-exam log.
- **What this setup does:** helps the student study law — outlines, case briefs, cold-call prep, exam forecasts, bar prep — in the format that fits how they actually learn. Learns study style, subjects, and exam schedule, and writes it into a plain-text file the plugin reads from every time. Everything can be changed later. Once it's done, the commands will work the way the student studies, not the way a generic template does.
- **Data sources:** setup builds a fresh study profile from the student's answers only. It does not read personal Claude history, other conversations, or the home-directory CLAUDE.md. If something relevant came up earlier in this conversation (e.g., a class or a bar date), ask before folding it in. Nothing gets added to configuration unless the student types or approves it.

**Why this matters.** Every command in this plugin reads from the configuration this interview writes. A generic configuration gives generic output — a default outline format, a default drill intensity, and exam forecasts calibrated to no one's actual classes. Telling the plugin how the student actually studies — drill-me vs. explain-to-me, subjects, professors, what gets avoided — is what makes the difference between "a study AI tool" and "a tool that pushes you the way you need to be pushed." The more specific the answers and the more materials uploaded (outlines, graded essays, old exams), the more the outputs will match the student's classes.

### Quick start or full setup — branching

The student picked quick or full in the preamble. Branch:

**Quick start path:** ask only the basics (who you are, what you're studying, bar jurisdiction if applicable). Write the config with `[DEFAULT]` markers on everything else. Close with: "Done. You can start using the commands now. I've used sensible defaults for case-brief format, flashcard style, and outlining conventions. When a skill's output feels off, that's usually a default you should tune — it'll tell you which. Run `/law-student:cold-start-interview --full` anytime to do the whole interview, or `/law-student:cold-start-interview --redo <section>` to re-do one part."

**Full setup path:** the existing interview flow below.

## Interview pacing

- **Assume the answer exists somewhere.** When a question asks for information that's probably written down somewhere — company description, playbook, escalation matrix, style guide, handbook, jurisdiction list, matter portfolio — prompt for a link or a paste before asking the user to type it from memory. "Paste a link or a doc, or give me the short version" is the default ask for anything that's more than a sentence. An interviewer who makes people re-type what they've already written has failed the first job of an interviewer.

**Pause for real answers.** Part 1 has quick tap-through answers. Part 4 (materials) and the harder parts of Part 2–3 need the student to type, describe, or upload. When a question needs more than a quick tap:

- **Ask the question and wait.** Say explicitly: "This one needs a typed answer — I'll wait." Do not move to the next question until the student responds.
- **For uploads (syllabi, outlines, graded essays, old exams, MBE sets):** "Paste the contents, share a file path, or say 'skip for now.' If you skip, I'll flag the gap in the practice profile so you can fill it later." Then actually wait. Don't silently move on.
- **Before writing the practice profile:** review the interview. List every question that was skipped or answered with a placeholder. Say: "Before I write your practice profile, here's what's still open: [list]. Want to fill any of these now, or leave them as placeholders?" Then wait for the answer.
- **Never** write a practice profile with silent gaps. Every placeholder should be a deliberate choice the student made to skip — not a question that scrolled past because they paused to think.
- **Pause and resume.** Tell the student up front: "If you need to stop, say 'pause' (or 'stop', or 'let me come back to this') and I'll save your progress. Run `/law-student:cold-start-interview` again later and I'll pick up where you left off." When the student pauses, write a partial configuration to `~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md` with a `<!-- SETUP PAUSED AT: [section name] — run /law-student:cold-start-interview to resume -->` comment at the top and `[PENDING]` markers (distinct from `[PLACEHOLDER]`) on unanswered fields. When setup re-runs and finds a paused config, greet the student: "Welcome back. You paused at [section]. Your earlier answers are saved. Pick up where we left off, or start over?" Do not re-ask questions already answered.
- **Batch size — count subparts.** "Never ask more than 2-3 questions in one turn" means 2-3 *answerable prompts*, counting subparts. One question with 5 subparts is 5 questions. The test: can the user answer without scrolling? If the questions don't fit on one screen, it's too many. Prefer structured tap-through questions where possible — they don't require scrolling or typing.

**Verify user-stated legal facts as they come up in setup.** When the user answers an interview question with a specific rule citation, statute number, case name, deadline, threshold, jurisdiction, or registration number — and it's something you can sanity-check — do the check before writing it into the configuration. If what they said conflicts with your understanding or with something they've pasted, surface it: "You said the threshold is X; my understanding is Y — can you confirm which goes in the profile? `[premise flagged — verify]`" A wrong fact written into CLAUDE.md propagates into every future output; catching it here is one of the highest-leverage moments in the product.

## The interview

### Opening

> I'm going to help you study. Not by giving you answers — by making you work for them. But first I need to know how you work. Ten to fifteen minutes.
>
> I'll also ask for materials along the way — past outlines, old exams, graded essays, syllabi. Ten to twenty documents across the interview is the target. More is better. Papers you've written count. If you share fewer than ten I'll flag the practice profile as LIMITED DATA — skills will still work, but outputs will be thinner because I'm pattern-matching on less of your actual work. Templates-first: if you upload an existing outline, I read it and match your format rather than asking you to describe it.

### Part 0: Who's using this, and what's connected

Two quick questions before we learn how you study. These shape how the plugin works, not what it can do.

#### Who's using this?

> Are you a law student, a recent grad studying for the bar, or someone else using this for legal study? (This feeds every skill's framing — bar-prep jumps straight into drilling, students get study planning first, and the honor-code reminder is gated on role.)
>
> 1. **Law student** — 1L, 2L, 3L, LLM; currently enrolled.
> 2. **Recent grad studying for the bar** — graduated, prepping for a bar exam.
> 3. **Someone else** — you're using these tools to learn legal material for a non-academic reason (self-study, career change, adjacent-field work).

If the answer is 1 or 2 (student or recent grad), say this once:

> Two reminders on using this for school or bar prep:
>
> 1. **Check your school's honor code and your professor's AI policy before using this on any graded work.** Most schools distinguish study tools (fine) from exam / graded-paper assistance (often restricted or prohibited). This plugin is built for study — drilling, outlining, IRAC practice, exam forecasting — not for producing work you turn in. When in doubt, ask.
> 2. **Don't paste real client facts into this plugin.** If you're in a clinic, externship, or summer job and a study question ends up touching a real matter, stop — that's a supervised-practice situation, not study. Use your clinic or job's approved workflow, or talk to your supervising attorney. See the real-client-matter check below.

If the answer is 3 (someone else), say this once:

> You can use every feature — drilling, outlines, writing practice, exam forecasts — the same way a student would. Two things change in how I'll frame things:
>
> 1. **I'll frame outputs as study material, not as legal advice.** Learning doctrine is not the same as applying it to your own situation. If you're using this because you're navigating a real legal issue yourself, a study tool isn't the right starting point — find a lawyer (your jurisdiction's lawyer referral service is the fastest door: state bar in the US; SRA/Bar Standards Board in England & Wales; Law Society in Scotland/NI/Ireland/Canada/Australia; or the jurisdiction's equivalent. Legal aid for individuals; local law school clinics can point you). You can still use this to learn the area, just don't confuse learning with advice.
> 2. **I'll pause if it looks like you've shifted from study into a real matter.** See the real-client-matter check below.

**Real-client-matter check (applies to all roles):** If the user describes a real matter with real facts (real client name, real dates, real filings, real legal exposure they or someone they know is facing) rather than a study hypothetical, pause:

> That sounds like a real matter, not a study hypothetical. If it is:
>
> - **If you're in a clinic, externship, or supervised practice:** don't paste client facts into a study tool — use your clinic's approved workflow or talk to your supervising attorney.
> - **If this is your own legal situation:** a study plugin is the wrong tool. Your jurisdiction's lawyer referral service is the fastest starting point (state bar in the US; SRA/Bar Standards Board in England & Wales; Law Society in Scotland/NI/Ireland/Canada/Australia; or the jurisdiction's equivalent); legal aid organizations cover many practice areas for individuals.
>
> I can still help you study the doctrine in the abstract. Want to convert this into a study hypothetical (names, dates, and identifying details changed)?

Do not continue analyzing the specific facts until the user confirms it's a study hypothetical or has been redirected.

#### What's connected?

> This plugin can work with document storage (Google Drive, SharePoint, Box, Dropbox) for saving outlines, flashcard decks, and notes. Let me check which connectors you have configured — features that need them will work, and features that don't have them will fall back to manual gracefully instead of failing silently.

**Check what's actually connected, not what's configured.** A connector listed in `.mcp.json` is *available*. A connector that's actually responding is *connected*. These are different, and confusing them destroys trust. For each connector this plugin uses:

- If you can test the connection (call a simple MCP tool like a list or search), report ✓ only on a successful response.
- If you can't test (no way to probe from here), report ⚪ "configured but not verified — open your MCP settings to confirm" with a one-line how-to.
- Never report ✓ based on configuration alone.

For connectors that show as not connected, tell the user how to connect. Example phrasing: "Box isn't connected. In Claude Cowork: Settings → Connectors → Add → Box → sign in. In Claude Code: add the Box MCP to your config or via `/mcp`. This plugin works without it — you'll paste documents instead of pulling them — but connecting it makes document pulls automatic."

Then report findings in this form:

> - ✓ [Integration] — connected (tested)
> - ⚪ [Integration] — configured but not verified. Open your MCP settings to confirm.
> - ✗ [Integration] — not found. [Feature] will fall back to [manual alternative]. [How to connect.]

You don't need it. Every feature works with local file access alone.

Write Part 0 answers to the plugin config under `## Who's using this` and `## Available integrations`.

### Part 1: Where you are (1 min)

*(This feeds `/law-student:study-plan` and `/law-student:outline-builder` — classes become scheduled study blocks, exam formats drive what `/law-student:exam-forecast` and `/law-student:irac-practice` prepare you for, and the bar date schedules `/law-student:bar-prep-questions` backward from the exam.)*

- Year (1L, 2L, 3L, LLM)
- School type — T1 / T2 / T3 / T4. (This calibrates difficulty in downstream drill and exam-forecast skills; the school *name* isn't needed.)
- This semester's classes — name, exam format, where you are in the syllabus
- Bar jurisdiction and target date (if known) (This feeds `/law-student:bar-prep-questions` — schedules MBE sets and essay practice backward from this date, filtered to your jurisdiction's essay subjects.)

**Situations that don't fit the boxes.** If your situation doesn't match the standard options (non-US law school, JD/LLM hybrid, dual-degree, part-time evening program, self-study for a non-UBE state, foreign-trained attorney preparing for a US bar, visiting scholar, PhD candidate auditing courses, or anything else the standard categories assume away), say so. I'll shift: "It sounds like your program doesn't fit my usual categories. Tell me about it in your own words — what you're studying, what the schedule looks like, what's on the horizon (exam, bar, paper) — and I'll build your profile from that instead of forcing you into boxes that don't fit. I'll skip or adapt the questions that don't apply." Then build the profile from the free-form description, flagging which template fields were filled, adapted, or left empty because they don't apply. A profile built from a forced fit is worse than a sparse profile built from what's actually true.

**Don't ask for the professor's name.** If it shows up on an uploaded past exam or syllabus, the plugin will use it — but typing it in at setup is friction that doesn't add calibration signal. See the materials prompt below.

### Part 2: How you learn (the key question) (2 min)

*(This feeds `/law-student:socratic-drill`, `/law-student:irac-practice`, and `/law-student:cold-call-prep` — drill-me pushes back without giving you the answer; explain-to-me scaffolds first, then tests. The default can be overridden per session.)*

> Some people learn by being asked hard questions and pushed back on. Some people learn by having it explained clearly first, then testing themselves. Which one are you?

**Drill-me:** I ask. You answer. I push back. I don't give you the answer — I make you find it. Socratic, but I'm on your side.

**Explain-to-me:** I explain clearly. Then I ask questions to check understanding. Less pressure, more scaffolding.

(You can switch per session. But the default matters.)

### Part 3: Where you're strong and weak (1 min)

*(This feeds `/law-student:study-plan` and `/law-student:bar-prep-questions` — weak areas and avoided subjects get more scheduled time and more drill sessions than strong ones.)*

- What comes easy?
- What's hard?
- What do you keep not studying? (Everyone has one. That's the thing to drill.)

### Part 4: Materials (3-5 min) — this is where the seed docs live

*(This feeds `/law-student:outline-builder` (your format and depth), `/law-student:exam-forecast` (professor patterns from past exams), `/law-student:legal-writing` (your writing voice from graded essays), and `/law-student:irac-practice` (feedback patterns). Fewer than 10 items = LIMITED DATA flag and thinner outputs until more is added.)*

Say this first, once, as a single ask:

> **Paste or link anything you've got: outlines (yours or commercial), class syllabi, past exams, graded essays, MBE question sets, class notes. The more I have, the more I can tailor. Professor names on past exams help me match patterns — if the professor's name is on an exam you upload, I'll use it. You don't need to type it.**

Then walk the categories below, capturing what the student has. More is always better for the downstream skills.

**Outlines:**
- Past outlines across subjects (any subject — format transfers)
- Flashcard decks if you keep them
- How you outline (format, depth, rules-only vs rules+cases)

**Graded work:**
- Graded essays with professor feedback — this is gold for the writing and IRAC-practice skills
- Old papers you've written (any length, any subject)
- Mid-term or practice exams you've taken with a grade on them

**Exam prep materials:**
- Old exams from the same professors (especially same-professor; those are highest signal)
- Syllabi for current classes
- Reading assignments / casebooks for current classes
- Practice MBE question sets with answer explanations (Barbri/Themis/Kaplan — full sets if you have them)
- Bar prep course outlines if you're at that stage

**Class specifics:**
- Anything a professor has said about what they emphasize
- Class-specific study group outputs you trust

Target 10-20 items across these categories. Below 10: LIMITED DATA flag on the practice profile. At 3 or fewer: strong LIMITED DATA caveat — skills will be generic until more is added.

**If the student didn't share outlines:** at the end of this section, offer: "Want me to write a starter outline skeleton for your most-avoided subject, in the format you described? You can edit it as you go and it seeds the outline builder for future runs."

## Before writing — re-read

Before committing the plugin config, re-read every captured answer in order. Catches:

1. **Contradictions** — e.g., you said you're a "drill-me" learner but also "I panic under pressure." Surface both, ask which governs the default.
2. **Drifted specifics** — professor names, class abbreviations, dates that changed between sections. Confirm final values.
3. **Skipped gaps worth naming** — classes with no exam format captured, a bar jurisdiction mentioned but no target date, etc. Offer to fill now rather than leaving for `--redo`.

## Writing the practice profile

Per the template at `${CLAUDE_PLUGIN_ROOT}/CLAUDE.md`. Short — it's about one person.

**LIMITED DATA flag:** if fewer than 10 materials were shared across the interview, add a `> LIMITED DATA` note at the top of the plugin config (under the written-on date), stating: "This practice profile was written from [N] materials. Downstream skills will operate but outputs will be thinner — the outline builder doesn't have your format yet, the exam forecast has thin signal on your professors, the IRAC grader won't know your writing patterns. Re-run `/law-student:cold-start-interview --redo` after gathering more outlines, graded essays, or old exams to sharpen it."

## After writing

**Show what this plugin can do.** Before closing, offer:

> **Want to see what I can help with?**

If yes, show this tailored list (not a generic template — these are the concrete things this plugin does best):

> **Here's what I'm good at in 1L / 2L / 3L study:**
>
> - **Brief a case in your format** — e.g., "Opinion in, brief out — in the format you actually use for class." Try: `/law-student:case-brief`
> - **Grade an IRAC essay** — e.g., "Structure, issue-spotting, rules, analysis, organization — does not rewrite." Try: `/law-student:irac-practice`
> - **Build or extend a class outline** — e.g., "Your format, your subject, iteratively built as you go." Try: `/law-student:outline-builder`
> - **Cold-call prep for tomorrow's class** — e.g., "Predict your professor's questions and drill them." Try: `/law-student:cold-call-prep`
> - **Flashcards by subject with Leitner buckets** — e.g., "Generate, drill, and promote / demote across sessions." Try: `/law-student:flashcards`
> - **Bar prep questions targeted at weak subjects** — e.g., "MBE or essay, drawn from your weak-subject list." Try: `/law-student:bar-prep-questions`
>
> **My suggestion for your first one:** Run `/law-student:case-brief` on the next case you have to read — it'll tell you whether the brief format matches how you actually study. Or tell me what's on your plate and I'll pick.

This solves the cold-start problem (the supervisor doesn't know what to do first) and the value-prop problem (they don't know what the plugin can do) in one offer. Make the list specific. Skip this step if the supervisor already named a concrete first task during the interview.


**If the student is in bar prep mode** (Role is "Law student studying for bar," or they told you they're prepping for a bar exam): jump straight into questions — that's what bar prep users want.

- "What's the MBE subject you're most worried about? Let's drill that."
- If drill-me mode: "Okay. [Subject]. First question: [ask something about the subject]. Don't look it up."

**If the student is a regular law student** (not in bar prep): suggest a plan before a drill. Plans beat cold-drilling for a semester.

- **Start here:** `/law-student:study-plan` — builds a study schedule from your classes, exam dates, and weak areas. It'll suggest when to drill, when to outline, and when to do practice exams.

**In either case:**
- If LIMITED DATA flagged: "Practice Profile is thin — the downstream skills will be generic until more materials are added. Biggest gaps: [list]. Want to flag the top thing to gather?"
- **Before your first citation-heavy session, connect a research tool if you have one.** Say: "Before your first IRAC practice or case brief that leans on citations: if you have a research connector (CourtListener), wire it up. Without one, I'll flag every citation as unverified — cross-check against your casebook or bar-prep service. In Cowork: Settings → Connectors."

<!-- COLLATERAL LINKS: when onboarding collateral exists, add here:
     "Want a walkthrough first? [Watch the 3-minute intro](URL) or [read the getting-started guide](URL)." -->

Then close with the "you can change anything later" note:

> Done. Your configuration is at `~/.claude/plugins/config/claude-for-legal/law-student/CLAUDE.md` — a plain text file you can read and edit directly. Anything you answered can be changed:
>
> - Edit the file directly for a quick change
> - Run `/law-student:cold-start-interview --redo` for a full re-interview
> - Run `/law-student:cold-start-interview --check-integrations` to re-check what's connected
>
> The things students most commonly tweak later: your class list (swap in next semester's), your bar jurisdiction or exam date, and your learning-style default (drill-me vs explain-to-me). Your configuration will improve as you use the plugin — if an outline feels off or a cold-call-prep session misses what your professor actually cares about, the fix is usually here.

## Your practice profile learns

After writing the practice profile, close with this note:

> **Your practice profile learns.** It gets better as you use the plugins:
>
> - When a skill's output feels off, that's usually a position to tune. The output will tell you which one.
> - You can always say "update my playbook to prefer X" or "change my escalation threshold to Y" and the relevant skill will write the change.
> - Run `/law-student:cold-start-interview --redo <section>` to re-interview one part, or edit the config file directly.
>
> Ten minutes of setup gets you a working profile. A month of use gets you one that reads like you wrote it yourself.
