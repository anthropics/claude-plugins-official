---
name: marketing-claims-review
description: >
  Review marketing copy for claims that need substantiation, reframing, or cutting.
  Use when the user says "review this marketing copy", "check these claims",
  "can we say this", "is this puffery or a problem", or pastes marketing content
  (landing pages, emails, ads, taglines).
argument-hint: "[paste copy, or file path]"
---

# /marketing-claims-review

1. Load `~/.claude/plugins/config/claude-for-legal/product-legal/CLAUDE.md` → Marketing claims standards.
2. Apply the claim taxonomy and review workflow below.
3. Extract every claim. Classify: puffery / factual / comparative / implied / absolute.
4. For each non-puffery claim: substantiation check, suggested fix.
5. Output: claim-by-claim with calls, suggested revision if short enough.

```
/product-legal:marketing-claims-review
[paste landing page copy]
```

---

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/product-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/product-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Purpose

Marketing wants to say the product is the best. Legal needs it to be true, or at least not provably false. This skill finds the claims that will get a demand letter from a competitor or an inquiry from a regulator, and suggests how to keep the energy while fixing the exposure.

## Load standards

Read `~/.claude/plugins/config/claude-for-legal/product-legal/CLAUDE.md` → `## Marketing claims`:
- Comparative claims policy (allowed with substantiation / discouraged / never)
- Substantiation standard (what's required before a claim ships)
- Common rejected claims (learn from history)

## Research the applicable standards before clearing copy

Research the currently operative advertising and substantiation standards for the applicable jurisdictions and media (for example, FTC, NAD, state UDAP regimes, sector regulators for healthcare / financial / children's products, and platform-specific policies). Identify what substantiation the *specific claim* requires — who measured it, when, sample size, apples-to-apples basis — not just whether *some* substantiation exists on file. Flag implied claims and comparative claims for heightened scrutiny. Verify currency: endorsement and review guides have been updated recently and continue to evolve. Cite primary sources with pinpoint references. If you cannot verify the current standard, flag for attorney verification — do not state a rule you haven't confirmed.

> **Only cite the standards that apply to the specific claims under review.** A blanket list of every FTC guideline, NAD practice note, or sector rule makes the load-bearing ones invisible. Do not cite the Endorsement Guides (16 CFR Part 255) unless the copy contains an endorsement, testimonial, or influencer content. Do not cite disclosure-overlay rules unless a claim in the asset triggers the overlay. Do not cite a sector regulator unless the copy targets or implicates that sector. A standard earns its place in the output by mapping to a specific quoted claim; otherwise drop it.

> **No silent supplement.** If a research query to the configured legal research tool returns few or no results for the applicable standard (FTC rule, NAD decision, state UDAP, sector rule, platform policy), report what was found and stop. Do NOT fill the gap from web search or model knowledge without asking. Say: "The search returned [N] results from [tool]. Coverage appears thin for [standard / jurisdiction]. Options: (1) broaden the search query, (2) try a different research tool, (3) search the web — results will be tagged `[web search — verify]` and should be checked against the issuing authority before relying, or (4) flag as unverified and stop. Which would you like?" A lawyer decides whether to accept lower-confidence sources.
>
> **Source attribution tiering.** Tag every citation with its source. For model-knowledge citations, use one of three tiers rather than a single blanket "verify" tag:
>
> - `[settled]` — stable, well-known statutory and regulatory references unlikely to have changed (e.g., FTC Act § 5, Lanham Act § 43(a) as a concept). Still verify before approving copy, but lower priority.
> - `[verify]` — model-knowledge citations that are real but should be verified: specific FTC enforcement actions, NAD decisions, state UDAP statutes, sector-specific rules, platform policies, case holdings, thresholds, effective dates, recent updates (the Endorsement Guides and disclosure rules update frequently).
> - `[verify-pinpoint]` — pinpoint citations (specific subsection letters, CFR subpart references, case paragraph numbers) carry the highest fabrication risk and should ALWAYS be verified against a primary source.
>
> Tool-retrieved citations keep their source tag (`[Westlaw]`, `[CourtListener]`, `[FTC site]`, `[NAD]`, `[platform policy]`, or the MCP tool name); web-search citations remain `[web search — verify]`; user-supplied citations (from substantiation files) remain `[user provided]`. The tiering surfaces the real verification work — a reader who verifies everything verifies nothing. Never strip or collapse the tags.

## Claim taxonomy

The categories below are structural patterns the reviewer should be able to recognize. Whether a given phrase is actionable depends on the currently operative rule in the applicable jurisdiction, the specific substantiation available, and the audience — research that before concluding.

### Vague / subjective claims

Subjective assertions with no measurable content. Whether they are actionable depends on jurisdiction, context, and audience — research before concluding.

| Example |
|---|
| "The best way to manage your projects" |
| "You'll love it" |
| "Revolutionary" |

### Specific factual claims

Measurable, specific, a reasonable person might rely on it.

| Example | Substantiation to look for |
|---|---|
| "50% faster than [competitor]" | Benchmark data, disclosed methodology, date |
| "Trusted by 10,000 companies" | Actual count (not cumulative signups — *currently* trusted) |
| "Saves 5 hours per week" | Study or customer data, disclosed sample |
| "Enterprise-grade security" | What does that mean? SOC 2? Spell it out or it's a promise |
| "HIPAA compliant" | BAA available, actually configured for it — this is a contractual promise |

### Comparative claims (heightened scrutiny)

Naming a competitor or implying one. Research the applicable rules for comparative advertising in the relevant jurisdictions and media before clearing.

| Example | Fix pattern |
|---|---|
| "Faster than Slack" | Either name Slack with head-to-head data you can defend, or abstract to "faster than legacy chat tools" with substantiation |
| "The only platform that does X" | False if anyone else does X — "The first platform to..." (if true) or drop "only" |
| "[Competitor] can't do this" | Show your feature. Let the viewer compare. |

Per `~/.claude/plugins/config/claude-for-legal/product-legal/CLAUDE.md` — if comparative claims are "never," flag all of them. If "allowed with substantiation," check for the substantiation.

### Implied claims

Not stated outright but a reasonable reader infers it. Research the treatment of implied claims under the applicable advertising regime — implied claims often carry the same substantiation burden as express ones.

| Example | Implication | Fix |
|---|---|---|
| "Finally, a secure alternative" | Competitors are insecure | "Finally, security you can verify" |
| Customer logos without context | These companies endorse us | "Customers include..." is fine; "Trusted by..." implies more |
| "Built for healthcare" | HIPAA compliant | Clarify or qualify |

### Absolute claims

No room for error. One counter-example makes them false. Research whether qualifications cure the issue in the applicable jurisdiction.

| Example | Fix pattern |
|---|---|
| "Never goes down" | "99.9% uptime" (with SLA that defines it) |
| "100% accurate" | A specific, substantiated percentage tied to a benchmark |
| "Guaranteed" | Only if you actually offer a guarantee with terms — this creates warranty exposure |
| "Always" / "Every" | "Typically" / "Most" |

## The review

### Step 1: Extract every claim

Read the copy. List every sentence or phrase that asserts a fact, makes a comparison, or promises something. Ignore pure puffery in the list.

### Step 2: Classify and check

For each claim:

```markdown
**Claim:** "[exact quote]"
**Type:** [Specific factual | Comparative | Implied | Absolute]
**Substantiation on file:** [Yes — link | No | Unknown]
**Call:** [✅ Fine | ⚠️ Needs substantiation | ⚠️ Needs rewording | 🔴 Cut]
**Suggested fix:** "[alternative phrasing that keeps the energy]"
**Why:** [one line]
```

### Step 3: Check against the product

Does the product actually do what the copy says? Not a philosophical question — check the PRD or ask the PM.

Common drift: marketing copy written from an early spec, product changed, nobody updated the copy.

### Step 4: Output

Prepend the work-product header from `~/.claude/plugins/config/claude-for-legal/product-legal/CLAUDE.md` `## Outputs` (it differs by user role — see `## Who's using this`).

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs]

# Marketing Review: [Campaign/Asset name]

**Reviewed:** [date]
**Asset:** [landing page / email / ad / etc.]

---

## Summary

[N] claims reviewed. [N]✅ [N]⚠️ [N]🔴

**Ready to ship:** [Yes | With changes below | No — rewrite needed]

> **Before emitting "Ready to ship: Yes" (i.e., approving a claim for external use / publication):** Read `## Who's using this` in `~/.claude/plugins/config/claude-for-legal/product-legal/CLAUDE.md`. If the Role is Non-lawyer:
>
> > Approving a marketing claim for publication is a legal act — once published, substantiation gaps and comparative-claim exposure become enforcement or competitor-challenge risk. Have you reviewed this with an attorney? If yes, proceed. If no, here's a brief to bring to them:
> >
> > [Generate a 1-page summary: asset, claims approved, claim types (specific factual / comparative / implied / absolute), substantiation on file for each, any implied claims flagged, and the three things to ask the attorney before the copy goes live.]
> >
> > If you need to find a lawyer: your professional regulator's referral service is the fastest starting point (state bar in the US; SRA/Bar Standards Board in England & Wales; Law Society in Scotland/NI/Ireland/Canada/Australia; or your jurisdiction's equivalent).
>
> Do not proceed past this gate to "Ready to ship: Yes" without an explicit yes. "With changes below" and "No — rewrite needed" do not require the gate — those are review calls, not approvals.

