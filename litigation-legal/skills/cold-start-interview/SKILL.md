---
name: cold-start-interview
description: House cold-start for the litigation plugin — branches by role (in-house, firm associate, solo) and side (plaintiff, defense, both), captures risk calibration, landscape, and house style, and writes the practice profile CLAUDE.md. Use on a fresh install, when the user wants to set up or redo the practice profile, or to re-check available integrations.
argument-hint: "[--redo | --check-integrations]"
---

# /cold-start-interview

1. Check `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md`. If already populated and no `--redo`, ask before overwriting.
2. Follow the workflow and reference below.
3. Run Part 0 (role, side, integration check). The interview branches by role and side.
   - **Role** routes the practice profile structure: **in-house** (portfolio of matters, outside counsel oversight, reserve methodology, board/audit reporting), **firm associate** (case work — matter context, case theory and pivot fact, seed brief in house style, eDiscovery/priv-log setup), or **solo** (caseload + contingency or retainer economics + client expectations + SOL tracking, then the case-theory and brief-style sections).
   - **Side** routes calibration vocabulary: **plaintiff** (asserting, case value, contingency, SOL cliff), **defense** (responding, exposure, reserves where applicable, insurance tender), or **both/varies** (captures a default and lets per-matter skills re-ask).

   After Part 0, walk the sections that match the selected role. Do not run the in-house path for solo users — reserves, ASC 450, and board-memo framing are not the right frame for a solo practice. Offer defaults; capture freeform overrides. Ask for seed documents at each section (non-pushy; note that sharing sharpens every downstream skill).
4. Surface gaps. If the user doesn't have an articulated risk framework or reporting threshold, note it and offer to think through it now or leave `[PLACEHOLDER]` to fill later.
5. Migration: if a populated CLAUDE.md (no `[PLACEHOLDER]` markers) exists at `~/.claude/plugins/cache/claude-for-legal/litigation-legal/*/CLAUDE.md` but not at the config path, copy it to the config path and show the user what was migrated.
6. Write `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md`. Date the footer.
7. Confirm with the user before finalizing: "Here's what I captured — anything wrong?"

## Flags

- `--redo` — re-run the full interview and overwrite `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md`.
- `--check-integrations` — re-scan available MCP connectors and refresh the `## Available integrations` table in `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` without re-running the full interview. Use after setting up a new connector (DMS, document storage, Gmail, scheduled-tasks, CLM).

When probing: only report ✓ if an MCP tool call actually succeeded. Configured-but-untested connectors should be marked ⚪ with a one-line how-to for confirming. Never report ✓ based on `.mcp.json` declarations alone — that misleads users into thinking something is wired up when it isn't.

---

# Cold-Start Interview: Litigation

## Purpose

Every matter intake, every chronology build, every brief draft, every status rollup reads from this file. If the frame isn't captured, the plugin makes weaker triage calls and the user has to think from scratch each time. This interview fills the frame once so everything downstream gets sharper.

The plugin serves three distinct litigation roles — in-house counsel managing a portfolio of matters, firm associates doing the underlying brief / deposition / discovery work, and solo practitioners running a caseload directly. The vocabulary is different for each, and the interview branches to match. Solo practitioners do not get the in-house path compressed — they get a dedicated solo path (caseload, contingency or retainer economics, client expectations) plus the brief / case-theory sections that apply to anyone who drafts.

The interview also asks which side the user mostly represents — plaintiff (asserting claims), defense (responding to claims), both, or varies by matter. Risk calibration, demand-letter posture, discovery stance, and chronology framing all differ by side, and the practice profile carries the default so downstream skills don't have to ask every time.

**Tone:** socratic, not checklist. If the user doesn't have a written framework, this is often the thing that forces articulation. Lean into that. Don't rush past gaps — name them, offer to think through, allow "leave for later."

## Cold-start check

Read `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md`:
- **Does not exist** → start the interview.
- **Contains `<!-- SETUP PAUSED AT: -->`** → greet the user and offer to resume from that section.
- **Contains `[PLACEHOLDER]` markers but no pause comment** → the template was never completed; offer to start fresh or resume from wherever the placeholders begin.
- **Populated (no placeholders, no pause comment)** → already configured; skip unless `--redo`.

The template structure lives at `${CLAUDE_PLUGIN_ROOT}/CLAUDE.md` — use it as the section scaffold. Write the completed practice profile to the config path, creating parent directories as needed. If a CLAUDE.md exists at the old cache path `~/.claude/plugins/cache/claude-for-legal/litigation-legal/*/CLAUDE.md` but not here, copy it forward.

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

Open with the fork-first preamble. Keep it to 3-4 short lines. Ask quick-or-full before anything else.

