---
name: cold-start-interview
description: >
  House cold-start interview (request list + prior memo), or --new-deal for
  deal-specific context. Modular: identifies which practice areas apply (M&A,
  Board & Secretary, Public Company, Entity Management), then asks targeted
  questions for each active module and writes only the relevant sections to the
  plugin config. Use on fresh install, when CLAUDE.md still has [PLACEHOLDER]
  markers, when starting a new deal, or to re-check integrations or refresh a
  module.
argument-hint: "[--redo | --new-deal | --check-integrations | --module [m&a | board | public | entities]]"
---

# /cold-start-interview

1. Check `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md`. If `--new-deal`, skip to per-deal setup. If `--check-integrations`, skip the interview — re-run only the Part 0 `What's connected?` check and rewrite the `## Available integrations` table in `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md`. When probing: only report ✓ if an MCP tool call actually succeeded. Configured-but-untested connectors should be marked ⚪ with a one-line how-to for confirming. Never report ✓ based on `.mcp.json` declarations alone — that misleads users into thinking something is wired up when it isn't.
2. Run the interview below (Part 0 first — role + integrations — then modules).
3. Seed docs: diligence request list + one prior issues memo.
4. Extract: categories, thresholds, memo format, AI tool config.
5. Migration: if a populated CLAUDE.md (no `[PLACEHOLDER]` markers) exists at `~/.claude/plugins/cache/claude-for-legal/corporate-legal/*/CLAUDE.md` but not at the config path, copy it to the config path and tell the user what was migrated.
6. Write `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md` (create parent directories as needed). For `--new-deal`, write `~/.claude/plugins/config/claude-for-legal/corporate-legal/deals/[code]/deal-context.md`.

---

## Purpose

Corporate counsel roles vary more than almost any other in-house function. A solo GC at a 50-person startup runs M&A, manages the cap table, and secretaries the board. A corporate counsel at a Fortune 500 might own only §16 filings and the disclosure committee process. This interview finds out which areas are live for you and builds only the relevant practice profile — nothing left blank that doesn't apply.

## Cold-start check

Read `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md`:
- **Does not exist** → start the interview.
- **Contains `<!-- SETUP PAUSED AT: -->`** → greet the user and offer to resume from that section.
- **Contains `[PLACEHOLDER]` markers but no pause comment** → the template was never completed; offer to start fresh or resume from wherever the placeholders begin.
- **Populated (no placeholders, no pause comment)** → already configured; skip unless `--redo` or `--module [name]`.

The template structure lives at `${CLAUDE_PLUGIN_ROOT}/CLAUDE.md` — use it as the section scaffold. Write the completed practice profile to the config path, creating parent directories as needed.

If a CLAUDE.md exists at the old cache path `~/.claude/plugins/cache/claude-for-legal/corporate-legal/*/CLAUDE.md` but not at the config path, copy it forward to the config path before proceeding.

- `--redo` — full re-interview, overwrites all sections
- `--module [m&a | board | public | entities]` — add or refresh a single module
- `--new-deal` — skip house setup, go straight to per-deal context (M&A module only)

---

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

Before asking anything else, show the fork-first preamble — 3-4 short lines, no longer:

> **`corporate-legal` is for people who support M&A deals, board and corporate governance, public company compliance, and entity management.** Not your area? `/legal-builder-hub:related-skills-surfacer`.
>
> **2 minutes** gets you your role, practice setting, jurisdiction, and module selection (M&A, board, public, entity management), plus working defaults for materiality thresholds, issues-memo format, board-minutes format, and disclosure-schedule format. **15 minutes** adds your real materiality thresholds, house consent and minutes formats from seed documents, your entity list and compliance cadence, deal-team briefing cadence, and escalation matrix.
>
> Quick or full? (Upgrade any time with `/corporate-legal:cold-start-interview --full`.)

Wait for the user's pick before showing anything else.

<!-- COLLATERAL LINKS: when onboarding collateral exists, prepend a line above the preamble:
     "Want a walkthrough first? [Watch the 3-minute intro](URL) or [read the getting-started guide](URL), then come back and run /corporate-legal:cold-start-interview." -->

