---
name: reg-feed-watcher
description: Check regulatory feeds now and report what's new since the last check, filtered by your materiality threshold. Use when the user says "check the feeds", "what's new", "regulatory update", when running from the scheduled agent, or when manually pasting a regulatory development for classification and diff.
argument-hint: "[optional: --since DATE]"
---

# /reg-feed-watcher

1. Load `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md` → watchlist, materiality threshold, feed config.
2. Use the workflow below.
3. Pull each feed. Filter by materiality.
4. Output: what's new, categorized by materiality tier.

---

## Purpose

Pull the feeds. Filter by materiality. Output what's left. The filter is the
value — unfiltered feeds are noise.

## Load context

`~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md` → watchlist, materiality threshold, feed configuration, digest output path (if set).

`references/source-catalog.md` (in this skill's directory) → curated catalog of RSS/JSON/HTML sources across US federal, US state, EU/UK, international, and secondary/aggregator categories. Use when configuring new sources or when the user's watchlist has coverage gaps (see Step 0).

## Workflow

### Step 0: Coverage check (before pulling)

Before running the pull, compare the watchlist + feed configuration in CLAUDE.md against `references/source-catalog.md`:

- Which categories (US federal / US state / EU-UK / international) does the user care about per their watchlist?
- Which of those categories have zero or very few sources configured?

If there's an obvious gap — e.g., user watches "EU regulators" in the watchlist but has only `edpb.europa.eu` configured in feeds, missing ICO, CNIL, DPC Ireland — surface it once at the top of the digest:

> **Coverage gap noticed:** Your watchlist includes [category], but only [N] feeds are configured. The source catalog lists [X] options in this category (e.g., [top 2-3 names]). Want me to suggest additions? Run `/regulatory-legal:cold-start-interview --redo` to update, or edit `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md` directly.

Don't nag the same gap repeatedly — if the user has explicitly said "skip state AGs for now," respect that. Note state in CLAUDE.md so it sticks.

### Step 1: Pull

Pull from all configured feed tiers. Every installation has Tier 1. Tiers 2
and 3 are additive — use them if configured, skip if not.

**Tier 1 — Free feeds (always active)**

For each regulator in the watchlist:

- **Federal Register API** (`https://www.federalregister.gov/api/v1/documents`)
  — query by agency slug, date range (since last check), document type. Returns
  structured data: document type, title, abstract, effective date, comment
  deadline (for NPRMs), and citation. Covers all US federal agencies.
- **Direct regulator RSS** — fetch and parse any RSS URLs in ~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md feed
  configuration (SEC, FTC, CFPB, state agencies, EU DPAs, etc.).

Agency slug reference for common watchlist regulators:
| Regulator | API slug |
|---|---|
| FTC | federal-trade-commission |
| SEC | securities-and-exchange-commission |
| CFPB | consumer-financial-protection-bureau |
| CPPA (CA) | RSS only — cppa.ca.gov/feed |
| DOL | labor-department |
| HHS | health-and-human-services-department |
| FCC | federal-communications-commission |

For any regulator not in this list: check federalregister.gov/agencies for the
correct slug, or fall back to direct RSS.

**Tier 2 — Paid feeds (if configured)**

- **TR Regulatory Intelligence MCP:** Query for updates since last check date,
  filtered to watchlist regulators.
- **CourtListener MCP:** Same.

De-duplicate across tiers — the same document may appear in multiple sources.
Prefer the richest source for the enriched output.

**No silent supplement.** If the feed pull returns few or no results for a regulator in the watchlist, report what was found and stop. Do NOT fill the gap from web search or model knowledge without asking. Say: "The feed check returned [N] items from [regulators hit]. Coverage appears thin for [regulator / topic]. Options: (1) broaden the date window, (2) try a different feed or MCP, (3) search the web — results will be tagged `[web search — verify]` and should be checked against the issuing authority's website before relying, or (4) stop here. Which would you like?" A lawyer decides whether to accept lower-confidence sources; Claude does not decide for them.

**Source attribution.** Tag every citation and regulatory item with where it came from: `[Federal Register]`, `[<regulator> RSS]`, `[TR]`, `[CourtListener]`, or the specific MCP tool name for items retrieved via connector; `[web search — verify]` for items from web search; `[model knowledge — verify]` for items surfaced from the model's training data; `[user provided]` for manually-pasted items. Items tagged `verify` carry higher fabrication risk than tool-retrieved items and should be checked first. Never strip or collapse the tags — they are the user's fastest signal about which citations to verify.

**Secondary sources.** Some catalog entries (IAPP, FPF, Hogan Lovells, Covington, Lexology, JD Supra, Artificial Lawyer, LawSites, and similar commentators/aggregators) report on primary regulatory action but are not the primary source. Tag any item pulled from these feeds with `[secondary source]` in addition to the feed-name tag — e.g., `[IAPP Daily Dashboard] [secondary source]`. In the digest, when a secondary-source item describes a regulator action, add a note: "→ Trace to primary: [link to regulator site if known, otherwise 'find on <regulator>.gov before relying']." Do not classify a secondary-source item as "Always material" on its own strength — bump it down a tier until the primary source is located.

**Tier 3 — Manual entry**

If the user has pasted regulatory text or a summary rather than invoking from
a scheduled feed check: treat the pasted content as a single item, skip to
Step 2 for classification, and record source as "manual entry." No feed pull
required. This path works regardless of subscription status.

Record the check timestamp after pulling. Next scheduled run pulls from here
forward.

### Step 2: Classify

Each item gets a materiality tier per `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md`:

| Item type | Match against threshold |
|---|---|
| Final rule | Usually "always material" |
| Proposed rule / NPRM | Usually "review-worthy" — and always log comment deadline |
| ANPR (Advance Notice of Proposed Rulemaking) | Review-worthy for **strategy**, not compliance — no imposed requirements yet, but signals direction and carries a real comment deadline. Log the comment deadline. Route to `/regulatory-legal:policy-diff` only as a pre-positioning analysis, not as a gap-closure diff. |
| RFI (Request for Information) | Same as ANPR — pre-rule, no compliance obligation, but comment deadline is real and direction-signaling is the value. |
| Enforcement action | Sector match → material; related-practice match → review-worthy; neither → FYI or skip |
| Guidance | Review-worthy |
| Speech / blog / statement | FYI or skip per threshold |
| Settlement | Depends — novel theory or big number → review-worthy; routine → skip |

**ANPR / RFI handling — specific.** Pre-rule items are distinct from NPRMs in one important way: they don't change the law, but they do carry comment deadlines and they signal the regulator's direction. Treat them as a separate branch:

- **Do not** classify an ANPR / RFI as "always material" — the compliance impact is zero until a rule issues.
- **Do** classify as review-worthy if any of the issue areas in the notice touch the watchlist's always-material categories (e.g., an ANPR on open banking in a fintech watchlist).
- **Do** log the comment deadline to `~/.claude/plugins/config/claude-for-legal/regulatory-legal/comment-tracker.yaml` with `item_type: ANPR` or `item_type: RFI` so the downstream tracker can distinguish these from compliance gaps.
- **Do** include in the digest entry a line that says explicitly: "Pre-rule. Comment deadline [date]. Route to `/regulatory-legal:policy-diff` only as a pre-positioning analysis (no compliance gap yet)." This primes the policy-diff skill to use its compressed pre-positioning branch rather than a full gap-closure diff.
- **Route to the comment-tracker, not the gap-tracker.** Comment-decision items are not compliance gaps; they belong in the comment tracker, and `gap-surfacer` uses the `comment-decision` `gap_type` (or declines to ingest, if the team routes these separately).

**NPRM comment deadline handling:**

For every NPRM classified at any tier above "skip":
- Extract comment deadline (Federal Register API returns this as structured data)
- If comment tracking is enabled in ~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md: append to `~/.claude/plugins/config/claude-for-legal/regulatory-legal/comment-tracker.yaml`
  with status "undecided" and the default comment decision owner from ~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md
- Include comment deadline in the output entry

### Step 3: Enrich

For each item above FYI tier:

- One-line summary (what changed)
- Why it might matter here (the relevance hook — "this is about [practice you do]")
- Link to source
- Effective date or comment deadline if applicable

Don't summarize FYI items individually — just count them.

## Output

The digest goes into the chat by default. **Also write it to a shareable file** whenever the output contains one or more items above FYI, unless the user's CLAUDE.md explicitly sets `Digest output → chat only`.

**File output behavior:**

1. Look for `Digest output path` in `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md`. If set, write there. Default if unset: `~/regulatory-legal-digests/reg-digest-YYYY-MM-DD.md`.
2. Create parent directories if needed.
3. Write the full digest as Markdown (same content as the chat output, including the work-product header, source tags, and the verify-citations footer).
4. If a file already exists at the path for today, append a new section with a timestamped subheader rather than overwriting — the same day may see multiple runs (morning digest, ad-hoc check).
5. After writing, tell the user: "Digest written to `<path>`. Share as-is, or convert to .docx with Pandoc: `pandoc <path> -o <path>.docx`."
6. If the write fails (permission, missing directory the user didn't authorize creating, disk), fall back to chat-only output and say so — don't silently drop the file request.

Format on disk matches the chat format exactly (below). Markdown renders well in GitHub, Notion, Obsidian, Google Docs (via "Import as Markdown" or Pandoc), and most email clients.

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

## Regulatory Feed Check — [date]

**Period:** [last check] to [now]
**Feeds checked:** [list active tiers — e.g., "Federal Register API, FTC RSS, TR"]
**Items found:** [N] total

### Bottom line

[N gaps need action by [date] — top 3: X, Y, Z]

### 🔴 Always material

**[Regulator] — [Title]**
[One-line summary]. [Relevance hook]. Effective [date].
[Link]
→ Recommend: run policy-diff against [likely affected policy]

[repeat for each]

### 🟡 Review-worthy

**[Regulator] — [Title]**
[One-line]. [Relevance]. [Deadline if any].
[Link]

[NPRMs: include "💬 Comment deadline: [date] — decision pending" if comment tracking enabled]

[repeat]

### 📝 FYI

[N] items — [expandable list of titles + links, no summaries]

---

**Last check updated to:** [timestamp]
**Comment tracker:** [N] NPRMs with open comment decisions — run /regulatory-legal:comments to review

---

**Verify citations before relying on them.** Regulatory citations here were AI-generated and have not been checked against a primary source. Before acting on any rule, guidance, or enforcement action above, confirm it against Westlaw, your firm's research platform, or the issuing authority's website — check accuracy, effective date, and current status. AI-generated regulatory citations are sometimes fabricated, misquoted, or stale. Source tags on each item (e.g., `[Federal Register]`, `[web search — verify]`) show where the citation came from; `verify` tags carry higher fabrication risk and should be checked first.
```

## Config-dependent fallbacks

This skill reads the watchlist, materiality threshold, and feed configuration from `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md`. When a required value is still `[PLACEHOLDER]` or empty, say so in the output — specifically, not generically:

- **Watchlist empty:** stop and say "The watchlist in your configuration is empty. I can't pull feeds without knowing which regulators to watch. Run `/regulatory-legal:cold-start-interview --redo` or edit `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md` and add at least one regulator."
- **Materiality threshold empty:** fall back to the default tiers and append: "This output used the default materiality tiers because your configuration doesn't have custom thresholds set. Tune them with `/regulatory-legal:cold-start-interview --redo` or by editing `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md`."
- **Feed configuration empty:** run Federal Register API only and append: "This output used only the free Federal Register API because your configuration doesn't list direct RSS or paid feeds. Add feeds with `/regulatory-legal:cold-start-interview --redo` or by editing `~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md`."

Say nothing about config when the relevant values are populated.

If nothing above FYI: "All quiet. [N] FYI items, nothing needing attention."

## Handoff

- **To policy-diff:** Any "always material" item with a likely policy impact → offer to run the diff.
- **To gap-surfacer:** If a diff finds a gap → tracked.
- **To comment-tracker:** Any NPRM classified above "skip" → comment deadline logged automatically if tracking is enabled.

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

## What this skill does not do

- Read every item in full. It classifies and enriches; deep reading is for the
  items that survive the filter.
- Change the materiality threshold. If the filter is wrong, edit ~/.claude/plugins/config/claude-for-legal/regulatory-legal/CLAUDE.md.
- Require TR or CourtListener. Free feeds are the baseline; paid feeds add depth.