> **`litigation-legal` is for people who work litigation — managing a portfolio of matters in-house, drafting briefs and doing discovery at a firm, or both as a solo practitioner.** Not your area? `/legal-builder-hub:related-skills-surfacer`.
>
> **2 minutes** gets you your role (in-house / firm-associate / solo), practice setting, side default (plaintiff / defense), and active matter count, plus working defaults for risk calibration, house brief style, and privilege conventions. **15 minutes** adds your real severity × likelihood bands, settlement-authority ladder (in-house) or fee economics (solo), outside-counsel roster, house brief style from a seed brief, privilege-log format, demand-letter templates, and landscape notes.
>
> Quick or full? (Upgrade any time with `/cold-start-interview --full`.)

**Quick start path:** ask only Part 0 (role, practice setting, integrations) and the path branch. Write the config with `[DEFAULT]` markers on everything else. Close with: "Done. You can start using the commands now. I've used sensible defaults for risk calibration, house style, and case-theory scaffolding. When a skill's output feels off, that's usually a default you should tune — it'll tell you which. Run `/litigation-legal:cold-start-interview --full` anytime to do the whole interview, or `/litigation-legal:cold-start-interview --redo <section>` to re-do one part."

**Full setup path:** the existing interview flow below. After the user picks, give the fuller orientation described next, then proceed to Part 0.

## After the user picks quick or full

Give the fuller orientation. One paragraph, in your own voice:

> "This plugin maintains: your practice profile (risk calibration, privilege conventions, house style), a matter ledger (`_log.yaml`), per-matter files (chronology, hold notices, histories, priv logs), and a work-product archive. It supports litigation work whether you're in-house managing a portfolio, a firm associate drafting briefs and depo outlines, or a solo practitioner doing both. It learns which role you're in, your risk calibration or case theory, your dispute landscape or production setup, your house conventions, and writes them into a plain-text file the plugin reads from every time. Everything you answer can be changed later."

Then the fresh-profile note:

> "Setup builds a fresh professional profile from your answers. It does not read your personal Claude history, other conversations, or your home-directory CLAUDE.md. If I notice relevant information in our conversation context — e.g., you mentioned your company or matter earlier — I'll ask before using it. Nothing personal gets folded into your practice configuration unless you type it or approve it."

Then: "Ready? A few quick questions first."

**Why this matters** (offer if the user pushes back on the time cost). Every matter intake, every portfolio status, every brief draft reads from the configuration this interview writes. A generic configuration gives generic output — a default risk matrix, a default citation style, a generic priv-log format. Telling the plugin the actual severity bands, the actual settlement authority ladder, the actual brief structure is what makes the difference between "a litigation AI tool" and "a tool that triages and drafts the way you do." Especially load-bearing: the pivot fact (if firm-side) and the seed documents.

Draw the practice profile only from the user's typed answers and documents they upload during the interview. Do not read `~/CLAUDE.md` or pull practice facts from ambient context. If something relevant is already visible in this conversation, ask before using it.

## Interview pacing

- **Assume the answer exists somewhere.** When a question asks for information that's probably written down somewhere — company description, playbook, escalation matrix, style guide, handbook, jurisdiction list, matter portfolio — prompt for a link or a paste before asking the user to type it from memory. "Paste a link or a doc, or give me the short version" is the default ask for anything that's more than a sentence. An interviewer who makes people re-type what they've already written has failed the first job of an interviewer.

**Pause for real answers.** Some questions have quick tap-through answers. Others need the user to type something, describe something, or upload an exemplar (board memo, hold template, demand letter, risk memo, case theory memo, seed brief). When a question needs more than a quick tap:

- **Batch size — count subparts.** "Never ask more than 2-3 questions in one turn" means 2-3 *answerable prompts*, counting subparts. One question with 5 subparts is 5 questions. The test: can the user answer without scrolling? If the questions don't fit on one screen, it's too many. Prefer structured tap-through questions where possible — they don't require scrolling or typing.
- **Ask the question and wait.** Say explicitly: "This one needs a typed answer — I'll wait." Do not move to the next question until the user responds. This matters most for the theory section (firm-associate path) — do not paraphrase a half-answer and push on.
- **For seed-document uploads:** "Paste the contents, share a file path, or say 'skip for now.' If you skip, I'll flag the gap in your practice profile so you can fill it later." Then actually wait.
- **Before writing the practice profile:** review every captured answer. List any questions that were skipped, answered with placeholders, or produced a contradiction. Say: "Before I write your practice profile, here's what's still open: [list]. Want to fill any of these now, or leave them as placeholders?" Then wait.
- **Never** write a practice profile with silent gaps. Every `[PLACEHOLDER]` should be a deliberate choice the user made to skip, not a question that scrolled past. The `LIMITED DATA` footer is for seed-document thinness only — not for questions the interview never actually asked.
- **Pause and resume.** Tell the user up front: "If you need to stop, say 'pause' (or 'stop', or 'let me come back to this') and I'll save your progress. Run `/litigation-legal:cold-start-interview` again later and I'll pick up where you left off." When the user pauses, write a partial configuration with a `<!-- SETUP PAUSED AT: [section name] — run /litigation-legal:cold-start-interview to resume -->` comment at the top and `[PENDING]` markers (distinct from `[PLACEHOLDER]`) on unanswered fields. When setup re-runs and finds a paused config, greet: "Welcome back. You paused at [section]. Your earlier answers are saved. Pick up where we left off, or start over?" Do not re-ask questions already answered.

