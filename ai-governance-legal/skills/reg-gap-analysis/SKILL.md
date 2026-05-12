---
name: reg-gap-analysis
description: >
  Diff a new AI regulation or guidance against your current governance posture —
  surfaces gaps, priorities, and a remediation plan with owners and deadlines.
  Use when an AI regulation moves (or you learn about one you missed), or when
  user says "new reg just dropped", "does [regulation] affect us", "gap analysis
  for EU AI Act", "compliance check against [AI law or guidance]", or pastes
  regulatory text.
argument-hint: "[regulation name, or paste regulatory text, or attach a document]"
---

# /reg-gap-analysis

1. Read `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`. Confirm regulatory footprint and use case registry are populated.
2. Use the framework below.
3. Scope: does this regulation apply? (Jurisdiction, threshold, builder/deployer, sector.) If not, one line and done.
4. Extract requirements. Diff against current state in `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`.
5. Prioritize gaps. Output: remediation plan with must-do / should-do / already compliant / accepted gaps.
6. Save as dated markdown doc for the file.

```
/ai-governance-legal:reg-gap-analysis "EU AI Act high-risk provisions"
```

---

## Purpose

The EU AI Act goes live. Colorado passes an AI law. The CFPB issues model risk
guidance. The FTC publishes an AI enforcement policy. Something moves — and now
you need to know what, if anything, you have to change.

This skill diffs the new requirement against your current AI governance posture
(per `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` — use case registry, vendor positions, impact assessment practices,
and AI policy commitments) and produces a gap list with a remediation plan.

The AI regulatory landscape is moving faster than any other area of law right now.
When a regulation is genuinely ambiguous, say so. Don't paper over uncertainty —
legal teams need to know when they're on solid ground versus when they're making a
judgment call.

## Load current state

Read `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`:
- `## Regulatory footprint` — what already applies
- `## Use case registry` — what AI you're actually running, and under what conditions
- `## AI policy commitments` — what you've publicly or contractually committed to
- `## Vendor AI governance` — what vendor positions are in place
- `## Impact assessment house style` — what assessment practices exist

If the regulation clearly doesn't apply (wrong jurisdiction, below threshold,
wrong sector, builder/deployer distinction eliminates you from scope), say so
directly: "Doesn't apply. Here's why: [reason]. No action needed."

---

## Research first, then workflow

Before running the gap analysis, research the currently operative AI regulatory regimes for the jurisdictions in the user's footprint. For each regime identify:

- **Scope** — who's covered (provider/builder vs. deployer vs. distributor vs. user; sectoral carve-outs).
- **Applicability thresholds** — revenue, user count, headcount, compute, model category, affected-population size.
- **Risk-tier definitions** — how the regime distinguishes tiers (prohibited / high-risk / limited-risk / minimal), what's in each.
- **Substantive obligations** — transparency, documentation, human oversight, bias testing, registration, incident reporting, vendor flow-down.
- **Enforcement mechanism** — which regulator, what penalties, any private right of action.
- **Effective dates** — many AI laws phase in obligations over 2-4 years; note which obligations are live vs. upcoming.

Cite the regulatory text with pinpoint references. Flag provisions subject to ongoing interpretation, delegated acts, or pending rulemaking. The AI regulatory landscape changes quickly — verify currency before advising.

Build the gap analysis from the researched requirements, not from hardcoded reference tables.

## Workflow

### Step 1: Scope the regulation

Before diffing, answer:

- **Does it apply?** Jurisdiction, threshold, sector carve-outs, builder vs. deployer distinction. Research the specific scoping rules in the regulation — don't assume.

  *Builder/deployer matters a lot here.* Many AI regimes impose different obligations on the entity that develops/provides the AI system versus the entity that deploys/uses it. Research which role the company occupies under each regime's definitions. Scope first; don't gap-analyze a law that doesn't apply.

- **When?** Effective date. Enforcement date (often different). Phase-in periods for specific provisions. Verify currency.

- **What's actually new?** Some "new" AI laws largely restate existing legal principles (consumer protection, anti-discrimination, sectoral risk management) applied to AI. Others are genuinely new obligations. Identify the delta from what you already do, not the full text of the law.

