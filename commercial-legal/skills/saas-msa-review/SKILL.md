---
name: saas-msa-review
description: >
  Reference: review of SaaS subscription agreements with attention to the terms
  that matter most in subscription deals — auto-renewal mechanics, price escalation,
  data portability, uptime SLAs, and subprocessor rights. Loaded by
  /commercial-legal:review when a SaaS or subscription agreement is detected.
user-invocable: false
---

# SaaS / Subscription Agreement Review

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/commercial-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/commercial-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Purpose

SaaS agreements have a distinct risk profile from one-time vendor contracts. The dollars compound over renewals, the data accumulates, and the switching cost grows every month. This skill reviews with that in mind.

It runs the standard playbook check from `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md` and adds a SaaS-specific overlay on the terms that bite hardest in subscription deals.

## Jurisdiction assumption

SaaS terms (auto-renewal notice requirements, price-escalation caps, data-portability mandates, subprocessor rules) are jurisdiction-sensitive — California, New York, and EU rules diverge materially, and some states have auto-renewal statutes that override private contract terms. This review applies the team's positions from `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md`, which assume the governing law recorded there. If the agreement picks a different governing law, or the deal spans jurisdictions with statutory overrides (e.g., EU-based users, California consumers), flag it — the analysis may not transfer as written.

> **No silent supplement.** If a research query to the configured legal research tool (Westlaw, or firm platform) returns few or no results for a statutory override that might bear on the deal (auto-renewal statute, data-portability mandate, consumer-protection rule), report what was found and stop. Do NOT fill the gap from web search or model knowledge without asking. Say: "The search returned [N] results from [tool]. Coverage appears thin for [jurisdiction / rule]. Options: (1) broaden the search query, (2) try a different research tool, (3) search the web — results will be tagged `[web search — verify]` and should be checked against a primary source before relying, or (4) flag as unverified and stop. Which would you like?" A lawyer decides whether to accept lower-confidence sources.
>
> **Source attribution.** Where the review cites a statute, regulation, or case (e.g., a state auto-renewal law overriding contract terms), tag the citation: `[Westlaw]`, `[statute / regulator site]`, or the MCP tool name for citations retrieved from a legal research connector; `[web search — verify]` for web-search citations; `[model knowledge — verify]` for citations recalled from training data; `[user provided]` for citations from the counterparty draft or house files. Citations tagged `verify` carry higher fabrication risk and should be checked first. Never strip or collapse the tags.

## Load the playbook

**Which side?** Before applying the playbook, determine which side the company is on for this SaaS agreement. Usually obvious: if the counterparty is a SaaS vendor selling you their platform, you're purchasing-side. If you are the SaaS vendor and the counterparty is your customer, you're sales-side. If it's not obvious (a reseller arrangement, a white-label deal), ask: "Which side is [company] on for this agreement — vendor or customer?" Read the matching playbook section (`### Sales-side playbook` or `### Purchasing-side playbook`) from the config. Note which side in the output so the reviewer knows which playbook was applied. If the matching side is `[Not configured]`, stop and tell the user to run `/commercial-legal:cold-start-interview --side <side>` before this review can proceed.

Read `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md` first. The general playbook for the matching side (liability, indemnity, termination, governing law) applies fully — run all the standard checks from the vendor-agreement-review skill.

Then look for a `## Playbook` → matching side → `SaaS positions` section. That's where the team records its positions on auto-renewal notice windows, acceptable price escalators, data export rights, SLA thresholds, subprocessor approval rights, and deprecation notice. This skill does not ship with defaults for these — the right numbers vary by deal size, vendor leverage, and the team's risk tolerance.

If `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md` doesn't address a SaaS-specific term that comes up in this review, ask:

> Your playbook doesn't cover [term — e.g., "maximum acceptable auto-renewal notice window" or "whether vendor retention of anonymized derivatives is acceptable"]. What's your team's position? I'll add it to `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md`.

Record the answer and proceed.

## SaaS-specific overlay

For each category below, list what you found in the contract and compare to the team's position in `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md`. Do not apply hardcoded thresholds from this skill.

### 1. Auto-renewal mechanics

The single most common way a SaaS deal goes wrong: nobody notices the renewal notice window and we're locked in for another year at a higher price.

