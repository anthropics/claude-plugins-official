---
name: cold-start-interview
description: >
  Cold-start setup — learns your jurisdictional footprint and escalation rules
  from your handbook and termination memos. Asks which states and countries
  have employees, reads seed documents, and builds a jurisdiction-aware
  escalation table. Use on fresh install, when CLAUDE.md still has
  [PLACEHOLDER] markers, or when re-running with --redo or --check-integrations.
argument-hint: "[--redo | --check-integrations]"
---

# /cold-start-interview

1. Check `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md`. If `--check-integrations`, skip the interview — re-run only the Part 0 `What's connected?` check and rewrite the `## Available integrations` table at that config path. When probing: only report ✓ if an MCP tool call actually succeeded. Configured-but-untested connectors should be marked ⚪ with a one-line how-to for confirming. Never report ✓ based on `.mcp.json` declarations alone — that misleads users into thinking something is wired up when it isn't.
2. Run the interview below (Part 0 first — role + integrations — then footprint): states/countries, hiring/term review triggers, severance practice.
3. Seed docs: handbook + 3 termination memos.
4. Build jurisdiction-specific escalation table.
5. If a populated CLAUDE.md (no `[PLACEHOLDER]` markers) exists at `~/.claude/plugins/cache/claude-for-legal/employment-legal/*/CLAUDE.md` but not at the config path, copy it to the config path and tell the user what was migrated.
6. Write `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md`, creating parent directories as needed.

---

# Cold-Start Interview: Employment Counsel

## Purpose

Employment law is jurisdictional down to the bone. The right answer in Texas is the wrong answer in California. This interview maps your footprint — every state and country with employees — and builds an escalation table that knows which rules apply where.

## Cold-start check

Read `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md`:
- **Does not exist** → start the interview.
- **Contains `<!-- SETUP PAUSED AT: -->`** → greet the user and offer to resume from that section.
- **Contains `[PLACEHOLDER]` markers but no pause comment** → the template was never completed; offer to start fresh or resume from wherever the placeholders begin.
- **Populated (no placeholders, no pause comment)** → already configured; skip unless `--redo`.

The template structure lives at `${CLAUDE_PLUGIN_ROOT}/CLAUDE.md` — use it as the section scaffold. Write the completed practice profile to the config path, creating parent directories as needed. If a CLAUDE.md exists at the old cache path `~/.claude/plugins/cache/claude-for-legal/employment-legal/*/CLAUDE.md` but not here, copy it forward.

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

> **`employment-legal` is for people who handle hiring, terminations, investigations, leave, policies, worker classification, and international expansion.** Not your area? `/legal-builder-hub:related-skills-surfacer`.
>
> **2 minutes** gets you your role, practice setting, and jurisdictional footprint (states + countries with employees), plus working defaults for termination risk flags, severance posture, and handbook policies. **15 minutes** adds your real termination review triggers and high-risk flags extracted from prior memos, offer-letter and severance templates, state-specific handbook supplements, worker-classification defaults, and leave-tracker integration.
>
> Quick or full? (Upgrade any time with `/cold-start-interview --full`.)

**Quick start path:** ask only Part 0 (role, practice setting, integrations) and jurisdictional footprint. Write the config with `[DEFAULT]` markers on everything else. Close with: "Done. You can start using the commands now. I've used sensible defaults for termination risk thresholds, severance posture, and handbook policies. When a skill's output feels off, that's usually a default you should tune — it'll tell you which. Run `/employment-legal:cold-start-interview --full` anytime to do the whole interview, or `/employment-legal:cold-start-interview --redo <section>` to re-do one part."

**Full setup path:** the existing interview flow below. After the user picks, give the fuller orientation described next, then proceed to Part 0.

## After the user picks quick or full

Give the fuller orientation. One paragraph, in your own voice:

> "This plugin maintains: your practice profile (jurisdictional footprint, termination flags, handbook references), a leave register with deadline alerts, and an investigation case file structure. It learns how you actually work — your practice, your risk calibration, your house conventions — and writes that into a plain-text file the plugin reads from every time. Everything you answer can be changed later."

Then the fresh-profile note:

> "Setup builds a fresh professional profile from your answers. It does not read your personal Claude history, other conversations, or your home-directory CLAUDE.md. If I notice relevant information in our conversation context — e.g., you mentioned your firm earlier — I'll ask before using it. Nothing personal gets folded into your practice configuration unless you type it or approve it."

Then: "Ready? A few quick questions first, then we'll go deeper."

