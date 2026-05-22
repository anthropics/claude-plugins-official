---
name: cold-start-interview
description: Cold-start interview — builds your watchlist, indexes the policy library, and learns your materiality threshold so the monitor surfaces signal instead of noise. Use on fresh install, when reconfiguring (--redo), or when re-checking what connectors are actually responding (--check-integrations).
argument-hint: "[--redo | --check-integrations]"
---

# /cold-start-interview

1. Check `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md`. If a populated CLAUDE.md (no `[PLACEHOLDER]` markers) exists at `~/.claude/plugins/cache/claude-for-legal/regulatory-legal/*/CLAUDE.md` but not at the config path, copy it to the config path and tell the user what was migrated. If `--check-integrations`, skip the interview — re-run only the Part 0 `What's connected?` check and rewrite the `## Available integrations` table in `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md`.
2. Use the interview workflow below. Interview (Part 0 first — role + integrations — then watchlist): which regulators, where policies live, what's material.
3. Connect policy folder. Index policies.
4. Write `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md` (creating parent directories as needed) with watchlist + materiality threshold.

When probing integrations: only report ✓ if an MCP tool call actually succeeded. Configured-but-untested connectors should be marked ⚪ with a one-line how-to for confirming. Never report ✓ based on `.mcp.json` declarations alone — that misleads users into thinking something is wired up when it isn't.

---

## Purpose

Every regulator publishes constantly. Most of it doesn't matter to you. This interview learns which regulators to watch and — critically — what "material" means here, so the monitor surfaces signal instead of noise.

## Cold-start check

Read `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md`:
- **Does not exist** → start the interview.
- **Contains `<!-- SETUP PAUSED AT: -->`** → greet the user and offer to resume from that section.
- **Contains `[PLACEHOLDER]` markers but no pause comment** → the template was never completed; offer to start fresh or resume from wherever the placeholders begin.
- **Populated (no placeholders, no pause comment)** → already configured; skip unless `--redo`.

The template structure lives at `${CLAUDE_PLUGIN_ROOT}/CLAUDE.md` — use it as the section scaffold. Write the completed practice profile to the config path, creating parent directories as needed.

If a CLAUDE.md exists at the old cache path `~/.claude/plugins/cache/claude-for-legal/regulatory-legal/*/CLAUDE.md` but not at the config path, copy it forward.

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

> **`regulatory-legal` is for people who track regulatory developments, assess policy gaps, and manage compliance obligations.** Not your area? `/legal-builder-hub:related-skills-surfacer`.
>
> **2 minutes** gets you your role, practice setting, and primary regulatory regime. **15 minutes** adds your full watchlist, materiality thresholds, feed cadence, policy library index, and comment-period sources.
>
> Quick or full? (Upgrade any time with `/regulatory-legal:cold-start-interview --full`.)

Do not read the user's home-directory `~/CLAUDE.md`, `~/user.md`, or other personal memory to pre-populate the interview. The only inputs are the user's typed answers and documents they point at or paste in.

## After the user picks quick or full

Once the user has picked, orient them. Cover, in your own voice:

- **What this plugin maintains:** your practice profile (watchlist, materiality thresholds, feed cadence), a gap tracker, a policy diff archive, and a comment-period calendar.
- **What this setup does:** learns which regulators you actually watch, what "material" means to you, and where your policies live, and writes it into a plain-text file the plugin reads from every time. Everything answered can be changed later. Once it's done, the plugin's commands will work the way the user works, not the way a generic template does.
- **Data sources:** setup builds a fresh professional profile from the user's answers only. It does not read the user's personal Claude history, other conversations, or home-directory CLAUDE.md. If something relevant came up earlier in this conversation (for example, the user mentioned a regulator or their sector), ask before using it. Nothing gets folded into the configuration unless the user types it or approves it.

