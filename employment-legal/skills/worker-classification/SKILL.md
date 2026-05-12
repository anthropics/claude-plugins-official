---
name: worker-classification
description: >
  Classify a proposed worker engagement — employee, IC, temp, or vendor — by
  running the applicable jurisdiction tests and flagging misclassification gaps
  between the intended arrangement and what the facts actually support.
  Prospective use only. Use when someone says "we want to bring on a
  contractor", "is this a vendor or a temp", "how should we classify this
  person", or describes a proposed working arrangement.
argument-hint: "[describe the proposed arrangement, or just start and I'll ask]"
---

# /worker-classification

Runs the applicable classification tests for the jurisdiction and flags where
the proposed arrangement doesn't match the structure you're trying to use.
Prospective only — for existing relationships, consult counsel.

## Instructions

1. Load `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` → jurisdictional footprint, escalation table.
2. Run the full workflow below.
3. If the attorney provides details upfront, extract what's available and ask
   only about the gaps. Do not re-ask information already provided.

## Examples

```
/employment-legal:worker-classification
We want to bring on a data scientist for 6 months, working out of our
SF office, using our tools, embedded in our analytics team.
```

```
/employment-legal:worker-classification
Is our recruiter contractor arrangement okay? She works exclusively for
us, sets her own hours, uses her own laptop, project fee per placement.
```

```
/employment-legal:worker-classification
(skill will ask for details)
```

---

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/employment-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/employment-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Purpose

The most expensive classification decision is the one nobody made consciously.
Someone describes what they want ("a contractor"), the engagement starts, and
two years later the facts look like employment. This skill walks the applicable
tests on the proposed arrangement before it starts — and tells you when what
you're describing doesn't match the structure you're trying to use.

This skill teaches the reasoning pattern. It does not state the law. Every
test formulation, statutory citation, threshold, and carve-out must come from
current research for the applicable jurisdiction.

## Prospective-only hard gate — run BEFORE intake

**This skill analyzes a PROPOSED engagement before the work starts.** Before any substantive intake (Step 1), ask:

> Has this work already started? Is the worker currently engaged, or have they been performing work under this arrangement for any period of time (days, weeks, months, or years)?

If the answer is yes — the engagement already exists, in any form, for any duration — **STOP**. Do not proceed to Step 1 intake. Classifying an existing arrangement is not a planning exercise; it's a liability assessment with remediation implications: back pay (OT, meal/rest premiums), unpaid employer-side payroll tax, benefits eligibility that was denied, unemployment and workers' comp back-exposure, state penalties (in CA, PAGA), IRS § 530 relief analysis, and — in strict-test jurisdictions with ongoing work — the prospective exposure of letting it run another day. That analysis is privileged, led by counsel, and coupled with a remediation plan.

Output exactly this block and wait for a response:

> **Out of scope — existing arrangement.**
>
> This skill is designed to analyze a worker engagement *before it starts*, so the classification choice informs how to structure the contract and operations. You've described an arrangement that already exists. Analyzing an existing engagement retroactively is a different exercise: reclassification risk assessment coupled with remediation planning — back-pay exposure, payroll-tax back-exposure, penalty exposure, benefits exposure, IRS § 530 relief analysis, and prospective restructuring. That work should be privileged, led by an attorney, and likely coupled with outside-counsel review given the dollar and enforcement exposure.
>
> Recommended next step: escalate per your config's escalation table (for retroactive classification, this typically routes to GC + outside employment counsel). I've flagged this for escalation routing.
>
> **If you want to proceed with the prospective-style analysis anyway for planning purposes, say "proceed anyway" — but understand:**
>
> - The output is NOT a remediation plan and should not be treated as one.
> - The output does NOT scope back-pay, penalty, or payroll-tax exposure for the period already worked.
> - The output does NOT substitute for the reclassification-risk assessment that this fact pattern actually calls for.
> - The output will carry a prominent banner reflecting this scope mismatch, and the consequential-action gate will require an attorney yes before the analysis is treated as reliable.
>
> Only say "proceed anyway" if you're using this skill for forward-looking planning (e.g., "if we were structuring this fresh today, how should we think about it?") and you have a separate plan for the remediation question.

**Only proceed past this gate with an explicit `"proceed anyway"` (or equivalent user instruction). A hesitant "I guess" does not count — re-prompt. If the user proceeds anyway, prepend this banner to every output of this skill for this session:**