**Why this matters** (offer if the user pushes back on the time cost). Every command in this plugin reads from the configuration this interview writes. A generic configuration gives generic output — a default jurisdiction table, a default list of high-risk termination flags, a default escalation matrix, and a review that treats California and Texas the same way. Telling the plugin the actual footprint, the actual hiring and termination triggers, and the actual reporting lines is what makes the difference between "an employment AI tool" and "a tool that knows where your people are and what has bitten you before."

The interview's information comes only from the user's typed answers and documents they explicitly upload. Do not read `~/CLAUDE.md`, personal notes, or any ambient context to fill in practice details. If relevant context is already visible in the conversation (company name, prior mentions), surface it as a question ("I think you mentioned X earlier — should I use that?") before using it.

## Interview pacing

- **Assume the answer exists somewhere.** When a question asks for information that's probably written down somewhere — company description, playbook, escalation matrix, style guide, handbook, jurisdiction list, matter portfolio — prompt for a link or a paste before asking the user to type it from memory. "Paste a link or a doc, or give me the short version" is the default ask for anything that's more than a sentence. An interviewer who makes people re-type what they've already written has failed the first job of an interviewer.
- **Batch size — count subparts.** "Never ask more than 2-3 questions in one turn" means 2-3 *answerable prompts*, counting subparts. One question with 5 subparts is 5 questions. The test: can the user answer without scrolling? If the questions don't fit on one screen, it's too many. Prefer structured tap-through questions where possible — they don't require scrolling or typing.

**Pause for real answers.** Some questions have quick tap-through answers (who's using this, which states). Others need the user to type something, describe something, or upload a document (handbook, term memos, jurisdiction table). When a question needs more than a quick tap:

- **Ask the question and wait.** Say explicitly: "This one needs a typed answer — I'll wait." Do not move to the next question until the user responds.
- **For uploads:** "Paste the contents, share a file path, or say 'skip for now.' If you skip, I'll flag the gap in your configuration so you can fill it later." Then actually wait.
- **Before writing the configuration:** review the interview. List any questions that were skipped or answered with placeholders. Say: "Before I write your configuration, here's what's still open: [list]. Want to fill any of these now, or leave them as placeholders?" Then wait for the answer.
- **Never** write a configuration with silent gaps. Every placeholder should be a deliberate choice the user made to skip, not a question that scrolled past. The LIMITED DATA flag only applies to documents the user chose to skip — not to questions the interview skipped on them.
- **Pause and resume.** Tell the user up front: "If you need to stop, say 'pause' (or 'stop', or 'let me come back to this') and I'll save your progress. Run `/employment-legal:cold-start-interview` again later and I'll pick up where you left off." When the user pauses, write a partial configuration to `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` with a `<!-- SETUP PAUSED AT: [section name] — run /employment-legal:cold-start-interview to resume -->` comment at the top and `[PENDING]` markers (distinct from `[PLACEHOLDER]`) on unanswered fields. When setup re-runs and finds a paused config, greet the user: "Welcome back. You paused at [section]. Your earlier answers are saved. Pick up where we left off, or start over?" Do not re-ask questions already answered.

**Verify user-stated legal facts as they come up in setup.** When the user answers an interview question with a specific rule citation, statute number, case name, deadline, threshold, jurisdiction, or registration number — and it's something you can sanity-check — do the check before writing it into the configuration. If what they said conflicts with your understanding or with something they've pasted, surface it: "You said the threshold is X; my understanding is Y — can you confirm which goes in the profile? `[premise flagged — verify]`" A wrong fact written into CLAUDE.md propagates into every future output; catching it here is one of the highest-leverage moments in the product.

## The interview

### Opening

> Employment law is the practice area where "it depends" is most often the honest answer. I need your map before I can tell you anything useful — where are your people, and what have you already dealt with?

### Part 0: Who's using this, and what's connected

Three quick questions before we get into employment specifics. These shape how the plugin works, not what it can do.

#### Who's using this?

> Who'll be using this plugin day to day? (This feeds the work-product header on every termination memo, handbook draft, and investigation summary — lawyer outputs get the privilege header, non-lawyer outputs get the "research notes, review with counsel" header.)
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

#### Practice setting

> Which of these best describes where you're practicing? (This feeds every skill's escalation framing — in-house gets "loop in GC," solo/small gets "call outside counsel," clinic gets "route to supervising attorney.")
>
> - **Solo / small firm (no hierarchy)** — I'll skip approval-chain questions and ask when you'd loop in a colleague or outside counsel instead.
> - **Midsize / large firm** — I'll ask about your approval chain, billing thresholds, and who signs off above you.
> - **In-house** — I'll ask about your escalation matrix, who the GC/CLO is, and when something goes to the business.
> - **Government / legal aid / clinic** — I'll ask about supervision structure and any restrictions on your practice.
> - **My practice doesn't fit any of these** — say so. I'll adapt.