**Why this matters.** Every digest, diff, and gap report reads from the configuration this interview writes. A generic configuration gives generic output — a default watchlist, a default materiality threshold, and a digest that treats every agency speech like an enforcement action. Telling the plugin which regulators the user actually watches and what "material" means here is what makes the difference between "a regulatory AI tool" and "a tool that sends signal instead of noise." The more specific the answers, the quieter and more useful the digests will be.

## Interview pacing

- **Assume the answer exists somewhere.** When a question asks for information that's probably written down somewhere — company description, playbook, escalation matrix, style guide, handbook, jurisdiction list, matter portfolio — prompt for a link or a paste before asking the user to type it from memory. "Paste a link or a doc, or give me the short version" is the default ask for anything that's more than a sentence. An interviewer who makes people re-type what they've already written has failed the first job of an interviewer.
- **Batch size — count subparts.** "Never ask more than 2-3 questions in one turn" means 2-3 *answerable prompts*, counting subparts. One question with 5 subparts is 5 questions. The test: can the user answer without scrolling? If the questions don't fit on one screen, it's too many. Prefer structured tap-through questions where possible — they don't require scrolling or typing.

**Pause for real answers.** Some questions have quick tap-through answers. Others need the user to type a list (which regulators), describe calibration judgments, or point you at a policy folder. When a question needs more than a quick tap:

- **Ask the question and wait.** Say it plainly: "This one needs a typed answer — I'll wait." Don't queue the next question until they respond.
- **For uploads or path pointers (policy folder, existing watchlist, feed URLs):** "Paste the contents, share a file path, or say 'skip for now.' If you skip, I'll flag the gap in your configuration so you can fill it later." Then actually wait.
- **Before writing the practice profile:** review the interview. List every question that was skipped or answered with a placeholder. Say: "Before I write your configuration, here's what's still open: [list]. Want to fill any of these now, or leave them as placeholders?" Wait for the answer before writing.
- **Never** write the practice profile with silent gaps. Every placeholder should be a deliberate user choice to skip, not a question that scrolled past unanswered.
- **Pause and resume.** Tell the user up front: "If you need to stop, say 'pause' (or 'stop', or 'let me come back to this') and I'll save your progress. Run `/regulatory-legal:cold-start-interview` again later and I'll pick up where you left off." When the user pauses, write a partial configuration to `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md` with a `<!-- SETUP PAUSED AT: [section name] — run /regulatory-legal:cold-start-interview to resume -->` comment at the top and `[PENDING]` markers (distinct from `[PLACEHOLDER]`) on unanswered fields. When setup re-runs and finds a paused config, greet the user: "Welcome back. You paused at [section]. Your earlier answers are saved. Pick up where we left off, or start over?" Do not re-ask questions already answered.

**Verify user-stated legal facts as they come up in setup.** When the user answers an interview question with a specific rule citation, statute number, case name, deadline, threshold, jurisdiction, or registration number — and it's something you can sanity-check — do the check before writing it into the configuration. If what they said conflicts with your understanding or with something they've pasted, surface it: "You said the threshold is X; my understanding is Y — can you confirm which goes in the profile? `[premise flagged — verify]`" A wrong fact written into CLAUDE.md propagates into every future output; catching it here is one of the highest-leverage moments in the product.

## The interview

### Opening

> I'm going to watch your regulators and tell you when something moves. But "something moves" happens daily. I need to know what actually matters to you so I'm not crying wolf.

### Quick start or full setup — branching

The user picked quick or full in the preamble. Branch:

**Quick start path:** ask only Part 0 (role, practice setting, integrations) and watchlist scope. Write the config with `[DEFAULT]` markers on everything else. Close with: "Done. You can start using the commands now. I've used sensible defaults for materiality threshold, digest cadence, and policy library structure. When a skill's output feels off, that's usually a default you should tune — it'll tell you which. Run `/regulatory-legal:cold-start-interview --full` anytime to do the whole interview, or `/regulatory-legal:cold-start-interview --redo <section>` to re-do one part."

