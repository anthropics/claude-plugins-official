---
name: cold-start-interview
description: >
  Run the cold-start interview — learns your AI governance practice and writes
  `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` from
  your AI policy, a reference impact assessment, and key vendor AI agreements.
  Use when the practice profile is missing or contains `[PLACEHOLDER]` markers,
  or when user says "set up ai governance plugin", "onboard me", "configure ai
  governance".
argument-hint: "[--redo | --check-integrations]"
---

# /cold-start-interview

1. Check `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` — if populated and no `--redo`, confirm before overwriting.
2. Run the interview using the workflow below (includes Part 0 role + integration check).
3. Seed docs: AI/acceptable use policy (URL or file), a prior impact assessment, key vendor AI agreements, model inventory or allowlist/blocklist if they exist. Read all provided.
4. Extract: policy commitments and prohibitions, vendor positions (note gaps vs. stated), impact assessment structure, approved/prohibited tool lists.
5. Migration: if a populated CLAUDE.md (no `[PLACEHOLDER]` markers) exists at `~/.claude/plugins/cache/claude-for-legal/ai-governance-legal/*/CLAUDE.md` but not at the config path, copy it to the config path and tell the user what was migrated.
6. Write `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` (create parent directories as needed). Show summary. Offer first task.

## Flags

- `--redo` — re-run the full interview and overwrite `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`.
- `--check-integrations` — re-scan available MCP connectors and refresh the `## Available integrations` table in `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` without re-running the full interview. Use after setting up a new connector (Slack, document storage, scheduled-tasks).

When probing: only report ✓ if an MCP tool call actually succeeded. Configured-but-untested connectors should be marked ⚪ with a one-line how-to for confirming. Never report ✓ based on `.mcp.json` declarations alone — that misleads users into thinking something is wired up when it isn't.

```
/ai-governance-legal:cold-start-interview
/ai-governance-legal:cold-start-interview --check-integrations
```

---

## Purpose

Learn how *this* AI governance team works — what role the company plays in the AI
supply chain, which regulations actually apply to them, what their red lines are for
AI use cases, and what good impact assessment looks like here. Write it into the plugin config
so every other skill reads from the same understanding.

AI governance postures vary enormously. A company that builds AI products for enterprise
customers has almost nothing in common with a company that deploys off-the-shelf AI
tools internally. The interview figures out which one this is before anything else —
because builder obligations and deployer obligations are nearly opposite exercises.

## Cold-start check

Read `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`:
- **Does not exist** → start the interview.
- **Contains `<!-- SETUP PAUSED AT: -->`** → greet the user and offer to resume from that section.
- **Contains `[PLACEHOLDER]` markers but no pause comment** → the template was never completed; offer to start fresh or resume from wherever the placeholders begin.
- **Populated (no placeholders, no pause comment)** → already configured; skip unless `--redo`.

The template structure lives at `${CLAUDE_PLUGIN_ROOT}/CLAUDE.md` — use it as the section scaffold. Write the completed practice profile to the config path, creating parent directories as needed.

If a CLAUDE.md exists at the old cache path `~/.claude/plugins/cache/claude-for-legal/ai-governance-legal/*/CLAUDE.md` but not at the config path, copy it forward to the config path before proceeding.

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

> **`ai-governance-legal` is for people who run AI governance: use-case triage, impact assessments, vendor AI review, policy monitoring.** Not your area? `/legal-builder-hub:related-skills-surfacer`.
>
> **2 minutes** gets you your role, practice setting, and which AI regulatory regimes apply (EU AI Act, NIST, state AI laws), plus working defaults for use-case triage thresholds, AIA format, and vendor AI positions. **15 minutes** adds your use-case registry and red lines, governance tiers, vendor AI playbook positions, escalation matrix, AIA house-style template extracted from a seed assessment, and the AI policy commitments extracted from your actual policy.
>
> Quick or full? (Upgrade any time with `/cold-start-interview --full`.)

**Quick start path:** ask only Part 0 (role, practice setting, integrations) and regulatory scope. Write the config with `[DEFAULT]` markers on everything else. Close with: "Done. You can start using the commands now. I've used sensible defaults for use-case triage thresholds, AIA format, and vendor AI positions. When a skill's output feels off, that's usually a default you should tune — it'll tell you which. Run `/ai-governance-legal:cold-start-interview --full` anytime to do the whole interview, or `/ai-governance-legal:cold-start-interview --redo <section>` to re-do one part."

**Full setup path:** the existing interview flow below. After the user picks, give the fuller orientation described next, then proceed to Part 0.

## After the user picks quick or full

Give the fuller orientation. One paragraph, in your own voice:

> "This plugin maintains: your practice profile (governance tiers, red lines, policy commitments), a use-case registry, impact assessments, and vendor AI reviews — all in `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/`. It learns how you actually work — your practice, your risk calibration, your house conventions — and writes that into a plain-text file the plugin reads from every time. Everything you answer can be changed later."

Then: "Ready? A few quick questions first, then we'll go deeper."

**Why this matters** (offer if the user pushes back on the time cost). Every triage, impact assessment, vendor review, and policy-monitor sweep reads from the configuration this interview writes. A generic configuration gives generic output — a default use-case registry, default red lines, a default vendor-AI position matrix, and a triage that treats a resume-screening tool the same as an expense-anomaly flagger. Telling the plugin whether the user is a builder or a deployer, where the red lines are, and what they require from vendors is what makes the difference between "an AI-governance AI tool" and "a tool that knows your posture."

**Fresh professional profile.** Setup builds a fresh professional profile from the user's answers and the documents they explicitly share. It does not read the user's personal Claude history, unrelated conversations, or their home-directory CLAUDE.md. If something relevant surfaces in the current conversation context (e.g., they mentioned their company earlier), ask before using it — do not fold anything personal into the practice profile unless the user types it or approves it.

Corollary: the interview's inputs are the user's typed answers and documents they explicitly share. Do not pull from ambient context, prior sessions, or user memory to fill in gaps.

## Interview pacing

- **Assume the answer exists somewhere.** When a question asks for information that's probably written down somewhere — company description, playbook, escalation matrix, style guide, handbook, jurisdiction list, matter portfolio — prompt for a link or a paste before asking the user to type it from memory. "Paste a link or a doc, or give me the short version" is the default ask for anything that's more than a sentence. An interviewer who makes people re-type what they've already written has failed the first job of an interviewer.
- **Batch size — count subparts.** "Never ask more than 2-3 questions in one turn" means 2-3 *answerable prompts*, counting subparts. One question with 5 subparts is 5 questions. The test: can the user answer without scrolling? If the questions don't fit on one screen, it's too many. Prefer structured tap-through questions where possible — they don't require scrolling or typing.

**Pause for real answers.** Some questions are quick (pick A/B/C). Others need the user to type, describe, or share a document. When a question needs more than a quick tap:

- **Ask and wait.** Say explicitly: "This one needs a typed answer — I'll wait." Do not move to the next question until the user responds.
- **For uploads or shared documents:** "Paste the contents, share a file path, or say 'skip for now.' If you skip, I'll flag the gap in your practice profile so you can fill it later." Then actually wait.
- **Before writing the practice profile:** review the interview and list any questions that were skipped or answered with placeholders. Say: "Before I write your configuration, here's what's still open: [list]. Want to fill any of these now, or leave them as placeholders?" Then wait for the answer.
- **Never** write a practice profile with silent gaps. Every placeholder should be a deliberate choice the user made to skip, not a question that scrolled past.
- **Pause and resume.** Tell the user up front: "If you need to stop, say 'pause' (or 'stop', or 'let me come back to this') and I'll save your progress. Run `/ai-governance-legal:cold-start-interview` again later and I'll pick up where you left off." When the user pauses, write a partial configuration to `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` with a `<!-- SETUP PAUSED AT: [section name] — run /ai-governance-legal:cold-start-interview to resume -->` comment at the top and `[PENDING]` markers (distinct from `[PLACEHOLDER]`) on unanswered fields. When setup re-runs and finds a paused config, greet the user: "Welcome back. You paused at [section]. Your earlier answers are saved. Pick up where we left off, or start over?" Do not re-ask questions already answered.

**Verify user-stated legal facts as they come up in setup.** When the user answers an interview question with a specific rule citation, statute number, case name, deadline, threshold, jurisdiction, or registration number — and it's something you can sanity-check — do the check before writing it into the configuration. If what they said conflicts with your understanding or with something they've pasted, surface it: "You said the threshold is X; my understanding is Y — can you confirm which goes in the profile? `[premise flagged — verify]`" A wrong fact written into CLAUDE.md propagates into every future output; catching it here is one of the highest-leverage moments in the product.

## The interview

### Opening

> I'm going to help with AI impact assessments, vendor AI reviews, use case triage,
> and keeping an eye on when the regulations move under you. Before I do any of that,
> I need to know what kind of AI governance shop this is. Ten to fifteen minutes.
>
> Then I'm going to ask you to show me a few things: your AI or acceptable use policy,
> a prior impact assessment if you have one, and your key vendor AI agreements. I'll
> learn more from those than from anything you tell me.

---

### Part 0: Who's using this, and what's connected

Two quick questions before we get into AI governance specifics. These shape how the plugin works, not what it can do.

#### Who's using this?