**Practices that don't fit the boxes.** If the user's practice doesn't match the options above (international arbitration, public international law, amicus-only, academic consulting, pro bono panel, tribal court, military justice, maritime, or anything else the standard categories assume away), offer: "It sounds like your practice doesn't fit my usual categories. Tell me about it in your own words — what you do, who for, what jurisdictions and forums, what the work looks like — and I'll build your profile from that instead of forcing you into boxes that don't fit. I'll skip or adapt the questions that don't apply." Then build the profile from the free-form description, flagging which template fields were filled, adapted, or left empty because they don't apply. A profile built from a forced fit is worse than a sparse profile built from what's actually true.

This one changes how the rest of the interview runs:

- **Solo / small firm (no hierarchy):** Skip or reframe escalation-chain questions later in the interview. Instead of "who approves above your threshold," ask "when do you call in outside counsel or a colleague for a second opinion." Escalation in the practice profile maps to "consult" not "route for approval." The escalation table at the end should have no internal tiers above the user; it lists outside counsel, an insurer, or "no further escalation" instead.
- **Midsize / large firm / in-house:** Ask the escalation question below — reporting line, who approves terminations above severance threshold, who signs off on RIFs, etc.
- **Government / legal aid / clinic:** Route to the supervision model — who reviews work product, what the sign-off chain looks like for client communications, whether a supervising attorney of record is assigned per matter.

**Escalation question (ask after the practice-setting answer, adapted to the branch above):**

> If your team has a shared escalation matrix or delegation-of-authority policy set at the team or department level, that's the one I want — paste it or link it. I'll use it as the baseline and ask about your personal overrides separately.

> "When a review finds something that needs someone more senior to sign off — a termination with discrimination or retaliation risk, an investigation that escalates, a classification call at the edge, an accommodation denial, or a decision that's above your authority — who does that go to? Give me a name or a role (the GC, your boss, the head of HR), or say 'I decide myself.' This is how the plugin knows when to say 'you can handle this' versus 'loop in [X].' (This feeds /termination-review, /worker-classification, /investigation-open, and every other skill's escalation routing.)"

Record the answer in the plugin config as `## Practice setting` (or include in the `## Who we are` section).

#### What's connected?

> This plugin can work with: HRIS (Workday, BambooHR, Rippling, ADP), document storage (Google Drive, SharePoint, Box), and Slack. Let me check which connectors you have configured — features that need them will work, and features that don't have them will fall back to manual gracefully instead of failing silently.

**Check what's actually connected, not what's configured.** A connector listed in `.mcp.json` is *available*. A connector that's actually responding is *connected*. These are different, and confusing them destroys trust. For each connector this plugin uses:

- If you can test the connection (call a simple MCP tool like a list or search), report ✓ only on a successful response.
- If you can't test (no way to probe from here), report ⚪ "configured but not verified — open your MCP settings to confirm" with a one-line how-to.
- Never report ✓ based on configuration alone.

For connectors that show as not connected, tell the user how to connect. Example phrasing: "Box isn't connected. In Claude Cowork: Settings → Connectors → Add → Box → sign in. In Claude Code: add the Box MCP to your config or via `/mcp`. This plugin works without it — you'll paste documents instead of pulling them — but connecting it makes document pulls automatic."

Then report findings in this form:

> - ✓ [Integration] — connected (tested)
> - ⚪ [Integration] — configured but not verified. Open your MCP settings to confirm.
> - ✗ [Integration] — not found. [Feature] will fall back to [manual alternative]. [How to connect.] If you set this up later, re-run `/employment-legal:cold-start-interview --check-integrations`.
>
> You don't need all of these. Core features work with file access alone — leave tracking falls back to a local register if there's no HRIS.

#### Write to the config CLAUDE.md

Write `## Who's using this`, `## Available integrations`, and `## Outputs` sections immediately after the first section of the config-path CLAUDE.md (the plugin config) per the template in `${CLAUDE_PLUGIN_ROOT}/CLAUDE.md`. These drive work-product header choice and feature-fallback behavior across every skill in this plugin.

### Part 1: The footprint (2-3 min)

> **What does [your company] do?** This is the single most important context — a SaaS vendor's playbook, a hardware distributor's playbook, and a services firm's playbook are completely different. You don't have to type it out: paste a link to your company website, your "about" page, your Wikipedia article, or your latest 10-K, and I'll extract what I need. Or give me the one-sentence version: what you sell, to whom, and how (direct sales / channel / marketplace / subscription).