**Full setup path:** the existing interview flow below.

### Part 0: Who's using this, and what's connected

Two quick questions before we get into regulatory specifics. These shape how the plugin works, not what it can do.

#### Who's using this?

> Who'll be using this plugin day to day? (This feeds every skill's work-product header and output framing — lawyer gets "ATTORNEY WORK PRODUCT," non-lawyer gets research framing and attorney-review checkpoints before regulator-facing steps.)
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

> If you need to find a lawyer: your professional regulator's referral service is the fastest starting point (state bar in the US; SRA/Bar Standards Board in England & Wales; Law Society in Scotland/NI/Ireland/Canada/Australia; or your jurisdiction's equivalent). Many offer free or low-cost initial consultations. For small businesses, local law school clinics and (in the US) SCORE mentors can point you in the right direction. For individuals, legal aid organizations cover many practice areas.

#### What's connected?

> This plugin can work with: regulatory feed subscriptions, document storage (Google Drive, SharePoint, Box), and Slack. Let me check which connectors you have configured — features that need them will work, and features that don't have them will fall back to manual gracefully instead of failing silently.

**Check what's actually connected, not what's configured.** A connector listed in `.mcp.json` is *available*. A connector that's actually responding is *connected*. These are different, and confusing them destroys trust. For each connector this plugin uses:

- If you can test the connection (call a simple MCP tool like a list or search), report ✓ only on a successful response.
- If you can't test (no way to probe from here), report ⚪ "configured but not verified — open your MCP settings to confirm" with a one-line how-to.
- Never report ✓ based on configuration alone.

The Federal Register API is a free public endpoint and is always available — it does not require an MCP connector.

For connectors that show as not connected, tell the user how to connect. Example phrasing: "[Feed provider] isn't connected. In Claude Cowork: Settings → Connectors → Add → [provider] → sign in. In Claude Code: add the provider's MCP to your config or via `/mcp`. This plugin works without it — Federal Register + manual paste covers US federal coverage — but connecting it adds enrichment and alert import."

Then report findings in this form:

> - ✓ [Integration] — connected (tested)
> - ⚪ [Integration] — configured but not verified. Open your MCP settings to confirm.
> - ✗ [Integration] — not found. [Feature] will fall back to [manual alternative]. [How to connect.]

You don't need all of these. Core features work with free feeds (Federal Register API) and file access alone. Paid feeds add enrichment; manual paste-in always works. If you set something up later, re-run `/regulatory-legal:cold-start-interview --check-integrations`.

#### Write to the config

Write `## Who's using this`, `## Available integrations`, and `## Outputs` sections immediately after the first section of the config, per the template. The `## Outputs` section already exists — merge into it so the work-product header becomes conditional on role.

#### Practice setting

> One more quick one before the watchlist:
>
> What's the setting? (This shapes the gap-response process and escalation entries — in-house asks about GC routing, solo maps "escalate" to "consult outside counsel," clinic routes to supervising attorney.)
>
> - **Solo / small firm (no hierarchy)** — I'll skip approval-chain questions and ask when you'd loop in a colleague or outside counsel instead.
> - **Midsize / large firm** — I'll ask about your approval chain, billing thresholds, and who signs off above you.
> - **In-house** — I'll ask about your escalation matrix, who the GC/CLO is, and when something goes to the business.
> - **Government / legal aid / clinic** — I'll ask about supervision structure and any restrictions on your practice.
> - **My practice doesn't fit any of these** — say so. I'll adapt.

**Practices that don't fit the boxes.** If the user's practice doesn't match the options above (international arbitration, public international law, amicus-only, academic consulting, pro bono panel, tribal court, military justice, maritime, or anything else the standard categories assume away), offer: "It sounds like your practice doesn't fit my usual categories. Tell me about it in your own words — what you do, who for, what jurisdictions and forums, what the work looks like — and I'll build your profile from that instead of forcing you into boxes that don't fit. I'll skip or adapt the questions that don't apply." Then build the profile from the free-form description, flagging which template fields were filled, adapted, or left empty because they don't apply. A profile built from a forced fit is worse than a sparse profile built from what's actually true.

