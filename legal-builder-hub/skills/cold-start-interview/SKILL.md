---
name: cold-start-interview
description: >
  Practice-profile interview that recommends and installs a starter pack of
  community legal skills. This IS the cold start for the whole ecosystem — it
  asks what kind of lawyer you are and recommends what to install first. Use
  on fresh install, when the user says "get me started" or "what should I
  install", or to re-run the integration-availability check after adding or
  removing an MCP connector.
argument-hint: "[--redo] [--check-integrations]"
---

# /cold-start-interview

1. Check `~/.claude/plugins/config/claude-for-legal/legal-builder-hub/CLAUDE.md`. If a populated CLAUDE.md (no `[PLACEHOLDER]` markers) exists at `~/.claude/plugins/cache/claude-for-legal/legal-builder-hub/*/CLAUDE.md` but not at the config path, copy it to the config path and tell the user what was migrated.
2. Run Part 0 (role + integration check), then the five questions (practice type, industry, team, tooling comfort), per the workflow below.
3. Match profile to registry skills. Recommend starter pack.
4. Show each recommended skill's SKILL.md summary. User picks.
5. Install picked skills. Write `~/.claude/plugins/config/claude-for-legal/legal-builder-hub/CLAUDE.md` (creating parent directories as needed) with `## Who's using this`, `## Available integrations`, profile + installed list.

**`--check-integrations`:** Re-run only the Part 0 integration-availability check. Updates the `## Available integrations` table in `~/.claude/plugins/config/claude-for-legal/legal-builder-hub/CLAUDE.md` without touching the role or practice profile. Use this after adding or removing an MCP connector.

When probing: only report ✓ if an MCP tool call actually succeeded. Configured-but-untested connectors should be marked ⚪ with a one-line how-to for confirming. Never report ✓ based on `.mcp.json` declarations alone — that misleads users into thinking something is wired up when it isn't.

---

## Cold-start check

Read `~/.claude/plugins/config/claude-for-legal/legal-builder-hub/CLAUDE.md`:
- **Does not exist** → start the interview.
- **Contains `<!-- SETUP PAUSED AT: -->`** → greet the user and offer to resume from that section.
- **Contains `[PLACEHOLDER]` markers but no pause comment** → the template was never completed; offer to start fresh or resume from wherever the placeholders begin.
- **Populated (no placeholders, no pause comment)** → already configured; skip unless `--redo`.

The template structure lives at `${CLAUDE_PLUGIN_ROOT}/CLAUDE.md` — use it as the section scaffold. Write the completed practice profile to the config path, creating parent directories as needed. If a CLAUDE.md exists at the old cache path `~/.claude/plugins/cache/claude-for-legal/legal-builder-hub/*/CLAUDE.md` but not here, copy it forward.

## Check for the shared company profile

Look for `~/.claude/plugins/config/claude-for-legal/company-profile.md`.

- **If it exists:** Read it. Show a one-line confirmation: "You're [name], [practice setting], at [company], [industry], operating in [jurisdictions]. Right? (Or say 'update' to change the shared profile.)" If confirmed, skip the company questions — go straight to the plugin-specific ones.
- **If it doesn't exist:** You'll be the first plugin this user set up. After the orientation and fork, ask the company questions and write them to the shared profile (per the template at `references/company-profile-template.md` in the plugin root), then continue with the plugin-specific questions. Tell the user: "I've saved your company profile — the other legal plugins will read it and skip these questions."

The company questions that belong in the shared profile (and should NOT be re-asked if it exists): practice setting, company name, industry, what-you-sell, size, jurisdictions, regulators, risk appetite, escalation names. The plugin-specific questions (playbook positions, review framework, house style, supervision model, etc.) stay per-plugin.

## Purpose

This plugin is the app store. The cold-start interview is the onboarding recommendation engine — asks what you do, recommends a starter pack, installs what you pick.

Unlike the other cold-starts, this one is short. Five questions, a recommendation, done.

## Install scope check