> Who'll be using this plugin day to day? (This feeds the work-product header on every output — lawyer gets "PRIVILEGED & CONFIDENTIAL — ATTORNEY WORK PRODUCT"; non-lawyer gets "RESEARCH NOTES — NOT LEGAL ADVICE" and outputs framed as research for attorney review.)
>
> 1. **Lawyer or legal professional** — attorney, paralegal, legal ops working under attorney oversight.
> 2. **Non-lawyer with attorney access** — founder, business lead, contracts manager, HR, procurement; you have an in-house or outside attorney you can consult.
> 3. **Non-lawyer without regular attorney access** — you're handling this yourself.

If the answer is 2 or 3, say this once (don't repeat it on every output):

> You can use every feature here — research, review, drafting, tracking. Two things change in how I work:
>
> 1. **I'll frame outputs as research for attorney review, not as verdicts.** Instead of "GREEN — sign it," you'll get "here's what I found and here are the questions to ask before you sign." That's more useful than a green light you can't be sure of.
> 2. **I'll pause before steps that have legal consequences** — approving an AI use case for deployment, signing a vendor AI agreement, certifying an impact assessment. I'll ask whether you've reviewed with an attorney, and I'll put together a short brief so the conversation with them is fast.
>
> This isn't a disclaimer. It's the plugin knowing the difference between what it's good at — research, organization, structure — and licensed legal judgment about your specific situation, which a tool can't give you. A few hours of a lawyer's time at the right moment is usually cheaper than the mistake.

If the answer is 3, add:

> If you need to find an attorney, solicitor, barrister, or other authorised legal professional: your professional regulator's referral service is the fastest starting point (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent). Many offer free or low-cost initial consultations. For small businesses, local law school clinics and SCORE mentors can point you in the right direction. For individuals, legal aid organizations cover many practice areas.

#### Practice setting

Ask once, early, so later questions about escalation and sign-off branch correctly:

> Practice setting? (This feeds the governance team and escalation matrix — every skill checks here before telling you to loop in someone above you, and the branching below reframes escalation as "consult" vs "route for approval" accordingly.)
>
> - **Solo / small firm (no hierarchy)** — I'll skip approval-chain questions and ask when you'd loop in a colleague or outside counsel instead.
> - **Midsize / large firm** — I'll ask about your approval chain, billing thresholds, and who signs off above you.
> - **In-house** — I'll ask about your escalation matrix, who the GC/CLO is, and when something goes to the business.
> - **Government / legal aid / clinic** — I'll ask about supervision structure and any restrictions on your practice.
> - **My practice doesn't fit any of these** — say so. I'll adapt.

**Practices that don't fit the boxes.** If the user's practice doesn't match the options above (international arbitration, public international law, amicus-only, academic consulting, pro bono panel, tribal court, military justice, maritime, or anything else the standard categories assume away), offer: "It sounds like your practice doesn't fit my usual categories. Tell me about it in your own words — what you do, who for, what jurisdictions and forums, what the work looks like — and I'll build your profile from that instead of forcing you into boxes that don't fit. I'll skip or adapt the questions that don't apply." Then build the profile from the free-form description, flagging which template fields were filled, adapted, or left empty because they don't apply. A profile built from a forced fit is worse than a sparse profile built from what's actually true.

Branching for later parts of the interview:

- **Solo practitioner or small firm without a hierarchy:** skip or reframe escalation-chain questions. Instead of "who approves above your threshold," ask "when do you call in outside counsel or a colleague for a second opinion." Escalation maps to "consult," not "route for approval." The `## Governance team and escalation` section in the practice profile should be written around consultation triggers, not internal approval levels.
- **In-house legal, midsize, or large firm:** ask the escalation chain as currently designed (Part 4).
- **Legal aid / clinic:** route toward a supervision-model framing in Part 4 — who supervises, when does a matter go up to the supervising attorney?
- **Government:** adapt — ask who inside the agency/office owns approval above the attorney's authority.

Record this in the `## Company profile` → `**Practice setting:**` line of the practice profile, and in the `## Governance team and escalation` structure.

#### What's connected?

> This plugin can work with: document storage (Google Drive, SharePoint, Box), scheduled-tasks, Slack. Let me check which connectors you have configured — features that need them will work, and features that don't have them will fall back to manual gracefully instead of failing silently.

**Check what's actually connected, not what's configured.** A connector listed in `.mcp.json` is *available*. A connector that's actually responding is *connected*. These are different, and confusing them destroys trust. For each connector this plugin uses:

- If you can test the connection (call a simple MCP tool like a list or search), report ✓ only on a successful response.
- If you can't test (no way to probe from here), report ⚪ "configured but not verified — open your MCP settings to confirm" with a one-line how-to.
- Never report ✓ based on configuration alone.

For connectors that show as not connected, tell the user how to connect. Example phrasing: "Google Drive isn't connected. In Claude Cowork: Settings → Connectors → Add → Google Drive → sign in. In Claude Code: add the Drive MCP to your config or via `/mcp`. This plugin works without it — you'll paste policies and assessments directly — but connecting it lets the policy-monitor skill crawl your AIA folder automatically."

Then report findings in this form:

> - ✓ [Integration] — connected (tested)
> - ⚪ [Integration] — configured but not verified. Open your MCP settings to confirm.
> - ✗ [Integration] — not found. [Feature] will fall back to [manual alternative]. [How to connect.]

You don't need all of these. Core features work with file access alone. If you set something up later, re-run `/ai-governance-legal:cold-start-interview --check-integrations`.

Write a `## Who's using this` section and an `## Available integrations` section into the plugin config immediately after the first section. Merge the work-product-header logic into the existing `## Outputs` section per the template.

---

### Part 1: Builder, deployer, or both? (3-4 min)

**What does [your company] do?** This is the single most important context — a SaaS vendor's playbook, a hardware distributor's playbook, and a services firm's playbook are completely different. You don't have to type it out: paste a link to your company website, your "about" page, your Wikipedia article, or your latest 10-K, and I'll extract what I need. Or give me the one-sentence version: what you sell, to whom, and how (direct sales / channel / marketplace / subscription). The builder/deployer question below only makes sense on top of this.

**This is the question that determines everything else.**

> **EU AI Act roles are per-system, not per-company.** If your jurisdiction
> footprint includes the EU, your role (provider, deployer, importer,
> distributor, authorized representative, product manufacturer) and risk tier
> are assessed for each AI system separately — you might be a deployer of
> one system and a provider of another. Instead of assigning one company-
> level role, I'll set up a system inventory. We can do 1-3 systems now and
> add the rest later with `/ai-governance-legal:ai-inventory add`. Or skip
> the inventory for now if you're not in the EU or not ready.

Walk through the role options if the user isn't sure:
- **Provider:** You develop an AI system (or have it developed) and place it
  on the EU market or put it into service under your own name or trademark.
- **Deployer:** You use an AI system under your own authority, not for
  personal non-professional use. (Most common inside companies.)
- **Importer:** You bring an AI system into the EU from a provider
  established outside the EU.
- **Distributor:** You make an AI system available on the EU market without
  being the provider or importer.
- **Authorized representative:** You act on behalf of a non-EU provider and
  are established in the EU.
- **Product manufacturer:** You put an AI system into a product under your
  own name or trademark. Treated as provider for the product.

**Offer to populate the inventory now.** Prompt: "Want me to walk through
1-3 of your AI systems now and set up the inventory? Or skip and come back
with `/ai-governance-legal:ai-inventory add` later?" If they accept, run the
Add flow and the classification walk-through from
`ai-governance-legal/skills/ai-inventory/SKILL.md` for each system. Save to
`~/.claude/plugins/config/claude-for-legal/ai-governance-legal/ai-systems.yaml`.

If they decline or their jurisdiction footprint excludes the EU, note that
in the config and move on. The inventory can be populated later.

**High-level context questions** (ask lightly regardless of inventory
choice, to size the practice):
- What kind of AI touches your company today — generative, classification,
  recommendation, automation, something else?
- Who experiences the AI — customers, employees, candidates, no humans?
- Do you train or fine-tune models, or only consume third-party AI?
- Do you have a model card, system card, or similar documentation
  practice — or does your AI use only involve tools built by others?
- Who manages vendor AI relationships — procurement, legal, a dedicated AI
  team?
- Are you using AI in any decisions that affect employees or customers?

**Shadow AI discovery.** After the formal tool inventory, ask: "Beyond your approved tools, what AI is actually in use?
- **Embedded AI in tools you've already approved:** Slack AI summaries, Microsoft Copilot, Salesforce Einstein, Gmail smart compose, Zoom AI Companion, CRM lead scoring, email drafting assistants. Many organizations adopted these as 'productivity tools' and never triaged them as AI.
- **Informally adopted tools:** Employees using ChatGPT, Gemini, Claude, Perplexity, or other consumer AI without central approval. Check with IT for SaaS spend, browser extension usage, and DLP alerts.
- **Vendor AI you may not know about:** A 'CRM tool' with an AI scoring feature, a 'document system' with AI classification, a 'HR platform' with AI screening. Ask vendors directly: 'Does your product use AI or machine learning for any feature we've enabled?'

Add anything surfaced to the use case registry as `[UNDOCUMENTED — NEEDS TRIAGE]`. A registry calibrated only to formal deployments while unapproved tools run in the shadows is a registry that lies. The triage skill will pick these up."

**If both:** Establish which side is the larger governance surface area for now —
that's where to go deep first.

---

### Part 2: Regulatory footprint (2-3 min)

> Which regulations are actually on your radar? I don't want to assume — tell me
> what's real for you. (This feeds /gap-check and /policy-monitor — the gap analysis diffs new regulations against your stated scope, and policy-monitor only watches regimes you've marked in scope.)

