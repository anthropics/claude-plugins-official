---
name: cold-start-interview
description: >
  Run the cold-start interview — learns your privacy practice and writes CLAUDE.md
  from your policy, DPA template, and a reference PIA. Use on first run, when
  CLAUDE.md is missing or has placeholders, or when the user says "set up the
  privacy plugin", "onboard me", "configure privacy", or wants to re-run the
  interview or re-check integrations.
argument-hint: "[--redo to re-run] [--check-integrations to re-probe integrations only]"
---

# /cold-start-interview

1. Check `~/.claude/plugins/config/claude-for-legal/privacy-legal/CLAUDE.md` — if populated and no `--redo`, confirm before overwriting.
2. Run the interview workflow below.
3. Seed docs: privacy policy (URL or file), DPA template, one reference PIA. Read all three.
4. Extract: policy commitments, DPA positions (note deltas vs. stated), PIA structure.
5. Migration: if a populated CLAUDE.md (no `[PLACEHOLDER]` markers) exists at `~/.claude/plugins/cache/claude-for-legal/privacy-legal/*/CLAUDE.md` but not at the config path, copy it to the config path and show the user what was migrated.
6. Write `~/.claude/plugins/config/claude-for-legal/privacy-legal/CLAUDE.md` (create parent directories as needed). Show summary. Offer first task.

## `--check-integrations`

Re-runs the integration availability check (document storage, Slack, scheduled-tasks) and updates `## Available integrations` in `~/.claude/plugins/config/claude-for-legal/privacy-legal/CLAUDE.md`. Does not re-interview. Use when you connect or disconnect an MCP and want the plugin to notice without rerunning the full setup.

When probing: only report ✓ if an MCP tool call actually succeeded. Configured-but-untested connectors should be marked ⚪ with a one-line how-to for confirming. Never report ✓ based on `.mcp.json` declarations alone — that misleads users into thinking something is wired up when it isn't.

```
/privacy-legal:cold-start-interview
```

```
/privacy-legal:cold-start-interview --check-integrations
```

---

# Cold-Start Interview: Privacy & Data Protection

## Purpose

Learn how *this* privacy team works — what regulations actually apply to them, what they will and won't agree to in a DPA, what a good PIA looks like here versus anywhere else. Write it into `~/.claude/plugins/config/claude-for-legal/privacy-legal/CLAUDE.md` so every other skill reads from the same understanding.

Privacy practices vary wildly by company. A B2B SaaS processor has almost nothing in common with a consumer app controller. The interview figures out which one this is before anything else.

## Cold-start check

Read `~/.claude/plugins/config/claude-for-legal/privacy-legal/CLAUDE.md`:
- **Does not exist** → start the interview.
- **Contains `<!-- SETUP PAUSED AT: -->`** → greet the user and offer to resume from that section.
- **Contains `[PLACEHOLDER]` markers but no pause comment** → the template was never completed; offer to start fresh or resume from wherever the placeholders begin.
- **Populated (no placeholders, no pause comment)** → already configured; skip unless `--redo`.

The template structure lives at `${CLAUDE_PLUGIN_ROOT}/CLAUDE.md` — use it as the section scaffold. Write the completed practice profile to the config path, creating parent directories as needed.

If a CLAUDE.md exists at the old cache path `~/.claude/plugins/cache/claude-for-legal/privacy-legal/*/CLAUDE.md` but not at the config path, copy it forward.

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

> **`privacy-legal` is for people who run the privacy program: PIAs, DPA reviews, DSAR responses, regulatory gap analysis.** Not your area? `/legal-builder-hub:related-skills-surfacer`.
>
> **2 minutes** gets you your role, which side of a DPA you sit on (processor/controller/both), and primary jurisdictions, with sensible defaults everywhere else. **15 minutes** adds your DPA playbook positions (processor and controller side), your PIA template structure from a reference PIA, your full regulatory footprint, and your processing-activity seeds.
>
> Quick or full? (Upgrade any time with `/cold-start-interview --full`.)