```
⚠️ SCOPE MISMATCH — OUT-OF-SCOPE USE
This skill analyzes prospective worker engagements. The arrangement here
already exists. This output is the prospective-style analysis the user
requested for planning purposes only — it is NOT a remediation plan, does
NOT scope existing back-pay / penalty / payroll-tax exposure, and does
NOT substitute for the reclassification-risk assessment this fact pattern
requires. The remediation question has been flagged for escalation to
counsel per your config's escalation table.
```

If the answer to "has this work already started?" is no (the engagement is genuinely prospective, not yet begun), proceed to load context.

---

## Load context

Read `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` → jurisdictional footprint, any classification history or
prior settlements noted, escalation table, and any house classification
policy the team has recorded.

## Output header

Prepend the work-product header from `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` → `## Outputs` (it differs by user role — see `## Who's using this`).

## Workflow

### Step 1 — Information gathering

Ask all of the following in a single block. Do not drip questions one at a
time. Briefly explain why you're asking — attorneys answer better when they
understand what the question is testing.

> To run the right classification tests I need to understand the proposed
> arrangement in detail. Please answer as many of these as you can — the more
> complete the picture, the more accurate the analysis:
>
> **The work**
> - What will this person actually do day-to-day?
> - Is this work part of your company's core business, or peripheral to it?
>   (e.g., a software engineer at a software company = core; an IT
>   contractor at a law firm = more peripheral)
> - Is this a defined project with a clear end, or ongoing indefinite work?
> - How specialized is the skill? Does this person have expertise your team
>   doesn't?
>
> **Control**
> - Who sets their hours and schedule — them or you?
> - Where will they work — your office, their location, or either?
> - Will you direct how they do the work (methods, process, sequence), or
>   just what the end result should be?
> - Will they supervise any of your employees?
>
> **Economics**
> - How will they be paid — hourly, daily, or fixed project fee?
> - Will you provide equipment, tools, or software, or do they use their own?
> - Do they work for other companies, or will this be exclusive?
> - Will they bear any financial risk — can they profit beyond the fee, or
>   lose money on the engagement?
> - Do they have their own business entity (LLC, S-corp, sole proprietor)?
>
> **The arrangement**
> - How do you want to structure this — direct contractor, staffing agency
>   temp, or vendor/SOW (company-to-company)?
> - If staffing agency: who pays the worker — the agency or you? Who controls
>   day-to-day work?
> - Will there be a written contract? Do you have a template in mind?
> - Roughly how long is the engagement — weeks, months, over a year?
> - Will they work alongside your employees doing similar work?
>
> **Purpose(s) of the classification**
> - What legal purposes does the classification need to serve — federal
>   payroll tax, FLSA wage/hour, state wage/hour, unemployment insurance,
>   workers' compensation, benefits eligibility? Different purposes are often
>   governed by different tests, and the answers can diverge.
>
> **Jurisdiction**
> - Where will this person physically perform the work?

Wait for responses before proceeding. If the attorney can't answer certain
questions, note the gaps — they affect the analysis.

### Step 2 — Identify the applicable tests

> **Research the applicable tests before proceeding.** For the jurisdiction(s)
> and purpose(s) identified in intake, research the currently operative
> classification test(s). Jurisdictions commonly use one or more of: an ABC
> test, an economic-realities test, a common-law right-to-control test, a
> hybrid, or a purpose-specific statutory test. The test that governs for
> federal payroll tax may not be the same test that governs for state
> wage/hour, unemployment, or workers' compensation — run each purpose on its
> own track. Cite the controlling statute, regulation, or case. Note the
> effective date of each rule and whether it has been recently amended.
> Identify any carve-outs or exceptions that may apply (e.g., B2B,
> professional services, construction, referral-agency, business-to-business
> contracting relationship). Verify currency. If you are uncertain about the
> current state of the law in any jurisdiction, flag it for attorney
> verification — do not state a test you haven't confirmed.

If `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` records the company's house classification policy, apply it
first and flag any tension with the researched test.