**Do not assume any regulation applies. Ask the user which regimes they think apply, then research the AI-specific regulations currently in effect or pending in the jurisdictions where the company operates, deploys AI, or has affected parties. This landscape changes quickly — verify currency.**

Prompts to walk through:

- **Jurisdictional footprint** — where are customers, employees, data subjects, and business operations? Does AI touch people in any of those places?
- **Cross-border AI regimes** — if the company has users, customers, or employees outside its home jurisdiction, research whether those jurisdictions' AI regimes reach the company's activity.
- **US state AI laws** — ask which US states the company operates in; research the state-specific AI, biometrics, and automated-decision laws currently in effect or pending in each.
- **Sector regulation** — financial services, healthcare, employment, education, critical infrastructure — ask about the company's sector and research the sector-specific AI guidance from the relevant regulator(s).
- **Contractual requirements** — do enterprise customers require AI disclosures, impact assessments, or AI-specific DPA terms?

**Open regulatory matters:**
- Any regulator who knows you by name? Investigations, voluntary commitments,
  consent orders relating to AI?
- Any pending procurement requirements (government contracts requiring AI
  certifications)?

**Practical calibration:**
> "Some teams are in full compliance mode for one or more AI-specific regimes; others are focused primarily on contract commitments from enterprise customers. Where are you on that spectrum?"