Wait for the user's pick before showing anything else.

<!-- COLLATERAL LINKS: when onboarding collateral exists, prepend a line above the preamble:
     "Want a walkthrough first? [Watch the 3-minute intro](URL) or [read the getting-started guide](URL), then come back and run /cold-start-interview." -->

## After the user picks quick or full

Once the user has chosen, orient them before the first interview question:

> "This plugin maintains your practice profile (DPA playbook, PIA house style, regulatory footprint), a processing-activity register, and per-activity PIAs and DPA reviews. This setup interview learns how you actually work — your practice, your DPA positions, your PIA house style — and writes it into a plain-text file the plugin reads from every time. Everything you answer can be changed later. Once it's done, the plugin's commands will work the way you work, not the way a generic template does."
>
> Then: "Setup builds a fresh professional profile from your answers. It does not read your personal Claude history, other conversations, or your home-directory CLAUDE.md. If I notice relevant information in our conversation context — e.g., you mentioned your company earlier — I'll ask before using it. Nothing personal gets folded into your practice configuration unless you type it or approve it."
>
> Then: "Ready? A few quick questions first, then we'll go deeper."

**Why this matters.** Every command in this plugin reads from the configuration this interview writes. A generic configuration gives you generic output — a default DPA position, a default PIA format, a default DSAR workflow, and a review that treats your B2B processor agreement the same as a consumer-controller one. Telling the plugin your actual regulatory footprint, your actual DPA positions, and your actual PIA house style is what makes the difference between "a privacy AI tool" and "a tool that works the way your program works." The more specific your answers, the more the outputs will feel like yours.

Populate the practice profile only from the user's typed answers and the three seed documents. Do not read `~/CLAUDE.md` or pull practice facts from ambient context. If something relevant is already visible in the conversation, ask before using it.

**Quick start path:** ask only Part 0 (role, practice setting, integrations) and regulatory footprint. Write the config with `[DEFAULT]` markers on everything else. Close with: "Done. You can start using the commands now. I've used sensible defaults for DPA positions, DSAR timing, and PIA thresholds. When a skill's output feels off, that's usually a default you should tune — it'll tell you which. Run `/privacy-legal:cold-start-interview --full` anytime to do the whole interview, or `/privacy-legal:cold-start-interview --redo <section>` to re-do one part."

**Full setup path:** the existing interview flow below.

## Interview pacing

- **Assume the answer exists somewhere.** When a question asks for information that's probably written down somewhere — company description, playbook, escalation matrix, style guide, handbook, jurisdiction list, matter portfolio — prompt for a link or a paste before asking the user to type it from memory. "Paste a link or a doc, or give me the short version" is the default ask for anything that's more than a sentence. An interviewer who makes people re-type what they've already written has failed the first job of an interviewer.
- **Batch size — count subparts.** "Never ask more than 2-3 questions in one turn" means 2-3 *answerable prompts*, counting subparts. One question with 5 subparts is 5 questions. The test: can the user answer without scrolling? If the questions don't fit on one screen, it's too many. Prefer structured tap-through questions where possible — they don't require scrolling or typing.

**Pause for real answers.** Some questions have quick tap-through answers (controller vs. processor, regulatory footprint). Others need the user to type something, describe something, or upload a document (privacy policy, DPA template, reference PIA, DPA negotiating positions, systems-list for DSARs). When a question needs more than a quick tap:

- **Ask the question and wait.** Say explicitly: "This one needs a typed answer — I'll wait." Do not move to the next question until the user responds.
- **For seed-document uploads:** "Paste the contents, share a file path or URL, or say 'skip for now.' If you skip, I'll flag the gap in your practice profile so you can fill it later." Then actually wait.
- **Before writing the practice profile:** review the interview. List any questions that were skipped or answered with placeholders (especially the three seed docs and DPA positions). Say: "Before I write your practice profile, here's what's still open: [list]. Want to fill any of these now, or leave them as placeholders?" Then wait for the answer.
- **Never** write a practice profile with silent gaps. Every `[PLACEHOLDER]` should be a deliberate choice the user made to skip, not a question that scrolled past. If the DPA template or reference PIA was skipped, note `[POSITIONS UNTESTED]` so downstream skills know.
- **Pause and resume.** Tell the user up front: "If you need to stop, say 'pause' (or 'stop', or 'let me come back to this') and I'll save your progress. Run `/privacy-legal:cold-start-interview` again later and I'll pick up where you left off." When the user pauses, write a partial configuration to `~/.claude/plugins/config/claude-for-legal/privacy-legal/CLAUDE.md` with a `<!-- SETUP PAUSED AT: [section name] — run /privacy-legal:cold-start-interview to resume -->` comment at the top and `[PENDING]` markers (distinct from `[PLACEHOLDER]`) on unanswered fields. When setup re-runs and finds a paused config, greet the user: "Welcome back. You paused at [section]. Your earlier answers are saved. Pick up where we left off, or start over?" Do not re-ask questions already answered.

**Verify user-stated legal facts as they come up in setup.** When the user answers an interview question with a specific rule citation, statute number, case name, deadline, threshold, jurisdiction, or registration number — and it's something you can sanity-check — do the check before writing it into the configuration. If what they said conflicts with your understanding or with something they've pasted, surface it: "You said the threshold is X; my understanding is Y — can you confirm which goes in the profile? `[premise flagged — verify]`" A wrong fact written into CLAUDE.md propagates into every future output; catching it here is one of the highest-leverage moments in the product.

## The interview

### Opening

> I'm going to help with DPAs, DSARs, PIAs, and keeping an eye on when the regs move under you. Before I do any of that, I need to know what kind of privacy shop this is. Ten minutes.
>
> Then I'm going to ask you to show me three things: your privacy policy, your standard DPA, and one PIA you think is good. I'll learn more from those than from anything you tell me.

### Part 0: Who's using this, and what's connected

Three quick questions before we get into privacy specifics. These shape how the plugin works, not what it can do.

#### Who's using this?

> Who'll be using this plugin day to day? (This feeds every skill's work-product header and output framing — lawyer gets "ATTORNEY WORK PRODUCT," non-lawyer gets research framing and attorney-review checkpoints before legally consequential steps.)
>
> 1. **Lawyer or legal professional** — attorney, paralegal, privacy ops working under attorney oversight.
> 2. **Non-lawyer with attorney access** — DPO-office non-lawyer, privacy program manager, founder handling privacy with an in-house or outside attorney you can consult.
> 3. **Non-lawyer without regular attorney access** — you're handling this yourself.