Check each element and compare against the team's `SaaS positions` in `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md`:

- **Renewal term length** (e.g., same as initial, longer, multi-year auto-convert)
- **Notice-to-cancel window** (number of days before renewal)
- **Notice method** (email, written notice to legal, portal-only, certified mail)
- **Price on renewal** (same, CPI-capped, then-current list, uncapped discretionary)

**Extract and record** the exact renewal date and the notice window regardless of whether any item is flagged. This feeds the renewal-tracker skill.

### 2. Price escalation

Check each element against `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md`:

- **Annual escalator** (fixed %, CPI, uncapped, etc.)
- **Usage overage pricing** (published rate card, premium rate, unspecified)
- **Scope of "fees"** (subscription only vs. "additional services" broadly defined)

### 3. Data portability and exit

When (not if) we leave this vendor, can we get our data out? Check each element against `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md`:

- **Export format** (open/standard, proprietary-but-documented, "commercially reasonable")
- **Export availability** (self-serve anytime, on request during term, only at termination)
- **Post-termination access** (days available to export after termination)
- **Export cost** (free, T&M, per-GB or per-record)
- **Deletion certification** (certified on request, none, vendor retains derivatives)

Vendor retention of "anonymized" or "aggregated" derivatives is a material position — confirm the team's stance in `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md` and flag either way.

### 4. Uptime and SLA

Only matters if the business actually depends on this service being up. If it's a nice-to-have tool, skip this section — don't spend negotiating capital on SLAs for a survey tool.

Check each element against `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md`:

- **Uptime commitment** (percentage, or "commercially reasonable efforts")
- **Measurement period** (monthly, quarterly, annual)
- **Remedy** (service credits — how calculated, whether capped, whether sole remedy)
- **Scheduled maintenance exclusions** (defined window, advance notice, unlimited)
- **Credit-as-sole-remedy** interaction with the liability cap

### 5. Subprocessors

This is a data protection issue but it's SaaS-specific because the subprocessor list *changes* over the life of the subscription.

Check each element against `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md`:

- **Current list** (published, on request, unavailable)
- **Change notification** (advance notice period, or none)
- **Objection rights** (blocking, notice-and-terminate, notice-only, none)

### 6. Service changes and deprecation

SaaS vendors change their product. Usually fine. Sometimes they deprecate the thing you bought.

Check each element against `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md`:

- **Material adverse changes** (right to terminate on material degradation, notice-only, unrestricted)
- **Deprecation notice period** for features the team relies on
- **Feature parity on replacement** (same price tier, higher tier)



## AI and machine learning rights

**AI/ML data rights decision procedure.** Don't just check whether an AI training clause exists. The #1 emerging negotiation point in SaaS contracts is structurally more than a one-line existence check. Work through:

1. **Explicit grant.** Does the contract explicitly grant the vendor rights to use Customer Data / Customer Content / Usage Data for AI training, model improvement, or ML development? Purchasing-side: this is usually a NO — customer data training the vendor's models means the customer is subsidizing the vendor's product and possibly leaking competitive information. Sales-side: this is revenue if you get it, reputation risk if you abuse it.
2. **Implicit grant via policy.** Does the contract incorporate the vendor's privacy policy or terms of service by reference? Can the vendor add training rights via a unilateral policy update? Check: "The parties agree to the Provider's Privacy Policy as updated from time to time" is a training-rights grant waiting to happen. Also watch for "service improvement" or "analytics" catch-alls and "usage data" definitions that carve logs/telemetry out of the Customer Data definition so data-use restrictions don't apply.
3. **Anonymization standard.** If the vendor claims it only trains on "anonymized" or "aggregated" data, what's the standard? "Anonymized" without a definition is weak. Does it meet GDPR Recital 26 / HIPAA Safe Harbor / a named standard? Is it reversible?
4. **Competitive contamination.** Does the vendor serve your competitors? If so, training on your data could leak competitive intelligence into outputs your competitors see. Is there a competitive isolation commitment?
5. **Opt-out scope and durability.** If there's an opt-out, does it cover all AI uses or only some? Does it survive renewals and TOS updates? Is it per-user or per-org? Many vendors default to training and offer an opt-out buried in an admin console — check whether the contract makes the default explicit.
6. **Output ownership.** If the SaaS product is itself AI-generated (drafting, summarization, analysis), who owns the outputs? Can the vendor use your outputs as training examples? Check third-party AI subprocessors too — the vendor may send customer data to a third-party LLM (OpenAI, Anthropic, Google) and the subprocessor list / data flow is where that shows up.
7. **Downstream regulatory chain.** Does the vendor's use of your data for AI create regulatory exposure for YOU? EU AI Act deployer obligations, FTC §5 undisclosed data-sharing exposure (see *FTC v. Humor Rainbow/OkCupid*), state AI laws.