---

### Part 3: Use case registry and red lines (4-5 min)

> Before the scenarios: do you have an existing AI use case registry, an AI policy, or a list of approved/prohibited AI tools I can read? Paste the contents, share a file path, or say 'no' and I'll walk through the scenarios. If you share one, I'll extract the positions and skip the scenarios that are already covered.

If not:

This is the equivalent of the DPA playbook for AI governance — most teams have
implicit red lines but rarely write them down. The goal is to extract the registry
*conversationally* from examples, not to ask for a formal document they don't have.

**Approach:** Ask about the most common use case categories for their context, then
walk through each one.

> "I want to build a picture of your use case landscape and where your lines are.
> I'll give you some scenarios — tell me if they'd be a yes, a conditional yes,
> or a hard no at your company."

**Scenario prompts (tailor to builder/deployer profile):**

*For deployers / internal use:*
- "An HR team wants to use AI to screen resumes before a recruiter looks at them.
  What happens — is that approved, conditional, or a no?"
- "A manager wants to use AI to summarize performance review notes before writing
  their own. Same question."
- "Customer support wants to use AI to draft responses before a human reviews and
  sends. Yes, conditional, no?"
- "Finance wants to use an AI tool to flag anomalies in expense reports."
- "Legal wants to use an AI assistant to first-draft NDAs."

*For builders / product AI:*
- "A PM wants to add an AI feature that surfaces personalized content recommendations
  based on user behavior."
- "A product team wants to use AI to score leads and prioritize sales outreach."
- "A feature uses AI to make automated decisions without human review in the loop.
  What triggers a review requirement?"

**For each use case, capture:**
- Approved / conditional / never
- If conditional: what does it take? (Privacy review, impact assessment, legal sign-off,
  specific vendor only, human-in-the-loop requirement, disclosure to affected parties?)
- If never: why is it a hard no? (Specific regulation? Company policy? Past incident?)

**The red lines question:**
> "What's the use case that's an automatic no — the thing someone could propose
> and you'd stop them immediately without needing to think about it?" (This feeds /triage — the skill checks proposed AI use cases against these red lines before doing anything else, and flags anything on the list as automatic stop.)

Common categories to probe if they're slow: biometric data, emotion detection,
political/religious inference, fully automated adverse decisions affecting employment
or credit, uses involving children.

**Governance tier question:**
> "Do you have a tiered approval process — some things the team can approve,
> some things go to legal, some things need the board? Or is it case by case?"

**If the user didn't upload a use-case registry:** at the end of this section, offer: "Want me to write this up as a standalone use-case registry and red-lines doc you can share and maintain? Same content I just captured — approved, conditional, never — formatted so product and PMs can check before they propose something."

---

### Part 4: Governance and escalation (2 min)

**The team:**
- How many people work on AI governance? Is there a dedicated AI ethics or
  responsible AI function, or does it sit in legal/privacy/security?
- Who owns the relationship with AI vendors — legal, procurement, IT?
- Is there a CISO, CPO, or equivalent who owns AI risk?

**Escalation:**

> "When a review finds something that needs someone more senior to sign off — a vendor AI agreement with training-on-data or liability issues, an AI use case that doesn't fit your registry, a regulatory gap that needs a decision, or a call above your authority — who does that go to? Give me a name or a role (the GC, the Chief Privacy Officer, your boss), or say 'I decide myself.' This is how the plugin knows when to say 'you can handle this' versus 'loop in [X].' (This feeds every skill's routing logic — /triage, /review-vendor-ai, and /gap-check all check the escalation matrix before telling you to hand something up.)"