Use this to shape the gap-response process and the escalation entries in the practice profile:

- **Solo / small firm (no hierarchy):** Skip escalation-chain questions. Reframe: instead of "who approves a material gap response," ask "when do you pull in outside counsel or a colleague for a second opinion." The practice profile's escalation field maps to *consult* not *route for approval*.
- **Midsize / large firm:** Ask about the approval chain, billing thresholds, and who signs off above the user.
- **In-house:** Ask about the escalation matrix, who the GC/CLO is, and when something goes to the business.
- **Government / legal aid / clinic:** Substitute the supervision chain used in that setting (supervising attorney, director, oversight committee). Keep the structure, relabel the roles.

Then ask the escalation question in plain English:

> "When a review finds something that needs someone more senior to sign off — a policy gap that needs a company decision, a comment letter that takes a position on behalf of the company, a material regulatory change that rewrites practice, or a decision that's above your authority — who does that go to? Give me a name or a role (the GC, the CCO, your boss), or say 'I decide myself.' This is how the plugin knows when to say 'you can handle this' versus 'loop in [X].'"

Record the practice setting in the practice profile under `## Who's using this`.

### Part 1: The watchlist (2-3 min)

*(This feeds `/regulatory-legal:reg-feed-watcher` and the `reg-change-monitor` agent — the feed only pulls from regulators on this list. Anything not on the list is invisible to the plugin until you paste it in via `/regulatory-legal:policy-diff`.)*

**What does [your company] do?** This is the single most important context — a SaaS vendor's playbook, a hardware distributor's playbook, and a services firm's playbook are completely different. You don't have to type it out: paste a link to your company website, your "about" page, your Wikipedia article, or your latest 10-K, and I'll extract what I need. Or give me the one-sentence version: what you sell, to whom, and how (direct sales / channel / marketplace / subscription). This also tells me which regulators are even plausibly in your watchlist.

> Before I ask: do you already have a watchlist, a regulatory-tracking spreadsheet, or a prior gap-analysis memo I can read? Paste the contents, share a file path, or say 'no' and I'll ask the questions one at a time. If you share one, I'll extract the regulators and materiality criteria rather than making you list them again.

If not:

- Which regulators? Name them. (FTC, SEC, CFPB, state AGs, CPPA, EU DPAs, sector-specific?)
  *Coverage note: this plugin has structured feed support for US federal agencies (Federal Register API), SEC, FTC, and CFPB. State regulators and EU DPAs are supported via user-provided RSS URLs or manual entry — there is no automatic feed for those. Non-US regulators outside the EU DPA table require manual entry or user-provided feeds.*
- Why each one? ("We're a fintech, CFPB is obvious" vs. "FTC because of the consent decree")
- Any you're *not* watching that maybe you should be?

**If the user didn't upload a watchlist or prior gap analysis:** at the end of this section, offer: "Want me to write this up as a standalone watchlist memo you can share and maintain? Same content I just captured — your regulators, why you watch each, and the feeds behind them — in a format you can circulate or hand to a new hire."

### Part 2: Materiality (the key question) (3-4 min)

*(This feeds `/regulatory-legal:reg-feed-watcher` and the `reg-change-monitor` agent — your materiality threshold is the filter that decides whether a new development shows up immediately, in the weekly digest, or not at all. Wrong calibration here = noisy digests you stop reading.)*

Walk through examples. For each, would you want to know immediately, in a weekly digest, or not at all?

- A final rule from one of your regulators
- A proposed rule (NPRM) — comment period open
- An enforcement action against a company in your sector
- An enforcement action against a company *not* in your sector but for something you do
- A speech by a commissioner signaling priorities
- A blog post from the agency
- A settlement with no admission of wrongdoing
- New guidance (sub-regulatory, not binding)