## After the user picks quick or full

Once the user has chosen, orient them before the first interview question:

> "This plugin maintains your practice profile (materiality thresholds, consent style, board format), per-deal folders with diligence grids, closing checklists, disclosure schedules, and a compliance calendar. It supports your corporate legal practice — M&A diligence, board consents, entity compliance, closing checklists — in your house format. This setup interview learns which of those areas are live for you and how you actually run them. It writes that into a plain-text file the plugin's skills read from every time. Everything you answer can be changed later. Once it's done, the plugin will work the way you work, not the way a generic template does."
>
> Then: "Ready? A few quick questions first, then we'll go deeper on the modules that apply."

**Why this matters.** Every command in this plugin reads from the configuration this interview writes. A generic configuration gives you generic output — a default materiality threshold, a default issues-memo format, a default consent style, a default closing-checklist structure. Telling the plugin how you actually run M&A, board, public, or entity work is what makes the difference between "a corporate AI tool" and "a tool that works the way you work." The more specific your answers — your real materiality cuts, your real resolution language, your real house format — the more the outputs will look like they came from your desk.

**Fresh professional profile.** Setup builds a fresh professional profile from the user's answers and documents they explicitly share. It does not read the user's personal Claude history, unrelated conversations, or their home-directory CLAUDE.md. If something relevant surfaces in the current conversation context (e.g., they mentioned the company earlier), ask before using it — do not fold anything personal into the corporate practice profile unless the user types it or approves it.

Corollary: the interview's inputs are the user's typed answers and documents they explicitly share. Do not pull from ambient context, prior sessions, or user memory to fill in gaps.

## Interview pacing

- **Assume the answer exists somewhere.** When a question asks for information that's probably written down somewhere — company description, playbook, escalation matrix, style guide, handbook, jurisdiction list, matter portfolio — prompt for a link or a paste before asking the user to type it from memory. "Paste a link or a doc, or give me the short version" is the default ask for anything that's more than a sentence. An interviewer who makes people re-type what they've already written has failed the first job of an interviewer.
- **Batch size — count subparts.** "Never ask more than 2-3 questions in one turn" means 2-3 *answerable prompts*, counting subparts. One question with 5 subparts is 5 questions. The test: can the user answer without scrolling? If the questions don't fit on one screen, it's too many. Prefer structured tap-through questions where possible — they don't require scrolling or typing.

**Pause for real answers.** Some questions are quick (entity type, exchange, fiscal year end). Others need the user to type, describe, or upload (prior issues memo, board minutes, consent precedent, org chart). When a question needs more than a quick tap:

- **Ask and wait.** Say explicitly: "This one needs a typed answer — I'll wait." Do not move to the next question until the user responds.
- **For uploads (issues memo, minutes, consents, org chart):** "Paste the contents, share a file path, or say 'skip for now.' If you skip, I'll flag the gap in your practice profile so you can fill it later." Then actually wait. These seed documents drive format extraction — skipping silently means every future output will be in a generic template instead of house format.
- **Before writing the practice profile:** review the interview and list any questions that were skipped or answered with placeholders — especially the seed documents per active module. Say: "Before I write your practice profile, here's what's still open: [list]. Want to fill any of these now, or leave them as placeholders?" Then wait.
- **Never** write a practice profile with silent gaps. Every placeholder should be a deliberate choice the user made to skip, not a question that scrolled past.
- **Pause and resume.** Tell the user up front: "If you need to stop, say 'pause' (or 'stop', or 'let me come back to this') and I'll save your progress. Run `/corporate-legal:cold-start-interview` again later and I'll pick up where you left off." When the user pauses, write a partial configuration to `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md` with a `<!-- SETUP PAUSED AT: [section name] — run /corporate-legal:cold-start-interview to resume -->` comment at the top and `[PENDING]` markers (distinct from `[PLACEHOLDER]`) on unanswered fields. When setup re-runs and finds a paused config, greet the user: "Welcome back. You paused at [section]. Your earlier answers are saved. Pick up where we left off, or start over?" Do not re-ask questions already answered.

---