Match each to a playbook position. The practice profile's `## AI/ML training rights` section should have positions for each. If the agreement is silent on all seven, that's still a finding: "The agreement is silent on AI/ML training rights — request an explicit prohibition or a defined carve-out tied to each of the seven dimensions above."

## Liability cap decision procedure

**The cap amount is the least important part of the cap.** Limitation-of-liability is not a single "check against playbook" item. Work through:

1. **Direct vs. indirect/consequential damages.** Does the cap apply to ALL liability, or only direct damages? A 12-month cap on direct damages with uncapped consequential damages is a completely different position than a 12-month aggregate cap. State both treatments explicitly.

2. **The cap base — quote it verbatim.** "12-month cap" could mean: (a) fees paid in the 12 months preceding the claim, (b) fees payable in the current 12-month period, (c) fees over the last 12 months of usage, (d) fees under the current order form, (e) total fees ever paid. These can differ by an order of magnitude. Quote the exact language. If ambiguous, flag it: "Cap base is ambiguous — `[the quoted language]` — could mean [X] or [Y]. Confirm before signing."

3. **Cap-carveout interaction.** A $100K cap with uncapped indemnity for data breach, IP, and confidentiality is functionally uncapped for the claims that actually arise in SaaS disputes. Enumerate what sits ABOVE the cap (the carveouts), what sits BELOW (what's actually capped), and assess whether the capped surface is meaningful: "The cap covers [general contract breach]. Data breach, IP indemnity, and confidentiality are carved out and uncapped. For this vendor's risk profile, the capped surface is [meaningful / nominal]."

4. **Your playbook position per dimension.** The practice profile should have positions for: direct cap (multiple of fees), indirect damages (excluded / capped / uncapped), carveout list (what's acceptable above the cap), and cap base (which definition you'll accept). If the playbook has one "standard position" field, note: "Your playbook has a single cap position — consider splitting into direct/indirect/carveouts/base for more precise review."

## Jurisdiction delta check

**The playbook applies one governing-law preference globally. Enforceability varies materially.** Check the SaaS contract's actual governing law against the top divergences before accepting playbook positions at face value:

- **Non-solicits/non-competes:** Unenforceable in CA (Bus. & Prof. Code §16600). Restricted in many EU jurisdictions. Enforceable with limitations elsewhere. `[jurisdiction — verify]`
- **Auto-renewal:** CA GBL §17600-17606, NY GBL §527-a, IL 815 ILCS 601 have specific consumer/B2B notice requirements. Other states vary. `[jurisdiction — verify]`
- **Liability exclusions:** EU and UK unfair contract terms rules (UCTA 1977, Consumer Rights Act 2015) constrain consumer exclusions. Some US states limit exclusion of gross negligence or willful misconduct. `[jurisdiction — verify]`
- **Indemnification:** Some states void indemnification for the indemnitee's own negligence. `[jurisdiction — verify]`
- **Confidentiality term:** Some jurisdictions limit "perpetual" confidentiality to a reasonable period. `[jurisdiction — verify]`

When the playbook position conflicts with the contract's governing-law enforceability, flag: "Your playbook prefers [X], but this contract is governed by [Y] law where [X] is [unenforceable / restricted / subject to statutory override]. `[jurisdiction — verify]`"

## Redline granularity

**Edit at the smallest possible granularity.** A redline is a negotiation artifact, not a rewrite. Wholesale clause replacement signals "we threw out your drafting" — it's aggressive, it forces the counterparty to re-read the whole clause, and it discards the parts of their drafting that were fine. Surgical redlines — strike a word, insert a phrase, restructure a subclause — signal "we have specific asks" and are faster to read, understand, and accept.

Default to the smallest edit that achieves the playbook position:
- Replace a **word** before a phrase. ("twelve (12)" → "twenty-four (24)")
- Replace a **phrase** before a sentence. ("paid by the Buyer" → "paid and payable by the Buyer")
- Restructure a **subclause** before replacing the sentence. (Add "(a)" and "(b)" to split a compound condition.)
- Replace a **sentence** before replacing the clause.
- Only replace a **whole clause** when the counterparty's version is so far from your position that surgical edits would be harder to read than a fresh draft — and when you do, say so in the transmittal: "We've replaced §8.2 rather than marking it up because the changes were extensive. Happy to walk you through the delta."

When in doubt, smaller. A client who receives a surgical redline trusts that you read carefully. A client who receives a wholesale replacement wonders whether you read at all.

## Output

Use the vendor-agreement-review memo structure, with a SaaS-specific section added after the standard playbook checks. The vendor-agreement-review memo already carries the privilege header.

**Dual severity.** Every SaaS-specific finding carries both axes (see CLAUDE.md `## Dual severity`):
- **Legal risk:** 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low
- **Business friction:** 🔴 Blocks deals | 🟠 Slows deals | 🟡 Confuses customers | 🟢 Invisible

Data-exit, auto-renewal, and price-escalation findings are the ones most likely to be 🟢 legal / 🔴 business — the clause is enforceable, but it's the reason a customer can't leave or a renewal surprises finance. Surface those at the business-friction severity, not the legal one.

```markdown
### Bottom line

[Can you sign / Need to fight for X first / Walk — one-sentence why]

### AI and machine learning rights

[The #1 emerging SaaS negotiation point. Flag: explicit ML training clauses, "service improvement" catch-alls, usage data definitions, output ownership, third-party AI subprocessors, opt-out vs opt-in. If the agreement is silent: "Silent on AI/ML training rights — request explicit prohibition or defined carve-out."]

## SaaS-specific findings

### Auto-renewal
**Renewal date:** [date]
**Notice window:** Cancel by [date] ([N] days before renewal)
**Renewal price mechanism:** [as written]
**Playbook fit:** [within position / deviation / not addressed]
**Flag for renewal-tracker:** [yes — and the record the tracker needs]

### Price escalation
[findings against `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md` positions]

### Data exit
[findings — this is the one the business owner should read]

### SLA
[findings, or "Skipped — service is not business-critical per [stakeholder]"]

### Subprocessors
[findings against `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md` positions]

### Service changes
[findings against `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md` positions]
```

## Handoffs

**To renewal-tracker:** When you find the renewal date and notice window, hand them off. The renewal-tracker register expects the following fields (see `skills/renewal-tracker/references/renewal-register.yaml` for the full schema):

```yaml
counterparty:         [name]
agreement:            [title]
signed_date:          [ISO date]
initial_term_end:     [ISO date]
renewal_mechanism:    [e.g., "auto-renew annual"]
notice_period_days:   [integer]
cancel_by_effective:            [ISO date — initial_term_end minus notice_period_days]
price_on_renewal:     [mechanism as written]
annual_value:         [integer, if stated]
business_owner:       [email, if known]
clm_id:               [id if available]
status:               active
```

If any field is not determinable from the contract or context, leave it out and note which fields were missing so the human can fill them in. `clm_id`, `annual_value`, and `business_owner` are especially likely to need human input.

**To escalation-flagger:** If any of the SaaS-specific checks hits the team's "never accept" or escalation-trigger list in `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md`, the escalation-flagger skill routes it.

## A note on what to fight over

SaaS vendors, especially large ones, negotiate their paper about as willingly as airlines negotiate ticket terms. Pick battles *per the team's playbook* — the `SaaS positions` section in `~/.claude/plugins/config/claude-for-legal/commercial-legal/CLAUDE.md` should distinguish between terms the team will always push on, terms it fights over only for material deals, and terms it lets slide. If the playbook doesn't draw those lines, ask.

Calibrate based on contract value and switching cost. A $5K/year tool with easy alternatives gets a lighter touch than a $500K/year platform we'll build on top of.

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

