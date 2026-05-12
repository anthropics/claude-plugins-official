---
name: termination-review
description: >
  Termination review — high-risk flag detection, severance + release, and
  final pay timing by jurisdiction. Jurisdiction-specific rules and release
  consideration periods are researched per review, not stored. Use when the
  user says "reviewing a termination", "can we fire this person", "term
  review", or describes a termination scenario.
argument-hint: "[describe the termination, or attach documentation]"
---

# /termination-review

1. Load `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` → termination review triggers, high-risk flags, severance practice, jurisdiction rules.
2. Use the workflow below.
3. Walk the checklist. Check every high-risk flag.
4. Final pay timing per employee's jurisdiction. Severance + release if applicable.
5. If any high-risk flag fires: escalate per table, don't proceed without sign-off.

---

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/employment-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/employment-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Purpose

Most terminations are fine. A few are lawsuits waiting to happen. This skill
runs the checklist that catches the second kind before the decision is final.
The skill does not state the law — every jurisdiction-specific rule and
release-period requirement is researched and cited at the time of review.

## Load context

`~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` → termination review triggers, high-risk flags, standard severance,
jurisdiction table.

## Output header

Prepend the work-product header from `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` → `## Outputs` (it differs by user role — see `## Who's using this`). Match the memo format from seed term memos referenced in that config where one exists. The work-product header is always first.

## Workflow

### Step 1: The basic facts

- Employee name (or role if staying abstract)
- Jurisdiction (where they work)
- Reason for termination (performance, misconduct, RIF, position elimination)
- How long employed
- Age (relevant to release requirements for older-worker protections)
- Whether any other employees are being terminated as part of the same
  decisional unit or program (relevant to group-termination release rules)
- When is the planned term date

### Step 2: High-risk flag scan

This is the most important step. Check every flag from `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md`. Default
set:

| Flag | Why it's high-risk | Check |
|---|---|---|
| **Recent complaint** | Retaliation claim | Has this employee filed any complaint (HR, ethics hotline, regulatory) recently? |
| **Protected leave** | Leave-law interference/retaliation | Currently on or recently returned from protected leave (FMLA/state equivalents, disability, parental, military)? |
| **Protected class + timing** | Discrimination claim | Protected class AND recently disclosed/visible (pregnancy announcement, religious accommodation request, disability disclosure)? |
| **Whistleblower** | Federal and state whistleblower statutes | Has this employee raised concerns about illegality, safety, fraud? |
| **Thin documentation** | "Why now?" problem | For performance terms: is there a PIP, written warnings, documented feedback? Or did this come out of nowhere? |
| **Comparator problem** | Disparate treatment | Is someone else doing the same thing and not being terminated? |
| **Contract/handbook promise** | Breach | Does the offer letter, handbook, or any writing promise a process that isn't being followed? |
| **Exempt misclassification** | FLSA + state wage claim with liquidated damages | See the classification check below. Fires on state + classification + title. |

**Exempt/non-exempt classification flag.** Fire this flag when ALL of the
following are true:

1. The employee works in a state with a high exempt salary threshold — **CA,
   NY, WA, CO, AK** (and any other state listed in
   `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` →
   `## Wage & hour` → Known classification risk areas as a high-threshold
   state) — **AND**
2. The employee is classified **exempt** (salaried, no overtime) — **AND**
3. The employee's title contains **"supervisor," "lead," "coordinator,"
   "analyst," "administrator,"** or **"specialist"** (case-insensitive, and
   any equivalent-scope title the practice profile flags as risky).

When all three fire, emit:

> 🔴 **Potential exempt misclassification** — [title] earning $[X] in
> [state]. The exempt salary threshold in [state] is approximately $[Y]
> `[model knowledge — verify]`. Before termination, route to
> `/employment-legal:wage-hour-qa` for a classification check — a misclassified
> employee who's terminated has a ready-made FLSA and state-wage claim with
> liquidated damages, attorneys' fees, and (in CA) PAGA exposure, which
> the separation agreement may not be able to release cleanly. A terminated
> plaintiff with unpaid-OT exposure is the most litigated wage-and-hour
> fact pattern in these states.

Do not suppress this flag because the title "looks managerial" — the whole
premise of the misclassification claim is that titles lie. Route to
`/employment-legal:wage-hour-qa` for the actual duties-and-salary test.

