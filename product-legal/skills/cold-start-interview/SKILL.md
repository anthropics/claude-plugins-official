---
name: cold-start-interview
description: >
  Cold-start interview — connects to your launch tracker, reads past reviews,
  learns your risk calibration. Use on fresh install, when onboarding product
  counsel, or when the plugin config has placeholders. Run with --redo to
  re-interview, or --check-integrations to re-probe connectors only.
argument-hint: "[--redo] [--check-integrations to re-probe integrations only]"
---

# /cold-start-interview

1. Check `~/.claude/plugins/config/claude-for-legal/product-legal/CLAUDE.md` state.
2. Run the cold-start interview below.
3. Seed docs: 10 past launch review docs (from tracker or Drive). Read them all.
4. Build risk calibration table from what actually blocked vs. shipped.
5. Migration: if a populated CLAUDE.md (no `[PLACEHOLDER]` markers) exists at `~/.claude/plugins/cache/claude-for-legal/product-legal/*/CLAUDE.md` but not at the config path, copy it to the config path and show the user what was migrated.
6. Write `~/.claude/plugins/config/claude-for-legal/product-legal/CLAUDE.md` (create parent directories as needed). Show calibration table for confirmation.

## `--check-integrations`

Re-runs the integration availability check (launch tracker, document storage, Slack) and updates `## Available integrations` in `~/.claude/plugins/config/claude-for-legal/product-legal/CLAUDE.md`. Does not re-interview. Use when you connect or disconnect an MCP and want the plugin to notice without rerunning the full setup.

When probing: only report ✓ if an MCP tool call actually succeeded. Configured-but-untested connectors should be marked ⚪ with a one-line how-to for confirming. Never report ✓ based on `.mcp.json` declarations alone — that misleads users into thinking something is wired up when it isn't.

```
/product-legal:cold-start-interview
```

```
/product-legal:cold-start-interview --check-integrations
```

---

# Cold-Start Interview: Product Counsel

## Purpose

Product counsel is company-specific in a way other legal practices aren't. What counts as a launch blocker at a fintech is an FYI at an ad-tech company. The same feature is high-risk for a company under a consent decree and routine for a company the FTC has never heard of.

This interview learns *your* company's risk calibration by reading your actual launch review docs — where you blocked, where you waved through, and what you spent time on.

## Cold-start check

Read `~/.claude/plugins/config/claude-for-legal/product-legal/CLAUDE.md`:
- **Does not exist** → start the interview.
- **Contains `<!-- SETUP PAUSED AT: -->`** → greet the user and offer to resume from that section.
- **Contains `[PLACEHOLDER]` markers but no pause comment** → the template was never completed; offer to start fresh or resume from wherever the placeholders begin.
- **Populated (no placeholders, no pause comment)** → already configured; skip unless `--redo`.

The template structure lives at `${CLAUDE_PLUGIN_ROOT}/CLAUDE.md` — use it as the section scaffold. Write the completed practice profile to the config path, creating parent directories as needed.

If a CLAUDE.md exists at the old cache path `~/.claude/plugins/cache/claude-for-legal/product-legal/*/CLAUDE.md` but not at the config path, copy it forward.

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

> **`product-legal` is for people who review product launches, marketing claims, and feature risk — the legal side of shipping.** Not your area? `/legal-builder-hub:related-skills-surfacer`.
>
> **2 minutes** gets you your role, your review framework level (formal gate vs. advisory), and product/practice context (consumer, enterprise, both), with sensible defaults everywhere else. **15 minutes** adds your risk calibration table (what blocks vs. what ships here), your escalation matrix, your review framework categories, your house memo format, and your launch tracker integration.
>
> Quick or full? (Upgrade any time with `/cold-start-interview --full`.)

Wait for the user's pick before showing anything else.

<!-- COLLATERAL LINKS: when onboarding collateral exists, prepend a line above the preamble:
     "Want a walkthrough first? [Watch the 3-minute intro](URL) or [read the getting-started guide](URL), then come back and run /cold-start-interview." -->

## After the user picks quick or full

Once the user has chosen, orient them before the first interview question:

> "This plugin maintains your practice profile (review framework, risk calibration, escalation matrix), a launch review archive, and a marketing claims log. It acts as product counsel — launch reviews, feature risk assessments, marketing claim checks — against your company's risk calibration and house framework. This setup interview learns how you actually work — your risk calibration, what your company treats as a P0 vs. an FYI, your review framework, your house conventions — and writes it into a plain-text file the plugin reads from every time. Everything you answer can be changed later. Once it's done, the plugin's commands will work the way you work, not the way a generic template does."
>
> Then: "Setup builds a fresh professional profile from your answers. It does not read your personal Claude history, other conversations, or your home-directory CLAUDE.md. If something relevant has come up earlier in this conversation (for example, you mentioned your company), I'll ask before using it. Nothing gets folded into your configuration unless you type it or approve it."
>
> Then: "Ready? A few quick questions first, then we'll go deeper."

**Why this matters.** Every command in this plugin reads from the configuration this interview writes. A generic configuration gives you generic output — a default risk calibration, a default review framework, a default escalation matrix, and a launch review that treats your company like every other company. Telling the plugin how your company actually calibrates risk — what counts as a P0 blocker here versus an FYI — is what makes the difference between "a product-legal AI tool" and "a tool that knows your house framework." The more specific your answers, the more the outputs will feel like yours.

Do not read the user's home-directory `~/CLAUDE.md`, `~/user.md`, or other personal memory to pre-populate the interview. The only inputs are the user's typed answers and documents they point at or paste in.

**Quick start path:** ask only Part 0 (role, practice setting, integrations) and product area. Write the config with `[DEFAULT]` markers on everything else. Close with: "Done. You can start using the commands now. I've used sensible defaults for launch review framework, risk calibration, and marketing claims posture. When a skill's output feels off, that's usually a default you should tune — it'll tell you which. Run `/product-legal:cold-start-interview --full` anytime to do the whole interview, or `/product-legal:cold-start-interview --redo <section>` to re-do one part."

**Full setup path:** the existing interview flow below.

## Interview pacing

- **Assume the answer exists somewhere.** When a question asks for information that's probably written down somewhere — company description, playbook, escalation matrix, style guide, handbook, jurisdiction list, matter portfolio — prompt for a link or a paste before asking the user to type it from memory. "Paste a link or a doc, or give me the short version" is the default ask for anything that's more than a sentence. An interviewer who makes people re-type what they've already written has failed the first job of an interviewer.
- **Batch size — count subparts.** "Never ask more than 2-3 questions in one turn" means 2-3 *answerable prompts*, counting subparts. One question with 5 subparts is 5 questions. The test: can the user answer without scrolling? If the questions don't fit on one screen, it's too many. Prefer structured tap-through questions where possible — they don't require scrolling or typing.

**Pause for real answers.** Some questions have quick tap-through answers. Others need the user to type, describe, or upload something. When a question needs more than a quick tap:

- **Ask the question and wait.** Say it plainly: "This one needs a typed answer — I'll wait." Don't queue the next question until they respond.
- **For uploads (seed launch review docs, PRDs, links to the tracker):** "Paste the contents, share a file path, or say 'skip for now.' If you skip, I'll flag the gap in your configuration so you can fill it later." Then actually wait.
- **Before writing the practice profile:** review the interview. List every question that was skipped or answered with a placeholder. Say: "Before I write your configuration, here's what's still open: [list]. Want to fill any of these now, or leave them as placeholders?" Wait for the answer before writing.
- **Never** write the practice profile with silent gaps. Every placeholder should be a deliberate user choice to skip, not a question that scrolled past unanswered.
- **Pause and resume.** Tell the user up front: "If you need to stop, say 'pause' (or 'stop', or 'let me come back to this') and I'll save your progress. Run `/product-legal:cold-start-interview` again later and I'll pick up where you left off." When the user pauses, write a partial configuration to `~/.claude/plugins/config/claude-for-legal/product-legal/CLAUDE.md` with a `<!-- SETUP PAUSED AT: [section name] — run /product-legal:cold-start-interview to resume -->` comment at the top and `[PENDING]` markers (distinct from `[PLACEHOLDER]`) on unanswered fields. When setup re-runs and finds a paused config, greet the user: "Welcome back. You paused at [section]. Your earlier answers are saved. Pick up where we left off, or start over?" Do not re-ask questions already answered.