Before the orientation, if you notice the working directory is inside a project (not the user's home directory), flag it. Say once:

> **Heads up — it looks like this plugin may be project-scoped, which means I can only read files in [current directory]. If you'll want me to read documents from elsewhere (Downloads, Documents, Dropbox), install user-scoped instead — see QUICKSTART.md. You can continue with project scope, but you'll need to move files into this folder.**

Ask the user to confirm before proceeding: continue with project scope, or pause to reinstall user-scoped. If the working directory *is* the user's home directory, skip this check silently.

## Before the interview starts

Show this preamble first (3-4 short lines, nothing more):

> **`legal-builder-hub` is for finding, installing, and managing community-contributed legal skills.** Looking for a practice-area workflow? Install one of the `legal-*` plugins directly; run `/legal-builder-hub:registry-browser` to see what's out there.
>
> **2 minutes** gets you role and practice area(s) — plus working defaults for registry watchlist, update cadence, and a permissive-by-default allowlist. **15 minutes** adds a calibrated starter pack matched to your practice, a trusted-sources policy written to `allowlist.yaml` (registries, publishers, licenses seeded from your deployment context), update notification preferences, and your industry/team-size signal for recommendations.
>
> Quick or full? (Upgrade any time with `/legal-builder-hub:cold-start-interview --full`.)

## After the user picks quick or full

Once the user has picked, orient them. Cover, in your own voice:

- **What this plugin maintains:** your practice profile (trusted sources, update preferences, deployment context), an `allowlist.yaml` that gates installs, and an install log.
- **What this setup does:** helps the user discover, install, and evaluate community legal skills — a practice-profile-driven starter pack plus a design-quality check before anything touches their workflow. Learns the practice profile and update preferences and writes them into a plain-text file the plugin reads from every time. Everything can be changed later.
- **Data sources:** setup builds a fresh practice profile from the user's answers only. It does not read personal Claude history, other conversations, or the home-directory CLAUDE.md. If something relevant came up earlier in this conversation (e.g., the user mentioned their firm or team), ask before folding it in. Nothing gets added to configuration unless the user types or approves it.

**Why this matters.** The hub's starter-pack recommendation and the auto-updater's filtering both read from the profile this interview writes. A generic profile gets a generic starter pack — skills that are plausibly useful but not matched to the user's actual practice. Telling the hub what kind of lawyer the user is and what they do most is what makes the difference between "here are all the skills other lawyers have built" and "here's the set that matches your work." The more specific the answers, the more the recommendations will feel like the user's own.

### Quick start or full setup — branching

The user picked quick or full in the preamble. Branch:

**Quick start path:** ask only role and practice area(s). Write the config with `[DEFAULT]` markers on everything else. Close with: "Done. You can start browsing and installing now. I've used sensible defaults for registry watchlist and update cadence. Run `/legal-builder-hub:cold-start-interview --full` anytime to do the whole interview, or `/legal-builder-hub:cold-start-interview --redo <section>` to re-do one part."

**Full setup path:** the existing interview flow below.

## Interview pacing

- **Assume the answer exists somewhere.** When a question asks for information that's probably written down somewhere — company description, playbook, escalation matrix, style guide, handbook, jurisdiction list, matter portfolio — prompt for a link or a paste before asking the user to type it from memory. "Paste a link or a doc, or give me the short version" is the default ask for anything that's more than a sentence. An interviewer who makes people re-type what they've already written has failed the first job of an interviewer.

Short as this interview is, the five questions vary — practice area and industry are tap-through, but "what's the thing you do most" needs a real answer. When a question needs more than a quick tap:

- **Ask the question and wait.** Say explicitly: "This one needs a typed answer — I'll wait." Do not move to the next question until the user responds.
- **If anything gets skipped:** "Skip for now and I'll flag it in your profile — you can fill it in with `--redo` later." Then move on, but track the skip.
- **Before writing the profile and recommending a starter pack:** if any answer was skipped or left as a placeholder, list them and ask: "Want to fill any of these now, or leave them as placeholders? Your starter-pack recommendation is only as good as the profile." Then wait.
- **Never** write the profile with silent gaps — every placeholder should be a deliberate skip the user confirmed.
- **Batch size — count subparts.** "Never ask more than 2-3 questions in one turn" means 2-3 *answerable prompts*, counting subparts. One question with 5 subparts is 5 questions. The test: can the user answer without scrolling? If the questions don't fit on one screen, it's too many. Prefer structured tap-through questions where possible — they don't require scrolling or typing.
- **Pause and resume.** Tell the user up front: "If you need to stop, say 'pause' (or 'stop', or 'let me come back to this') and I'll save your progress. Run `/legal-builder-hub:cold-start-interview` again later and I'll pick up where you left off." When the user pauses, write a partial configuration to `~/.claude/plugins/config/claude-for-legal/legal-builder-hub/CLAUDE.md` with a `<!-- SETUP PAUSED AT: [section name] — run /legal-builder-hub:cold-start-interview to resume -->` comment at the top and `[PENDING]` markers (distinct from `[PLACEHOLDER]`) on unanswered fields. When setup re-runs and finds a paused config, greet the user: "Welcome back. You paused at [section]. Your earlier answers are saved. Pick up where we left off, or start over?" Do not re-ask questions already answered.

**Verify user-stated legal facts as they come up in setup.** When the user answers an interview question with a specific rule citation, statute number, case name, deadline, threshold, jurisdiction, or registration number — and it's something you can sanity-check — do the check before writing it into the configuration. If what they said conflicts with your understanding or with something they've pasted, surface it: "You said the threshold is X; my understanding is Y — can you confirm which goes in the profile? `[premise flagged — verify]`" A wrong fact written into CLAUDE.md propagates into every future output; catching it here is one of the highest-leverage moments in the product.

## The interview

### Opening

> I'll help you find and install community legal skills — things other lawyers have built and shared. First, what kind of lawyer are you? I'll recommend a starting pack.

### Part 0: Who's using this, and what's connected

Two quick questions before the practice profile. These shape how the plugin works, not what it can do.

#### Who's using this?

> Who'll be using this plugin day to day? (This feeds the Role signal carried across every plugin you install — skills with non-lawyer mode read from here instead of re-asking, and the `recommend` and `qa` outputs structure for non-lawyer readers when appropriate.)
>
> 1. **Lawyer or legal professional** — attorney, paralegal, legal ops working under attorney oversight.
> 2. **Non-lawyer with attorney access** — founder, business lead, contracts manager, HR, procurement; you have an in-house or outside attorney you can consult.
> 3. **Non-lawyer without regular attorney access** — you're handling this yourself.

If the answer is 2 or 3, say this once:

> This plugin discovers and installs skills. Skills you install will have their own guardrails based on your role — I'll carry your answer here forward so you don't have to answer it per plugin.

If the answer is 3, add:

> If you need to find an attorney, solicitor, barrister, or other authorised legal professional: your professional regulator's referral service is the fastest starting point (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent). Many offer free or low-cost initial consultations. For small businesses, local law school clinics and SCORE mentors can point you in the right direction. For individuals, legal aid organizations cover many practice areas.

#### What's connected?

> This plugin can work with: Slack (for new-skill / update notifications). Let me check which connectors you have configured — features that need them will work, and features that don't have them will fall back to manual gracefully instead of failing silently.

**Check what's actually connected, not what's configured.** A connector listed in `.mcp.json` is *available*. A connector that's actually responding is *connected*. These are different, and confusing them destroys trust. For each connector this plugin uses:

- If you can test the connection (call a simple MCP tool like a list or search), report ✓ only on a successful response.
- If you can't test (no way to probe from here), report ⚪ "configured but not verified — open your MCP settings to confirm" with a one-line how-to.
- Never report ✓ based on configuration alone.

For connectors that show as not connected, tell the user how to connect. Example phrasing: "Slack isn't connected. In Claude Cowork: Settings → Connectors → Add → Slack → sign in. In Claude Code: add the Slack MCP to your config or via `/mcp`. This plugin works without it — update notifications surface on next `/legal-builder-hub:registry-browser` or `/legal-builder-hub:auto-updater` instead of proactively — but connecting it makes notifications real-time."

Then report findings in this form:

> - ✓ [Integration] — connected (tested)
> - ⚪ [Integration] — configured but not verified. Open your MCP settings to confirm.
> - ✗ [Integration] — not found. [Feature] will fall back to [manual alternative]. [How to connect.]

You don't need this. Core features — browse, install, QA, update — work with file access alone.

Write Part 0 answers to the plugin config under `## Who's using this` and `## Available integrations`. This plugin writes `## Who's using this` so other plugins installed afterward can read the role from here instead of re-asking.

Before the five questions: "Do you already have a list of community-skill registries you watch, or an allowlist / blocklist of skill sources your team uses? Paste the contents, share a file path, or say 'no' and I'll add the default. If you share one, I'll read it and add those registries plus your allowlist to the profile rather than making you re-type them. (This feeds /legal-builder-hub:skill-installer — the installer reads `allowlist.yaml` before fetching anything, and blocks any source that isn't on the list in restrictive mode.)"

**Deployment context.** After the allowlist question and before writing the file, ask:

> "How are you going to use the skills you install — just for yourself, shared across your firm, or embedded in a product or service you ship to others? (Personal / Firm-internal / Product-embedding.) (This feeds `allowlist.yaml` — the deployment context seeds the `licenses:` list, and /legal-builder-hub:skill-installer refuses to fetch any skill under a license not on that list.) This sets your license defaults. Most open source licenses are fine for personal use. Firm-internal adds file-level copyleft (LGPL, MPL — fine when you're not distributing). Product-embedding is the strict one: strong copyleft (GPL, AGPL) creates obligations that need legal review before you ship, so those get flagged rather than defaulted."

Record the answer in the profile under `## Sources I trust` as `Deployment context: [personal | firm-internal | product-embedding]`. The allowlist's `licenses:` seeding below reads from it.

**Write the allowlist to `allowlist.yaml`, not just the profile.** The installer's gate reads from `~/.claude/plugins/config/claude-for-legal/legal-builder-hub/allowlist.yaml`, not from CLAUDE.md. If you only record the answer in the profile, the installer sees an empty allowlist and falls back to permissive regardless of what the user said — silently defeating the headline structural defense. After this question:

1. Write `allowlist.yaml` at the config path, following the schema in `skill-installer/references/allowlist.md`:
   - `mode:` — the template default is `restrictive` (fail-closed). Offer `permissive` for Solo/small firm (they don't have IT-curated publisher lists, so restrictive mode would refuse everything). Keep `restrictive` for Midsize/large firm, In-house, or Government (those have security policies that want a firm gate). Always confirm: "I'm setting the allowlist to [mode]. Restrictive refuses unknown sources until you add them — safest, but you'll need to approve each new publisher. Permissive flags unknown sources and asks you before installing — more convenient, less strict. Which do you want?" Never write permissive without explicit user consent.
   - `registries:` — what the user provided plus the default.
   - `publishers:` — GitHub owners/orgs the user named or that own the trusted registries.
   - `connectors:` — empty unless the user provided a list; in restrictive mode, prompt: "Restrictive mode needs a connector allowlist — paste approved MCP server URLs, or I'll leave it empty and skills declaring any connector will be refused."
   - `licenses:` — seed based on the deployment-context answer above:
     - **Personal** → `MIT`, `Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`, `ISC`, `CC0-1.0`.
     - **Firm-internal** → same as Personal plus `LGPL-2.1-only`, `LGPL-3.0-only`, `MPL-2.0`.
     - **Product-embedding** → same as Personal. Also write a top-of-file comment in `allowlist.yaml`: `## License review required before shipping — anything not on this list needs legal sign-off.` Strong copyleft (GPL, AGPL) is deliberately excluded from the default here; adding those requires a deliberate edit.
2. Also summarize in the profile's `## Sources I trust` section so a human can see the policy.
3. Tell the user where it lives: "Your allowlist is at `~/.claude/plugins/config/claude-for-legal/legal-builder-hub/allowlist.yaml`. The installer reads it before fetching anything."

If the user uploads a registry/allowlist file: read it, extract the registry URLs and allowlist/blocklist entries, confirm what you found, write `allowlist.yaml` per the schema, and summarize in the profile.

**Freshness reminders.** After the allowlist question (deployment context is set) and before the five questions, ask:

> "When a community skill bundles reference material — regulations, statutes, procedural templates — how long should it be trusted before I remind you to verify it's still current? (6 months is a common default for regulatory content. 12 months for procedural/stylistic content. Set it tighter if you work in a fast-moving area.)"

Accept either a single number (apply to regulatory; use the category defaults below for the others) or per-category answers. Validate each answer shapes to `N days`, `N months`, or `N years` with `N` a positive integer ≤ 120 — reject free-form prose and re-ask.

Write the answer to a `## Freshness reminders` section in the profile (insert after `## Sources I trust` and before `## Installed starter pack`):

```markdown
## Freshness reminders

| Content category | Max age before reminder | Rationale |
|---|---|---|
| regulatory | 6 months | Regulators update frequently; enforcement priorities shift |
| procedural | 12 months | Court rules and procedures change slower |
| stylistic | 24 months | House style, formatting templates |
| unknown | 3 months | A skill that doesn't declare freshness is treated cautiously |

When a skill's `last_verified` + `freshness_window` is past, or the user's threshold (above) is past — whichever is tighter — the skill-installer surfaces a warning before running.
```

If the user gave tighter numbers, write those in place of the defaults. If the user said "use defaults," write the table as shown.

**If the user didn't upload a registry list:** after the five questions, offer: "Want me to write your watched registries and update preferences up as a standalone policy note you can share with your team? Same content I'm saving to your profile, formatted so teammates or a new builder can see which sources you trust and how you want updates handled."

### The five questions

1. **Practice area** — In-house or firm? Commercial, privacy, product, employment, litigation, M&A, something else? (This feeds /legal-builder-hub:related-skills-surfacer — the practice area is the primary key that maps to the starter pack.)

   **Practices that don't fit the boxes.** If the user's practice doesn't match the options (international arbitration, public international law, amicus-only, academic consulting, pro bono panel, tribal court, military justice, maritime, or anything else the standard categories assume away), offer: "It sounds like your practice doesn't fit my usual categories. Tell me about it in your own words — what you do, who for, what jurisdictions and forums, what the work looks like — and I'll build your profile from that instead of forcing you into boxes that don't fit. I'll skip or adapt the questions that don't apply." Then build the profile from the free-form description, flagging which template fields were filled, adapted, or left empty because they don't apply. A profile built from a forced fit is worse than a sparse profile built from what's actually true.

2. **Industry** — Tech, healthcare, finance, other, doesn't matter? (This feeds /legal-builder-hub:related-skills-surfacer and /legal-builder-hub:registry-browser — industry narrows the starter pack and filters registry results.)

3. **Team size** — Solo, small team (2-5), large legal department? (This feeds the `allowlist.yaml` mode default — Solo/small gets permissive, Midsize/large/In-house/Government gets restrictive.)

4. **What's the thing you do most?** — Contract review, compliance, launch reviews, deal support, brief writing, etc. (This feeds /legal-builder-hub:related-skills-surfacer — the surfacer nudges you when you're doing something the community has a skill for.)

5. **Tooling comfort** — Builder (you write your own skills), tinkerer (you edit what's installed), just-make-it-work (you want it to work out of the box)? (This feeds /legal-builder-hub:related-skills-surfacer — builders get the raw registries and /legal-builder-hub:skills-qa framework; just-make-it-work gets a curated, working pack.)

### Recommend

Map the profile to registry skills:

| Profile | Starter pack |
|---|---|
| In-house commercial, tech | commercial-legal plugin + lpm-skills (matter intake, scope control) |
| Privacy counsel | privacy-legal plugin + any community DPA/PIA skills |
| Product counsel | product-legal plugin + community marketing-review skills |
| Firm litigation | litigation-legal plugin + lpm-skills (matter planning, budget) |
| Solo / small team | Everything lightweight — triage skills over full review skills |
| Builder | the raw registries and the skills-qa framework — they'll build and validate their own |

For each recommended skill: show the SKILL.md description. Let them pick — don't install anything without a yes.

## Writing the practice profile

Short. Profile + installed list + registry prefs. Per the template at `${CLAUDE_PLUGIN_ROOT}/CLAUDE.md`.

## After writing

**Show what this plugin can do.** Before closing, offer:

> **Want to see what I can help with?**

If yes, show this tailored list (not a generic template — these are the concrete things this plugin does best):

> **Here's what I'm good at in legal skill management:**
>
> - **Browse community legal skills** — e.g., "See what other practitioners have built for your practice area." Try: `/legal-builder-hub:registry-browser`
> - **Install a skill from a registry** — e.g., "Add a community skill to your environment — license-gated and allowlist-checked before it runs." Try: `/legal-builder-hub:skill-installer`
> - **Check for updates** — e.g., "See which installed skills have newer versions in their source registry." Try: `/legal-builder-hub:auto-updater`
> - **Get skill recommendations** — e.g., "Based on recent activity in your other plugins, surface skills worth trying." Try: `/legal-builder-hub:related-skills-surfacer`
> - **Evaluate a skill against the design framework** — e.g., "Run the Legal Skill Design Framework on a skill — nine design parameters, three failure modes, a trust-surface check." Try: `/legal-builder-hub:skills-qa`
>
> **My suggestion for your first one:** Browse the registry and pick one skill that matches a current project — install it and see how the allowlist gate feels. Or tell me what's on your plate and I'll pick.

This solves the cold-start problem (the supervisor doesn't know what to do first) and the value-prop problem (they don't know what the plugin can do) in one offer. Make the list specific. Skip this step if the supervisor already named a concrete first task during the interview.


- "Here's what I installed. Want to see what else is in the registries?"
- "The related-skills-surfacer will nudge you when you're doing something the community has a skill for. Want that on or off?"
- **Before the first installed skill that cites authority, connect a research tool.** Say: "Before the first installed skill that cites authority: connect a research tool if one of the installed plugins needs it. Without one, skills will flag every citation as unverified. In Cowork: Settings → Connectors. In Claude Code: authorize when a skill prompts you."

<!-- COLLATERAL LINKS: when onboarding collateral exists, add here:
     "Want a walkthrough first? [Watch the 3-minute intro](URL) or [read the getting-started guide](URL)." -->

Then close with the "you can change anything later" note:

> Done. Your configuration is at `~/.claude/plugins/config/claude-for-legal/legal-builder-hub/CLAUDE.md` — a plain text file you can read and edit directly. Anything you answered can be changed:
>
> - Edit the file directly for a quick change
> - Run `/legal-builder-hub:cold-start-interview --redo` for a full re-interview
> - Run `/legal-builder-hub:cold-start-interview --check-integrations` to re-check what's connected
>
> The things most commonly tweaked later: your watched registries (add or drop sources), your update preference (notify vs. manual), and the scope of your practice profile (add an industry or a second practice type as your work shifts). Your configuration will improve as you use the plugin — if recommendations feel off, the profile is usually the fix.

## Your practice profile learns

After writing the practice profile, close with this note:

> **Your practice profile learns.** It gets better as you use the plugins:
>
> - When a skill's output feels off, that's usually a position to tune. The output will tell you which one.
> - You can always say "update my playbook to prefer X" or "change my escalation threshold to Y" and the relevant skill will write the change.
> - Run `/legal-builder-hub:cold-start-interview --redo <section>` to re-interview one part, or edit the config file directly.
>
> Ten minutes of setup gets you a working profile. A month of use gets you one that reads like you wrote it yourself.

## Registries watched by default

- **lpm-skills** (github.com/legalopsconsulting/lpm-skills) — legal project management, practice-area agnostic
- User can add others via `/legal-builder-hub:registry-browser`