> Before I ask the footprint questions: do you have a jurisdiction table, a state-by-state coverage memo, or a list of active employee locations from your HRIS I can read? Paste the contents, share a file path, or say 'no' and I'll ask the questions one at a time. If you share one, I'll extract the footprint rather than making you list it from memory. (This feeds /wage-hour-qa, /worker-classification, /hiring-review, /termination-review, /policy-drafting — every wage-hour question, worker-classification check, and handbook supplement branches on your jurisdictions.)

If not:

- Every US state with at least one employee. All of them.
- Every country outside the US.
- Remote-first or office-based? (Remote-first means the footprint keeps expanding without anyone telling you.)
- Which state has the most employees? That's your default jurisdiction when the question doesn't specify.

**If the user didn't upload a jurisdiction list:** at the end of this section, offer: "Want me to write this up as a standalone jurisdiction table you can maintain and share? Same footprint data I just captured, in a format that's easier to edit as the company grows."

### Part 2: The review triggers (2-3 min)

> "**Do you want to build your positions now?** It makes the review skills (hiring-review, termination-review, policy-drafting) much better — they'll know your stance and fallbacks instead of generic ones. It takes about 3-4 minutes. Skip if you just want to try the other commands; the review skills will use defaults and tell you when they hit a position you haven't set."

> If your team has a shared playbook, escalation matrix, or delegation-of-authority policy set at the team or department level, that's the one I want — paste it or link it. I'll use it as the baseline and ask about your personal overrides separately.

> Before the questions: do you have a termination checklist, a severance template, an offer-letter template, or an existing review-trigger playbook I can read? Paste the contents, share file paths, or say 'no' and I'll walk through the questions. If you share them, I'll extract the triggers and escalation points rather than making you describe them.

If not:

**Hiring:** When does legal see an offer?
- Every offer? Only exec? Only with restrictive covenants? Never?
- What's in the standard offer letter? Restrictive covenants vary by state — non-competes are unenforceable in California, fine in Florida.

**Termination:** When does legal see a termination?
- Every term? Performance only? RIFs only?
- What's the standard severance — formula, discretionary, none?
- Release required? Always, or only above X severance?

**The high-risk flags:** What makes a termination scary? (This feeds /termination-review — every future termination memo gets checked against these flags before the skill concludes.)
- Recent complaint (harassment, discrimination, whistleblower)
- Recently returned from protected leave
- Protected class + thin documentation
- Anything else that's bitten you before?

**If the user didn't upload a termination checklist or severance template:** at the end of this section, offer: "Want me to write this up as standalone termination-review checklist and high-risk-flag memo you can share? Same content I just captured, formatted so HR partners can read it without a legal decoder."

### Part 3: Seed documents (3-4 min)

**Where does leave data live?**

Before asking for documents, ask one infrastructure question:

> Do you have an HRIS — Workday, BambooHR, Rippling, ADP, or something else — that tracks employee leave? And does legal have read access to it? (This feeds /leave-tracker and /log-leave — with HRIS access, the tracker pulls leaves automatically; without, it runs off a local register you update manually.)

- If HRIS with legal read access: note the system name
- If HRIS without legal access, or no leave tracking module: note "manual"
- If no HRIS: note "manual"

**Seed documents**

> This is the most important part — I want to see how your team actually works, not just what your policies say. I need two things:
>
> 1. **Your handbook.** Current version. I'll read it to know what you've promised employees and where the gaps are. (This feeds /policy-drafting and /hiring-review — every policy draft and offer-letter check gets cross-referenced against what the handbook already commits to.)
>
> 2. **Recent employment documents — the more the better.** Ten is a good floor; twenty gives a much clearer picture. Mix it up: termination memos, offer letters, severance agreements, PIPs, accommodation requests — whatever you have. If you have fewer than ten, share what you can, but flag it. (These feed /termination-review and /hiring-review — the skills extract your house format, severance posture, and high-risk patterns from your actual documents, not a generic template.)

If they have an HRIS or good document visibility: aim for 10-20 documents across the types described above.

If they have poor visibility (scattered folders, no system): accept whatever they can pull. Flag every section of the practice profile built from fewer than 10 documents with [LIMITED DATA — N documents reviewed].

**From the handbook:** Policies with jurisdictional variants (PTO accrual, final pay, leave). State supplements if any. The gaps — things the handbook doesn't cover that it should.

**From the seed documents:** What got checked on terminations. What high-risk flags look like in practice. Offer letter format and standard restrictive covenant language. Severance agreement format for the termination-review skill to match. Any patterns in what the team actually approves vs. what the policies say.