### Step 2: Extract requirements

Read the regulation, guidance, or summary. List every substantive requirement:

| # | Requirement | Citation | Category |
|---|---|---|---|
| 1 | [requirement] | [section] | [see categories below] |

**Categories:**
- **Transparency** — disclosures to users, employees, or affected parties about AI use
- **Impact assessment** — required documentation before deployment
- **Human oversight** — mandatory human review, override, or appeals mechanisms
- **Accuracy / testing** — bias testing, accuracy documentation, validation
- **Governance** — registration, record-keeping, designated responsible persons
- **Vendor flow-down** — obligations to pass down to AI vendors or pass up from AI vendors
- **Prohibited practices** — outright bans on specific AI capabilities or uses
- **Rights** — what affected parties can request or invoke

### Step 3: Diff against current state

For each requirement:

```markdown
### [Requirement #N]: [short name]

**Regulation says:** [requirement, quoted or paraphrased]

**We currently:** [what `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` / AI policy / use case registry / assessment
practice shows]

**Gap:** [None | Partial | Full]

**If partial/full — what's missing:** [specific — not "more documentation" but
"no human review step is documented for [use case category]"]

**Effort to close:** [Policy update only | Process change | Product/system change |
New assessment required | Vendor renegotiation | Registration / filing]

**Risk of non-compliance:** [penalty range, enforcement likelihood, reputational]
```

### Step 4: Prioritize

Not every gap is equal. Sort by:

1. **Hard deadline with teeth** — effective date + active enforcement + real penalties
2. **Prohibited practice** — if the gap is a prohibition, not a process requirement,
   that's the first priority regardless of enforcement date
3. **Effort-to-impact ratio** — updating policy language is cheap; adding human
   oversight to a deployed system is not
4. **Use case overlap** — gaps that affect multiple use cases in the registry are
   higher priority than single-use-case gaps

### Step 5: Remediation plan

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

## Remediation Plan: [Regulation name]

**Effective date:** [date]
**Enforcement begins:** [date if different]
**Applies to us as:** [Builder / Deployer / Both]

### Must-do before enforcement

| Gap | Fix | Owner | Due | Status |
|---|---|---|---|---|
| [gap] | [specific fix] | [name] | [date] | [ ] |

### Should-do (important but not blocking enforcement)

[same table]

### Already compliant

[list of requirements where gap = None — useful context for the legal/executive
summary of where you actually stand]

### Accepted gaps (risk accepted, not fixing)