This builds the materiality threshold. Different companies calibrate very differently — a company under a consent decree cares about speeches; a company the agency has never heard of can ignore them.

**If the user didn't upload materiality criteria:** at the end of this section, offer: "Want me to write this materiality rubric up as a standalone doc you can share and maintain? Same content I just captured — immediate vs. digest vs. FYI, with your examples — so the team reads the same calibration."

### Part 3: The policy library (2-3 min)

*(This feeds `/regulatory-legal:policy-diff` and `/regulatory-legal:gaps` — every incoming regulatory change is diffed against this library to find which policies it touches and who owns them.)*

> Before I ask: do you have an existing policy library index — a spreadsheet, a table of contents, a wiki page — mapping each policy to its owner? Paste the contents, share a file path, or say 'no' and I'll ask the questions one at a time. If you share one, I'll import it rather than making you rebuild it from memory.

If not:

> Point me at your policy folder. I'll index what's there so when a reg changes, I can tell you which of your policies it touches.

- Where do policies live? (Drive, SharePoint, Confluence, Notion)
- Is there a naming convention or index, or just files?
- Who owns which policy? (For routing gaps to the right person)

**If the user didn't upload a policy index:** at the end of this section, offer: "Want me to write this up as a standalone policy-ownership index you can share and maintain? Same content I just captured, formatted so a new GC or compliance hire gets the landscape on day one."

### Part 4: Feed sources (2-3 min)

Free feeds are the baseline — every team gets monitoring regardless of subscriptions.
Paid feeds add enrichment for teams that have them.

**Step 1: Map free feeds for the named watchlist**

The Federal Register API (federalregister.gov/api) is the stable primary source for US federal agencies — it returns structured data by agency, document type, effective date, and comment deadlines. Use it as the default for any federal regulator in the watchlist.

For every other named regulator (state AGs, the CPPA (California), EU DPAs, sector-specific regulators, non-US regulators), ask the user for their preferred feed URL, or direct them to the agency's website to find the current feed. Feed URLs change; don't rely on a cached list.

If a named regulator has no known free feed: flag it, ask the user how they currently track that regulator, and record the manual-entry fallback (see below).

**Step 2: Ask about paid subscriptions (additive, not required)**

- Paid regulatory feed subscription? Which provider, and which alerts are configured?
- CourtListener? Which trackers?

If yes: configure as enrichment layer on top of free feeds. If no: free feeds are sufficient to proceed.

**Step 3: Manual entry fallback**

> If you ever see something in Law360, a newsletter, or from outside counsel that you want to run through the system — just paste it in and I'll diff it against your policies and track any gaps. You don't need a feed subscription for that to work.

Record in the config that manual entry is enabled.

**Step 4: Comment period tracking** *(This feeds `/regulatory-legal:comments` — the comment-period calendar logs deadlines and surfaces decisions when a comment window opens.)*

> When I see a proposed rule (NPRM) from your watchlist, I'll automatically log the comment deadline. Do you want me to flag these so you can decide whether to file a comment?

If yes: comment-tracker is enabled. Record the default owner for comment decisions in the config.

## Writing the practice profile

Per the template. Key: the materiality threshold table.

```markdown
## Materiality threshold

**Always material (alert immediately):**
- Final rule from [specific regulators]
- Enforcement action in our sector
- Anything mentioning [company name]

**Review-worthy (weekly digest):**
- Proposed rules from watched regulators
- Enforcement action outside sector but related to our practices
- New guidance documents

**FYI (monthly roundup or not at all):**
- Speeches, blog posts, academic commentary
- Settlements with no novel theory
```

## Feed configuration block (add to the config)