> **No silent supplement.** If a research query to the configured legal research tool returns few or no results for a jurisdiction-and-purpose combination, report what was found and stop. Do NOT fill the gap from web search or model knowledge without asking. Say: "The search returned [N] results from [tool]. Coverage appears thin for [jurisdiction / purpose / test]. Options: (1) broaden the search query, (2) try a different research tool, (3) search the web — results will be tagged `[web search — verify]` and should be checked against a primary source before relying, or (4) flag as unverified and stop. Which would you like?" A lawyer decides whether to accept lower-confidence sources.
>
> **Source attribution.** Tag every citation — each classification test, statute, regulation, or case — with where it came from: `[Westlaw]`, `[CourtListener]`, or the MCP tool name for citations retrieved from a legal research connector; `[web search — verify]` for web-search citations; `[model knowledge — verify]` for citations recalled from training data; `[user provided]` for citations the attorney supplied. Citations tagged `verify` carry higher fabrication risk and should be checked first. Never strip or collapse the tags.

### Step 3 — Apply the researched tests to the facts

For each test identified in Step 2, apply it to the intake facts. Score each
factor or prong explicitly — do not summarize. The attorney needs to see which
factors are clean and which are problems.

Use a structure like the one below, but populate the *factors* from the
researched test, not from this file:

```
Test: [name of test, per research]
Purpose: [what this test governs — federal tax / state wage-hour / UI / etc.]
Source: [pinpoint cite to statute/regulation/case]
Currency: [verified as of date]

| Factor / prong | Intake facts | Signal / pass-fail |
|---|---|---|
| [Factor 1 from researched test] | [from intake] | [direction or pass/fail] |
| [Factor 2] | [from intake] | [direction or pass/fail] |
| ...                            |                |                   |

Structure of the test:
[How the test weighs factors — e.g., a multi-factor balancing test, or a
conjunctive test where each prong must be satisfied, or a hybrid. State this
from research, not from memory.]

Result under this test:
[Employee-leaning / IC-leaning / Fails prong X / Uncertain — contested prong]
```

Repeat for each applicable test.

**Notes on contested prongs.** Some prongs of some tests are heavily contested
in case law and fact-sensitive. Identify contested prongs explicitly — do not
paper over them. The fact that a test is stated does not mean its application
to these facts is settled; flag prongs that require attorney judgment or that
have generated recent litigation in the jurisdiction.

### Step 4 — Classify and flag gaps

**The classification call**

Based on the test results, state the most accurate classification for this
proposed arrangement:

- **Employee (W-2):** Facts support employment under one or more applicable
  tests for the relevant purpose(s).
- **Independent Contractor (1099):** Facts support IC status under all
  applicable tests for the relevant purpose(s).
- **Temp via staffing agency:** Worker will be on the agency's payroll;
  company is a client — co-employment risk exists if company exercises
  day-to-day control. Research the applicable joint-employer standard if
  relevant.
- **Vendor/SOW:** Company-to-company engagement; worker is employed by the
  vendor entity — cleanest structure if facts support it.
- **Unclear / close call:** Facts cut both ways under one or more tests —
  state which test is the problem and why.

If tests give different answers for different purposes (e.g., defensible as
IC for federal tax but fails a state wage/hour test), say so explicitly and
name the controlling purpose and jurisdiction.

**The gap analysis**

This is the most important output. Compare the intended structure against what
the facts actually support:

```
Intended structure: [what they said they want]
What the facts suggest: [what the researched tests say this actually is]

Gaps — where the arrangement doesn't match the intended structure:
🔴 [Factor]: [What they described] conflicts with [intended classification]
   because [specific researched test language + cite]. This is a significant
   misclassification risk if the engagement proceeds as described.
🟡 [Factor]: [What they described] is a weaker point under [test]. Not
   disqualifying alone, but combined with other factors increases risk.
✅ [Factor]: Supports [intended classification]. No issue.
```

**Escalation trigger**

Escalate per `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` if any of the following, or any team-specific
triggers recorded in that config:
- The jurisdiction uses a strict test and the proposed work is core to the
  company's business — do not proceed without counsel review.
- Prior misclassification settlement or audit noted in the config — heightened
  scrutiny applies.
- Worker will supervise employees or have significant budget authority.
- Engagement expected to exceed 12 months with no clear project endpoint.
- Any contested prong where the outcome changes the classification.

### Step 5 — Output