Also ask:
- Has anything been escalated to the board or C-suite over AI in the last year?

**External commitments:**
- Have you signed any voluntary AI commitments, adopted industry standards, or published a customer-facing AI principles page?
- Do you publish an AI transparency report or have public AI principles?

---

### Part 5: Seed documents (3-4 min)

> "I want to see what you actually have. Tell me which of these exist, and share
> what you can. (The AI policy feeds /policy-monitor drift detection; the prior impact assessment becomes the /aia-generation template; the vendor agreements become the starting playbook for /review-vendor-ai.)"
>
> 1. **AI or acceptable use policy.** Your internal or public-facing policy on how
>    AI can and can't be used. This tells me your committed positions.
>
> 2. **A prior AI impact assessment or AI risk assessment.** Even a rough one.
>    I'll learn your structure, depth, and what you flag as high-risk.
>
> 3. **Key vendor AI agreements or AI addenda.** The contracts with your main AI
>    vendors. I want to see what you've actually agreed to — liability, data use,
>    auditability, etc.
>
> 4. **Model inventory or AI system register.** If you have one — even a spreadsheet
>    listing what AI you're running and where.
>
> 5. **Allowlist or blocklist.** Approved tools, prohibited tools, or a tiered
>    approved vendor list.
>
> If you don't have any of these — that's fine and not unusual. Tell me that and
> I'll work with what you have.

**Graceful degradation — "I have nothing" path:**

If they have no seed documents:
> "That's okay. Here's what we'll do: I'll set up a baseline practice profile using what
> you told me in the interview, and I'll flag every section that's based on what you
> said rather than a reviewed document. Those are the sections to check hardest.
>
> The two things that matter most to nail down first are your use case red lines
> (so the triage skill works correctly) and your vendor positions (so we can review
> the next agreement that comes in). We can build those from scratch in the next
> 20 minutes if you want."

**How to read the seed docs:**

**AI/acceptable use policy:** Extract every commitment and prohibition. These bind
every impact assessment and vendor review — the impact assessment skill needs to
check new use cases against stated policy.

**Prior impact assessment:** Extract the structure as a template. Section headings,
depth of analysis, format of risk statements, what mitigation looks like here. This
becomes the default output format for the aia-generation skill.

**Vendor AI agreements:** Map each vendor's data use terms, liability positions,
auditability commitments, and any AI-specific provisions. Flag gaps against what the
company said they require.

**Model inventory:** Note every AI system in production. Cross-reference against
whether an impact assessment was done for each. Gaps are the backlog.

### Part 6: Outputs and policy document location (1 min)

> "Two last things — I need to know where to look to keep your AI policy current."

- **Where do you save completed AIAs, triage results, and vendor AI reviews?** A folder
  path or shared drive location. (This feeds /policy-monitor — the skill crawls this folder to detect when your practice has drifted ahead of your written AI policy.)
- **Where is the actual AI or acceptable use policy document?** The one that gets
  published internally or shared with customers/employees. I'll need to read it to
  suggest edits when drift is found.
- **Is there a naming convention for output files?** (e.g., `AIA_UseCase_YYYY-MM-DD`)
  or is it ad hoc?

If outputs aren't saved anywhere yet:
> "That's fine — the policy-monitor skill will still work in direct-query mode
> ('we want to start doing X, does our AI policy cover it?'). The crawl sweep just
> won't have anything to scan until you start saving outputs."

---

## Writing the practice profile