If the answer is 2 or 3, say this once (don't repeat it on every output):

> You can use every feature here — triage, DPA review, PIAs, DSAR responses, reg-gap analysis, policy monitoring. Two things change in how I work:
>
> 1. **I'll frame outputs as research for attorney review, not as verdicts.** Instead of "cleared to sign," you'll get "here's what I found and here are the questions to ask before you sign." That's more useful than a green light you can't be sure of.
> 2. **I'll pause before steps that have legal consequences** — sending a DSAR response, signing a DPA, submitting a DPIA to a regulator, giving breach notification. I'll ask whether you've reviewed with an attorney, and I'll put together a short brief so the conversation with them is fast.
>
> This isn't a disclaimer. It's the plugin knowing the difference between what it's good at — research, organization, structure — and licensed legal judgment about your specific situation, which a tool can't give you. A few hours of a lawyer's time at the right moment is usually cheaper than the mistake.

If the answer is 3, add:

> If you need to find a licensed attorney, solicitor, barrister, or other authorised legal professional in your jurisdiction: your professional regulator's referral service is the fastest starting point (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent). Many offer free or low-cost initial consultations. For small businesses, local law school clinics and SCORE mentors can point you in the right direction. For individuals, legal aid organizations cover many practice areas.

#### Practice setting

> Which of these best describes where you're practicing? (This feeds the escalation matrix every skill uses — in-house asks about GC/CPO routing, solo maps "escalate" to "consult outside counsel," clinic routes to supervising attorney.)
>
> - **Solo / small firm (no hierarchy)** — I'll skip approval-chain questions and ask when you'd loop in a colleague or outside counsel instead.
> - **Midsize / large firm** — I'll ask about your approval chain, billing thresholds, and who signs off above you.
> - **In-house** — I'll ask about your escalation matrix, who the GC/CLO is, and when something goes to the business.
> - **Government / legal aid / clinic** — I'll ask about supervision structure and any restrictions on your practice.
> - **My practice doesn't fit any of these** — say so. I'll adapt.

**Practices that don't fit the boxes.** If the user's practice doesn't match the options above (international arbitration, public international law, amicus-only, academic consulting, pro bono panel, tribal court, military justice, maritime, or anything else the standard categories assume away), offer: "It sounds like your practice doesn't fit my usual categories. Tell me about it in your own words — what you do, who for, what jurisdictions and forums, what the work looks like — and I'll build your profile from that instead of forcing you into boxes that don't fit. I'll skip or adapt the questions that don't apply." Then build the profile from the free-form description, flagging which template fields were filled, adapted, or left empty because they don't apply. A profile built from a forced fit is worse than a sparse profile built from what's actually true.

This reshapes the escalation section and some of the DPA-authority questions:

- **Solo / small firm (no hierarchy):** Skip internal escalation chain. In the escalation table, the "escalate to" column becomes outside counsel or "no further escalation." For DPA negotiation, replace "escalate to GC" with "consult outside counsel" where applicable.
- **Midsize / large firm:** Ask about the approval chain, billing thresholds, and who signs off above the user — as currently designed.
- **In-house:** Ask the full escalation matrix — who's the GC/CLO, DPO reporting line, when to loop in Security for a breach, when something goes to the business.
- **Government / legal aid / clinic:** Route toward the supervision model — supervising attorney, review mechanics for DPIAs and DSAR responses, sign-off chain before external communication, and any restrictions on the user's practice.

Record the answer in the practice profile's `## Who we are` section (as `**Practice setting:**`).

#### What's connected?

> This plugin can work with: document storage (Google Drive, SharePoint), Slack, and scheduled-tasks. Let me check which connectors you have configured — features that need them will work, and features that don't have them will fall back to manual gracefully instead of failing silently.

**Check what's actually connected, not what's configured.** A connector listed in `.mcp.json` is *available*. A connector that's actually responding is *connected*. These are different, and confusing them destroys trust. For each connector this plugin uses:

- If you can test the connection (call a simple MCP tool like a list or search), report ✓ only on a successful response.
- If you can't test (no way to probe from here), report ⚪ "configured but not verified — open your MCP settings to confirm" with a one-line how-to.
- Never report ✓ based on configuration alone.

For connectors that show as not connected, tell the user how to connect. Example phrasing: "Box isn't connected. In Claude Cowork: Settings → Connectors → Add → Box → sign in. In Claude Code: add the Box MCP to your config or via `/mcp`. This plugin works without it — you'll paste documents instead of pulling them — but connecting it makes document pulls automatic."

Then report findings in this form:

> - ✓ [Integration] — connected (tested)
> - ⚪ [Integration] — configured but not verified. Open your MCP settings to confirm.
> - ✗ [Integration] — not found. [Feature] will fall back to [manual alternative]. [How to connect.] If you set this up later, re-run `/privacy-legal:cold-start-interview --check-integrations`.
>
> You don't need all of these. Core features work with file access alone.

#### Record to CLAUDE.md

Write `## Who's using this` and `## Available integrations` sections immediately after `## Who we are`, and update `## Outputs` so the work-product header is conditional on role (see the practice profile template below).

### Part 1: What kind of privacy shop is this? (2-3 min)

**The business model question (this determines everything):**

> **What does [your company] do?** This is the single most important context — a SaaS vendor's playbook, a hardware distributor's playbook, and a services firm's playbook are completely different. You don't have to type it out: paste a link to your company website, your "about" page, your Wikipedia article, or your latest 10-K, and I'll extract what I need. Or give me the one-sentence version: what you sell, to whom, and how (direct sales / channel / marketplace / subscription).

- Whose data flows through the company?
- Are you mostly a **controller** (your own users, your own purposes) or mostly a **processor** (customers' data, their purposes)? Both? (This feeds `/dpa-review` — the skill auto-detects which side of the DPA you're on and applies the right half of your playbook.)
- B2B, B2C, or both? Enterprise or SMB customers?

**Regulatory footprint:**
- Which regulations actually apply? GDPR? CCPA/CPRA? HIPAA? FERPA? Sector-specific? (This feeds `/reg-gap-analysis` — every new reg gets diffed against this list to see if it reaches you, and `/use-case-triage` uses it to spot which regimes apply to a new processing activity.)
- Any regulators who know you by name yet? Open inquiries, consent decrees, anything?
- Where does the data physically live? US only? EU? Multi-region?

**The team:**
- How many privacy people? Is there a DPO? In-house or outside?
- "When a review finds something that needs someone more senior to sign off — a DPA position above your approval threshold, a DSAR with legal exemptions in play, a novel processing activity that doesn't fit the PIA template, a regulator inquiry, or a decision that's above your authority — who does that go to? Give me a name or a role (the GC, the CPO, your boss), or say 'I decide myself.' This is how the plugin knows when to say 'you can handle this' versus 'loop in [X].'"

### Part 2: DPA negotiating positions (3-4 min)

*(These positions feed `/dpa-review` — every inbound DPA is redlined against your standards, fallbacks, and never-accepts. Wrong positions here = wrong redlines every time.)*

Before the structured questions: "Do you have an existing DPA template, a DPA negotiation playbook, or a fallback-positions memo I can read? Paste the contents or share a file path, and I'll extract the positions rather than making you re-type them. If not, say 'no' and I'll ask the questions one at a time."

If the user uploads: read it, extract the positions, confirm what you found, and skip the corresponding detailed questions.

**If the user didn't upload a DPA playbook:** at the end of this section, offer: "Want me to write this up as a standalone DPA playbook you can share and maintain? Same content I just captured for your practice profile, formatted as a team-facing doc you can circulate or hand to a new privacy hire."


This is where the skill earns its keep — most privacy teams have DPA positions but rarely write them down.

**When you're the processor (customers send you a DPA):**
- Do you have a standard DPA you push, or do you take customer paper?
- Audit rights: SOC 2 report is the offer, right? Or do you accept on-site?
- Breach notification: what's the shortest window you've agreed to?
- Subprocessor approval: notification only, or does the customer get a veto?
- Data location commitments: can you commit to a region, or is it "wherever AWS puts it"?
- Deletion on termination: how many days, and do you certify?

**When you're the controller (you send a DPA to vendors):**
- Same questions, opposite polarity. What do you *require* from vendors?

**The one thing in a DPA that makes you say no:**
- What's the term that's an automatic reject?

### Part 3: House style (1-2 min)

**PIAs:** *(This feeds `/pia-generation` — the skill uses your trigger, format, depth, and sign-off as the default template for every PIA it drafts.)*
- What triggers a PIA at your company? Every new feature? Only certain categories?
- How long is a good PIA — two pages or twenty?
- Who signs off — just you, or is there a review committee?

**DSARs:** *(This feeds `/dsar-response` — the systems list drives the locate step, the handler drives who gets the runbook, the SLA drives deadline calculations.)*
- Volume — one a month or a hundred?
- Who handles them — you, or a support team with a runbook?
- What systems does a DSAR touch — how many places does user data live?

### Part 4: Seed documents (3-4 min)

> I want to see three things. They'll tell me how you actually work.
>
> 1. **Your current privacy policy.** The public one. I'll read it to understand what you've committed to — every PIA and DPA has to be consistent with it.
>
> 2. **Your standard DPA template.** The one you push on customers (or vendors). This is your stated playbook — I'll compare it to what you told me.
>
> 3. **One PIA you're happy with.** Not a perfect one — a *representative* one. I'll learn your structure, your tone, how deep you go, what you skip.

**How to read the seed docs:**

**Privacy policy:** Extract every commitment. Data categories collected, purposes, retention, third parties, user rights. These are promises the PIA skill needs to check against.

**DPA template:** Map every term to the interview answers. Deltas are interesting — "you said 72-hour breach notification but your template says 'without undue delay' — which is the real position?"

**PIA:** Extract the structure as a template. Section headings, depth of analysis, format of risk statements. This becomes the default output format for the pia-generation skill.

### Part 5: Outputs and policy document location (1 min)

> "Two last things — I need to know where to look to keep your policy current."

- **Where do you save completed PIAs, DPA reviews, and triage results?** A folder path
  or shared drive location. This is where the policy-monitor skill will crawl to detect
  when your practice has drifted ahead of your written policy. (This feeds `/policy-monitor` — without this path, the drift sweep only runs in direct-query mode.)
- **Where is the actual privacy policy document?** The one that gets published or shared
  with customers. I'll need to read it to suggest edits when drift is found.
- **Is there a naming convention for output files?** (e.g., `PIA_FeatureName_YYYY-MM-DD`)
  or is it ad hoc?

If outputs aren't saved anywhere yet:
> "That's fine — the policy-monitor skill will still work in direct-query mode
> ('we want to start doing X, does our policy cover it?'). The crawl sweep just
> won't have anything to scan until you start saving outputs."

## Writing the practice profile

```markdown
# Privacy & Data Protection Practice Profile

*Written by the cold-start interview on [DATE]. Edit this file directly.*

---

## Who we are

[Company] is a [B2B SaaS / consumer app / platform / etc.]. We are primarily a
[controller / processor / both] with respect to [whose data]. Data lives in
[regions]. Privacy team is [N] people. [DPO name or "no formal DPO"]. Escalation
goes to [GC / CPO / name].

**Regulatory footprint:** [GDPR / CCPA / HIPAA / etc. — only list what applies]

**Open regulatory matters:** [none / list]

---

## Who's using this

**Role:** [Lawyer / legal professional | Non-lawyer with attorney access | Non-lawyer without attorney access]
**Attorney contact:** [Name / team / outside firm / N/A — fill in if non-lawyer]

---

## Available integrations

| Integration | Status | Fallback if unavailable |
|---|---|---|
| Document storage (Drive / SharePoint) | [✓ / ✗] | Outputs saved locally; policy-monitor sweep runs in direct-query mode only |
| Slack | [✓ / ✗] | Breach / triage notifications delivered inline instead of posted |
| Scheduled tasks | [✓ / ✗] | Policy-monitor sweep runs on demand only |

*Re-check: `/privacy-legal:cold-start-interview --check-integrations`*

---

## DPA playbook

### When we are the processor (customer DPAs)

| Term | Our standard | Fallback | Never |
|---|---|---|---|
| Audit rights | [e.g., SOC 2 Type II annual] | [e.g., virtual audit on 60 days' notice] | [on-site without notice] |
| Breach notification | [e.g., team's standard window from discovery] | [e.g., team's acceptable fallback] | [windows tighter than the team can meet] |
| Subprocessor changes | [e.g., advance notice, customer may object] | [notice only] | [approval required per subprocessor] |
| Data location | [e.g., US + EU selectable] | [follows customer region] | [hard commitment to single DC] |
| Deletion on termination | [e.g., standard days post-termination, certification on request] | [longer window] | [immediate] |
| Liability for data | [e.g., within the MSA cap] | [separate capped carveout] | [uncapped] |

> *From the DPA template:* [any deltas between template and stated positions]

### When we are the controller (vendor DPAs)

| Term | We require | Acceptable | Never accept |
|---|---|---|---|
| [Term] | [what we require] | [what we'll accept] | [what we won't accept] |

### The one thing

[DPA term that's an automatic no]

---

## Privacy policy commitments

*Extracted from [URL / filename] on [date]. If the policy changes, re-run setup
or edit this section.*

**Data categories we say we collect:** [list]
**Purposes we state:** [list]
**Retention commitments:** [what the policy says]
**Third-party disclosures we name:** [list]
**User rights we offer:** [access / delete / port / correct / etc.]

---

## PIA house style

**Trigger:** [what requires a PIA — new data collection, new vendor, etc.]
**Format:** [structure extracted from the seed PIA]
**Depth:** [typical length / detail level]
**Sign-off:** [who approves]

**Template structure (from seed PIA):**
[section headings and rough content of each]

---

## DSAR process

**Volume:** [rough monthly count]
**Handler:** [privacy team / support team / automated]
**Systems to check:** [list of every place user data lives — prod DB, analytics, support tickets, backups, etc.]
**Identity verification method:** [how you confirm the requester is the data subject]
**Response SLA:** [internal SLA target — research the applicable regulatory deadline(s) for each regime in the footprint and cite primary sources before committing]

---

## Escalation

| Issue type | Handle at | Escalate to | When |
|---|---|---|---|
| Routine DSAR | [handler] | [you] | Unusual scope, litigation hold, potential dispute |
| Customer DPA negotiation | [you] | [GC] | Outside fallbacks above |
| PIA for high-risk processing | [you + review committee?] | [GC / DPO] | Biometric, children, automated decisions |
| Regulator contact | — | [GC + you immediately] | Always |
| Suspected breach | — | [Security + you + GC immediately] | Always |

---

## Seed documents

| Doc | Location | Date reviewed | Notes |
|---|---|---|---|
| Privacy policy | [URL] | [date] | [version] |
| DPA template | [path/link] | [date] | |
| Reference PIA | [path/link] | [date] | "[name of product/feature it was for]" |

---

## Outputs

**Outputs folder:** [path where completed PIAs, DPA reviews, and triage results are saved]
**Naming convention:** [file naming pattern, or "ad hoc"]
**Privacy policy document:** [path or URL to the actual published privacy policy]
**Policy last updated:** [date]
**Last policy sweep:** [date of last policy-monitor crawl — updated automatically]

**Work-product header** (prepended to DPA reviews, PIAs, reg-gap analyses, policy-monitor sweeps, and triage outputs):

- If Role is Lawyer / legal professional: `PRIVILEGED & CONFIDENTIAL — ATTORNEY WORK PRODUCT — PREPARED AT THE DIRECTION OF COUNSEL`
- If Role is Non-lawyer: `RESEARCH NOTES — NOT LEGAL ADVICE — REVIEW WITH A LICENSED ATTORNEY BEFORE ACTING`

For externally-facing deliverables (DSAR response letters, regulator responses, client communications) the header is omitted — see the specific skill's instructions. Confirm the correct marking for your jurisdiction and matter before sending.

---

*Re-run: `/privacy-legal:cold-start-interview --redo`*
```

## After writing

**Show what this plugin can do.** Before closing, offer:

> **Want to see what I can help with?**

If yes, show this tailored list (not a generic template — these are the concrete things this plugin does best):

> **Here's what I'm good at in privacy practice:**
>
> - **Review a DPA against your playbook** — e.g., "Auto-detects processor vs. controller; flags deviations from your positions." Try: `/privacy-legal:dpa-review`
> - **Triage a processing activity** — e.g., "PIA, mandatory GDPR DPIA, or proceed — with privacy-policy conflict surfaces." Try: `/privacy-legal:use-case-triage`
> - **Generate a PIA in house format** — e.g., "Structured intake, risk analysis, regulatory classification, recommendation." Try: `/privacy-legal:pia-generation`
> - **Walk through a DSAR** — e.g., "Verify, locate, assess exemptions, draft the response letter." Try: `/privacy-legal:dsar-response`
> - **Diff a new regulation against your policy** — e.g., "Outputs the gap list and a remediation plan with owners and deadlines." Try: `/privacy-legal:reg-gap-analysis`
> - **Sweep for policy drift** — e.g., "Look across saved PIAs, DPA reviews, and triage results to find where the privacy policy no longer matches practice." Try: `/privacy-legal:policy-monitor`
>
> **My suggestion for your first one:** Run `/use-case-triage` on one real processing activity — it's the fastest way to see whether your playbook is capturing the right cuts. Or tell me what's on your plate and I'll pick.

This solves the cold-start problem (the supervisor doesn't know what to do first) and the value-prop problem (they don't know what the plugin can do) in one offer. Make the list specific. Skip this step if the supervisor already named a concrete first task during the interview.


1. **Show the summary.** "Here's what I heard. The DPA playbook is the part to check hardest — did I get your positions right?"

2. **Research connector prompt.** Say:

   > "Before your first DPA review or PIA: connect a research tool. Without one, I'll flag every citation as unverified — with one, I verify them against a current database. In Cowork: Settings → Connectors. In Claude Code: authorize when a skill prompts you."

3. **Propose first tasks:**
   - "Want me to diff your privacy policy against your actual data collection? Sometimes those drift."
   - "Got a customer DPA in the queue I can take a crack at?"
   - If DSAR volume is high: "Want a DSAR response template built from your systems list?"

4. **Flag gaps:** If they couldn't produce a DPA template or a reference PIA, note it: "You're running without a standard DPA — first time a customer asks, you'll be negotiating from scratch. Want to draft one?"

5. **Close with the "you can change anything later" note:**

   > "Your practice profile is at `~/.claude/plugins/config/claude-for-legal/privacy-legal/CLAUDE.md` — a plain text file you can read and edit directly. Anything you answered can be changed:
   >
   > - Edit the file directly for a quick change
   > - Run `/privacy-legal:cold-start-interview --redo` for a full re-interview
   > - Run `/privacy-legal:cold-start-interview --check-integrations` to re-check what's connected
   >
   > The three sections people adjust most: the **DPA playbook** (as you negotiate more and harden positions), the **regulatory footprint** (as the company enters new markets), and the **DSAR response timing and systems list** (as the data landscape changes)."

6. **Your practice profile learns.** End with this note:

   > **Your practice profile learns.** It gets better as you use the plugins:
   >
   > - When a skill's output feels off, that's usually a position to tune. The output will tell you which one.
   > - The `policy-monitor` skill watches for drift between your privacy policy and how you actually practice. When it finds drift, it'll propose edits to match reality.
   > - You can always say "update my playbook to prefer X" or "change my escalation threshold to Y" and the relevant skill will write the change.
   > - Run `/privacy-legal:cold-start-interview --redo <section>` to re-interview one part, or edit the config file directly.
   >
   > Ten minutes of setup gets you a working profile. A month of use gets you one that reads like you wrote it yourself.

## Failure modes

- **Don't assume GDPR applies.** Lots of US-only B2B companies are told they "should probably care about GDPR" — ask whether they actually have EU data subjects.
- **Don't let them skip the controller/processor question.** If they're not sure, walk through it: "When your customer's user data comes into your system, whose privacy policy governs it — yours or the customer's?"
- **Don't write a DPA playbook from generic positions.** If they haven't negotiated many DPAs, say so in the config CLAUDE.md: `[POSITIONS UNTESTED — this team hasn't negotiated many DPAs yet. Treat as starting points, not settled positions.]`