**If a back-pay number is being computed as part of this review (severance
modeling, settlement posture, exposure estimate), do NOT compute it in this
skill.** Route to `wage-hour-qa` → Step 2a and use its regular-rate
scaffold: §207(e) inclusions (non-discretionary bonuses, commissions,
shift diffs) in the regular rate, 0.5× premium when straight time was
already paid for OT hours (else 1.5×), liquidated damages under §216(b),
and 2-year / 3-year willful SOL under §255(a). Every back-pay number
carries `[verify — consult wage-and-hour counsel before asserting or
paying]`. A clean-looking wrong number here is the specific failure mode
this scaffold prevents.

**Any flag fires → escalate per `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` before the term proceeds.** Not
after. Before.

### Step 3: Jurisdiction-specific requirements

> **Research the applicable rules for the employee's jurisdiction before
> finalizing the plan.** Specifically:
>
> - Final-pay timing — this varies widely by state and often depends on
>   whether the employee was terminated or resigned. Research the currently
>   operative rule, including any waiting-time or late-pay penalties.
> - Accrued-PTO payout — research whether the jurisdiction requires payout,
>   and any interaction with accrual-cap or use-it-or-lose-it policies.
> - Required notices — research any jurisdiction-specific notices required at
>   termination (e.g., state unemployment, continuation-coverage notices
>   beyond federal COBRA, benefits continuation).
> - Mass-layoff / plant-closing notices — research federal WARN Act and any
>   state "mini-WARN" or local ordinance that may apply if this is part of a
>   larger reduction. Coverage thresholds and notice periods differ.
>
> Cite primary sources. Verify currency.
>
> **No silent supplement.** If a research query to the configured legal research tool returns few or no results for the jurisdiction's final-pay, PTO, notice, or WARN rule, report what was found and stop. Do NOT fill the gap from web search or model knowledge without asking. Say: "The search returned [N] results from [tool]. Coverage appears thin for [jurisdiction / rule]. Options: (1) broaden the search query, (2) try a different research tool, (3) search the web — results will be tagged `[web search — verify]` and should be checked against a primary source before relying, or (4) stop here and flag for attorney verification. Which would you like?" A lawyer decides whether to accept lower-confidence sources.
>
> **Source attribution.** Tag every citation in the plan — final-pay rule, PTO rule, notices, WARN / mini-WARN, OWBPA consideration periods, state release restrictions — with where it came from: `[Westlaw]`, `[CourtListener]`, or the MCP tool name for citations retrieved from a legal research connector; `[web search — verify]` for web-search citations; `[model knowledge — verify]` for citations recalled from training data; `[user provided]` for citations the user supplied. Citations tagged `verify` carry higher fabrication risk and should be checked first. Never strip or collapse the tags.

### Step 4: Severance and release

Per `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` → standard severance:

- Is severance being offered? Per formula or discretionary?
- Release required? (Usually yes if paying severance — that's the
  consideration.)

> **Research the applicable release-consideration rules.** If the employee is
> 40 or over, federal law (OWBPA) imposes specific requirements that affect
> the consideration period, revocation period, required advisements, and —
> for group terminations — required decisional-unit disclosures. The specific
> consideration period differs between an individual termination, a group
> RIF, and a group exit incentive; the rule also depends on the employee's
> age and the number of employees affected. Do not state the day count from
> memory — research the currently operative rule for the specific situation
> and cite primary sources. Also research any state-law analogs or parallel
> release requirements. Verify currency.

Separately, consider whether any of the following apply to the release:
- State-specific waiver restrictions (some states limit what can be released
  or require specific language).
- Federal or state restrictions on non-disclosure or non-disparagement
  clauses that relate to sexual harassment, discrimination, or other
  protected categories.
- Separation-agreement rules on NLRA-protected activity.

### Step 5: Documentation check

For performance terminations especially:

- Is there a paper trail? Written warnings, PIP, feedback docs?
- Does the paper trail tell a consistent story?
- Is there anything in writing that contradicts the reason (recent positive
  review, bonus, promotion)?

The "why now" question: if this person has been underperforming for a year,
what changed? The answer should be documented.

## Output