---

## Claim-by-claim

[All the claim blocks from Step 2, grouped: 🔴 first, then ⚠️, then ✅]

---

## Suggested revision

[For short assets — under 50 words, or a tweet, headline, one-liner, tagline, short ad — the output in this block is the actual revised copy with the fixes applied inline, not a description of what changed. The reader should be able to copy-paste this block into the asset.
For longer assets (>50 words but <300 words), show the revised copy with fixes applied inline.
For longer assets (300+ words), summarize the changes as a bulleted diff ("Strip Claim 1. Rewrite Claim 3 to drop 'any.' Soften Claim 4 for regulated-domain risk.") rather than pasting the whole asset.
A meta-description of changes is never an acceptable output for a short asset — when the asset is one line, the output should BE the revised one line.]

---

## Substantiation needed before ship

| Claim | Need | From whom |
|---|---|---|
| [claim] | [data type] | [PM / data team / eng] |

---

## Citation check

Any FTC rules, NAD decisions, state UDAP statutes, sector regulations, or platform policies cited in this review were generated by an AI model and have not been verified against a primary source. Before relying on a specific rule to clear or reject copy, verify it against a legal research tool (Westlaw, CourtListener, or your firm's research platform) for accuracy and current effective date — endorsement guides, platform rules, and state UDAP regimes all update frequently. Source tags on each citation (e.g., `[FTC site]`, `[web search — verify]`) show where it came from; `verify` tags carry higher fabrication risk and should be checked first.
```

## Disclosure overlays

Copy that involves any of the fact patterns below sits inside an additional disclosure regime. Research the currently operative disclosure requirements in the applicable jurisdictions (including any platform policies and sector-specific rules) and verify currency — these regimes are updated frequently.

- **Testimonials / reviews** — material connections between the speaker and the advertiser are typically disclosable; research the current form and placement rules
- **Influencer content** — research the current tagging, clarity, and conspicuousness requirements for the channel and audience
- **"Results may vary" / atypical results** — research whether a disclosure (and what form) is required when shown results aren't representative
- **Free trial / auto-renewal / negative option** — research the current conspicuousness and consent requirements for auto-conversion terms

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

## What this skill does not do

- It doesn't write the marketing. It fixes what's wrong with it. The suggested rewrites keep the energy, but the marketer owns the voice.
- It doesn't substantiate claims. It identifies which ones need it and who has the data.
- It doesn't review design or imagery — words only. If an image implies a claim (competitor logo with a red X through it), flag it, but visual review is a human judgment.