```markdown
# AI Governance Practice Profile

*Written by the cold-start interview on [DATE]. Edit this file directly.*

---

## Company profile

[Company] is a [description — what the company does and who its customers are].

**AI role:** [Builder / Deployer / Both — and what that means for this company
specifically]

**Builder profile (if applicable):** [Type of AI built, customer segments, whether
models are trained or fine-tuned, whether AI makes consequential decisions]

**Deployer profile (if applicable):** [AI tools in use, where AI touches the product
or operations, vendor relationship owner]

**Regulatory footprint:** [Only list what actually applies — EU AI Act / Colorado /
BIPA / sector-specific / contractual requirements only]

**Open regulatory matters:** [none / list]

**External commitments:** [voluntary commitments, public AI principles, transparency
reports — or none]

---

## Use case registry

*Extracted from interview on [DATE]. Add new use cases as they arise.*

| Use case | Approved | Conditions / Requirements | Never — reason |
|---|---|---|---|
| [e.g., Resume screening AI] | Conditional | Impact assessment required; human reviews every decision; disclosure to candidates | Fully automated adverse decision |
| [e.g., AI-drafted legal documents] | Conditional | Attorney reviews before use; no privileged matter input | — |
| [e.g., Emotion/sentiment detection for HR] | Never | — | Company policy; high litigation risk |
| [add rows from interview] | | | |

### Red lines

The following are automatic nos, regardless of framing:

- [Red line 1 — reason]
- [Red line 2 — reason]
- [Add from interview]

### Governance tiers

| Risk tier | Approval path | Example use cases |
|---|---|---|
| Standard | [team approval / department head] | Internal productivity tools, assistive drafting |
| Elevated | [Legal / privacy review required] | Customer-facing AI, HR use cases, data-heavy tools |
| High | [C-suite / board-level] | Consequential automated decisions, biometric, new AI product launch |

---

## Impact assessment house style

**Trigger:** [What requires an impact assessment — new AI feature, new vendor, new
use case, specific risk categories]

**Format:** [Structure extracted from seed impact assessment — or baseline if none
provided]

**Depth:** [Typical length / detail level — or "to be established"]

**Sign-off:** [Who approves — just legal, or a review committee]

**Template structure (from seed assessment or baseline):**

1. [Section 1 heading and rough content]
2. [Section 2]
3. [etc.]

*Note: [If no seed doc — "Baseline structure. Update after completing first
assessment."]*

---

## Vendor AI governance

### What we require from AI vendors

| Term | Our standard | Acceptable fallback | Never |
|---|---|---|---|
| Data use | [e.g., No training on our data without opt-in] | [Limited retention for safety only] | [Unrestricted training on our inputs] |
| Auditability | [e.g., SOC 2 + annual third-party audit] | [Documented internal audit process] | [No audit rights] |
| Liability for AI outputs | [e.g., within the MSA cap] | [Separate capped carveout] | [Zero vendor liability for AI errors] |
| Incident notification | [e.g., 72 hours for AI system failures affecting us] | | |
| Human review rights | [e.g., can demand human review of consequential outputs] | | |
| Model change notification | [e.g., 30 days notice for material model changes] | | |

### The one thing

[Vendor AI term that's an automatic no]

---

## AI policy commitments

*Extracted from [policy name / URL] on [date]. If the policy changes, re-run setup
or edit this section.*

**Prohibited uses stated:** [list]
**Required safeguards stated:** [list]
**Disclosure obligations stated:** [what the policy says about disclosing AI use
to customers, employees, or affected parties]
**Approved vendors / tools:** [list or "maintained in allowlist"]
**Prohibited vendors / tools:** [list or "maintained in blocklist"]

---

## Governance team and escalation

**Team:** [N people / function — where AI governance sits in the org]
**Vendor relationship owner:** [who manages AI vendor contracts]
**AI risk owner:** [CISO / CPO / GC / dedicated role]

| Issue | Handle at | Escalate to | When |
|---|---|---|---|
| New use case — standard tier | [team / department] | [you] | Ambiguous risk tier |
| New use case — elevated tier | [you + legal review] | [GC] | Outside approved categories |
| New use case — high tier | [you + GC] | [C-suite / board] | New consequential AI product, biometric, automated adverse decision |
| Vendor AI incident | [you + security] | [GC + C-suite] | Data exposure, model failure affecting customers |
| Regulator inquiry | — | [GC + you immediately] | Always |
| Employee AI misuse | [HR + you] | [GC] | Policy violation with legal exposure |

---

## Seed documents

| Doc | Location | Date reviewed | Notes |
|---|---|---|---|
| AI / acceptable use policy | [path/URL] | [date] | [version or "none — baseline used"] |
| Reference impact assessment | [path/link] | [date] | "[feature/use case it was for]" |
| Key vendor AI agreement | [path/link] | [date] | "[vendor name]" |
| Model inventory | [path/link] | [date] | "[N systems as of date — or none]" |
| Allowlist / blocklist | [path/link] | [date] | |

---

*Re-run: `/ai-governance-legal:cold-start-interview --redo`*
```

## After writing

**Show what this plugin can do.** Before closing, offer:

> **Want to see what I can help with?**

If yes, show this tailored list (not a generic template — these are the concrete things this plugin does best):

> **Here's what I'm good at in AI governance:**
>
> - **Review vendor AI terms** — e.g., "A vendor sent AI provisions in their SaaS agreement — check them against your training-on-data, liability, and model-change positions." Try: `/ai-governance-legal:vendor-ai-review`
> - **Triage a proposed AI use case** — e.g., "A PM wants to add an AI feature — run it against your registry for approved / conditional / not approved." Try: `/ai-governance-legal:use-case-triage`
> - **Run an AI impact assessment** — e.g., "A high-risk use case needs a structured AIA with regulatory classification and recommended conditions." Try: `/ai-governance-legal:aia-generation`
> - **Diff a new AI regulation against your posture** — e.g., "A new AI rule dropped — see what gaps it opens and what remediation it forces." Try: `/ai-governance-legal:reg-gap-analysis`
> - **Sweep for policy drift** — e.g., "Look across saved AIAs, triage results, and vendor reviews to find where your AI policy no longer matches practice." Try: `/ai-governance-legal:policy-monitor`
>
> **My suggestion for your first one:** Triage one real use case from your backlog — it's the fastest way to feel what the registry gives you. Or tell me what's on your plate and I'll pick.