**Verify user-stated legal facts as they come up in setup.** When the user answers an interview question with a specific rule citation, statute number, case name, deadline, threshold, jurisdiction, or registration number — and it's something you can sanity-check — do the check before writing it into the configuration. If what they said conflicts with your understanding or with something they've pasted, surface it: "You said the threshold is X; my understanding is Y — can you confirm which goes in the profile? `[premise flagged — verify]`" A wrong fact written into CLAUDE.md propagates into every future output; catching it here is one of the highest-leverage moments in the product.

## Part 0: Who's using this + role routing

### Who's using this?

> Who'll be using this plugin day to day? (This feeds the work-product header on every matter briefing, chronology, priv log, and demand draft — lawyer outputs get the privilege header, non-lawyer outputs get the "research notes, review with counsel" header.)
>
> 1. **Lawyer or legal professional** — attorney, paralegal, legal ops working under attorney oversight.
> 2. **Non-lawyer with attorney access** — founder, business lead, contracts manager, HR, procurement; you have an in-house or outside attorney you can consult.
> 3. **Non-lawyer without regular attorney access** — you're handling this yourself.

If the answer is 2 or 3, say this once (don't repeat it on every output):

> You can use every feature here — research, review, drafting, tracking. Two things change in how I work:
>
> 1. **I'll frame outputs as research for attorney review, not as verdicts.** Instead of "GREEN — sign it," you'll get "here's what I found and here are the questions to ask before you sign." That's more useful than a green light you can't be sure of.
> 2. **I'll pause before steps that have legal consequences** — sending a demand, responding to a subpoena, issuing or releasing a legal hold, filing a brief, submitting a privilege log, designating documents in discovery, closing a matter, accepting a settlement. I'll ask whether you've reviewed with an attorney, and I'll put together a short brief so the conversation with them is fast.
>
> This isn't a disclaimer. It's the plugin knowing the difference between what it's good at — research, organization, structure — and licensed legal judgment about your specific situation, which a tool can't give you. A few hours of a lawyer's time at the right moment is usually cheaper than the mistake.

If the answer is 3, add:

> If you need to find a licensed attorney, solicitor, barrister, or other authorised legal professional in your jurisdiction: your professional regulator's referral service is the fastest starting point (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent). Many offer free or low-cost initial consultations.

### Role (the branching question — ask early)

> **How do you work litigation?** (This determines which pillars of the interview run — in-house gets reserves and board memos, firm-associate gets case theory and seed briefs, solo gets caseload economics plus the firm-associate brief work. It also sets defaults for /matter-intake, /portfolio-status, /oc-status, and every other skill's vocabulary.)
>
> **(a) In-house managing a portfolio** — matters, outside counsel, deadlines, demands, holds. You own many matters at once, most of which are run by outside firms. Status rollups and board memos are part of your job.
>
> **(b) At a firm doing brief drafting, discovery, deposition prep, document review** — you're the associate or paralegal responsible for actually producing the work product. One or a few matters, deep on each.
>
> **(c) Solo / small firm running a caseload** — you intake, triage, advise, and draft. No partner above you; no in-house reserve / board-memo layer. Economics are contingency or retainer, not billable hours to a large client.
>
> **(d) Something else** — describe in a sentence.

Record the answer in the practice profile's `## Role` section at the top (`in-house | firm-associate | solo | other`). Downstream skills read this to pick defaults (e.g., chronology mode, which commands are primary, which vocabulary to use).

**Branching rules for the rest of this interview:**

- `in-house` → run the **In-house path** (Pillars 1–3 below). Skip the firm-associate and solo sections.
- `firm-associate` → run the **Firm-associate path** (Parts A–D below). Skip the in-house portfolio / OC / board-memo questions and the solo caseload / economics questions.
- `solo` → run the dedicated **Solo path** (Sections S1–S3 below) — caseload, client expectations, contingency or retainer economics, office management — **then** run the Firm-associate path (Parts A–D) because solo practitioners still write briefs and work cases. Do NOT run the In-house path — reserves, ASC 450, board memos, and settlement-authority ladders up to a GC are not the right frame for a solo practice.
- `other` → ask for a one-sentence description, then pick the closest branch.

### Which side do you mostly represent?

Ask this right after the role question. It's load-bearing for risk-calibration framing, demand-letter posture, discovery stance, and the way chronologies are built.

> **Which side do you mostly represent?** (This feeds /demand-draft, /demand-received, /subpoena-triage, /chronology, and /claim-chart — plaintiff framing treats demand letters as assertions and discovery as offensive, defense framing treats them as received and responsive.)
>
> **(a) Plaintiff / claimant** — you bring claims for individuals or businesses. Demand letters are assertions you draft and send. Discovery is offensive. Statute of limitations is a cliff you work against. Economics are often contingency.
>
> **(b) Defense / respondent** — you defend businesses or individuals against claims. Demand letters are received and triaged. Discovery is defensive. Exposure is assessed, reserved (in-house), tendered to insurance (where applicable).
>
> **(c) Both** — your practice regularly includes both. Ask for a default (plaintiff or defense); individual skills will ask per-matter when it matters.
>
> **(d) Varies by matter** — no strong default; every matter gets asked.

Record under `## Side` in the practice profile (`plaintiff | defense | both [default plaintiff/defense] | varies`). Branching rules for calibration that follows:

- **Plaintiff:** risk calibration is about case value, contingency economics, client expectations, statute of limitations exposure. Demand letters are the assertion. Discovery is offensive. Settlement-authority conversations are with the client, not a GC/board. (For firm-associate plaintiff-side: partner review replaces GC escalation.)
- **Defense:** risk calibration is about exposure, reserves (in-house only), settlement authority, insurance coverage. Demand letters are received and triaged. Discovery is defensive — responding, asserting privilege, narrowing.
- **Both / varies:** the interview captures the default and the skills (`demand-draft`, `subpoena-triage`, `matter-intake`, `chronology`, `claim-chart`) ask per-matter when the side changes the output.

### Practice setting

> Which best describes where you're practicing?
>
> 1. **Solo practitioner**
> 2. **Small firm (2–10)**
> 3. **Midsize firm**
> 4. **Large firm / Am Law**
> 5. **In-house** (company legal department)
> 6. **Government**
> 7. **Legal aid**
> 8. **Clinic**
> 9. **Other**

This refines escalation / supervision language in the practice profile:

- **Solo / small without hierarchy (1, 2):** Reframe authority-ladder questions as "when do you call in outside counsel or a colleague for a second opinion." Escalation maps to *consult* not *route for approval*.
- **Midsize / large firm / in-house / government (3, 4, 5, 6):** Ask the full escalation chain, authority ladder, and internal-contacts table.
- **Legal aid / clinic (7, 8):** Route toward the supervision model — supervising attorney of record, sign-off chain, review-queue mechanics.
- **Other (9):** Ask for a one-sentence description, then pick the closest branch.

**Practices that don't fit the boxes.** If the user's practice doesn't match the options above (international arbitration, public international law, amicus-only, academic consulting, pro bono panel, tribal court, military justice, maritime, or anything else the standard categories assume away), offer: "It sounds like your practice doesn't fit my usual categories. Tell me about it in your own words — what you do, who for, what jurisdictions and forums, what the work looks like — and I'll build your profile from that instead of forcing you into boxes that don't fit. I'll skip or adapt the questions that don't apply." Then build the profile from the free-form description, flagging which template fields were filled, adapted, or left empty because they don't apply. A profile built from a forced fit is worse than a sparse profile built from what's actually true.

### What's connected?

> This plugin can work with: DMS (iManage), document storage (Google Drive, SharePoint, Box), Gmail, scheduled-tasks, CLM (Ironclad), eDiscovery (Everlaw, Relativity, DISCO, Aurora), legal research (CourtListener, Descrybe, Trellis), outside-counsel recommendations (TopCounsel). Let me check which connectors you have configured — features that need them will work, and features that don't will fall back gracefully instead of failing silently.

**Check what's actually connected, not what's configured.** A connector listed in `.mcp.json` is *available*. A connector that's actually responding is *connected*. These are different, and confusing them destroys trust. For each connector this plugin uses:

- If you can test the connection (call a simple MCP tool like a list or search), report ✓ only on a successful response.
- If you can't test (no way to probe from here), report ⚪ "configured but not verified — open your MCP settings to confirm" with a one-line how-to.
- Never report ✓ based on configuration alone.

For connectors that show as not connected, tell the user how to connect. Example phrasing: "Box isn't connected. In Claude Cowork: Settings → Connectors → Add → Box → sign in. In Claude Code: add the Box MCP to your config or via `/mcp`. This plugin works without it — you'll paste documents instead of pulling them — but connecting it makes document pulls automatic."

Then report findings in this form:

> - ✓ [Integration] — connected (tested)
> - ⚪ [Integration] — configured but not verified. Open your MCP settings to confirm.
> - ✗ [Integration] — not found. [Feature] will fall back to [manual alternative]. [How to connect.]

You don't need all of these. Core features work with file access alone.

Write a `## Role`, `## Who's using this`, and `## Available integrations` section into the plugin config immediately after the opening. Add `## Outputs` with the work-product header rule per the CLAUDE.md template.

---

## In-house path (role == `in-house`)

*Skip this whole section if the user's role is `firm-associate` or `solo`.*

> I want to capture the frame you triage matters against — your risk calibration, the dispute landscape, and how you write. Once, so every matter intake reads from it. I'll offer defaults where there are reasonable ones. You can accept, edit, or leave blank to come back to.
>
> I'll also ask for seed documents along the way — prior board memos, reserve memos, litigation hold templates, exemplar demand letters, a sample risk memo. Ten to twenty total across the interview is the target. Anything below ten and I'll flag the practice profile as LIMITED DATA in the footer — skills will still run, but their outputs will be thinner because they're matching on weaker patterns. Templates-first: if you upload an exemplar, I'll read it and only ask about gaps rather than walking the full structure from scratch.

### Pillar 0 — Company profile

Team-level context. If another `-legal` plugin already has a `## Company profile` block populated, copy it here rather than re-enter.

- Org / legal entity
- Industry
- Public / private / subsidiary
- Regulated status
- Core jurisdictions (operational + frequent-fora)
- Headcount + legal team size
- Key internal contacts (GC, CFO, HR lead, Comms, CISO, Board lit/audit chair) — names + when to loop in
- This counsel's name and reporting line

### Pillar 1 — Risk calibration

> Before the structured questions: do you have an existing risk-calibration memo, a reserve-policy document, or an outside-counsel billing-guidelines doc I can read? Paste the contents, share file paths, or say 'no' and I'll walk the pillar question by question. If you share one, I'll extract the severity bands, materiality thresholds, and authority ladder and only ask about gaps.

If not:

**Risk appetite (2 min)** — in a sentence, how does this company approach litigation? (This feeds /matter-briefing and /portfolio-status — sets how conservative or aggressive every matter briefing is when calling a matter's risk tier.)

**Severity × likelihood (3–5 min)** — offer the default 3×3. Severity bands (dollar and non-dollar triggers). Likelihood bands. If unarticulated: "Fair. A lot of counsel don't. Want to sketch now, or leave the default?"

**Materiality thresholds (2–3 min)** — reserve trigger, disclosure trigger, board/audit committee, GC-only escalation. *Seed doc opportunity:* reserve memo template or disclosure checklist.

**Settlement authority (1–2 min)** — dollar ladder, special carve-outs (structural relief requires board regardless of dollar).

**Plain-English escalation (1 min).** Ask directly:

> When a matter needs something above your authority — a settlement offer above your band, a demand you can't answer alone, a hold decision that needs the GC — who does that go to? Give me a name, a role, or "I decide myself."

(Solo practitioners: "I decide myself" is the right answer; the question still matters for the record. If you loop in outside counsel for second opinions, name the firm.)

**Insurance profile (1–2 min)** — lines in force (D&O, EPL, Cyber, GL/E&O), carriers, limits, retentions, tendering protocol.

**Offer:** "If you didn't upload a risk-calibration memo, want me to write your risk calibration and authority ladder up as a standalone memo you can share and maintain?"

### Pillar 2 — Landscape

*Company profile lives in Pillar 0. Landscape is litigation-specific.*

- Business context (30 sec) — one-paragraph on what we do and why we get sued.
- Dispute patterns (2–3 min) — matter types, frequency, posture.
- Frequent adversaries (1–2 min).
- Outside counsel bench (2–3 min) — firms, lead partners, matter type, rate posture, engagement letter status. *Seed doc:* outside counsel guidelines. (This feeds /oc-status — the skill later drafts weekly status requests to these firms.)
- Frequent fora (30 sec).
- Document storage (2–3 min) — where matter docs live (filesystem, Drive, SharePoint, Box, Gmail, CLM, DMS, eDiscovery), default matter folder pattern, how docs get shared with OC.
- Conflicts clearance (1–2 min) — how this shop runs conflicts; who does it; hard block on intake or parallel.

### Pillar 3 — House style

> Before the structured questions: do you have a house-style guide, a template board memo, a hold-notice template, or exemplar demand letters I can read? Paste the contents, share file paths, or say 'no' and I'll walk the questions.

If not:

- Board / audit committee memo (2 min) — format, tone, cadence. *Seed doc:* recent board memo (redacted fine).
- Reserve memo — format and approver. *Seed doc:* sample reserve memo.
- Outside counsel directives — email format, cadence, budget posture.
- Privilege conventions — marking; default subjective-call posture (mark and flag); review mechanic (inline / queue / both). (This feeds /privilege-log-review — the skill applies your marking rules and review mechanic on every priv-log pass.)
- Legal hold — template, issuance protocol, refresh cadence. *Seed doc:* hold template. (This feeds /legal-hold — the skill issues, refreshes, and releases holds using your house template.)
- Escalation — channel norms, subject-line convention.
- Demand-letter practice — *not asked here.* Demand posture (tone, time limits, marking, signer) is set per matter, not per practice. `/litigation-legal:demand-intake` and `/litigation-legal:demand-draft` will ask when they need it — those calls depend on the relationship, the amount, and whether litigation is likely, and a practice-level default tends to mis-calibrate the specific letter. What the setup interview *does* want here: insurance-tender timing (who you notify and when, before sending) and materiality threshold for matter creation (below $X, record only; above, create a matter). Those are practice-level.

**Offer:** "If you didn't upload a house-style guide or templates, want me to write your house-style rules up as a standalone style memo?"

---

## Solo path (role == `solo`)

*Skip this whole section if the user's role is `in-house` or `firm-associate`. Solo users run this path **and** the Firm-associate path that follows.*

> Solo practice is its own frame — caseload, client expectations, retainer or contingency economics, office management. The in-house world (ASC 450 reserves, board memos, outside-counsel oversight, settlement-authority ladders up to a GC) doesn't apply here, and I'm not going to pretend it does. The firm-world reserves questions don't apply either. What I need from you is the shape of your actual caseload and how you run your practice.
>
> A few seed documents help — a prior demand letter, a retainer agreement, a client-update email you'd be willing to share as an exemplar. Anything we can learn from saves a round trip later.

### Section S1 — Practice shape and caseload

- **Caseload size** — roughly how many active matters do you carry at once? What's too many?
- **Matter mix** — rough percentages: plaintiff vs defense, practice areas (e.g., PI, family, employment, small business disputes, landlord/tenant). No need to be precise; a sentence is enough.
- **Jurisdictions** — the state(s) and courts you primarily practice in. Include federal if relevant.
- **Typical case duration** — weeks, months, years? Useful for downstream skills to scale effort and deadline horizons.
- **Capacity flags** — is there a point where you stop accepting cases? How do you know you're over capacity?

### Section S2 — Client expectations and economics

*This replaces what the in-house path calls "risk calibration / reserve methodology / settlement authority ladder." Solos don't run reserves and don't escalate to a GC; the same decisions show up as client-facing economics.*

**Fee structure (the main driver).** Pick the one that fits most of your work:

- **Contingency** (default assumption for plaintiff-side PI, employment, consumer): what's your standard percentage? Pre-suit vs post-suit? What's the cost advance posture — client, firm, hybrid? At what exposure do you stop taking a case on contingency?
- **Hourly / retainer**: hourly rate, standard retainer, trust-account mechanics.
- **Flat fee**: which matter types, and the fee range.
- **Mixed**: describe the mix.

**Client expectations (2 min).** Ask directly:

- How often do you update clients on their matters (weekly, monthly, event-based)?
- What form do updates take — phone call, email, letter, client portal?
- What's your default posture on settlement conversations with the client (aggressive push to settle, let the client drive, case-dependent)?

**Exposure / case-value read (plaintiff-side).** What's your quick mental framework for deciding a case is worth taking? Examples: "liability clear, damages > $50K, statute has a year or more, client credible" — no judgment on the specifics; just capture yours.

**Exposure read (defense-side solo — less common but possible).** What's your mental model of acceptable exposure vs reportable to client? Solo defense is usually for individuals or small businesses without an insurance layer — capture how you actually think about it.

**When you call for help.** Solos don't have a GC or a partner above them, but most have someone — co-counsel, a mentor, a local listserv, a bar committee. Who do you call for a second opinion, and on what kinds of matters?

> Give me a name, a role, or "nobody — I decide on my own."

**Client updates in writing (1 min).** *Seed doc opportunity:* a recent client update email or letter (redacted). This is the solo equivalent of an in-house board memo — it's how you communicate status to your stakeholder. If the user shares one, read it and extract the structure and tone for the house-style section.

### Section S3 — Office management and landscape

*Skip any question where the answer is obvious from earlier context.*

- **Statute of limitations tracking** — how do you track SOL cutoffs across the caseload? (Calendar, case-management software, a paper docket, memory — whatever's real.) This is the solo equivalent of the in-house "materiality / reserve trigger" because missing a SOL is the failure mode that ends a solo career.
- **Case management software** — Clio, MyCase, PracticePanther, Smokeball, Rocket Matter, paper files, spreadsheets, other.
- **Document storage** — Google Drive, Dropbox, OneDrive, local filesystem, the case-management tool's storage. Where do matter documents actually live?
- **Frequent fora** — courts you actually appear in.
- **Frequent adverse parties / counsel** — repeat players you regularly see on the other side.
- **Bench of co-counsel / referral attorneys** — who do you associate in for cases outside your comfort zone? Who refers out to you?
- **Conflicts clearance** — how do you run conflicts? A solo's version is usually informal (memory + a client list check), which is fine — capture what it is.

### Solo house style

Skip the board-memo / reserve-memo / outside-counsel-directive questions entirely. Solo house style is:

- **Client update** — format, tone, cadence. *Seed doc:* a recent update letter or email.
- **Retainer / engagement agreement** — template. *Seed doc:* the exemplar (redacted fine).
- **Privilege conventions** — marking; review mechanic.
- **Legal hold** — even for a solo, preservation matters when litigation is anticipated. Template, if any. *Seed doc:* hold notice if issued.
- **Demand-letter practice** — *not asked here.* Demand posture (tone, time limits, marking, signer) is set per matter, not per practice — the solo equivalent of "who signs" answers itself (you), and tone/marking/timing depend on the specific dispute. `/litigation-legal:demand-intake` will ask when it drafts.

**Offer:** "If you didn't upload a client-update exemplar or retainer, want me to write your house-style rules up as a standalone memo you can reuse?"

After Section S3, continue to the **Firm-associate path** below. Solo practitioners write briefs, build chronologies, and prep depositions like firm associates do — the case-theory and seed-brief work applies.

---

## Firm-associate path (role == `firm-associate` or `solo`)

> Before I touch a document, I need the theory. What's our story? What's theirs? What does the case turn on? Then I need to see how your firm writes — a brief you're proud of — so my drafts don't look like they came from somewhere else.

### Part A: The matter (2 min)

- Matter name, client, case number, court
- Our side (plaintiff / defendant)
- Partner and senior associate (skip if solo / small without hierarchy)
- Stage (pleadings, discovery, summary judgment, trial prep)
- Key dates coming up

### Part B: The theory — this is everything (3–4 min)

> Tell me our theory of the case. Not the complaint — the story. If you had to tell a jury why we win in two sentences, what are they?

- Our theory in a paragraph
- Their theory in a paragraph (know the other side)
- **The pivot fact** — the fact the case turns on
- Key facts for us
- Key facts against us (the ones you're worried about)
- The legal issue that matters most

### Part C: Seed documents (3–4 min)

> Two things:
>
> 1. **The case theory memo**, if one exists. If the theory lives in someone's head and not on paper, that's fine — we just captured it above.
>
> 2. **A prior brief in house style.** Not from this case — any case. The best one you've got. I'll learn your citation style, structure, tone, how you organize arguments. (This feeds /brief-section-drafter — every future brief section gets drafted in your extracted citation format, heading structure, and tone, not a generic template.)

**From the brief:** citation format (Bluebook, ALWD, local rules), section structure, heading conventions, tone (aggressive / measured), length norms.

### Part D: Document review setup (1–2 min)

> Before the questions: do you have a privilege-log format, a chronology format, or a review-protocol doc I can read? Paste the contents, share file paths, or say 'no' and I'll ask one at a time.

If not:
- eDiscovery platform (Everlaw, Relativity, DISCO, Aurora)
- Review protocol — coding categories, who makes priv calls
- Privilege log format
- Key custodians and date range

**Offer:** "If you didn't upload a priv-log or chronology format, want me to write your review protocol and priv-log format up as a standalone reference you can share with a review team?"

---

## Before writing — re-read

Before committing the plugin config, re-read every captured answer in order. This catches three categories of mistake:

1. **Contradictions between answers** — e.g., user said "fight everything" in risk appetite and "settle quickly" in demand-letter default. Surface both, ask which governs.
2. **Drifted specifics** — names, dates, thresholds that changed between sections. Confirm the final value.
3. **Skipped gaps worth naming** — sections left blank that the user might want to complete now rather than via `--redo`.

Also: if the role is `firm-associate`, double-check that the pivot fact and the seed brief were captured. These are load-bearing. If either is missing, name it explicitly before writing.

## Writing the practice profile

Write the completed practice profile to the plugin config, using the template at `${CLAUDE_PLUGIN_ROOT}/CLAUDE.md` as the section scaffold. Fill every section captured; leave `[PLACEHOLDER]` for sections the user skipped. Date the footer.

**Section gating by role:**

- `in-house` → full in-house structure (Company profile, Risk calibration with ASC 450 / reserve / board-memo rows, Outside counsel bench, Board/audit committee memo). Omit or mark N/A for solo-only sections (fee structure, retainer, contingency).
- `firm-associate` → firm-world structure (case theory, pivot fact, partner review, seed brief). Omit reserve / board-memo / ASC 450 sections; omit solo fee / retainer sections.
- `solo` → solo structure (caseload, fee structure, client expectations, SOL tracking, retainer or contingency, office management) **plus** the firm-associate sections (case theory, seed brief). Omit in-house reserve / ASC 450 / board-memo / settlement-authority-ladder-to-GC sections entirely — they are not the right frame for a solo practice and including them as placeholders adds noise rather than structure.

Where a template section carries in-house-only vocabulary ("ASC 450 reserves", "board / audit committee memo"), either omit the section for non-in-house roles or translate the vocabulary into the equivalent solo or firm-associate concept. Solo equivalent of "board memo" is "client update letter." Solo equivalent of "reserve methodology" is "case-value read" (plaintiff) or "exposure read" (defense). Do not carry the accounting-standard language into a solo profile.

**LIMITED DATA flag:** if fewer than 10 seed documents were shared across the interview, add a `> LIMITED DATA` note at the top (under the written-on date): "This practice profile was written from [N] seed documents and interview answers. Downstream skills will operate but outputs will be thinner until more exemplars are added. Re-run `/cold-start-interview --redo` after collecting more templates to sharpen calibration."

## Gap surfacing

After the interview, before writing, summarize and **wait for an answer**:

> Here's what I captured. Gaps I noticed:
> - [list any skipped sections, placeholders left blank, questions where the user said "come back later"]
>
> Want to fill any of these now, or leave them as placeholders? You can also fill them later via `/litigation-legal:cold-start-interview --redo` or by editing the plugin config directly. This one is worth thinking about before I write: [name the most important gap and why].

Do not proceed to writing until the user answers.

## After writing

**Show what this plugin can do.** Before closing, offer:

> **Want to see what I can help with?**

If yes, show this tailored list (not a generic template — these are the concrete things this plugin does best):

> **Here's what I'm good at in litigation practice:**
>
> - **Intake a new matter** — e.g., "Uniform intake questions, writes matter.md + history.md, appends to the portfolio log." Try: `/litigation-legal:matter-intake`
> - **Triage an inbound demand** — e.g., "Options analysis, portfolio cross-check, handoff to matter intake if it graduates." Try: `/litigation-legal:demand-received`
> - **Draft a demand letter** — e.g., "Privilege / FRE 408 gate, .docx output, post-send checklist, matter-creation offer." Try: `/litigation-legal:demand-draft`
> - **Build a deposition outline** — e.g., "Docs + topics + impeachment + exhibits, tied to case theory." Try: `/litigation-legal:deposition-prep`
> - **Issue or refresh a legal hold** — e.g., "Draft the hold memo, update the log, schedule a refresh." Try: `/litigation-legal:legal-hold`
> - **Portfolio rollup** — e.g., "Risk distribution, upcoming deadlines, stale matters across the active portfolio." Try: `/litigation-legal:portfolio-status`
>
> **My suggestion for your first one:** Run `/portfolio-status` — it shows you at a glance where the portfolio sits, and it's zero-input to try. Or tell me what's on your plate and I'll pick.

This solves the cold-start problem (the supervisor doesn't know what to do first) and the value-prop problem (they don't know what the plugin can do) in one offer. Make the list specific. Skip this step if the supervisor already named a concrete first task during the interview.


- If `in-house`: "The in-house practice profile is now written. Every matter intake will read from it. Want to run `/litigation-legal:matter-intake` on your most live matter to see it in action?"
- If `firm-associate`: "Here's the theory as I captured it. Read the pivot fact — did I get it right? What's the next deadline? Let's start there."
- If `solo`: "Your solo practice profile is written — caseload shape, fee economics, how you run the office — plus the case-theory and brief-style work for a live matter. Want to run `/litigation-legal:matter-intake` on your most live matter and see what the intake looks like with your configuration?"

### Close with the "you can change anything later" note

> "Your practice profile is at `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` — a plain text file you can read and edit directly. Anything you answered can be changed:
>
> - Edit the file directly for a quick change
> - Run `/litigation-legal:cold-start-interview --redo` for a full re-interview
> - Run `/litigation-legal:cold-start-interview --new-matter` to reuse the practice profile on a new matter (firm-associate / solo)
> - Run `/litigation-legal:cold-start-interview --check-integrations` to re-check what's connected
>
> The sections people adjust most: for in-house, the **severity × likelihood thresholds** and the **outside counsel bench**; for firm associate, the **case theory** (especially the pivot fact) and the **house brief style** extracted from the seed brief; for solo, the **fee structure** (contingency percentage or hourly rate) and the **side default** (plaintiff / defense) — a wrong default there skews every demand-letter and chronology output. When an output feels off, the fix is usually here."

### Before your first matter

**Connect a research tool.** Without one, I'll flag every citation as unverified — with one, I verify them against a current database. In Cowork: Settings → Connectors. In Claude Code: authorize when a skill prompts you.

<!-- COLLATERAL LINKS: when onboarding collateral exists, add here:
     "Want a walkthrough? [Watch the 3-minute intro](URL) or [read the getting-started guide](URL)." -->

### Your practice profile learns

After writing the practice profile, close with this note:

> **Your practice profile learns.** It gets better as you use the plugins:
>
> - When a skill's output feels off, that's usually a position to tune. The output will tell you which one.
> - You can always say "update my playbook to prefer X" or "change my escalation threshold to Y" and the relevant skill will write the change.
> - Run `/cold-start-interview --redo <section>` to re-interview one part, or edit the config file directly.
>
> Ten minutes of setup gets you a working profile. A month of use gets you one that reads like you wrote it yourself.

## What this skill does not do

- Decide the framework for the user. Defaults are starting points; the user's judgment is the actual content.
- Pretend gaps aren't there. Better to leave `[PLACEHOLDER]` honestly than to invent a threshold.
- Fight the user. If they say "I don't have that yet," note it and move on.
- Read personal `~/CLAUDE.md` or other ambient context without asking.
