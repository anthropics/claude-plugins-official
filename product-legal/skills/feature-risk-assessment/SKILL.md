---
name: feature-risk-assessment
description: >
  Deeper risk assessment for a single feature or product area when the launch
  review found something that needs more than a line item. Structured analysis:
  what could go wrong, how likely, how bad, what mitigates it. Use when user
  says "deep dive on this risk", "risk assessment for [feature]", "what could
  go wrong with", or when launch-review flags a novel issue.
---

# Feature Risk Assessment

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/product-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/product-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Purpose

The launch review is broad. This is deep. When a single issue needs more than a table row — a novel AI feature, a children's product, something a regulator is actively looking at — this skill produces a standalone assessment.

Not every launch needs one. Most don't. This is for the 10% where "PIA done, shipped" isn't the right level of scrutiny.

## When to run this

- Launch review found a pattern that's **not in the calibration table** (novel)
- Launch review found something in the **"usually blocks"** category
- GC or leadership asked "what's the risk here" and wants more than a one-liner
- The feature is in an area with **active regulatory attention** (AI, children, biometric, health)
- Someone outside legal is worried and a structured answer would help

If none of the above, the launch review is enough. Don't generate paperwork for its own sake.

## Structure

### 1. What we're assessing

One paragraph. What the feature does, what's new about it, why it got escalated to a full assessment.

### 2. The risks

For each distinct risk (aim for 2-5, not 15):

```markdown
### Risk [N]: [Short name]

**Scenario:** [What would have to happen for this to go wrong. Be specific —
not "data breach" but "the recommendation algo surfaces a user's sensitive
category interest to someone who shouldn't see it because X."]

**Who gets hurt:** [Users? The company? A third party? Specific.]

**How likely:** [Low / Medium / High — with a reason. "Low — would require
both X and Y to fail simultaneously." Not just a vibes rating.]

**How bad if it happens:** [Low / Medium / High — with a reason. "High —
regulatory fine + class action exposure + press" vs. "Low — one angry
tweet, no actual harm."]

**Existing mitigations:** [What already reduces the likelihood or impact]

**Gap:** [What's missing, if anything]

**Residual risk:** [After existing mitigations — is this acceptable or does
it need more?]
```

### 3. Regulatory landscape (if relevant)

Only include if a regulator is actively interested in this space. If so:

- Which regulator, what they've said/done recently
- How this feature would look to them
- Whether we'd rather they hear about it from us or from a headline

### 4. Precedent (if any)

Has another company done something similar? What happened?

- If nothing bad happened → useful, not dispositive
- If something bad happened → what was different about their situation, does it apply here

Don't overweight precedent. Regulators change priorities; one company getting away with something doesn't mean the next one will.

### 5. Options

Present 2-3 realistic paths:

```markdown
| Option | Description | Risk reduction | Cost |
|---|---|---|---|
| A: Ship as designed | [current plan] | None | None |
| B: Ship with [mitigation] | [change] | [how much] | [eng effort, timeline, UX] |
| C: Don't ship [component] | [scope cut] | [how much] | [product impact] |
```

### 6. Recommendation

Pick one. Explain why. Acknowledge what you're trading off.

```markdown
**Recommended: Option [X]**

[Why. What risk remains. Why that's acceptable. Who accepts it.]

**If the answer is "not my call":** [Who decides, what they need to know]
```

## Calibration check

Before finalizing, check against `~/.claude/plugins/config/claude-for-legal/product-legal/CLAUDE.md` → Risk calibration:

- Is this risk assessment calibrated to *this company*, or is it generic?
- A risk that's "High" at a company under a consent decree might be "Medium" at one that isn't
- The assessment should reflect the actual regulatory posture, litigation history, and risk appetite captured in the practice profile

## Handoffs

- **To AI governance:** If the deep-dive was triggered by an AI feature — which
  it often is — run `/ai-governance-legal:aia-generation [feature]` in parallel or
  immediately after. The feature risk assessment frames the decision; the AIA
  documents the AI system specifically in the format AI governance needs. They're
  not duplicates: the FRA is a product-legal decision doc; the AIA is the
  governance record.
- **To privacy:** If the feature involves new data collection or processing,
  run `/privacy-legal:pia-generation [feature]`. The FRA's risk section
  will likely overlap with the PIA's — flag that overlap so work isn't duplicated,
  but both docs need to exist.
- **To AI governance vendor review:** If the feature uses a new AI vendor,
  run `/ai-governance-legal:vendor-ai-review [vendor agreement]` if not already done
  during the launch review.

## Output format

Standalone doc, 2-4 pages. Prepend the work-product header from `~/.claude/plugins/config/claude-for-legal/product-legal/CLAUDE.md` `## Outputs` (it differs by user role — see `## Who's using this`).

Not a slide deck, not a memo to file — a decision document someone reads and then decides.

Save where `~/.claude/plugins/config/claude-for-legal/product-legal/CLAUDE.md` → Launch review process says review docs go. If the doc is going to be shared with anyone outside the privileged loop (e.g., posted to a broadly-shared ticket), drop the work-product header only for that externally-facing copy and keep the privileged original in the matter file.

## Citation check

If the assessment cites cases, statutes, regulations, or enforcement actions — in the Regulatory landscape or Precedent sections especially — those citations were generated by an AI model and have not been verified against a primary source. Before the decision document goes to a decisionmaker, verify each citation against a legal research tool (Westlaw, CourtListener, or your firm's research platform) for accuracy, good law status, and current enforcement posture. A risk assessment built on a fabricated enforcement action is worse than no assessment.

> **No silent supplement.** If a research query to the configured legal research tool returns few or no results for the regime or precedent the assessment needs, report what was found and stop. Do NOT fill the gap from web search or model knowledge without asking. Say: "The search returned [N] results from [tool]. Coverage appears thin for [regime / precedent]. Options: (1) broaden the search query, (2) try a different research tool, (3) search the web — results will be tagged `[web search — verify]` and should be checked against the issuing authority before relying, or (4) flag as unverified and stop. Which would you like?" A lawyer decides whether to accept lower-confidence sources.
>
> **Source attribution.** Tag every citation in the Regulatory landscape and Precedent sections with where it came from: `[Westlaw]`, `[CourtListener]`, `[regulator site]`, or the MCP tool name for citations retrieved from a legal research connector; `[web search — verify]` for web-search citations; `[model knowledge — verify]` for citations recalled from training data; `[user provided]` for citations from the feature team. Citations tagged `verify` carry higher fabrication risk and should be checked first. Never strip or collapse the tags — the decisionmaker needs to see which citations to verify first.

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

## What this skill does not do

- It doesn't assess every feature. Most features get a launch review and that's it.
- It doesn't make the decision. It frames the decision. Someone with authority picks an option.
- It doesn't do quantitative risk modeling. If the company has a formal risk framework with numbers, use that — this is qualitative.
