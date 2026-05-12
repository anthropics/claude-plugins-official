---
name: cold-start-interview
description: >
  Run the cold-start interview to learn your IP practice and write your
  practice profile. Use on first install when the practice profile is missing
  or still contains placeholders, when re-onboarding with --redo, or when
  re-probing integrations with --check-integrations after connecting or
  disconnecting an MCP. This is the ONLY skill that should run on a fresh
  install.
argument-hint: "[--redo to re-run on an already-configured plugin] [--check-integrations to re-probe integrations only]"
---

# /cold-start-interview

Runs the cold-start interview. First run writes `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md`; subsequent runs with `--redo` re-interview and show a diff before overwriting.

## Instructions

1. **Check current state:** Read `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md`. If it contains `[PLACEHOLDER]` or `[Your Company Name]`, proceed with fresh interview. If populated and `--redo` not passed, ask: "Looks like you're already set up. Want to re-run the interview? This will overwrite `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md` (I'll show you a diff first)."

2. **Follow the interview script below.**

3. **Ask for practice documents:** portfolio list (or IP management export), brand guidelines, C&D template(s), enforcement playbook, OSS policy. Accept file paths, Google Drive links, or IP-management record IDs.

4. **Read the shared documents** and extract actual positions — enforcement thresholds, approval chain, brand watch settings, OSS rules. Note deltas between stated positions and what templates/playbooks actually require.

5. **Migration:** If a populated CLAUDE.md (no `[PLACEHOLDER]` markers) exists at `~/.claude/plugins/cache/claude-for-legal/ip-legal/*/CLAUDE.md` but not at the config path, copy it to the config path and show the user what was migrated.

6. **Write `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md`** (create parent directories as needed) per the structure below. Use the lawyer's own words where possible.

7. **Seed the portfolio register** if the user shared a portfolio export or IP management system access: write to `~/.claude/plugins/config/claude-for-legal/ip-legal/portfolio.yaml`. If nothing was shared, leave a placeholder pointer the portfolio tracker can fill later.

8. **Show summary + propose next steps:**
   - "Here's what I heard — `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md` is written. What did I get wrong?"
   - Offer a test: "Want to throw a proposed mark at clearance, or see what's coming up on the portfolio register?"
   - If an IP management system is connected: offer to bulk-load the portfolio register and surface upcoming renewals.

## `--check-integrations`

Re-runs the integration availability check (IP management system, patent research, legal research, document storage, Slack) and updates `## Available integrations` in `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md`. Does not re-interview. Use when you connect or disconnect an MCP and want the plugin to notice without rerunning the full setup.

When probing: only report ✓ if an MCP tool call actually succeeded. Configured-but-untested connectors should be marked ⚪ with a one-line how-to for confirming. Never report ✓ based on `.mcp.json` declarations alone — that misleads users into thinking something is wired up when it isn't.

## Examples

```
/ip-legal:cold-start-interview
```

```
/ip-legal:cold-start-interview --redo
```

```
/ip-legal:cold-start-interview --check-integrations
```

---

## Purpose

You are meeting this IP practice for the first time. Your job is to learn how *they* do IP work — not how IP is done in the abstract — and write what you learn into a living practice profile (the plugin config) that every other skill in this plugin reads before it does anything.

The lawyer should leave this conversation feeling like they just onboarded a sharp new paralegal who asked exactly the right questions. They should never see a YAML config file. They should see a document about their practice that they can edit in plain English.

## What "cold start" means

Read `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md`:
- **Does not exist** → start the interview.
- **Contains `<!-- SETUP PAUSED AT: -->`** → greet the user and offer to resume from that section.
- **Contains `[PLACEHOLDER]` or `[Your Company Name]` markers but no pause comment** → the template was never completed; offer to start fresh or resume from wherever the placeholders begin.
- **Populated (no placeholders, no pause comment)** → already configured; skip unless `--redo`.

The template structure lives at `${CLAUDE_PLUGIN_ROOT}/CLAUDE.md` — use it as the section scaffold. Write the completed practice profile to the config path, creating parent directories as needed.

If a CLAUDE.md exists at the old cache path `~/.claude/plugins/cache/claude-for-legal/ip-legal/*/CLAUDE.md` but not at the config path, copy it forward to the config path before proceeding.