[if any — with documented rationale and who accepted the risk. Documenting accepted
risk is better governance than leaving it unaddressed silently.]
```

---

## Research the regulation before building the gap analysis

Do not rely on hardcoded reference tables for specific regimes. For each regulation in scope, research the currently operative text:

- Which obligations apply to the company's role (provider/builder, deployer, importer, distributor)?
- Which tier does the system fall into under the regime's own classification (prohibited / high-risk / limited-risk / minimal, or the regime's equivalent)?
- What are the live vs. phase-in dates for each obligation?
- Are there delegated acts, implementing acts, or regulator guidance that affect interpretation?
- For builder contexts: are there model-level obligations (technical documentation, training data transparency, copyright compliance, systemic-risk testing)?
- For prohibited-practice categories: check any use case in the registry that might touch them and flag as critical regardless of enforcement date.

Cite primary sources with pinpoint references. Flag ambiguity for attorney judgment.

> **No silent supplement.** If a research query to the configured legal research tool (Westlaw, EUR-Lex, regulator sites, or firm platform) returns few or no results for a regime's text, delegated act, or guidance, report what was found and stop. Do NOT fill the gap from web search or model knowledge without asking. Say: "The search returned [N] results from [tool]. Coverage appears thin for [regime / topic]. Options: (1) broaden the search query, (2) try a different research tool, (3) search the web — results will be tagged `[web search — verify]` and should be checked against the issuing authority before relying, or (4) flag as unverified and stop. Which would you like?" A lawyer decides whether to accept lower-confidence sources.
>
> **Source attribution tiering.** Tag every citation in the gap analysis with its source. For model-knowledge citations, use one of three tiers rather than a single blanket "verify" tag:
>
> - `[settled]` — stable, well-known statutory and regulatory references unlikely to have changed (e.g., GDPR Art. 22, the existence of Regulation (EU) 2024/1689 as the EU AI Act, Colorado AI Act as C.R.S. § 6-1-1701 et seq.). Still verify before filing, but lower priority.
> - `[verify]` — model-knowledge citations that are real but should be verified: specific delegated / implementing acts, regulator guidance, standards, enforcement actions, case holdings, thresholds, effective dates, phase-in provisions, harmonized-standards references.
> - `[verify-pinpoint]` — pinpoint citations (specific article numbers, annex references, subsection letters, paragraph numbers, standard-clause references) carry the highest fabrication risk and should ALWAYS be verified against a primary source. EU AI Act article numbers in particular shifted during consolidation; every pinpoint cite to the Act should be verified against the Official Journal text.
>
> Tool-retrieved citations keep their source tag (`[Westlaw]`, `[EUR-Lex]`, `[regulator site]`, or the MCP tool name); web-search citations remain `[web search — verify]`; user-supplied citations remain `[user provided]`. The tiering surfaces the real verification work — a reader who verifies everything verifies nothing. Never strip or collapse the tags.
>
> **For non-lawyer users, uncertain dates, thresholds, and phase-in provisions go in a confirm-list, not inline.** A `[verify]` tag on "effective February 1, 2026" reads as "effective February 1, 2026" to a non-lawyer who doesn't know what the tag means. Read `## Who's using this` in `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`. If Role is **Non-lawyer** and a date, deadline, phase-in, threshold, or effective-date assertion is uncertain (would carry `[verify]` or `[verify-pinpoint]` if inline), replace the inline assertion with "effective date: confirm with counsel" (or "threshold: confirm with counsel") and collect all uncertain items in a final gap-analysis section titled: "**Things I'm not certain about — ask your attorney to confirm before relying on this:**" with each item listed (what I said, what's uncertain, why it matters to the gap). Lawyer-role users keep the inline `[verify]` treatment.

---

## Integration with other skills

**From aia-generation:** AIAs flag regulatory obligations for specific
systems → those feed here when a regulation is new or coverage is uncertain.

**From use case triage:** Newly triaged use cases that hit regulatory triggers →
gap analysis runs on the specific requirement for that use case type.

**To regulatory-legal plugin, if the plugin is installed:** This skill is the manual
version. The monitor plugin watches feeds and triggers this analysis automatically
when something relevant changes.

---

## Output

Save as a dated markdown doc. The remediation plan table becomes a tracker — update
status as items close.

If the gap analysis concludes "no gaps, we're compliant," still write the doc. It's
useful evidence that you looked, and useful baseline when the regulation is amended.

**Cite check before relying on this.** Citations here were generated by an AI model and have not been verified against primary sources. Before relying on any citation — statute, regulation, delegated act, guidance, or case — run a verification pass against a legal research tool (Westlaw, CourtListener, or your firm's platform) for accuracy, currency, and subsequent history. Fabricated or misquoted citations in filed materials have resulted in sanctions. Source tags on each citation (e.g., `[EUR-Lex]`, `[web search — verify]`) show where it came from; `verify` tags carry higher fabrication risk and should be checked first.

---

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

## What this skill does not do

- It doesn't interpret ambiguous regulatory language authoritatively. The EU AI Act
  in particular has significant interpretive questions that aren't resolved yet.
  When the reg is genuinely ambiguous: say so, state the conservative read, and
  flag for outside counsel if the issue is material.
- It doesn't track regulatory changes proactively. It runs when you point it at a
  change. For proactive monitoring, see the `regulatory-legal` plugin, if the plugin is installed.
- It doesn't implement fixes. It plans them.
- It doesn't substitute for sector-specific legal counsel where specialized knowledge
  is required (healthcare AI, financial services model risk management, etc.).
