---
name: international-expansion
description: >
  Reference: implementation-planning framework for international hiring — EOR
  vs. entity decision framing, cross-functional triggers for tax/finance/HR,
  structured outside-counsel briefing requests, and a persistent gap tracker.
  Loaded by /expansion-kickoff and /expansion-update; not invoked directly.
user-invocable: false
---

# International Expansion Skill

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/employment-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/employment-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Purpose

International hiring gets handled sloppily at scaleups because nobody owns
the full picture. Legal knows the employment-law questions but not the PE
risk questions. Finance knows the cost model but not the employee-representation
triggers. HR knows the comp benchmarks but not the Day 1 compliance requirements.

This skill doesn't replace any of those functions. It maps the terrain, drafts
the right questions for each stakeholder, produces a briefing request that
walks outside counsel through the country-specific issues, and creates a
tracker that keeps the project moving across sessions.

This skill assumes expansion is decided. It is not a "should we expand?"
framework.

This skill does not contain country-specific employment law. The substantive
rules change frequently and vary by role, headcount, and industry — the skill
routes every country through an outside-counsel briefing rather than relying
on a stored reference table.

## Load context

Read `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` → jurisdictional footprint, escalation table, any existing
expansion notes.

## Output header

Prepend the work-product header from `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` → `## Outputs` (it differs by user role — see `## Who's using this`).

## Workflow

### Step 1 — Information gathering

Ask all of the following in a single block:

> Before I build the expansion plan I need to understand the shape of this
> expansion. Please answer what you can — gaps in the answers are themselves
> useful data:
>
> **The expansion**
> - Which country?
> - What roles are you hiring? (Job function matters — a sales rep closing
>   deals creates different legal exposure than an engineer writing code)
> - How many hires are planned in the next 12 months?
> - When do you need the first person to start?
>
> **Current state**
> - Do you already have a legal entity in this country?
> - Have you used an EOR provider before? Are you already considering one?
> - Has tax or finance been looped in yet?
> - Do you have outside employment counsel in this country?
>
> **Strategic context**
> - Is this a long-term strategic commitment (building a real team) or
>   testing the market (one or two hires, see how it goes)?
> - Who is the executive sponsor making the structure decision?

Wait for responses before proceeding.

### Step 2 — EOR vs. entity framing

Do not make this decision. Frame it with enough precision that the CFO and
tax counsel can make it.

Work through the following factors against the intake answers and produce a
structured framing document:

**The core trade-off:**

| Factor | Points toward EOR | Points toward Entity |
|---|---|---|
| Headcount in 12 months | Fewer hires | More hires |
| Timeline to first hire | Short runway | Longer runway available |
| Strategic commitment | Testing the market | Long-term presence |
| Cost sensitivity | EOR markup acceptable | Scale makes entity more efficient |
| Control needs | Low — EOR employer handles local HR | High — want direct employer relationship |
| IP sensitivity | Lower | Higher — entity ownership cleaner |

Specific headcount break-even points, EOR markup ranges, setup costs, and
timelines vary by country and provider — do not hardcode them. Route those
questions to tax/finance and the EOR provider.

**PE risk flag (route to tax counsel):**
If roles include sales, business development, account management, or anyone
with authority to negotiate or sign contracts on behalf of the company —
flag this explicitly:

> PE Risk: [Role type] may create a taxable permanent establishment in
> [country] even before a legal entity exists. This is a tax question, not
> an employment question. Tax counsel must assess before the first hire.

**Produce the question for the CFO/tax:**

> Questions for your CFO and tax counsel:
> - At [N] hires over 12 months, at what headcount does entity setup become
>   more cost-effective than EOR (accounting for EOR markup, setup costs,
>   and ongoing compliance burden)?
> - [If PE-risk roles:] Do these role types create a taxable permanent
>   establishment in [country]? If yes, does that change the entity timeline?
> - If we start with EOR and convert to entity later, what are the transition
>   risks for the employees already on the EOR?
> - Who is our preferred EOR provider for this country, and have we vetted
>   their local compliance track record?

### Step 3 — Cross-functional triggers

For each function that needs to be looped in, state: what they need to do,
and the specific questions legal should ask them. Do not just say "loop in
finance." Draft the ask.