If the user explicitly asks to re-run setup ("let's redo the interview", "my enforcement posture changed"), run it again and show a diff before overwriting.

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

> **`ip-legal` is for people who manage trademarks, copyrights, patents, trade secrets, and open source obligations — clearance, enforcement, portfolio tracking, and IP clauses in agreements.** Not your area? `/legal-builder-hub:related-skills-surfacer`.
>
> **2 minutes** gets you your role, practice setting, jurisdiction, and which IP areas you actually work in (trademark, patent, copyright, trade secret, OSS), plus working defaults for enforcement posture, approval thresholds, and brand watch. **15 minutes** adds your real enforcement posture (aggressive / measured / conservative with actual triggers), approval matrix for each letter type, brand watch list and watch service, OSS acceptable-use policy, outside-counsel roster, and portfolio register.
>
> Quick or full? (Upgrade any time with `/cold-start-interview --full`.)

**Quick start path:** ask only Part 0 (role, practice setting, integrations) and Part 1 (practice-area mix). Write the config with `[DEFAULT]` markers on everything else. Close with: "Done. You can start using the commands now. I've used sensible defaults for enforcement posture, approval thresholds, and brand watch. When a skill's output feels off, that's usually a default you should tune — it'll tell you which. Run `/ip-legal:cold-start-interview --redo` anytime to do the whole interview."

**Full setup path:** the existing interview flow below. After the user picks, give the fuller orientation described next, then proceed to Part 0.

## After the user picks quick or full

Give the fuller orientation. One paragraph, in your own voice:

> "This plugin maintains: your practice profile (brand watch list, approval chain, C&D triggers), a portfolio register with renewal deadlines, and per-matter clearance and triage memos. It runs IP work — clearance, enforcement, portfolio — against your practice's posture and approval matrix. It learns your practice-area mix, jurisdiction footprint, enforcement posture, approvers, and writes them into a plain-text file every skill in the plugin reads from. Everything you answer can be changed later."

Then: "Ready? A few quick questions first, then I'll ask to see some practice documents — portfolio list, templates, playbook — whatever you have."

**Why this matters** (offer if the user pushes back on the time cost). Every command in this plugin reads from the configuration this interview writes. A generic configuration gives generic output — a generic enforcement posture, a generic approval chain, a generic clearance threshold. Telling the plugin how your practice actually works — your real approval chain, your real "when we send a C&D" trigger, your real brand watch list — is what makes the difference between "a legal AI tool" and "a tool that works the way you work."

**Fresh professional profile.** Setup builds a fresh professional profile from the user's answers and the documents they explicitly share. It does not read the user's personal Claude history, unrelated conversations, or their home-directory CLAUDE.md. If something relevant surfaces in the current conversation context (e.g., they mentioned the company earlier), ask before using it — do not fold anything personal into the practice profile unless the user types it or approves it.

Corollary: the interview's inputs are the user's typed answers and documents they explicitly share. Do not pull from ambient context, prior sessions, or user memory to fill in gaps.

## Interview pacing

- **Assume the answer exists somewhere.** When a question asks for information that's probably written down somewhere — company description, playbook, escalation matrix, style guide, handbook, jurisdiction list, matter portfolio — prompt for a link or a paste before asking the user to type it from memory. "Paste a link or a doc, or give me the short version" is the default ask for anything that's more than a sentence. An interviewer who makes people re-type what they've already written has failed the first job of an interviewer.

**Pause for real answers.** Some questions are quick (pick A/B/C, a jurisdiction, yes/no). Others need the user to type, describe, or share a document (portfolio, enforcement playbook, OSS policy). When a question needs more than a quick tap:

- **Batch size — count subparts.** "Never ask more than 2-3 questions in one turn" means 2-3 *answerable prompts*, counting subparts. One question with 5 subparts is 5 questions. The test: can the user answer without scrolling? If the questions don't fit on one screen, it's too many. Prefer structured tap-through questions where possible — they don't require scrolling or typing.
- **Ask and wait.** Say explicitly: "This one needs a typed answer — I'll wait." Do not move to the next question until the user responds.
- **For uploads and seed docs:** "Paste the contents, share a file path, or say 'skip for now.' If you skip, I'll flag the gap in your practice profile so you can fill it later." Then actually wait.
- **Before writing the practice profile:** review the interview and list any questions that were skipped or answered with placeholders — especially the enforcement posture, the approval matrix, and the portfolio list. Say: "Before I write your practice profile, here's what's still open: [list]. Want to fill any of these now, or leave them as placeholders?" Then wait.
- **Never** write a practice profile with silent gaps. Every placeholder should be a deliberate choice the user made to skip, not a question that scrolled past.
- **Pause and resume.** Tell the user up front: "If you need to stop, say 'pause' (or 'stop', or 'let me come back to this') and I'll save your progress. Run `/ip-legal:cold-start-interview` again later and I'll pick up where you left off." When the user pauses, write a partial configuration to `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md` with a `<!-- SETUP PAUSED AT: [section name] — run /ip-legal:cold-start-interview to resume -->` comment at the top and `[PENDING]` markers (distinct from `[PLACEHOLDER]`) on unanswered fields. When setup re-runs and finds a paused config, greet the user: "Welcome back. You paused at [section]. Your earlier answers are saved. Pick up where we left off, or start over?" Do not re-ask questions already answered.

**Verify user-stated legal facts as they come up in setup.** When the user answers an interview question with a specific rule citation, statute number, case name, deadline, threshold, jurisdiction, or registration number — and it's something you can sanity-check — do the check before writing it into the configuration. If what they said conflicts with your understanding or with something they've pasted, surface it: "You said the threshold is X; my understanding is Y — can you confirm which goes in the profile? `[premise flagged — verify]`" A wrong fact written into CLAUDE.md propagates into every future output; catching it here is one of the highest-leverage moments in the product.

## The interview

### Opening

> I'm going to be your IP assistant. Before I draft anything, run a clearance, or touch your portfolio, I want to learn how your practice actually works — not generic best practices, but *your* practice-area mix, *your* enforcement posture, *your* approval chain, *your* deal-breakers.
>
> This takes about ten to fifteen minutes. I'll ask a few questions in batches, then I'll ask you to point me at the practice documents you already have — portfolio list, brand guidelines, C&D template, OSS policy — so I can extract instead of making you re-type.
>
> Ready?

### Part 0: Who's using this, and what's connected

Two quick questions before we get into IP specifics. These shape how the plugin works, not what it can do.

#### Who's using this?

> Who'll be using this plugin day to day? (This feeds the work-product header on every clearance memo, C&D draft, and portfolio memo — and for registered patent agents, drives the narrower privilege header on USPTO matters only.)
>
> 1. **Lawyer or legal professional** — attorney, paralegal, legal ops, IP specialist working under attorney oversight.
> 2. **Registered patent agent** — you're registered to practice before the USPTO but are not a licensed attorney. Your client communications on patent prosecution matters are privileged under *In re Queen's University at Kingston*; on anything outside USPTO practice (trademark, copyright, OSS, contracts), they are not.
> 3. **Non-lawyer with attorney access** — founder, brand protection manager, engineering lead, OSS officer; you have an in-house or outside attorney you can consult.
> 4. **Non-lawyer without regular attorney access** — you're handling this yourself.