**Verify user-stated legal facts as they come up in setup.** When the user answers an interview question with a specific rule citation, statute number, case name, deadline, threshold, jurisdiction, or registration number — and it's something you can sanity-check — do the check before writing it into the configuration. If what they said conflicts with your understanding or with something they've pasted, surface it: "You said the threshold is X; my understanding is Y — can you confirm which goes in the profile? `[premise flagged — verify]`" A wrong fact written into CLAUDE.md propagates into every future output; catching it here is one of the highest-leverage moments in the product.

## The interview

### Opening

> Before I ask about your specific workflows, I want to understand which areas of corporate work are actually live for you. That way I only set up what you need and skip the rest.

**Quick start path:** ask only Part 0 (role, practice setting, integrations) and which modules are active. Write the config with `[DEFAULT]` markers on everything else. Close with: "Done. You can start using the commands now. I've used sensible defaults for materiality thresholds, disclosure schedule format, and board-minutes format. When a skill's output feels off, that's usually a default you should tune — it'll tell you which. Run `/corporate-legal:cold-start-interview --full` anytime to do the whole interview, or `/corporate-legal:cold-start-interview --redo <section>` to re-do one part."

**Full setup path:** the existing interview flow below.

---

### Part 0: Who's using this, and what's connected

Three quick questions before we get into corporate specifics. These shape how the plugin works, not what it can do.

#### Who's using this?

> Who'll be using this plugin day to day? (This feeds the work-product header on every memo, consent, minutes draft, and diligence memo — lawyer outputs get the privilege header, non-lawyer outputs get the "research notes, review with counsel" header.)
>
> 1. **Lawyer or legal professional** — attorney, paralegal, legal ops working under attorney oversight.
> 2. **Non-lawyer with attorney access** — founder, business lead, contracts manager, HR, procurement; you have an in-house or outside attorney you can consult.
> 3. **Non-lawyer without regular attorney access** — you're handling this yourself.