## Build the jurisdiction table

This is the core output. For each state/country in the footprint:

| Jurisdiction | Special rules | Auto-escalate |
|---|---|---|
| California | No non-competes. Final pay due last day (or 72hrs if employee quits w/o notice). Meal/rest break penalties. PAGA exposure. | Any termination. Any restrictive covenant. |
| New York | Pay transparency in postings. NYC has separate rules. Final pay next regular payday. | Exec hires (pay transparency). |
| [etc.] | | |

Don't invent rules for jurisdictions they didn't name. If they have one employee in Montana and no memo ever mentioned Montana, note `[Montana: 1 employee, no history — research on first issue]`.

## Writing the practice profile

Per the template structure at `${CLAUDE_PLUGIN_ROOT}/CLAUDE.md`. Write the completed practice profile to the plugin config, creating parent directories as needed. Key sections: jurisdictional footprint, hiring/termination review triggers, high-risk flags, the jurisdiction-specific escalation table.

## After writing

**Show what this plugin can do.** Before closing, offer:

> **Want to see what I can help with?**

If yes, show this tailored list (not a generic template — these are the concrete things this plugin does best):

> **Here's what I'm good at in employment law practice:**
>
> - **Review an offer letter and restrictive covenants** — e.g., "Jurisdiction check on non-compete enforceability, pay transparency, and required notices." Try: `/employment-legal:hiring-review`
> - **Termination review with risk flags** — e.g., "Severance, release, final pay timing, and high-risk indicators flagged before the decision." Try: `/employment-legal:termination-review`
> - **Classify a worker engagement** — e.g., "Employee / IC / temp / vendor — with misclassification gap analysis." Try: `/employment-legal:worker-classification`
> - **Ask a jurisdiction-aware wage/hour question** — e.g., "Multi-state workforce question routed against the jurisdictions in your footprint." Try: `/employment-legal:wage-hour-qa`
> - **Kick off international expansion** — e.g., "New country on the roadmap — plan the employment-law workstream." Try: `/employment-legal:expansion-kickoff`
> - **Open an internal investigation** — e.g., "Create the privileged workspace, start the log, route interviews." Try: `/employment-legal:investigation-open`
>
> **My suggestion for your first one:** Run `/termination-review` on a hypothetical termination — it's the skill most likely to surface how the risk calibration reads. Or tell me what's on your plate and I'll pick.

This solves the cold-start problem (the supervisor doesn't know what to do first) and the value-prop problem (they don't know what the plugin can do) in one offer. Make the list specific. Skip this step if the supervisor already named a concrete first task during the interview.


- "Here's your jurisdiction table. The California row is the one to double-check."
- "What's the next termination? Let me take a look."
- Flag handbook gaps: "Your handbook doesn't have a remote work policy and you're remote-first. Want one?"
- Check HRIS field: "You said your HRIS is [system] — want me to run the leave tracker now to see if anything is open?"
- If manual leave tracking: "You don't have an HRIS leave module — I'll track leaves in a register file. Use /employment-legal:log-leave to add any leaves that are currently open."

**Before your first review**: connect a research tool. Without one, I'll flag every citation as unverified — with one, I verify them against a current database. In Cowork: Settings → Connectors. In Claude Code: authorize when a skill prompts you.

<!-- COLLATERAL LINKS: when onboarding collateral exists, add here:
     "Want a walkthrough? [Watch the 3-minute intro](URL) or [read the getting-started guide](URL)." -->


### Close with the "you can change anything later" note

After writing the configuration, say:

> "Done. Your configuration is at `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` — a plain text file you can read and edit directly. Anything you answered can be changed:
>
> - Edit the file directly for a quick change
> - Run `/employment-legal:cold-start-interview --redo` for a full re-interview
> - Run `/employment-legal:cold-start-interview --check-integrations` to re-check what's connected
>
> The three settings people adjust most: the **jurisdiction list** (as your footprint grows), the **high-risk termination flags** (as you calibrate what's actually scary vs. what's noise), and the **escalation matrix** (as reporting lines shift)."

## Your practice profile learns

After writing the configuration, close with this note:

> **Your practice profile learns.** It gets better as you use the plugins:
>
> - When a skill's output feels off, that's usually a position to tune. The output will tell you which one.
> - You can always say "update my playbook to prefer X" or "change my escalation threshold to Y" and the relevant skill will write the change.
> - Run `/employment-legal:cold-start-interview --redo <section>` to re-interview one part, or edit the config file directly.
>
> Ten minutes of setup gets you a working profile. A month of use gets you one that reads like you wrote it yourself.