**Tax counsel** (always required before first hire)

What they need to do: PE risk analysis, determine whether entity is required
for tax purposes, advise on equity tax treatment in this jurisdiction.

Questions legal should ask:
- Does hiring a [role type] in [country] create a permanent establishment or
  taxable nexus before we have an entity?
- What is our exposure window if we start hiring before the PE question is
  resolved?
- How are our equity awards (RSUs/options) taxed in [country]? Do we need
  local tax counsel to advise employees at grant and vesting?
- If we set up an entity, what intercompany services agreement is needed
  between the subsidiary and the US parent?

**Finance / Payroll** (required before first paycheck)

What they need to do: identify local payroll provider (or confirm EOR handles
it), budget mandatory employer contributions, set up local banking if entity.

Questions legal should ask:
- Have we identified a local payroll provider? (If EOR: confirm EOR handles
  payroll including local social contributions)
- What are the mandatory employer contributions in [country] — pension,
  social insurance, healthcare — and are these budgeted in the comp model?
- How will equity grants be administered for employees in [country]? Has
  anyone modeled the employer-side tax withholding obligations at vesting?

**HR / Total Rewards** (required before offer is made)

What they need to do: benefits benchmarking, comp benchmarking against local
market, confirm mandatory vs. supplemental benefits.

Questions legal should ask:
- What benefits are legally mandatory in [country] vs. market-standard? (Do
  not want to accidentally promise more than required or less than market)
- Is our standard equity package competitive in this market, or does local
  practice differ significantly?
- Who will be this person's day-to-day manager — local or remote from HQ?
  (Affects employee-representation analysis and employment agreement terms
  in some jurisdictions)

**Outside counsel** (required — do not skip)

What they need to do: research and advise on the local employment framework
for this role and headcount, review/draft local employment agreement, flag
any structural issues with the proposed arrangement.

The outside-counsel briefing request in Step 4 is the agenda for this
engagement. Send it at the start — do not ask piecemeal.

### Step 4 — Country-specific briefing request

Instead of a stored country reference table, this skill produces a structured
outside-counsel briefing request. Substantive local law (entity requirements,
statutory benefits and contributions, termination protections, notice periods,
employee-representation / works-council / collective-bargaining obligations,
mandatory leave, restrictive covenants, data protection, work authorization)
varies by country *and* by role and headcount *and* by industry, and changes
frequently. Treat every country as a country that requires verification — do
not rely on the skill's own knowledge.

Draft the briefing request below, tailored to the intake answers:

**Outside counsel briefing request — [Country]**

> We are planning to hire [N] employees in [Country] starting [date], in the
> following roles: [roles]. Target headcount over 12 months: [N]. Preferred
> structure (subject to your advice and tax counsel): [EOR / entity /
> undecided]. We need a briefing covering each of the following. Please
> answer as questions with cites to primary law, not as a reference table —
> we want to be able to track changes over time.
>
> 1. **Entity and engagement structure** — what are our options (direct
>    hire via entity, EOR, contractor) and what are the practical and legal
>    trade-offs for this headcount and these roles?
>
> 2. **Employment contract requirements** — what form is required or standard?
>    What must be included? What cannot be included or is unenforceable?
>    What language or translation requirements apply?
>
> 3. **Termination** — what are the notice requirements and severance
>    obligations? How difficult is termination in practice (protected-cause
>    standards, social-selection rules in RIFs, reasonable-notice common-law
>    exposure)? What documentation standard should we establish from day one?
>
> 4. **Mandatory benefits and employer contributions** — what must we provide
>    by law (pension, social insurance, healthcare, paid leave, bonuses)?
>    What are the current employer contribution rates we should budget?
>    Please cite the controlling statute and verify currency.
>
> 5. **Restrictive covenants** — are non-competes enforceable? Under what
>    conditions and with what compensation requirements? What confidentiality
>    and IP assignment language holds up?
>
> 6. **Employee representation** — are there works council, employee
>    representation, union, or collective bargaining requirements? At what
>    headcount do they trigger? What consultation or co-determination rights
>    apply? Are we covered by any sectoral collective agreement even if we
>    are not unionized?
>
> 7. **Data protection** — what obligations apply to employee data? Is there
>    a data transfer mechanism needed for employee data flowing to the US?
>
> 8. **Work authorization** — what permits or visas are required for foreign
>    nationals? What are the processing timelines?
>
> 9. **Industry-specific rules** — are there sector rules, awards, or
>    collective agreements that apply to our industry regardless of whether
>    we are unionized?
>
> 10. **Contractor/independent-contractor risk** — what is the country's test
>     for classification, and what are the deemed-employment or reclassification
>     risks for any contractor arrangements we may consider?
>
> 11. **Equity / incentive compensation** — any local tax, securities, or
>     employment-law rules that govern how we grant RSUs, options, or other
>     equity here?
>
> 12. **Day 1 compliance** — what must be in place before the first employee
>     starts? Registration requirements, notices, filings, posters?
>
> 13. **Top 2-3 things that surprise US companies hiring here for the first
>     time** — what do you wish clients had asked you earlier? What has
>     *changed recently* that a US team might not have caught?