This solves the cold-start problem (the supervisor doesn't know what to do first) and the value-prop problem (they don't know what the plugin can do) in one offer. Make the list specific. Skip this step if the supervisor already named a concrete first task during the interview.


1. **Show the summary.** "Here's what I heard. The use case registry is the part to
   check hardest — did I capture your red lines correctly? Those drive the triage
   skill."

2. **Propose first tasks:**
   - "Want me to run a triage on the use cases you mentioned and give you a risk
     tier and impact assessment checklist for each?"
   - "Got a vendor AI agreement in the queue I can review against your positions?"
   - If no impact assessment template: "Want to build your impact assessment template
     from scratch now? Fifteen minutes."
   - If no policy: "You're running without a written AI policy — if something goes
     wrong, you'll be explaining your governance verbally. Want to draft one?"

3. **Flag gaps:** Call out explicitly what's missing and what risk that creates.
   Don't soften it.
   - No model inventory: "You don't have a register of what AI you're running. That
     means you can't do a systematic impact assessment review and you can't respond
     quickly to an incident. That's the first thing to fix."
   - No vendor AI terms: "Your vendor agreements may have no AI-specific provisions —
     which means your vendors can train on your data, change their models without
     notice, and disclaim all liability for AI errors. Worth reviewing the next
     renewal."

4. **Connect to privacy:** If the company has a privacy plugin configured, note:
   "Some of this overlaps with your privacy practice — PIAs and AI impact assessments
   often cover the same ground. Once both plugins are calibrated, I can flag when a
   use case needs both."

5. **Close with a note on changeability.** End with something like:

   > "Done. Your configuration is at `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` — it's a plain text file you can read and edit directly. Anything you answered can be changed:
   >
   > - Edit the file directly for a quick change
   > - Run `/ai-governance-legal:cold-start-interview --redo` for a full re-interview
   > - Run `/ai-governance-legal:cold-start-interview --check-integrations` to re-check what's connected
   >
   > The sections most often adjusted after first setup are the use case registry and red lines, vendor AI review red lines, and the regulatory regimes in scope. Your configuration will improve as you use the plugin — when a skill's output feels off, the fix is usually here."

6. **Before your first triage**: connect a research tool. Without one, I'll flag every citation as unverified — with one, I verify them against a current database. In Cowork: Settings → Connectors. In Claude Code: authorize when a skill prompts you.

<!-- COLLATERAL LINKS: when onboarding collateral exists, add here:
     "Want a walkthrough? [Watch the 3-minute intro](URL) or [read the getting-started guide](URL)." -->

## Your practice profile learns

After writing the practice profile, close with this note:

> **Your practice profile learns.** It gets better as you use the plugins:
>
> - When a skill's output feels off, that's usually a position to tune. The output will tell you which one.
> - The `policy-monitor` agent watches for drift between your AI governance policy and your practice, and proposes updates.
> - You can always say "update my playbook to prefer X" or "change my escalation threshold to Y" and the relevant skill will write the change.
> - Run `/cold-start-interview --redo <section>` to re-interview one part, or edit the config file directly.
>
> Ten minutes of setup gets you a working profile. A month of use gets you one that reads like you wrote it yourself.

## Failure modes

- **Don't let them skip the builder/deployer question.** If they say "both," get
  specific about which side creates the larger governance obligation right now. The
  skills work differently depending on the answer.
- **Don't assume any specific regime applies.** Companies often get told they "should probably care" about a given AI regime — research whether the regime actually reaches them (jurisdictional nexus, threshold, system category) before treating it as in scope.
- **Don't write a use case registry from generic positions.** If they've never
  formally approved or rejected a use case, say so in the plugin config: `[POSITIONS FROM
  INTERVIEW — these reflect stated preferences, not formally reviewed policy. Treat
  as starting points.]`
- **Don't skip the "I have nothing" path.** Some of the best-run teams haven't
  documented anything yet. The interview still has value; just make clear in the
  practice profile which sections are from stated positions vs. reviewed documents.
- **Don't merge this with the privacy interview.** The overlap is real — PIAs,
  vendor assessments, policy frameworks — but the orientation is different enough
  that running them together loses sharpness. If both plugins are being set up, run
  them sequentially.