> **Research-connector pre-flight.** Before emitting the analysis, check whether a legal research connector is reachable for this session — Westlaw, CourtListener, or any firm-configured research MCP. Collect this into the reviewer note per CLAUDE.md `## Outputs`: if no connector returns results in Step 2 (or none is configured at run time), record it in the **Sources:** line of the reviewer note — e.g., `not connected — cites from training knowledge; the highest-fabrication pinpoints in classification analyses are ABC-test codifications, state carve-out subsections (e.g., CA Lab. Code §§ 2775/2776/2783), element counts in B2B exemptions, and purpose-specific test selection — spot-check those first`. Per-citation `[model knowledge — verify]` tags remain inline. Do not emit a standalone banner above the output.

> **Jurisdiction assumption.** This analysis applies the tests operative in the jurisdiction(s) identified in intake. Classification rules vary materially by state and country, and the test that governs for one purpose (e.g., federal payroll tax) often differs from the test that governs another (e.g., state wage/hour). If the work will be performed in a jurisdiction not analyzed here, or if a new purpose is added later, this analysis may not apply as written.

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

## Worker Classification Analysis
**Proposed arrangement:** [what they described]
**Jurisdiction:** [state/country]
**Purpose(s):** [federal tax / state wage-hour / UI / WC / benefits]
**Tests applied:** [list, each with pinpoint cite and currency date]

---

### Bottom line

[Can you proceed / Need to fix X first / Stop — one-sentence why]

---

### Classification

**Closest classification:** [Employee / IC / Temp via agency / Vendor-SOW / Unclear]

[One paragraph summary of why — test results in plain language, tied to the
cited sources.]

---

### Test results

#### [Test name — per research]
Purpose: [...] | Source: [...] | Currency: [...]
[Scored table from Step 3]
**Result:** [Employee-leaning / IC-leaning / Fails prong X / Mixed]

#### [Additional researched tests — repeat the block]

---

### Gap analysis

[Flags as structured in Step 4 — 🔴 significant risks, 🟡 weaker points,
✅ clean factors]

---

### Escalation

[None needed | Escalate to [name] before proceeding — [reason]]

---

### Next steps

[If IC viable: "Proceed — ensure the written agreement reflects the terms that
support IC status under the researched test."]
[If gaps exist: "Address the following before using IC structure: [list]"]
[If agency/vendor is cleaner: "Consider restructuring as [agency/SOW] — here's
why it's cleaner for this fact pattern."]
[If escalation needed: "Do not proceed until counsel reviews the [specific
issue]."]
[If employee confirmed: "Classification confirmed as W-2 employee — run
`/employment-legal:hiring-review` to review the offer letter, restrictive
covenants, and jurisdiction-specific requirements."]
[If IC confirmed: "Classification confirmed as independent contractor — no
offer letter review needed. Ensure the written agreement reflects IC-supporting
terms before the engagement starts."]
[If agency/vendor: "Engagement should be structured through [agency/vendor
entity] — coordinate with them on worker agreement. No `/hiring-review` needed."]
```

## Consequential-action gate (classify a worker)

**Before producing a "Proceed as IC / employee / agency / vendor" final recommendation:** Read `## Who's using this` in `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md`. If the Role is **Non-lawyer**:

> Classifying a worker has legal consequences — misclassification exposes the company to back wages, taxes, benefits, penalties, and private-action risk, and in several states is strict-liability. Have you reviewed this classification call with an attorney? If yes, proceed. If no, here's a brief to bring to them:
>
> - The arrangement (work, control, economics, structure) as described
> - Jurisdiction and which tests were applied
> - Test-by-test results with cites and currency
> - Gap analysis (🔴 / 🟡 / ✅) with the weak prongs called out
> - Open questions and what's unresolved
> - What could go wrong (the misclassification theory this arrangement most likely fails on; prior-audit/settlement overlay if any)
> - What to ask the attorney (is IC viable here; would restructuring through an agency or vendor remove the risk; what contract terms do we need to support the classification)
>
> If you need to find an attorney, solicitor, barrister, or other authorised legal professional: contact your professional regulator (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent) for a referral service.

Do not produce a final "IC viable" / "use this classification" output past this gate without an explicit yes. A marked-DRAFT analysis for attorney review is fine.

---

## What this skill does NOT do

- Analyze an existing relationship retroactively — this is prospective only.
- Draft the contractor agreement or SOW.
- Advise on remediation if misclassification has already occurred.
- State the law for any jurisdiction on its own — every test, factor, and
  carve-out must come from verified current research.
- Substitute for outside counsel on close calls — strict-test jurisdictions,
  contested prongs, and prior-audit situations should always get a human
  review before the engagement starts.

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