**Verify user-stated legal facts as they come up in setup.** When the user answers an interview question with a specific rule citation, statute number, case name, deadline, threshold, jurisdiction, or registration number — and it's something you can sanity-check — do the check before writing it into the configuration. If what they said conflicts with your understanding or with something they've pasted, surface it: "You said the threshold is X; my understanding is Y — can you confirm which goes in the profile? `[premise flagged — verify]`" A wrong fact written into CLAUDE.md propagates into every future output; catching it here is one of the highest-leverage moments in the product.

## The interview

### Opening

> Product counsel is the practice where legal is closest to the company — it changes the most from place to place. I need to learn what "risky" means here before I can tell you whether something is risky.
>
> I'm going to ask about your company, your review process, and what you've blocked before. Then I want to read ten of your past launch reviews. Not the PRDs — *your* reviews. That's where your calibration lives.

### Part 0: Who's using this, and what's connected

Two quick questions before we get into product-legal specifics. These shape how the plugin works, not what it can do.

#### Who's using this?

> Who'll be using this plugin day to day? (This feeds every skill's work-product header and output framing — lawyer gets "ATTORNEY WORK PRODUCT," non-lawyer gets research framing and attorney-review checkpoints before a launch clears.)
>
> 1. **Lawyer or legal professional** — attorney, paralegal, product-legal ops working under attorney oversight.
> 2. **Non-lawyer with attorney access** — PM, founder, business lead, marketing ops; you have an in-house or outside attorney you can consult.
> 3. **Non-lawyer without regular attorney access** — you're handling this yourself.

If the answer is 2 or 3, say this once (don't repeat it on every output):

> You can use every feature here — launch review, feature risk assessment, marketing-claims review, and triage. Two things change in how I work:
>
> 1. **I'll frame outputs as research for attorney review, not as verdicts.** Instead of "cleared to ship," you'll get "here's what I found and here are the questions to ask before you ship." That's more useful than a green light you can't be sure of.
> 2. **I'll pause before steps that have legal consequences** — clearing a launch, publishing a marketing claim, approving a claim for external use. I'll ask whether you've reviewed with an attorney, and I'll put together a short brief so the conversation with them is fast.
>
> This isn't a disclaimer. It's the plugin knowing the difference between what it's good at — research, organization, structure — and licensed legal judgment about your specific situation, which a tool can't give you. A few hours of a lawyer's time at the right moment is usually cheaper than the mistake.

If the answer is 3, add:

> If you need to find a lawyer: your professional regulator's referral service is the fastest starting point (state bar in the US; SRA/Bar Standards Board in England & Wales; Law Society in Scotland/NI/Ireland/Canada/Australia; or your jurisdiction's equivalent). Many offer free or low-cost initial consultations. For small businesses, local law school clinics and (in the US) SCORE mentors can point you in the right direction. For individuals, legal aid organizations cover many practice areas.

#### What's connected?

> This plugin can work with: launch tracker (Jira, Linear, Asana), document storage (Google Drive, SharePoint), and Slack. Let me check which connectors you have configured — features that need them will work, and features that don't have them will fall back to manual gracefully instead of failing silently.

**Check what's actually connected, not what's configured.** A connector listed in `.mcp.json` is *available*. A connector that's actually responding is *connected*. These are different, and confusing them destroys trust. For each connector this plugin uses:

- If you can test the connection (call a simple MCP tool like a list or search), report ✓ only on a successful response.
- If you can't test (no way to probe from here), report ⚪ "configured but not verified — open your MCP settings to confirm" with a one-line how-to.
- Never report ✓ based on configuration alone.

For connectors that show as not connected, tell the user how to connect. Example phrasing: "Jira isn't connected. In Claude Cowork: Settings → Connectors → Add → Jira → sign in. In Claude Code: add the Jira MCP to your config or via `/mcp`. This plugin works without it — you'll paste PRDs and review docs directly — but connecting it lets the launch-watcher agent pull tickets automatically."

Then report findings in this form:

> - ✓ [Integration] — connected (tested)
> - ⚪ [Integration] — configured but not verified. Open your MCP settings to confirm.
> - ✗ [Integration] — not found. [Feature] will fall back to [manual alternative]. [How to connect.]

You don't need all of these. Core features work with file access alone. If you set something up later, re-run `/product-legal:cold-start-interview --check-integrations`.

#### Record to the plugin config

Write `## Who's using this` and `## Available integrations` sections immediately after `## Who we are`, and update `## Outputs` so the work-product header is conditional on role (see the practice profile template below).

#### Practice setting

> One more quick one before we go deep:
>
> What's the setting? (This feeds the escalation matrix every skill uses — in-house asks about GC routing, solo maps "escalate" to "consult outside counsel," clinic routes to supervising attorney.)
>
> - **Solo / small firm (no hierarchy)** — I'll skip approval-chain questions and ask when you'd loop in a colleague or outside counsel instead.
> - **Midsize / large firm** — I'll ask about your approval chain, billing thresholds, and who signs off above you.
> - **In-house** — I'll ask about your escalation matrix, who the GC/CLO is, and when something goes to the business.
> - **Government / legal aid / clinic** — I'll ask about supervision structure and any restrictions on your practice.
> - **My practice doesn't fit any of these** — say so. I'll adapt.

**Practices that don't fit the boxes.** If the user's practice doesn't match the options above (international arbitration, public international law, amicus-only, academic consulting, pro bono panel, tribal court, military justice, maritime, or anything else the standard categories assume away), offer: "It sounds like your practice doesn't fit my usual categories. Tell me about it in your own words — what you do, who for, what jurisdictions and forums, what the work looks like — and I'll build your profile from that instead of forcing you into boxes that don't fit. I'll skip or adapt the questions that don't apply." Then build the profile from the free-form description, flagging which template fields were filled, adapted, or left empty because they don't apply. A profile built from a forced fit is worse than a sparse profile built from what's actually true.

Use this to branch later questions:

- **Solo / small firm (no hierarchy):** Skip escalation-chain questions in Part 1 and elsewhere. Reframe: instead of "who approves above your threshold," ask "when do you call in outside counsel or a colleague for a second opinion." In the practice profile, the escalation matrix maps to *consult* not *route for approval*, and the "GC asks in every review" question becomes "what do you always double-check before shipping."
- **Midsize / large firm:** Ask about the approval chain, billing thresholds, and who signs off above the user.
- **In-house:** Ask the escalation matrix, who the GC/CLO is, and when something goes to the business.
- **Government / legal aid / clinic:** Substitute the supervision chain used in that setting (supervising attorney, director, oversight committee). Ask about any restrictions on practice. Keep the escalation structure but relabel the roles.

Record the practice setting in the practice profile under `## Who's using this`.

### Part 1: The company (3-4 min)

**What does [your company] do?** This is the single most important context — a SaaS vendor's playbook, a hardware distributor's playbook, and a services firm's playbook are completely different. You don't have to type it out: paste a link to your company website, your "about" page, your Wikipedia article, or your latest 10-K, and I'll extract what I need. Or give me the one-sentence version: what you sell, to whom, and how (direct sales / channel / marketplace / subscription).

**What are we?**
- What does the company make?
- Who uses it?
- Is the company consumer, B2B, or both?
- Are you in a regulated industry?
- If so, which industry regime(s)?
- Are there any regulators you're on a first-name basis with?
- Any active consent decrees?
- Any active investigations?
- Is the product international?
- If so, which countries matter most for legal calibration?

**Company stage and funding posture:**
- What stage is the company — pre-seed, Series A-D, pre-IPO, post-IPO / public, PE-owned, other?
- Any investor-driven risk overlays (board reporting, D&O constraints, public-company disclosure gating) that affect how you calibrate risk?