Add this briefing request to the expansion tracker as a single open item:
owner = Outside Counsel, status = open, with the full briefing agenda in
the questions field. If the jurisdiction is one the team has asked about
before, still send the briefing — this is a currency check, not a first
contact.

### Step 5 — Create the expansion tracker

Write a new file to `~/.claude/plugins/config/claude-for-legal/employment-legal/expansion-[country-slug].yaml` with all open items
identified in Steps 2-4. This file persists across sessions.

Format:

```yaml
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]
country: [Country name]
country_slug: [lowercase-hyphenated]
kickoff_date: [ISO date]
first_hire_target: [ISO date or "TBD"]
headcount_12mo: [N]
roles: [list]
strategic_commitment: [testing / long-term]
eor_or_entity: [EOR / entity / undecided]
outside_counsel_engaged: [true / false]
pe_risk_flagged: [true / false]
last_updated: [ISO date]

open_items:
  - id: 1
    category: [structure / tax / finance / hr / outside-counsel / compliance]
    item: "[what needs to happen]"
    owner: "[function or person]"
    status: [open / in-progress / done / blocked]
    due: [ISO date or null]
    questions:
      - "[specific question drafted in Steps 2-4]"
    notes: ""

  - id: 2
    [etc.]
```

Generate one open item per action identified across Steps 2-4. Do not collapse
multiple actions into one item — each item should be completable and
attributable to a single owner.

### Step 6 — Output

> **Jurisdiction assumption.** This plan frames the expansion to the single country identified in intake. Local employment law, tax rules, employee-representation obligations, and data-protection requirements vary materially by country, region, industry, and headcount, and change frequently. Every substantive local-law answer comes from the outside-counsel briefing request, not from this skill. If the plan is adapted for another country later, re-run the briefing.

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

## International Expansion: [Country] — [Date]

**First hire target:** [date]
**Headcount (12 months):** [N]
**Roles:** [list]
**Tracker:** ~/.claude/plugins/config/claude-for-legal/employment-legal/expansion-[slug].yaml

---

### EOR vs. Entity

[Framing from Step 2 — table, PE risk flag if applicable, questions for CFO/tax]

---

### Who needs to be looped in — and what to ask them

**Tax counsel** — [N] questions
[Questions from Step 3]

**Finance / Payroll** — [N] questions
[Questions from Step 3]

**HR / Total Rewards** — [N] questions
[Questions from Step 3]

**Outside counsel** — see briefing request below
[Full briefing request from Step 4]

---

### Open items ([N] total)

| # | Item | Owner | Status |
|---|---|---|---|
| 1 | [item] | [owner] | Open |
[etc.]

---

Run `/employment-legal:expansion-update [country]` to update status
as items close.
```

## What this skill does NOT do

- Advise on specific local employment law — that is outside counsel's job.
- Make the EOR vs. entity decision — frames it for the right decision-makers.
- Draft the local employment agreement — flags that outside counsel must do
  this.
- State country-specific rules from its own knowledge — every country is
  routed through an outside-counsel briefing.
- Substitute for outside counsel engagement — every new country requires
  local counsel, no exceptions.