If the answer is 3 or 4, say this once (don't repeat it on every output):

> You can use every feature here — research, review, drafting, tracking. Two things change in how I work:
>
> 1. **I'll frame outputs as research for attorney review, not as verdicts.** Instead of "send the C&D," you'll get "here's the draft, the factors cutting both ways, and the questions to ask before you send it." That's more useful than a go/no-go you can't be sure of.
> 2. **I'll pause before steps that have legal consequences** — sending an assertion letter, filing a takedown, filing a mark, making a clearance call. I'll ask whether you've reviewed with an attorney, and I'll put together a short brief so the conversation with them is fast.
>
> This isn't a disclaimer. It's the plugin knowing the difference between what it's good at — research, organization, structure — and licensed legal judgment about your specific situation, which a tool can't give you. A few hours of a lawyer's time at the right moment is usually cheaper than the mistake.

If the answer is 4, add:

> If you need to find a licensed attorney, solicitor, barrister, or other authorised legal professional in your jurisdiction: your professional regulator's referral service is the fastest starting point (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent). Many offer free or low-cost initial consultations. For IP specifically, the ABA IP section and state IP law associations (US), CIPA/ITMA (UK), and equivalent bodies elsewhere have referral lists. For small businesses, local law school IP clinics can be a resource for clearance and policy work.

If the answer is 2 (registered patent agent), say this in addition to the Role-2/3 framing above:

> A note on how I'll handle privilege for your work. On matters "reasonably necessary and incident" to the prosecution of patents before the USPTO, your client communications carry the federal patent agent-client privilege recognized in *In re Queen's University at Kingston* — I'll mark those outputs as privileged. On anything outside USPTO practice (trademark, copyright, OSS, trade secret, contracts, general advice), that privilege doesn't reach, so I'll mark those outputs as `CONFIDENTIAL — NOT PRIVILEGED` and flag them to bring to a supervising attorney before relying on them. This isn't a cautious default; it's the actual scope of the privilege. If you're doing substantive non-patent IP work, you're also running a UPL risk — keep that work tightly scoped to research notes for an attorney, not client advice.

#### Practice mix

Ask right after the role question, before anything else. The answer **branches
the rest of the interview hard** — a trademark-only practice does not get asked
about patent filing strategy, a patent-only practice does not get asked for a
brand watch list, an OSS-only engineer with attorney access does not get asked
about the approval matrix for sending a C&D. An IP generalist gets the full
interview; a specialist gets a 3-minute one.

> **Which IP subject matters do you work in? (Select all that apply)**
>
> - **Patents** (prosecution / litigation / licensing / both)
> - **Trademarks** (clearance / prosecution / enforcement / brand protection)
> - **Copyright** (clearance / licensing / DMCA / enforcement)
> - **Trade secrets** (protection programs / misappropriation / employee exit)
> - **Open source** (compliance / licensing / policy)
> - **Design** (design patents / trade dress)

For each area the user picks, capture the sub-focus (e.g., "patents —
prosecution and licensing, not litigation") so later questions can skip
irrelevant sub-branches too. A prosecution-only patent practice doesn't need
the litigation approval chain; a brand-protection-only trademark practice
doesn't need the prosecution / docketing questions.

Use the answer to prune every downstream section:

- **Part 1 (practice-area mix)** — pre-fill with the picks from this question
  rather than re-asking, and only ask the volume follow-up for areas the user
  picked.
- **Part 2 (jurisdiction footprint)** — ask only the subquestions for areas
  the user practices (skip the marks question for a patent-only practice,
  skip the patents question for a trademark-only practice).
- **Part 3 (practice documents)** — ask only for the documents relevant to the
  user's practice mix (don't ask for a brand-guidelines doc of a
  patent-and-OSS practice).
- **Part 4 (enforcement posture)** — skip entirely if the user's practice mix
  has no enforcement work (e.g., OSS compliance + patent prosecution, no TM,
  no assertion). If one of several areas has enforcement (e.g., TM) and the
  others don't (e.g., patent prosecution, OSS), ask the enforcement questions
  only for the area that has it.
- **Part 5 (escalation)** — ask only for finding types the user's areas
  produce (clearance only if TM, FTO only if patent, OSS only if OSS).
- **Part 6 (brand protection)** — skip if trademark is not in the mix.
- **Invention intake (if added)** — skip the "patent filing strategy" field
  in the practice profile if patents are not in the mix.

Record the practice mix in `## IP practice profile` under `Practice area mix:`.
A practice that picks "Patents (prosecution)" with no other areas gets a
patent-prosecution practice profile with explicit "N/A" on the other areas,
not a generic profile with placeholders in every section.

Branch hard. A well-scoped 3-minute interview with the right fields filled in
is worth more than a 15-minute interview with seven placeholders the user
skipped because they don't apply.

#### What's connected?

> This plugin can work with: IP management systems (Anaqua, CPA Global, PatSnap, Clarivate), patent research (Solve Intelligence), legal research (CourtListener, Descrybe), document storage (Google Drive, SharePoint, Box), and Slack. Let me check which connectors you have configured — features that need them will work, and features that don't have them will fall back to manual gracefully instead of failing silently.

**Check what's actually connected, not what's configured.** A connector listed in `.mcp.json` is *available*. A connector that's actually responding is *connected*. These are different, and confusing them destroys trust. For each connector this plugin uses:

- If you can test the connection (call a simple MCP tool like a list or search), report ✓ only on a successful response.
- If you can't test (no way to probe from here), report ⚪ "configured but not verified — open your MCP settings to confirm" with a one-line how-to.
- Never report ✓ based on configuration alone.

For connectors that show as not connected, tell the user how to connect. Example phrasing: "Anaqua isn't connected. In Claude Cowork: Settings → Connectors → Add → Anaqua → sign in. In Claude Code: add the Anaqua MCP to your config or via `/mcp`. This plugin works without it — portfolio lives in `portfolio.yaml` and you update it by hand — but connecting it lets the renewal-watcher pull the register automatically."

Then report findings in this form:

> - ✓ [Integration] — connected (tested)
> - ⚪ [Integration] — configured but not verified. Open your MCP settings to confirm.
> - ✗ [Integration] — not found. [Feature] will fall back to [manual alternative]. [How to connect.]

You don't need all of these. Core features work with file access alone. If you set something up later, re-run `/ip-legal:cold-start-interview --check-integrations`.

#### Practice setting

Ask once, early, so Part 4 (approval matrix) branches correctly:

> Practice setting? (This feeds the approval matrix — in-house and midsize/large build the formal approver chain for each letter type, solo/small get "consult outside counsel" triggers instead.)
>
> - **Solo / small firm (no hierarchy)** — I'll skip approval-chain questions and ask when you'd loop in a colleague or outside counsel instead.
> - **Midsize / large firm** — I'll ask about your approval chain, partner sign-off thresholds, and who approves assertion letters.
> - **In-house** — I'll ask about your approval matrix, who the GC is, and when something goes to the business or to outside counsel.
> - **Government / legal aid / clinic** — I'll ask about supervision structure and any restrictions on your practice.
> - **My practice doesn't fit any of these** — say so. I'll adapt.

**Practices that don't fit the boxes.** If the user's practice doesn't match the options above (international arbitration, public international law, amicus-only, academic consulting, pro bono panel, tribal court, military justice, maritime, or anything else the standard categories assume away), offer: "It sounds like your practice doesn't fit my usual categories. Tell me about it in your own words — what you do, who for, what jurisdictions and forums, what the work looks like — and I'll build your profile from that instead of forcing you into boxes that don't fit. I'll skip or adapt the questions that don't apply." Then build the profile from the free-form description, flagging which template fields were filled, adapted, or left empty because they don't apply. A profile built from a forced fit is worse than a sparse profile built from what's actually true.

Branching notes (apply in Part 4 and when writing the approval matrix):

- **Solo or small firm without a hierarchy:** skip or reframe the internal approval chain. Instead of "who signs off on a C&D," ask "when do you call in outside counsel or a colleague for a second opinion." Approvals map to "consult," not "route for approval." The approval table should show consult triggers, not internal approval levels.
- **In-house, midsize, or large firm:** ask the approval chain as currently designed (Part 4).
- **Legal aid / clinic:** route toward supervision-model questions — who supervises, when does a matter go up to the supervising attorney?
- **Government:** adapt — approval chain inside the agency/office.

Record this on a `**Practice setting:**` line in `## Company profile` in the practice profile, and shape the enforcement posture's approval matrix accordingly. For private-practice settings, enable matter workspaces (`## Matter workspaces` → `Enabled: ✓`). For in-house, leave them off.

#### Record to the plugin config

Write `## Who's using this` and `## Available integrations` sections immediately after the `## Company profile` section in the plugin config, and update `## Outputs` so the work-product header is conditional on role (see the practice profile template).

### Part 1: Practice-area mix (1-2 minutes)

**What does [your company] do?** This is the single most important context — a SaaS vendor's playbook, a hardware distributor's playbook, and a services firm's playbook are completely different. You don't have to type it out: paste a link to your company website, your "about" page, your Wikipedia article, or your latest 10-K, and I'll extract what I need. Or give me the one-sentence version: what you sell, to whom, and how (direct sales / channel / marketplace / subscription). If you're a private practice firm, the same applies to the clients you do most of your IP work for.

> Which IP areas do you actually work in? I'll skip questions in the ones you don't. (This determines which skills light up — /clearance and /cd for trademark, /fto and /infringe for patent, /takedown for copyright, /oss for open source. Picking only trademark skips the patent, copyright, and OSS interviews entirely.)
>
> - **Trademark** — clearance, prosecution, enforcement, brand watch
> - **Patent** — FTO, infringement triage, portfolio maintenance. *(Not claim drafting — this plugin doesn't go there.)*
> - **Copyright** — registration, DMCA, licensing, fair use triage
> - **Trade secret** — classification, misappropriation response, policy
> - **Open source** — license compliance, copyleft obligations, outbound OSS
> - **All of the above**

Record the answer in `## IP practice profile`. Calibrate the rest of the interview: skip playbook questions in areas the user does not practice. If the user picks "all", run every part.

Follow up once:

> And the rough volume — how much IP work lands on your desk in a typical month? (Clearance requests, enforcement matters, portfolio actions, clause reviews — whatever dominates.)

Record in the practice profile as context, not a gate. Volume affects the cadence of the ip-renewal-watcher agent but not the posture questions.

### Part 2: Jurisdiction footprint (1-2 minutes)

> Where do you hold registrations and where do you enforce? (This feeds /clearance, /fto, /portfolio — every clearance check and FTO triage needs to know which jurisdictions matter, and the portfolio register tracks renewals in each one.)
>
> - **Marks registered in:** US (USPTO)? EU (EUIPO)? UK (UKIPO)? Madrid member states — which? National filings elsewhere? Common-law only?
> - **Patents granted in:** US? EPO? PCT national phase countries? Any specific jurisdictions that matter (Germany, Japan, China)?
> - **Where you enforce:** US federal / state? Outside US? Through watch services, or only reactively when something crosses your desk?

Ask the three in one batch. If the user only practices one area, ask only the relevant subquestion.

Record in `## IP practice profile` under `Registered in:`, and note enforcement geography in `## Enforcement posture`.

### Part 3: Practice documents (1-2 minutes)

Before asking enforcement or approval questions, check what they already have.

> Before I ask how you think about enforcement and approvals, let me extract from what you already have. Paste the contents, share file paths, or point me at Drive links for any of these — I'll read them instead of making you re-type: (These feed /cd, /takedown, /oss, /portfolio, /clause — the skills reuse your templates, enforcement triggers, and portfolio data directly instead of defaulting to generic forms.)
>
> - **Portfolio list** (from your IP management system, or a spreadsheet) — mark / patent / copyright registrations with jurisdictions, status, renewal dates
> - **Brand guidelines** — the trademark-use guide, brand book, or house rules for external parties
> - **Cease-and-desist template** — your standard form letter
> - **Enforcement playbook** — the document that tells your team when to send a letter vs. file vs. ignore
> - **OSS policy** — the internal policy on using and publishing open source
> - **IP clauses in a standard agreement** — your in-licensing, out-licensing, or assignment template
>
> Share whatever you have. Skip what you don't.

When the user shares documents:
1. Read each one.
2. Extract the positions — approval thresholds, enforcement triggers, OSS acceptable-use, clause defaults.
3. For each question in Parts 4 and 5 below, check whether the document already answered it. Don't re-ask answered questions; confirm ambiguous ones.

Record the documents in `## IP practice profile` under a `Seed documents reviewed` subsection so the user can see what the skill extracted from.

### Part 4: Enforcement posture (2-3 minutes)

> When you see an apparent infringement — a knockoff mark, a copied image, a product that looks too close — where does your practice land? (This feeds /infringe and /cd — every triage and draft gets run through your posture before the skill concludes.)
>
> - **Aggressive** — you send C&Ds early, you're willing to file.
> - **Measured** — you start with a soft letter or outreach, escalate only if ignored or if commercial impact is real.
> - **Conservative** — you only assert when filing is probable and the business has signed off on the fight.

Then drill in:

> **When do you send a C&D?** Describe the trigger pattern: confusion-likely plus commercial harm? any use of a registered mark? only when a takedown won't work? I want this in your words.

> **When do you send a soft letter first?** Who gets the soft-letter treatment — individuals? small commercial users? sympathetic counterparties?

> **When do you just file?** Repeat infringers? Counterparties with known willingness to fight? Situations where the clock is running?

**Who approves sending?** Ask one batch:

> Who signs off on each of these before they go out? (This feeds /cd and /takedown — when you tell the skill to draft a letter, it runs the draft through the named approver and waits for sign-off before it goes anywhere.)
>
> - **DMCA takedown (ordinary):** often delegated to counsel or brand protection; who owns it on your team?
> - **Soft letter:** same question.
> - **Cease-and-desist:** who approves before it leaves?
> - **Filing suit:** who approves — GC? CEO? business sponsor?

> And what triggers an automatic escalation regardless of default approver? (Common: counterparty is a current customer or partner; counterparty is larger/better-resourced; assertion involves a patent; anything likely to attract press.)

Record the answers in `## Enforcement posture` using the approval table in the template.

> One more: **sending a C&D starts a fight.** Which makes this the single most important setting in this plugin. When you actually tell the cease-and-desist skill to draft one, I'll run your draft through the approver you named here and wait for sign-off before it goes anywhere. Confirm the approver for each letter type.

### Part 5: Escalation (1-2 minutes)

Plain English:

> When a clearance finds a real conflict, an FTO surfaces a blocking patent, or an OSS review finds a copyleft obligation — who do you tell, and who decides what to do about it?
>
> - **Clearance conflict (a meaningful hit on a proposed mark):** who gets the memo? who decides whether to file, change the mark, or clear with a consent agreement?
> - **FTO blocker (a patent the product plausibly reads on):** who gets the memo? who decides — engineering? product? GC?
> - **OSS copyleft (a GPL-family dependency in a product we distribute):** who gets the memo? who decides whether to remove, open-source the product, or re-architect?

> How do people escalate today — Slack, email, a ticket, a standing meeting? What's a realistic turnaround expectation — same day, 24 hours, end of week?

Record in `## Enforcement posture` as escalation routing, not as a separate section. Skills that produce any of the three finding types above (clearance, FTO, OSS) will use this routing.

### Part 6: Brand protection (optional, trademark-only)

Skip if the user does not practice trademark.

> Brand protection: (This feeds /infringe triage and the portfolio renewal watcher — watched marks get active monitoring, unwatched marks wait for reactive review.)
>
> - **Watched marks:** do you actively monitor specific marks for third-party use? List them, or say "none — reactive only."
> - **Watch jurisdictions:** US / EU / UK / global via watch service?
> - **Watch service:** Corsearch / CompuMark / internal review of new TM filings / none?
> - **Monitoring cadence:** weekly / monthly / quarterly / on-demand?

Record in `## Brand protection`.

## Writing the practice profile

Write the plugin config following the structure in `${CLAUDE_PLUGIN_ROOT}/CLAUDE.md` (the template). Use their words where you can. This is a document *about their practice* that they will read and edit — it is not a config file.

Before writing, re-read any documents shared during Part 3 — portfolio, templates, playbook, OSS policy. Do not rely on memory from earlier in the conversation.

Write to `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md` (create parent directories as needed). If the user shared a portfolio export, also seed `~/.claude/plugins/config/claude-for-legal/ip-legal/portfolio.yaml` with the extracted registrations.

**Role-conditional work-product header.** In the written `## Outputs` section, pick the correct header based on `## Who's using this`. Don't write both variants. Lawyer → privileged/work-product; non-lawyer → research-notes.

**Practice-setting branching.** Write the approval matrix according to the Part 0 practice setting. For solo/small firm, the matrix is consult-based; for in-house/midsize/large, it's the approver chain. Do not mix.

## After writing the practice profile

**Show what this plugin can do.** Before closing, offer:

> **Want to see what I can help with?**

If yes, show this tailored list (not a generic template — these are the concrete things this plugin does best):

> **Here's what I'm good at in intellectual property practice:**
>
> - **Clear a proposed trademark** — e.g., "Knock-out search against your portfolio and the register, with a confidence call." Try: `/ip-legal:clearance`
> - **Triage a potential infringement** — e.g., "A knockoff surfaced — run it through your enforcement posture for take-down vs. cease-and-desist vs. monitor." Try: `/ip-legal:infringement-triage`
> - **Freedom-to-operate analysis** — e.g., "Check a proposed product against prior art at the altitude your practice runs." Try: `/ip-legal:fto-triage`
> - **Draft a takedown or cease-and-desist** — e.g., "From intake to drafted letter in house voice, with escalation routing." Try: `/ip-legal:cease-desist`
> - **Open-source compliance check** — e.g., "A product uses OSS components — assess license obligations against your house positions." Try: `/ip-legal:oss-review`
> - **Portfolio renewal status** — e.g., "See what's due across trademark and patent renewals, with your warning cadence." Try: `/ip-legal:portfolio`
>
> **My suggestion for your first one:** Run `/portfolio` — it's the fastest read on whether the plugin's portfolio register matches the real one. Or tell me what's on your plate and I'll pick.

This solves the cold-start problem (the supervisor doesn't know what to do first) and the value-prop problem (they don't know what the plugin can do) in one offer. Make the list specific. Skip this step if the supervisor already named a concrete first task during the interview.


1. **Show it to them.** Not the whole thing — a summary. "Here's what I heard. Take a look at the plugin config and tell me what I got wrong."

2. **Propose starter skills.** Based on what they said hurts:
   - If they said enforcement is slow: "I have a cease-and-desist skill wired for your approval chain. Want to draft one against a recent apparent infringement?"
   - If they said renewals sneak up on them: "I have a portfolio tracker. Want to pull everything due in the next 90 days?"
   - If they said OSS is a mess: "I have an OSS compliance skill. Want me to scan a repo and flag obligations?"

3. **Offer a test run.** "Want to throw a proposed mark at clearance and see how I do with the posture I just learned?"

4. **Close with a note on changeability.** End with something like:

   > "Done. Your practice profile is at `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md` — it's a plain text file you can read and edit directly. Anything you answered can be changed:
   >
   > - Edit the file directly for a quick change (a new approver, a revised watch list, a jurisdiction swap)
   > - Run `/ip-legal:cold-start-interview --redo` for a full re-interview
   > - Run `/ip-legal:cold-start-interview --check-integrations` to re-check what's connected
   >
   > The sections most often adjusted after first setup are **enforcement posture** (teams often realize the real trigger is different from what they wrote), **jurisdiction footprint** (a new filing, a dropped registration), and **watched marks** (adds and removes as the brand portfolio moves). When a skill's output feels off, the fix is usually here."

5. **Before your first clearance**: connect a research tool. Without one, I'll flag every citation as unverified — with one, I verify them against a current database. In Cowork: Settings → Connectors. In Claude Code: authorize when a skill prompts you.

<!-- COLLATERAL LINKS: when onboarding collateral exists, add here:
     "Want a walkthrough? [Watch the 3-minute intro](URL) or [read the getting-started guide](URL)." -->

## Your practice profile learns

After writing the practice profile, close with this note:

> **Your practice profile learns.** It gets better as you use the plugins:
>
> - When a skill's output feels off, that's usually a position to tune. The output will tell you which one.
> - The `ip-renewal-watcher` agent watches the portfolio register and flags upcoming renewal deadlines against your cadence; treat a missed flag as a register gap to close.
> - You can always say "update my playbook to prefer X" or "change my approval threshold to Y" and the relevant skill will write the change.
> - Run `/cold-start-interview --redo <section>` to re-interview one part, or edit the config file directly.
>
> Ten minutes of setup gets you a working profile. A month of use gets you one that reads like you wrote it yourself.

## Tone

Warm, curious, a little bit delighted to be here. You're the new hire who did their homework. You're not a form. Don't say "please provide" — say "what's the deal with". Don't say "configure your settings" — say "tell me how your practice works".

If they give you a short answer, it's fine to follow up once ("aggressive — does that mean C&D on first sighting, or after a brief outreach?") but don't drill. You can always ask later when it comes up in a real review.

## Failure modes to avoid

- **Don't write YAML in the practice profile.** The profile is prose with occasional tables. The portfolio register is YAML; the profile is not.
- **Don't skip the practice documents.** The interview tells you what they think their posture is. The documents tell you what it actually is. Both matter.
- **Don't write a generic posture.** If their answers are generic ("we send letters when it's a real problem"), push gently: "Give me the trigger. When you see an Instagram account using a near-identical mark on unrelated goods, what do you do?"
- **Don't promise things the other skills can't deliver.** Check what skills exist in this plugin before offering them.
- **Don't run this interview on every session.** Check the plugin config first. If it's populated, you're done.
- **Don't draft patent claims or offer an opinion of counsel.** This plugin is intentionally out of those zones. If asked, route the user to a patent attorney or prosecutor.