> **Research-connector pre-flight.** Before emitting the memo, check whether a legal research connector is reachable for this session — Westlaw, CourtListener, or any firm-configured research MCP. Collect this into the reviewer note per CLAUDE.md `## Outputs`: if no connector returns results in Step 3 (or none is configured at run time), record it in the **Sources:** line of the reviewer note — e.g., `not connected — cites from training knowledge; the highest-fabrication topics in termination-law memos are final-pay timing, OWBPA group/individual distinctions, state-specific NDA / non-disparagement rules (e.g., CA SB 331), and NLRB positions (e.g., McLaren Macomb) — spot-check those first`. Per-citation `[model knowledge — verify]` tags remain inline. Do not emit a standalone banner above the memo.

> **Jurisdiction assumption.** This review assumes the employee's jurisdiction as stated in Step 1 and any defaults from `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` → Jurisdictional footprint. Employment rules, final-pay timing, release requirements, and notice obligations vary materially by jurisdiction. If the employee works in a different state or country, or if choice-of-law is contested, this analysis may not apply as written.

Match the memo format from seed term memos referenced in `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md`. If none:

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

## Termination Review: [Role/Name] — [Date]

**Jurisdiction:** [State]
**Reason:** [Performance / Misconduct / RIF / Elimination]
**Planned date:** [Date]

---

### Bottom line

[Can you proceed / Need to fix X first / Stop — one-sentence why]

---

### High-risk flags

[Every flag from Step 2. ✅ Clear or 🔴 FLAG with detail.]

**Escalation:** [None needed | Escalate to [name] before proceeding — [which flag]]

---

### Jurisdiction requirements ([State])

- Final pay: [researched rule and cite; state whether PTO is included per the
  researched rule and any team policy]
- Required notices: [list, each researched and cited]
- Mass-layoff notice (if applicable): [researched rule and cite]

---

### Severance and release

- Severance: [amount per formula / none]
- Release: [required / not — if required, research and apply the
  consideration-period, revocation-period, advisement, and (for groups)
  decisional-unit-disclosure requirements that govern this specific
  situation; cite primary sources and verify currency]
- [Any state-law release rules or non-disclosure/non-disparagement
  restrictions that apply]

---

### Documentation

[Assessment of paper trail. Gaps flagged.]

---

### Go / No-go

[Clear to proceed | Proceed with changes below | Hold — escalation pending]

### Checklist for term day

- [ ] Final paycheck ready, correct amount, delivered per researched rule
- [ ] Continuation-coverage notices (COBRA / state analogs) prepared
- [ ] [State] unemployment notice prepared
- [ ] Severance agreement (if applicable) with the consideration period
      required for this specific situation
- [ ] Return of property / access cutoff coordinated
- [ ] [etc.]
```

## Consequential-action gate (terminate an employee)

**Before producing a "Go" recommendation or a term-day checklist marked ready:** Read `## Who's using this` in `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md`. If the Role is **Non-lawyer**:

> Terminating an employee has legal consequences — wrongful-termination, discrimination, retaliation, and wage-law claims all trace back to how this decision is structured. Have you reviewed this termination with an attorney? If yes, proceed. If no, here's a brief to bring to them:
>
> - Employee, jurisdiction, reason, planned date
> - Every high-risk flag the review surfaced (recent complaint, protected leave, protected class + timing, whistleblower, thin documentation, comparator, contract/handbook promise) — with detail
> - Jurisdiction-specific findings (final pay, PTO, required notices, mass-layoff rules) and where they were cited from
> - Severance/release analysis, including any OWBPA/older-worker-protection angles
> - Open questions and what's unresolved
> - What could go wrong (the claim theory this fact pattern supports)
> - What to ask the attorney (is this a clean term; do we need more documentation first; does the release need specific language; do we need to stagger decisional units)
>
> If you need to find an attorney, solicitor, barrister, or other authorised legal professional: contact your professional regulator (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent) for a referral service. Employment is one of the practice areas where a short consult before the termination meeting consistently outvalues a post-termination claim defense.

Do not produce a "Clear to proceed" output past this gate without an explicit yes. A marked-DRAFT flagged for attorney review is fine.

---

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

## What this skill does not do

- Make the termination decision. It checks the decision.
- Have the conversation. The manager does that.
- State release or jurisdiction rules from memory — every rule is researched
  and cited at the time of review.
- Guarantee no lawsuit. It reduces the risk by catching the obvious problems.