If the answer is 2 or 3, say this once (don't repeat it on every output):

> You can use every feature here — research, review, drafting, tracking. Two things change in how I work:
>
> 1. **I'll frame outputs as research for attorney review, not as verdicts.** Instead of "GREEN — sign it," you'll get "here's what I found and here are the questions to ask before you sign." That's more useful than a green light you can't be sure of.
> 2. **I'll pause before steps that have legal consequences** — signing a contract, terminating someone, sending a demand, filing something, clearing a launch, responding to a regulator. I'll ask whether you've reviewed with an attorney, and I'll put together a short brief so the conversation with them is fast.
>
> This isn't a disclaimer. It's the plugin knowing the difference between what it's good at — research, organization, structure — and licensed legal judgment about your specific situation, which a tool can't give you. A few hours of a lawyer's time at the right moment is usually cheaper than the mistake.

If the answer is 3, add:

> If you need to find an attorney, solicitor, barrister, or other authorised legal professional: contact your professional regulator (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent) — most offer a lawyer referral service as the fastest starting point. Many offer free or low-cost initial consultations. For small businesses, local law school clinics (and equivalents like SCORE mentors in the US) can point you in the right direction. For individuals, legal aid organizations cover many practice areas.

#### What's connected?

> This plugin can work with: VDR (Intralinks, Datasite, Box), board portal (Diligent, BoardEffect), document storage, and Slack. Let me check which connectors you have configured — features that need them will work, and features that don't have them will fall back to manual gracefully instead of failing silently.

**Check what's actually connected, not what's configured.** A connector listed in `.mcp.json` is *available*. A connector that's actually responding is *connected*. These are different, and confusing them destroys trust. For each connector this plugin uses:

- If you can test the connection (call a simple MCP tool like a list or search), report ✓ only on a successful response.
- If you can't test (no way to probe from here), report ⚪ "configured but not verified — open your MCP settings to confirm" with a one-line how-to.
- Never report ✓ based on configuration alone.

For connectors that show as not connected, tell the user how to connect. Example phrasing: "Box isn't connected. In Claude Cowork: Settings → Connectors → Add → Box → sign in. In Claude Code: add the Box MCP to your config or via `/mcp`. This plugin works without it — you'll paste documents instead of pulling them — but connecting it makes document pulls automatic."

Then report findings in this form:

> - ✓ [Integration] — connected (tested)
> - ⚪ [Integration] — configured but not verified. Open your MCP settings to confirm.
> - ✗ [Integration] — not found. [Feature] will fall back to [manual alternative]. [How to connect.] If you set this up later, re-run `/corporate-legal:cold-start-interview --check-integrations`.
>
> You don't need all of these. Core features work with file access alone.

#### Practice setting

Ask once, early, so Part 1 (company profile) and every module's escalation question branch correctly:

> Practice setting? (This feeds every skill's escalation framing — in-house gets "loop in GC," solo/small gets "call outside counsel," clinic gets "route to supervising attorney.")
>
> - **Solo / small firm (no hierarchy)** — I'll skip approval-chain questions and ask when you'd loop in a colleague or outside counsel instead.
> - **Midsize / large firm** — I'll ask about your approval chain, billing thresholds, and who signs off above you.
> - **In-house** — I'll ask about your escalation matrix, who the GC/CLO is, and when something goes to the business.
> - **Government / legal aid / clinic** — I'll ask about supervision structure and any restrictions on your practice.
> - **My practice doesn't fit any of these** — say so. I'll adapt.

**Practices that don't fit the boxes.** If the user's practice doesn't match the options above (international arbitration, public international law, amicus-only, academic consulting, pro bono panel, tribal court, military justice, maritime, or anything else the standard categories assume away), offer: "It sounds like your practice doesn't fit my usual categories. Tell me about it in your own words — what you do, who for, what jurisdictions and forums, what the work looks like — and I'll build your profile from that instead of forcing you into boxes that don't fit. I'll skip or adapt the questions that don't apply." Then build the profile from the free-form description, flagging which template fields were filled, adapted, or left empty because they don't apply. A profile built from a forced fit is worse than a sparse profile built from what's actually true.

Branching notes:

- **Solo or small firm without a hierarchy:** skip or reframe internal escalation-chain questions. Instead of "who approves above your authority," ask "when do you bring in outside counsel for a second opinion." In the practice profile, write the `**Escalation:**` line in `## Company profile` around consultation triggers (outside counsel firm, named senior colleague), not internal approval levels. In the M&A module, the "deal lead" question still applies.
- **In-house, midsize, or large firm:** ask the escalation chain as currently designed (Part 1).
- **Legal aid / clinic:** route toward a supervision-model framing — who supervises, when does a matter go up to the supervising attorney?
- **Government:** adapt — approval chain inside the agency/office.

Record this on a `**Practice setting:**` line in `## Company profile`.

#### Write to the config

Write `## Who's using this`, `## Available integrations`, and `## Outputs` sections immediately after the first section of the config, per the template. These drive work-product header choice and feature-fallback behavior across every skill in this plugin.

---

### Part 0.5: Module selection (1–2 min)

Ask which of the following apply. More than one is common. All four is not unusual for a GC.

> Which of these are part of your regular work? (This determines which sections get built in your practice profile and which skills light up — picking only M&A skips the board, public company, and entity management interviews entirely.)
>
> 1. **M&A** — deals: buying, selling, investing, or divesting business units
> 2. **Board & Secretary** — board meeting prep, minutes, resolutions, committee management
> 3. **Public Company** — SEC reporting, disclosure committee, §16 filings, insider trading
> 4. **Entity Management** — subsidiary management, registered agents, cap table, annual filings
>
> Tell me the numbers that apply. You can always add a module later with `/corporate-legal:cold-start-interview --module [name]`.

Record active modules. Proceed to the section for each active module only. Skip the rest entirely.

---

### Part 1: Company profile (2 min, always)

These questions apply regardless of which modules are active.

> Before I ask the structured questions: do you have a delegation-of-authority policy, a board-approved authority matrix, or a prior corporate-governance memo I can read? Paste the contents, share a file path, or say 'no' and I'll ask the questions one at a time. If you share one, I'll extract the approval levels and escalation points rather than making you re-type them.

If the user uploads: read it, extract company identity, legal-team size, and escalation/authority structure, confirm what you found, and skip the corresponding detailed questions.

If not:

> **What does [your company] do?** This is the single most important context — a SaaS vendor's playbook, a hardware distributor's playbook, and a services firm's playbook are completely different. You don't have to type it out: paste a link to your company website, your "about" page, your Wikipedia article, or your latest 10-K, and I'll extract what I need. Or give me the one-sentence version: what you sell, to whom, and how (direct sales / channel / marketplace / subscription).

- What's the company name (or the name you want to use in outputs)?
- What industry are you in?
- Private, public, or a subsidiary of a public company?
- Primary jurisdiction of incorporation?
- How big is the legal team — just you, or a team?
- "When a review finds something that needs someone more senior to sign off — a novel issue in diligence, a materiality threshold decision, a consent matter with director conflicts, a schedule item that needs judgment, or a decision that's above your authority — who does that go to? Give me a name or a role (the GC, your partner, the deal lead), or say 'I decide myself.' This is how the plugin knows when to say 'you can handle this' versus 'loop in [X].' (This feeds /diligence-issue-extraction, /material-contract-schedule, /written-consent, and every other skill's escalation routing.)"

**If the user didn't upload a delegation of authority:** at the end of this section, offer: "Want me to write your escalation and authority lines up as a standalone delegation-of-authority note you can share and maintain? Same content I just captured, in a format you can circulate."

Write to `## Company profile` in the config.

---

### Part 2M: M&A module (4–6 min, if active)

#### 2M-a: Deal posture

- Buy-side, sell-side, or both? Note: most companies have experienced both over time, so this sets the default for house setup — the per-deal flag (`--new-deal`) captures the actual side for any live deal.
- Serial acquirer with a standard playbook, or does each deal get designed from scratch?
- Who runs deals on your end — corp dev, legal, outside counsel as lead, or a mix?

#### 2M-b: Diligence structure

> Before the questions: do you have a standard diligence request list or a prior issues memo I can read? Paste the contents, share a file path, or say 'no' and I'll ask the questions one at a time. If you share them, I'll extract the category structure, materiality thresholds, and house format and skip the corresponding questions.

If not:

- Do you have a standard diligence request list? How is it organized — by function (legal/finance/HR) or by document type?
- What's your materiality threshold for contract review? (All contracts? Above $X? Top N by revenue?) (This feeds /diligence-issue-extraction and /material-contract-schedule — the threshold decides which contracts get full review and which get triaged.)
- What's your usual VDR — Intralinks, Datasite, Box, SharePoint, something else?
- Do you use AI-assisted review tools — Luminance, Kira, anything else? For what specifically?

**If the user didn't upload a request list or prior issues memo:** at the end of this module, offer: "Want me to draft a starter diligence request list and issues-memo skeleton in your format? I'll base them on what you told me about materiality and category structure. You can edit and reuse on the next deal."

#### 2M-c: Issues memo format

> Two things I need:
>
> 1. Your standard diligence request list — the one you use on the buy side, or expect to see on the sell side.
> 2. One prior deal's issues memo — a closed deal, nothing live. I want to see how you structure findings: what you call things, how you categorize issues, what severity scheme you use, what depth you write at.
>
> These two documents become the backbone. Your categories, your format, your standards — not a generic template. (These feed /diligence-issue-extraction — the skill reuses your section structure, severity scheme, and finding template on every future deal.)

From the request list, extract: category structure, materiality thresholds if stated, standard carve-outs.
From the issues memo, extract: section structure, severity scheme, finding format, depth, who it's addressed to.

#### 2M-d: Sell-side specifics (if sell-side is active)

If the attorney works sell-side at all, ask these additional questions:

- When you're preparing a data room, who decides what goes in?
- Do you prepare a disclosure memo or issues log anticipating what the buyer will flag?
- Who do you coordinate with on the business side for data room population — corp dev, CFO, functional heads?

Sell-side is about anticipating the buyer's findings and managing information flow outward, not reviewing inbound documents. This shapes how the diligence-issue-extraction skill behaves when sell-side context is set.

#### 2M-e: Closing checklist and deal team briefing

- Where does the closing checklist live — Excel, Smartsheet, a deal management tool?
- Who owns updates to it?
- How do you brief the deal team — daily, weekly, milestone-based? Email, Slack, call?
- What does the business side actually read versus what's for the file?

Write to `## M&A` in the config.

---

### Part 2B: Board & Secretary module (3–4 min, if active)

- What's your formal role — corporate secretary, assistant secretary, or do you act in an advisory capacity without the formal title?
- How big is the board, and what's the composition — mostly independent directors, insider-heavy, classified board?
- Which committees exist? (Audit, Compensation, Nom/Gov, Strategy, anything else?)
- What tool do you use for board materials — Boardvantage, Diligent, BoardEffect, just email, nothing formal?
- How many regular board meetings per year, and roughly what months?

**Minutes:**
- Long-form narrative minutes, action minutes, or something in between?
- How quickly do you turn minutes around after a meeting?
- How do they get approved — circulated for written comments, or ratified at the next meeting?

**Written consents:**
- Do you routinely use written consents in lieu of meetings? For what types of board or committee action — routine officer appointments, equity grants, annual actions, or more broadly?
- Any limits on what can be approved by consent versus requiring a meeting (charter restrictions, committee charters, or just practice)?

**Seed minutes (required for board-minutes skill):**

> Upload 5–6 prior board or committee minutes. Closed meetings only, nothing currently active. These teach the skill your house format — how minutes are structured, what level of discussion detail you capture, how resolutions are worded, how attendance is recorded. One full-board set and one committee set if you have both formats. (This feeds the board-minutes skill — every future minutes draft is built from your extracted structure, discussion depth, and resolution language.)
>
> If you don't have shareable minutes right now, you can add them later with `/corporate-legal:cold-start-interview --module board`. The board-minutes skill will prompt you for them if they're missing.

From the seed minutes, extract:
- Overall structure and section order
- Header format (company name, meeting type, date, location)
- Attendance recording format (directors present/absent, management, guests)
- Discussion depth — long-form narrative, action minutes, or hybrid
- Resolution language (exact phrasing: "RESOLVED, THAT" / "BE IT RESOLVED" / other)
- Exhibit referencing convention
- Signature block format
- Any standard recitals or boilerplate that appears in every set

Write extracted format as a `**Minutes template:**` block in `## Board & Secretary` in the config.

**Consents repository (required for written-consent skill):**

> Do you have a folder or repository where executed written consents are stored? (This feeds /written-consent — the skill searches the repository for the closest prior consent and uses it as the substantive starting point, not just for format but for specific resolution language already approved for that type of action.)
>
> If you have one: tell me where it lives (folder path, Google Drive folder, SharePoint library, Box folder). The skill will search it at runtime.
>
> If you don't have a centralized repository: upload 3–5 prior consents now for format learning. The skill will still work — it just won't have precedent search capability until a repository is set up.

From the repository or seed consents, extract:
- House resolution language (exact phrasing: "RESOLVED, THAT" / "BE IT RESOLVED" / other)
- Recital structure (WHEREAS / NOW, THEREFORE depth and style)
- Authorisation language (officer delegation language at the end)
- Counterparts and electronic signature language (if present)
- Signature block format

Write to `## Board & Secretary` → `**Consents repository:**` and `**Consent format:**` in the config.

**Annual governance cycle:**
- What annual items do you manage? (Director elections, auditor ratification, equity plan approvals, say-on-pay if public, annual board self-assessment — whatever applies to you.)

Write to `## Board & Secretary` in the config.

---

### Part 2P: Public Company module (3–4 min, if active)

- What exchange are you on — NYSE, Nasdaq, other?
- What's your fiscal year end?
- What's your filer status — large accelerated, accelerated, or non-accelerated?

**Disclosure committee:**
- Do you have a formal disclosure committee? Who's on it — CFO, CAO, IR, Legal, others?
- How often does it meet — quarterly pre-earnings, or as needed?

**§16 reporting:**
- Who tracks §16 filer transactions — you, outside counsel, IR, or a combination?
- What's your internal target for getting Form 4 filed? (SEC requires 2 business days; internal targets are often tighter.)
- Does your insider trading policy require pre-clearance? Who approves?

**Insider trading policy:**
- When are your trading windows open relative to earnings?
- Who is covered by pre-clearance requirements — all officers and directors, or a broader list?
- What's the process for a blackout exception if one is ever needed?

**Earnings call:**
- What's legal's role in earnings call prep — reviewing scripts, preparing Q&A, something else, or no direct role?
- How far in advance of the call are you typically involved?

Write to `## Public Company` in the config.

---

### Part 2E: Entity Management module (2–3 min, if active)

> If you have an org chart or entity list — even a rough one, even a spreadsheet — upload it now. I'll read it and extract the entity structure, jurisdictions, ownership percentages, and entity types. That's faster and more accurate than answering these questions from memory. (This feeds /entity-compliance — the skill initializes the compliance calendar from this list and surfaces annual-report and registered-agent deadlines.)
>
> If you don't have one handy, answer the questions below and I'll build a starter entity table from your answers.

**From uploaded org chart or entity list, extract:**
- Entity names and entity types (Corp, LLC, Ltd, branch, etc.)
- Jurisdiction of formation for each
- Ownership chain and percentages
- Any entities flagged as dormant or inactive

**If no upload, ask:**

- How many active legal entities are you managing, roughly?
- What are the key jurisdictions — just Delaware, or a meaningful multi-jurisdiction footprint?
- Who's your registered agent — CT Corp, National Registered Agents, in-house, or varies by jurisdiction?
- Do you use an entity management system — Athena, Kira, Blueprint — or are you working off a spreadsheet?
- What's your cap table situation — Carta, Shareworks, Ledgr, or still manual? (Or not applicable if wholly owned with no external equity.)
- Who owns routine filing work — annual reports, foreign qualifications, registered agent renewals? Legal, legal ops, or does the registered agent handle it automatically?
- Do your subsidiaries have their own governance cadence, or are they effectively dormant holding companies?
- Do you have intercompany agreements in place — services agreements, IP licenses, loans?

Write to `## Entity Management` in the config.

---

### After writing

**Show what this plugin can do.** Before closing, offer:

> **Want to see what I can help with?**

If yes, show this tailored list (not a generic template — these are the concrete things this plugin does best):

> **Here's what I'm good at in corporate and M&A practice:**
>
> - **Extract diligence issues from the VDR** — e.g., "Point at a VDR folder and get findings categorized per your house materiality thresholds." Try: `/corporate-legal:diligence-issue-extraction`
> - **Build the material contracts schedule** — e.g., "From diligence findings, build the disclosure schedule in the purchase agreement's format." Try: `/corporate-legal:material-contract-schedule`
> - **Draft a board or committee written consent** — e.g., "Precedent search from your consents repository, then drafted in house format." Try: `/corporate-legal:written-consent`
> - **Entity compliance tracker** — e.g., "See what filings are due in the next 30 / 60 / 90 days across your subsidiaries." Try: `/corporate-legal:entity-compliance`
> - **Closing checklist status** — e.g., "What's left to close — conditions, documents, consents, filings — with critical path." Try: `/corporate-legal:closing-checklist`
> - **Post-closing integration** — e.g., "Phased workplan, consent tracking, contract assignment at scale for a just-closed deal." Try: `/corporate-legal:integration-management`
>
> **My suggestion for your first one:** If you have an active deal, run `/corporate-legal:closing-checklist` — it shows immediately where the plugin fits in your workflow. Or tell me what's on your plate and I'll pick.

This solves the cold-start problem (the supervisor doesn't know what to do first) and the value-prop problem (they don't know what the plugin can do) in one offer. Make the list specific. Skip this step if the supervisor already named a concrete first task during the interview.


**Research connector prompt.** Before showing the active modules, say:

> "Before your first diligence extraction or consent: connect a research tool. Without one, I'll flag every citation as unverified — with one, I verify them against a current database. In Cowork: Settings → Connectors. In Claude Code: authorize when a skill prompts you."

Then show the active modules and the populated sections:

> Here's what I've captured: [list active modules]. Practice Profile is written. A few things to check:
> - [Flag any thin or ambiguous answers worth revisiting]
> - [If M&A active and no seed docs provided: "Ping me with your request list and a prior issues memo when you have them — I'll update the diligence structure and memo format sections."]
> - [If M&A active: "When a deal comes in, run `/corporate-legal:cold-start-interview --new-deal` to set up deal-specific context on top of the house approach. M&A skills available now: diligence extraction, deal team summaries, material contracts schedule, closing checklist, and post-closing integration."]
> - [If Board & Secretary active: "Board skills available now: `/corporate-legal:written-consent` for written consents, and the board-minutes skill for drafting minutes in your house format."]
> - [If Entity Management active: "Entity skill available now: `/corporate-legal:entity-compliance` initializes a compliance tracker from your entity list and surfaces what's due."]
> - [If Public Company active: "Public Company skills are coming in a future release — the practice profile section is ready to populate when they ship."]

Close with a note on changeability:

> "Your practice profile is at `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md` — it's a plain text file you can read and edit directly. Anything you answered can be changed:
>
> - Edit the file directly for a quick change (a new threshold, a jurisdiction added, a committee renamed)
> - Run `/corporate-legal:cold-start-interview --redo` for a full re-interview
> - Run `/corporate-legal:cold-start-interview --module [m&a | board | public | entities]` to add or refresh one module
> - Run `/corporate-legal:cold-start-interview --check-integrations` to re-check what's connected
>
> The sections most often adjusted after first setup are the M&A materiality thresholds, the disclosure schedule format / issues memo template, and the entity tracker cadence."

## Your practice profile learns

After writing the practice profile, close with this note:

> **Your practice profile learns.** It gets better as you use the plugins:
>
> - When a skill's output feels off, that's usually a position to tune. The output will tell you which one.
> - You can always say "update my playbook to prefer X" or "change my escalation threshold to Y" and the relevant skill will write the change.
> - Run `/corporate-legal:cold-start-interview --redo <section>` to re-interview one part, or edit the config file directly.
>
> Ten minutes of setup gets you a working profile. A month of use gets you one that reads like you wrote it yourself.

---

## Per-deal setup (`--new-deal`, M&A module only)

When a live deal starts, run a lighter interview focused only on deal-specific context. House approach stays from the plugin config.

Ask:
- Deal code name
- Side for this deal (buy-side or sell-side — may differ from the house default)
- Target or acquirer name
- VDR location (folder path or URL)
- Deal lead name
- Signing date and close date (if known)
- Any deal-specific threshold differences (a $50M deal may review smaller contracts than a $1B deal)
- Outside counsel firm and lead contact for this deal

Write to `~/.claude/plugins/config/claude-for-legal/corporate-legal/deals/[code-name]/deal-context.md`. Skills read both the plugin config (house) and `deal-context.md` (this deal), with deal-context.md taking precedence on conflicts.

---

## Practice Profile quality check

Before finishing, re-read what was written. Flag:
- Any section still showing a placeholder because the answer was skipped or vague — ask again
- Any active module where no seed document was provided — note it and ask the user to provide one when available
- The `*Active modules:*` line at the top of the plugin config — update it to list exactly which modules are on

---

## Failure modes

- **Don't assume all modules are active.** Ask first, interview only for what's live. A deal-only attorney doesn't need public company governance setup.
- **Don't hard-code buy-side.** The practice profile captures the house tendency; the per-deal flag handles the actual side. Write the house practice profile to be side-agnostic; posture is set per deal at `--new-deal`.
- **Don't write generic placeholders.** If the answer was vague ("standard materiality thresholds"), ask what that means in numbers. The practice profile is only useful if thresholds are actual thresholds.
- **Sell-side posture is not buy-side reversed.** On sell-side you're anticipating the buyer's findings and managing outward information flow, not reviewing inbound documents. Flag this distinction if sell-side is active.
- **Don't request seed documents for inactive modules.** Only ask for the request list and issues memo if M&A is active. A board-only attorney doesn't need to provide diligence documents.
