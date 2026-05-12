---
name: diligence-issue-extraction
description: >
  Read VDR documents and extract issues per house categories and materiality
  thresholds, producing findings in house memo format. Use when user says
  "review the data room", "extract issues from [folder]", "diligence review",
  "what's in the VDR", or points at VDR documents.
argument-hint: "[VDR folder path or category name]"
---

# /diligence-issue-extraction

1. Load `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md` + `~/.claude/plugins/config/claude-for-legal/corporate-legal/deals/[code]/deal-context.md`.
2. Use the workflow below.
3. Check `ai-tool-handoff` — if category is bulk and tool is configured, hand off first.
4. Read docs, apply materiality filter, extract per category.
5. Findings in house memo format. Hand off consents to closing checklist.

---

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/corporate-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/corporate-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Purpose

The VDR has 2,000 documents. Somewhere in there are the 30 that matter for the deal. This skill reads documents against the diligence categories and materiality thresholds from `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md`, extracts issues, and writes them in house memo format.

## Load context

- `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md` → Diligence structure (categories, materiality thresholds)
- `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md` → Issues memo format (how findings are stated)
- `~/.claude/plugins/config/claude-for-legal/corporate-legal/deals/[code]/deal-context.md` → deal-specific thresholds, VDR location

If deal-context.md doesn't exist, ask which deal this is for.

## Workflow

### Step 1: Inventory the VDR

If VDR MCP (Box/Intralinks/Datasite) is connected, pull the index. Map VDR folders to diligence request list categories. Note gaps — request list categories with no corresponding VDR content.

```markdown
## VDR Inventory: [Deal code]

| Request category | VDR folder | Docs | Status |
|---|---|---|---|
| Corporate & Organizational | /01-Corporate | 45 | Reviewed |
| Material Contracts | /02-Contracts | 312 | In progress |
| IP | /03-IP | 89 | Not started |
| [etc.] | | | |

**Gaps:** [Request categories with no VDR content — follow-up request needed]
```

### Step 2: Apply materiality filter

Per `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md` / deal-context thresholds. Don't review everything if the threshold says contracts >$X.

For contracts specifically: sort by stated value (if in filename/metadata) or by counterparty significance. Review top-down until you hit the threshold or the category is exhausted.

### Step 3: Extract issues

For each document read, check against the standard diligence concerns for its category:

**Material contracts — standard extraction set:**
- Change of control provision (triggered by this deal? consent required?)
- Assignment restriction (can the contract move to buyer?)
- Exclusivity / non-compete (restricts buyer's business?)
- MFN (most favored nation — pricing constraints)
- Termination rights (can counterparty walk because of the deal?)
- Unusual indemnities or liability exposure

**Corporate — standard extraction set:**
- Cap table accuracy, outstanding options/warrants
- Board consent requirements for the transaction
- Stockholder agreement restrictions (drags, tags, ROFR)
- Subsidiary structure and intercompany arrangements

**IP — standard extraction set:**
- Ownership chain (assignments from founders/employees in place?)
- Open source in the product (copyleft risk)
- Key IP licensed vs. owned
- Pending or threatened IP litigation

**Employment — standard extraction set:**
- Change-of-control severance triggers (parachute cost)
- Key employee retention risk
- Pending employment litigation
- Classification risk (contractors who look like employees)

**Litigation — standard extraction set:**
- Pending matters and reserves
- Threatened claims
- Regulatory inquiries
- Pattern litigation (consumer class actions, etc.)

### Step 4: State each finding

> **Source attribution.** Where a finding references a statute, regulation, case, or regulator action — e.g., a change-of-control provision analyzed under an applicable law, an IP ownership gap cited against a specific doctrine, a pending litigation matter with a case citation — tag the citation with where it came from: `[Westlaw]`, `[CourtListener]`, or the MCP tool name for citations retrieved from a legal research connector; `[web search — verify]` for web-search citations; `[model knowledge — verify]` for citations recalled from training data; `[user provided]` for citations from the VDR, deal-team memos, or outside-counsel feedback. Document-source citations (VDR path, Bates, filename) retain their native reference. Citations tagged `verify` carry higher fabrication risk and should be checked first. Never strip or collapse the tags.
>
> **When disagreeing with a user's cited statute, quote the text or decline to characterize it.** If the user (or a deal-team note, or a sell-side disclosure) cites a statute for a proposition you don't think is correct, and you don't have the statute text available from a connected research tool or the VDR, do not invent a description of what the statute says. Say instead: "That section doesn't match what I'd expect a [bulk-sales notice / successor-liability / whatever] requirement to say — I'd need to pull the actual text to tell you what it actually covers. `[statute unretrieved — verify]`" Then either (a) retrieve the text via the configured research tool and quote it, (b) ask the user to paste the text, or (c) flag for outside counsel. A confident wrong description of a real statute is worse than "I don't know" — a deal-team memo citing a fabricated subchapter is harder to un-believe than a gap. Applies in every skill that characterizes a statute, not just issue extraction.
>
> **No silent supplement.** If a research query to the configured legal research tool returns few or no results for a legal basis the finding needs (e.g., the rule governing a change-of-control consent requirement, an IP assignment doctrine, an employment classification test), report what was found and stop. Do NOT fill the gap from web search or model knowledge without asking. Say: "The search returned [N] results from [tool]. Coverage appears thin for [rule / doctrine]. Options: (1) broaden the search query, (2) try a different research tool, (3) search the web — results will be tagged `[web search — verify]` and should be checked against a primary source before relying, or (4) flag as unverified and stop. Which would you like?" A lawyer decides whether to accept lower-confidence sources.

Per the finding template in `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md`. If the seed memo used this:

```
Issue #N: [Title]
Category: [request list category]
Severity: [level per house scheme]
Documents: [VDR path + doc name]
Finding: [what the document says and why it matters]
Recommendation: [price adjustment / indemnity / consent required / rep & warranty / walk]
```

...then use exactly that. If the seed memo was bullets, write bullets.

**Severity calibration** (if house scheme is R/Y/G):
- 🔴 **Red:** Affects deal value or structure. Change of control requiring major customer consent. Undisclosed material litigation. IP ownership gap.
- 🟡 **Yellow:** Needs attention, solvable. Consent required but likely obtainable. Open source requiring remediation. Employment classification risk.
- 🟢 **Green:** Noted for file. Consistent with reps. No action needed beyond the rep.

### Step 5: Assemble per category

Group findings by request list category. Within category, sort by severity.

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

> This output is derived from VDR materials that are privileged, confidential, or both. It inherits the source's privilege and confidentiality status — distribution beyond the privilege circle can waive privilege. Store with the matter's privileged files and make distribution decisions deliberately.

# Diligence Issues: [Deal code] — [Category]

**Documents reviewed:** [N] of [M] in category
**Coverage:** [All | >$X threshold | Top N]
**Findings:** [N]🔴 [N]🟡 [N]🟢

---

### Bottom line

[🔴 N blocking · 🟠 N high · 🟡 N medium] — [the one thing the deal team needs to know]

---

[Each finding in house format]

---

## Gaps

- [Request list item with no responsive document]
- [Document referenced but not in VDR]
```

## Handoffs

- **To ai-tool-handoff:** If Luminance/Kira is in use per `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md`, hand bulk contract review there. This skill handles the nuanced documents (side letters, amendments, anything the AI tool struggles with).
- **To deal-team-summary:** Aggregated findings feed the deal team brief.
- **To material-contract-schedule:** Contract-level extractions feed the disclosure schedule.
- **To closing-checklist:** Any finding that implies a discrete pre-closing action becomes a checklist item. The handoff is not limited to third-party consents — it also covers:
  - **Shareholder vote / other closing action** — §280G cleansing votes, required stockholder consents, required board resolutions, appraisal-rights notice periods, conversion mechanics, or any other corporate approval the deal needs to close. Characterize the action, the approval threshold, the statutory or charter source, and the timing constraint.
  - **Regulatory filings and approvals** — HSR, CFIUS, foreign-investment review, sector-specific approvals flagged during extraction.
  - **Consents from counterparties** — change-of-control, anti-assignment, MFN-triggering consents.
  - **Releases, terminations, or pay-offs** — employment releases tied to change-of-control, payoff letters, lien releases.
  - **Escrow / holdback mechanics** — if extraction surfaces an indemnity escrow, R&W insurance deliverable, or holdback tied to a specific issue.
  Every finding with a pre-closing action tag should reach closing-checklist, not just the ones labeled "consent." If a finding sits in the gray zone (might need a closing action, might be a post-closing covenant), hand it off with a flag — closing-checklist can drop it if the purchase agreement says otherwise. Under-handoff is a one-way door; over-handoff is corrected in review.


**Successor liability.** Flag: pending or threatened tort/products-liability claims, environmental matters and cleanup obligations, bulk-sale/fraudulent-transfer exposure (is the seller retaining enough assets to pay its remaining creditors?), seller's post-closing dissolution plan (if seller dissolves, plaintiffs chase the buyer), and whether the purchase agreement has an assumed/excluded-liabilities schedule that actually covers the known exposures. Even in asset deals, the "de facto merger," "mere continuation," and "product line" doctrines can transfer liability — this is the analysis that surprises buy-side clients who think they're buying assets clean.

## Batch processing

For large categories (300 contracts), process in batches. After each batch, update the running issues list and flag anything 🔴 immediately — don't wait for the full category to surface a deal-affecting issue.

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

If the extraction surfaced more than ~10 issues, or any time the user asks: offer the dashboard (see CLAUDE.md `## Outputs → Dashboard offer for data-heavy outputs`). Shape the offer for this output — counts by severity (🔴 / 🟠 / 🟡 / 🟢), counts by house category, and a sortable grid of issues with materiality, category, and VDR source.

## What this skill does not do

- It doesn't make the materiality call on close cases. It applies the threshold; a human decides the borderline.
- It doesn't negotiate reps and warranties. It produces the findings that inform them.
- It doesn't replace bulk AI review. For high-volume clause extraction, hand off to Luminance/Kira per `~/.claude/plugins/config/claude-for-legal/corporate-legal/CLAUDE.md`. This skill is for the judgment layer.