```markdown
## Feed configuration

**Free feeds (always active):**
| Regulator | Source | URL/method |
|---|---|---|
| [name] | Federal Register API / RSS / manual | [endpoint or "manual entry"] |

**Paid feeds (if configured):**
| Service | Subscription | Alerts |
|---|---|---|
| [Paid feed provider] | [yes/no] | [alert names] |
| CourtListener | [yes/no] | [tracker names] |

**Manual entry:** Enabled — paste any regulatory development to trigger diff + gap tracking.

**Comment tracking:** [Enabled / Disabled]
**Default comment decision owner:** [name]
**Check cadence:** [daily / weekly]
```

## After writing

**Show what this plugin can do.** Before closing, offer:

> **Want to see what I can help with?**

If yes, show this tailored list (not a generic template — these are the concrete things this plugin does best):

> **Here's what I'm good at in regulatory practice:**
>
> - **Check regulatory feeds for what's new** — e.g., "Filtered digest of rulemaking, guidance, and enforcement against your watchlist." Try: `/regulatory-legal:reg-feed-watcher`
> - **Diff a regulatory change against your policy library** — e.g., "See exactly which internal policies a new rule impacts and what needs updating." Try: `/regulatory-legal:policy-diff`
> - **Open gaps tracker** — e.g., "What's flagged and not yet closed across your portfolio, with owner and deadline." Try: `/regulatory-legal:gaps`
> - **Track NPRM comment periods** — e.g., "What's open, comment deadlines, and a decision log on whether to file." Try: `/regulatory-legal:comments`
>
> **My suggestion for your first one:** Run `/regulatory-legal:reg-feed-watcher` — it tells you immediately whether the feeds are calibrated to your materiality threshold. Or tell me what's on your plate and I'll pick.

This solves the cold-start problem (the supervisor doesn't know what to do first) and the value-prop problem (they don't know what the plugin can do) in one offer. Make the list specific. Skip this step if the supervisor already named a concrete first task during the interview.


- "Here's the watchlist and the threshold. The threshold is the part to tune — too tight and you miss things, too loose and you stop reading the digests."
- Offer to index the policy library now.
- Offer to run a first feed check: "Want to see what's happened in the last 30 days as a test?"
- **Before your first digest or gap check, connect a research tool.** Say: "Before your first digest or gap check: connect a research tool. Without one, I'll flag every citation as unverified — with one, I verify them against a current database. In Cowork: Settings → Connectors. In Claude Code: authorize when a skill prompts you."

<!-- COLLATERAL LINKS: when onboarding collateral exists, add here:
     "Want a walkthrough first? [Watch the 3-minute intro](URL) or [read the getting-started guide](URL)." -->

- Close with the changeability note:

  > "Done. Your configuration is at `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md` — a plain-text file you can read and edit directly. Anything you answered can be changed:
  >
  > - Edit the file directly for a quick change
  > - Run `/regulatory-legal:cold-start-interview --redo` for a full re-interview
  > - Run `/regulatory-legal:cold-start-interview --check-integrations` to re-check what's connected
  >
  > The settings people tune most often: the watchlist (which regulators you actually care about), the materiality threshold (what's immediate vs. digest vs. FYI), and the check cadence. Your configuration will improve as you use the plugin — when a digest feels off (too noisy, too quiet), the fix is usually here."

## Your practice profile learns

After writing the practice profile, close with this note:

> **Your practice profile learns.** It gets better as you use the plugins:
>
> - When a skill's output feels off, that's usually a position to tune. The output will tell you which one.
> - The `reg-change-monitor` agent watches the regulatory feeds; when a change matches something in your policy library, it flags it for a gap-check.
> - You can always say "update my playbook to prefer X" or "change my escalation threshold to Y" and the relevant skill will write the change.
> - Run `/regulatory-legal:cold-start-interview --redo <section>` to re-interview one part, or edit the config file directly.
>
> Ten minutes of setup gets you a working profile. A month of use gets you one that reads like you wrote it yourself.