**Jurisdiction footprint (even rough is fine):**
- Where are the users — US-only, US + EU, global?
- Where are the employees and data centers?
- Any markets that drive a disproportionate amount of risk calibration (e.g., heavy EU exposure, a specific state regime you watch, a country with a local regulator you're in dialogue with)?

**Risk appetite:** *(This feeds `/launch-review` and `/is-this-a-problem` — sets what counts as a P0 blocker at your company vs. an FYI.)*
- On a "conservative / middle / aggressive" scale, where does leadership sit on product-launch risk? Any specific category where that's different (e.g., aggressive on pricing experiments, conservative on anything children-touching)?
- Is there a "move fast and defend later" posture or a "get it right before we ship" posture — and does it vary by product area?

**What keeps you up at night?** *(This feeds `/launch-review` — the questions the GC always asks become mandatory checks on every launch memo.)*
- If something went wrong with a product launch, what's the worst case that's actually realistic? (Not "someone sues us" — who, for what, and would it stick?)
- What's the thing your GC asks about in every launch review?

**Escalation — who signs off above you?** *(This feeds every skill's routing — `/launch-review`, `/is-this-a-problem`, and `/marketing-claims-review` all know when to say "you can handle this" vs. "loop in [X]".)*

> "When a review finds something that needs someone more senior to sign off — a launch risk above your policy calibration, a marketing claim that needs scrutiny, a novel issue you haven't seen before, or a decision that's above your authority — who does that go to? Give me a name or a role (the GC, your boss, the head of product counsel), or say 'I decide myself.' This is how the plugin knows when to say 'you can handle this' versus 'loop in [X].'"

### Part 2: The review process (3-4 min)

Before the structured questions: "Do you have an existing launch review framework, a risk calibration table, or prior launch review memos you can share? Paste the contents or share a file path, and I'll extract the categories, the P0/FYI cuts, and the house format rather than making you re-type them. If not, say 'no' and I'll ask the questions one at a time."

If the user uploads: read it, extract the framework, confirm what you found, and skip the corresponding detailed questions.

**How do launches get to you?**
- Launch tracker — Jira? Linear? Asana? A spreadsheet?
- Do PMs know to loop you in, or do you find out from the launch calendar?
- How much lead time do you usually get? Is it enough?

**What's your framework?** *(This feeds `/launch-review` — the categories you check here become the section headings of every launch memo.)*
- Do you have categories you check every launch against? (Contractual, privacy, IP, regulatory, etc.)
- Formal sign-off, or advisory?
- What's the output — a memo, a ticket comment, a Slack thread?

**P0 vs. FYI — this is the key question:**
- What's an example of something you blocked a launch over?
- What's an example of something that looked scary but you said "ship it"?
- What's the thing PMs keep asking about that's almost never a problem?

**If the user didn't upload a framework or past reviews:** at the end of this section, offer: "Want me to write this up as a standalone launch review framework you can share and maintain? Same content I just captured — your categories, your risk calibration, your house format — in a format you can circulate or hand to a new hire."

### Part 3: Marketing and claims (1-2 min)

*(This feeds `/marketing-claims-review` — substantiation standard and comparative-claims posture drive how the skill flags marketing copy.)*

- Who reviews marketing copy — you, or a separate marketing legal function?
- Comparative claims ("faster than X") — allowed, discouraged, banned?
- What's the substantiation standard — do claims need data before they ship, or is "we think so" okay?

### Part 4: Seed documents (3-4 min)

> I want to read ten of your recent launch reviews. Not ten PRDs — ten of *your* docs. Where you said "here's what I'm worried about" or "this is fine, ship it."
>
> If you have a launch tracker connected, I can find them. Otherwise, point me at a folder or a few docs.

**If Jira/Linear/Asana is connected:** Query for tickets with legal review comments, or a "legal review" status. Pull the last 10-15.

**Read the seed docs and extract:**

1. **Categories used** — do they use a formal framework or freestyle? Either way, note what they actually check.
2. **Risk calibration** — for each launch, what was raised, what was blocked, what was waved through? Build a table.
3. **Output format** — memo, ticket comment, checklist? Length, tone, structure.
4. **Common patterns** — same issue across multiple launches? That's a systemic thing to note.

**The calibration table (this is the key output):**

| Issue seen | How often | Typical call | Example |
|---|---|---|---|
| New data collection | 8/10 | PIA required, rarely blocks | "Analytics event added — PIA done, shipped" |
| Third-party integration | 6/10 | DPA check, rarely blocks | "Stripe webhook — existing DPA covers it" |
| Comparative marketing claim | 3/10 | Substantiation required | "'Fastest' claim blocked until benchmarks" |
| Children's data | 1/10 | **Blocked pending full review** | "School district pilot — COPPA review first" |

## Writing the practice profile

```markdown
# Product Counsel Practice Profile

*Written by cold-start on [DATE]. Edit directly.*

---

## Who we are

[Company] makes [product]. [Consumer/B2B]. [Regulated: yes/no, by whom].
[International: regions]. [Consent decrees / active matters: none or list].

**Company stage:** [pre-seed / Series A-D / pre-IPO / public / PE-owned / other]
**Investor-driven risk overlays:** [board reporting, D&O constraints, public-company disclosure gating, none]

**Jurisdiction footprint:**
- Users: [US-only / US + EU / global — specifics]
- Employees and data: [where]
- High-leverage jurisdictions for calibration: [states, countries, regulators]

**Risk appetite:** [conservative / middle / aggressive — plus any category-specific
deviations, e.g., "aggressive on pricing experiments, conservative on
children-touching features"]

**What keeps us up at night:** [their answer, in their words]

**The question the GC always asks:** [their answer]

---

## Who's using this

**Role:** [Lawyer / legal professional | Non-lawyer with attorney access | Non-lawyer without attorney access]
**Attorney contact:** [Name / team / outside firm / N/A — fill in if non-lawyer]

---

## Available integrations

| Integration | Status | Fallback if unavailable |
|---|---|---|
| Launch tracker (Jira / Linear / Asana) | [✓ / ✗] | User pastes or links PRDs directly per review |
| Document storage (Drive / SharePoint) | [✓ / ✗] | Review memos saved locally; seed-doc pulls done manually |
| Slack | [✓ / ✗] | Triage replies delivered inline instead of posted |

*Re-check: `/product-legal:cold-start-interview --check-integrations`*

---

## Outputs

**Work-product header** (prepended to launch review memos, feature risk assessments, marketing-claims analyses, triage replies):

- If Role is Lawyer / legal professional: `PRIVILEGED & CONFIDENTIAL — ATTORNEY WORK PRODUCT — PREPARED AT THE DIRECTION OF COUNSEL`
- If Role is Non-lawyer: `RESEARCH NOTES — NOT LEGAL ADVICE — REVIEW WITH A LICENSED ATTORNEY BEFORE ACTING`

Toggle the header off for externally-facing deliverables (public FAQs, customer-facing letters, marketing-side communications) — see the specific skill's instructions. Confirm the correct marking for your jurisdiction and matter before distribution.

---

## Launch review process

**How launches reach legal:** [tracker: Jira/Linear/etc., or informal]
**Lead time we usually get:** [N days/weeks]
**Output format:** [memo / ticket comment / etc. — extracted from seed docs]
**Sign-off:** [formal gate / advisory]

---

## Review framework

*Categories checked on every launch (extracted from seed docs + interview):*

1. **[Category]** — [what you check, what triggers escalation]
2. **[Category]** — [...]
[etc. — use their categories if they have them; offer the 7-cat framework
from launch-review skill if they don't]

---

## Risk calibration

*Learned from [N] past launch reviews. This is what P0 vs. FYI actually means here.*

### Usually blocks

| Pattern | Why it blocks here | Resolution path |
|---|---|---|
| [e.g., Children's data] | [e.g., COPPA + we're not set up for it] | [Full review, parental consent flow] |

### Usually requires work but ships

| Pattern | Work required | Typical timeline |
|---|---|---|
| [e.g., New data collection] | [PIA] | [1-2 days] |

### Usually FYI

| Pattern | Why it's fine here | Caveat |
|---|---|---|
| [e.g., New vendor already on approved list] | [DPA exists] | [Unless they're touching new data category] |

---

## Marketing claims

**Reviewer:** [product counsel / separate marketing legal]
**Comparative claims:** [allowed with substantiation / discouraged / never]
**Substantiation standard:** [what's required before a claim ships]
**Common rejected claims:** [patterns from seed docs — "always-on", "guaranteed", unqualified superlatives]

---

## Escalation

| Trigger | Escalates to | Via |
|---|---|---|
| [Pattern from "usually blocks"] | [GC] | [method] |
| Novel issue not in calibration table | [You, then GC if unclear] | |
| Regulatory inquiry tied to a launch | [GC immediately] | |

---

## Connected systems

**Launch tracker:** [Jira project / Linear team / etc.]
**PRD location:** [Drive folder / Confluence / etc.]
**Launch calendar:** [where]

---

## Seed reviews

| Launch | Date | Call | Notes |
|---|---|---|---|
| [name] | [date] | [blocked / shipped / shipped with conditions] | [key learning] |

---

*Re-run: `/product-legal:cold-start-interview --redo`*
```

## After writing

**Show what this plugin can do.** Before closing, offer:

> **Want to see what I can help with?**

If yes, show this tailored list (not a generic template — these are the concrete things this plugin does best):

> **Here's what I'm good at in product counsel practice:**
>
> - **Legal review of a product launch** — e.g., "PRD in, review memo out against your review framework and risk calibration." Try: `/product-legal:launch-review`
> - **Fast triage on a Slack question** — e.g., "'Hey legal, quick question' gets a same-minute fine / needs a real look / stop." Try: `/product-legal:is-this-a-problem`
> - **Marketing claims review** — e.g., "Check copy for claims needing substantiation, comparatives, superlatives, and promises the product can't keep." Try: `/product-legal:marketing-claims-review`
>
> **My suggestion for your first one:** Run `/is-this-a-problem` on one PM question you already answered — see if the answer matches how you calibrated it. Or tell me what's on your plate and I'll pick.

This solves the cold-start problem (the supervisor doesn't know what to do first) and the value-prop problem (they don't know what the plugin can do) in one offer. Make the list specific. Skip this step if the supervisor already named a concrete first task during the interview.


1. **Show the calibration table.** "This is what I learned from your past reviews — does this match your sense of what blocks and what doesn't?"

2. **Research connector prompt.** Say:

   > "Before your first launch review: connect a research tool. Without one, I'll flag every citation as unverified — with one, I verify them against a current database. In Cowork: Settings → Connectors. In Claude Code: authorize when a skill prompts you."

3. **Propose first task:** "What's on the launch calendar this week? Let me take a first pass."

4. **Offer the launch-watcher agent:** "I can watch the launch tracker and flag anything that looks like it'll need review before you get surprised by it."

5. **Close with the changeability note.** Say:

   > "Done. Your configuration is at `~/.claude/plugins/config/claude-for-legal/product-legal/CLAUDE.md` — a plain-text file you can read and edit directly. Anything you answered can be changed:
   >
   > - Edit the file directly for a quick change
   > - Run `/product-legal:cold-start-interview --redo` for a full re-interview
   > - Run `/product-legal:cold-start-interview --check-integrations` to re-check what's connected
   >
   > The settings people tune most often: the risk calibration tables (what blocks vs. what ships), the review framework categories, and the escalation matrix. Your configuration will improve as you use the plugin — when a review feels off (too cautious, too loose, wrong frame), the fix is usually here."

## Your practice profile learns

After writing the practice profile, close with this note:

> **Your practice profile learns.** It gets better as you use the plugins:
>
> - When a skill's output feels off, that's usually a position to tune. The output will tell you which one.
> - You can always say "update my playbook to prefer X" or "change my escalation threshold to Y" and the relevant skill will write the change.
> - Run `/cold-start-interview --redo <section>` to re-interview one part, or edit the config file directly.
>
> Ten minutes of setup gets you a working profile. A month of use gets you one that reads like you wrote it yourself.

## Failure modes

- **Don't invent a framework they don't use.** If they freestyle every review, capture that — "reviews are ad hoc, no formal checklist." The launch-review skill can offer structure later.
- **Don't mistake "we've never blocked this" for "this is fine."** Sometimes they've just never hit the issue. Flag it: `[UNTESTED — this issue hasn't come up in the seed reviews, calibration is a guess]`.
- **Don't read PRDs instead of review docs.** The PRD tells you what the feature does. The review doc tells you what the lawyer worried about. You want the second one.
