---
name: hiring-review
description: >
  Review an offer letter and any restrictive covenants — jurisdiction check
  included. Substantive rules (covenant enforceability, pay-transparency,
  salary-history limits, exemption criteria) are researched per hire, not
  stored. Use when the user says "review this offer", "can we use a
  non-compete here", "check this offer letter", "hiring in [state]", or
  attaches an offer.
argument-hint: "[offer letter file, or describe the hire]"
---

# /hiring-review

1. Load `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` → jurisdictional footprint, hiring review triggers, restrictive covenant policy.
2. Use the workflow below.
3. Check: jurisdiction, classification, restrictive covenants, background check compliance.
4. Flag anything that hits the jurisdiction-specific escalation table.

---

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/employment-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/employment-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Purpose

Offer letters are mostly boilerplate until they're not. The jurisdiction check
and the restrictive-covenant check are where this skill earns its keep. The
skill does not state the law — every jurisdiction-specific rule is researched
and cited at the time of review.

## Load context

`~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` → jurisdictional footprint, hiring review triggers, restrictive
covenant policy, offer letter template location.

## Output header

Prepend the work-product header from `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` → `## Outputs` (it differs by user role — see `## Who's using this`).

## Workflow

### Step 1: Jurisdiction

Where will this person work? Not where HQ is — where *they* are.

If remote: their home state/country governs. If hybrid: usually their home
state, but check the offer letter's choice-of-law clause (may or may not hold
up).

Check the jurisdiction table in `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` for this state/country. If it's
not in the table — new jurisdiction — flag that: "First hire in [state]. The
jurisdiction table doesn't cover this. Research needed before offer goes out."

### Step 2: Classification

Exempt or non-exempt? The offer should say, and the role should support it.

| Test | Check |
|---|---|
| Salary basis | Paid a fixed salary regardless of hours? |
| Salary level | Above the applicable federal and state thresholds? |
| Duties test | Does the role actually involve the exempt duties? |

> **Research before calling exemption.** Identify the currently operative
> salary thresholds (federal and state — several states index annually and
> several have tiered thresholds by employer size) and the applicable duties
> test(s) for the role. Cite primary sources. Verify currency.

If the offer says exempt but the role description does not support the
exempt duties — flag it. Misclassification is expensive.

### Step 3: Restrictive covenants

If the offer includes a non-compete, customer non-solicit, employee
non-solicit, or confidentiality/IP assignment:

> **Research enforceability before advising.** For the employee's jurisdiction,
> identify the currently operative rules on each restrictive covenant in the
> offer. Non-compete enforceability in particular has shifted in multiple
> states in recent years through legislation, agency action, and litigation —
> do not rely on prior memory of which states permit non-competes. Note:
> - The specific type of covenant (non-compete, customer non-solicit, employee
>   non-solicit, confidentiality/trade-secret, IP assignment) — each has its
>   own rules.
> - Any salary or income threshold that conditions enforceability.
> - Any notice, consideration, or garden-leave requirements.
> - Any industry-specific carve-outs (e.g., healthcare, broadcasting).
> - Duration and geographic-scope reasonableness tests.
> - Choice-of-law and choice-of-forum enforceability for out-of-state covenants.
> Cite primary sources. Verify currency.

Per `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` restrictive covenant policy: does this hire even get one?
Some companies use them selectively. Apply the house policy first, then
research overlays from the jurisdiction.

> **No silent supplement.** If a research query to the configured legal research tool returns few or no results for the jurisdiction's exemption thresholds, restrictive-covenant rules, pay-transparency law, or any other item you're researching, report what was found and stop. Do NOT fill the gap from web search or model knowledge without asking. Say: "The search returned [N] results from [tool]. Coverage appears thin for [jurisdiction / topic]. Options: (1) broaden the search query, (2) try a different research tool, (3) search the web — results will be tagged `[web search — verify]` and should be checked against a primary source before relying, or (4) flag as unverified and stop. Which would you like?" A lawyer decides whether to accept lower-confidence sources.
>
> **Source attribution.** Tag every citation in the review with where it came from: `[Westlaw]`, `[CourtListener]`, or the MCP tool name for citations retrieved from a legal research connector; `[web search — verify]` for web-search citations; `[model knowledge — verify]` for citations recalled from training data; `[user provided]` for citations the user supplied. Citations tagged `verify` carry higher fabrication risk and should be checked first. Never strip or collapse the tags.

### Step 4: Jurisdiction-specific requirements

Check the `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md` table for this jurisdiction. Common categories to
research for each hire:

- **Pay transparency** — does the jurisdiction require a salary range in the
  posting? If so, is this offer within the posted range? Research the current
  rule (including any recent amendments or new enforcement guidance).
- **Ban-the-box** — does the jurisdiction or locality restrict the timing or
  scope of criminal-history inquiries?
- **Salary-history limits** — is the jurisdiction one that restricts asking
  about or relying on prior salary? Research current rules and recent
  amendments.
- **Required offer-letter or onboarding notices** — some jurisdictions require
  specific notices at offer or hire (wage-notice statutes, sick-leave notices,
  etc.). Research what is currently required and whether a template exists.

Cite primary sources. Verify currency.

### Step 5: Offer letter content

Read the letter. Check:

**Employment-at-will is US-only.** "At-will" means either party can terminate without cause or notice (subject to statutory exceptions). This concept does not exist outside the US:

- **US (most states):** At-will is the default. Offer letters often include "at-will" language to defeat implied-contract arguments. Check that it's present if US.
- **Montana:** Not at-will — Wrongful Discharge from Employment Act requires cause after probation.
- **UK:** No at-will. Employees have statutory protections from day 1 (unfair dismissal after 2 years of service, automatic unfair dismissal for protected reasons from day 1). The offer letter must contain the written statement of particulars (ERA 1996 s.1): pay, hours, notice period, holidays, pension, disciplinary/grievance procedures.
- **EU:** No at-will. Termination requires cause, notice, and often works council consultation or collective redundancy procedures. The offer letter requirements vary by member state but notice periods and written particulars are standard.
- **Australia:** No at-will. Fair Work Act minimum notice periods, unfair dismissal protections, NES.
- **Canada:** No at-will. Common law reasonable notice (can be months), ESA minimums, wrongful dismissal exposure.
- **Singapore, other APAC:** No at-will. Employment Act and contract-based protections.

**Check for at-will language ONLY if the jurisdiction is US.** For non-US jurisdictions, check instead for: notice period (and whether it meets statutory minimum), the written-statement particulars the jurisdiction requires, probation period terms, and any jurisdiction-specific mandatory clauses.

**Never recommend adding at-will language to a non-US offer letter.** It's legally meaningless, it can conflict with mandatory statutory terms, and it signals to the employee's lawyer that the employer didn't understand the jurisdiction.

- At-will language present and not undermined elsewhere (US only — see above)
- Contingencies clear (background check, reference, I-9 if US / right-to-work verification for the applicable jurisdiction)
- Start date, title, salary, reporting structure stated
- Equity terms (if any) consistent with the plan
- Integration clause so the letter is the whole deal
- For non-US: notice period meets statutory minimum, jurisdiction's required written-statement particulars included, probation period compliant with local rules

## Output

> **Jurisdiction assumption.** This review applies the rules of the employee's work jurisdiction identified in Step 1. Enforceability of restrictive covenants, exemption thresholds, pay-transparency obligations, salary-history limits, and required notices vary materially by state and locality, and several have shifted recently. If the candidate's work location changes, or the role spans jurisdictions, this review may not apply as written.

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

## Hiring Review: [Candidate] — [Role] — [Jurisdiction]

**Overall:** [Clear to send | Changes needed | Escalate]

### Jurisdiction: [State/Country]
[Jurisdiction table entry. Any auto-escalate triggers that fire.]

### Classification
[Exempt/non-exempt call, grounded in researched thresholds and duties test.
Any flags.]

### Restrictive covenants
[If any. Enforceability call per researched jurisdiction rules, with pinpoint
cites and currency note. Suggested changes.]

### Jurisdiction-specific requirements
[Pay transparency, notices, salary-history rules, etc. — each researched and
cited, or flagged as needing research.]

### Offer letter
[Any issues with the letter itself]

### Action items
- [ ] [specific change needed before sending]
```

## Consequential-action gate (make an offer)

**Before producing a "Clear to send" recommendation or a final offer letter for signature:** Read `## Who's using this` in `~/.claude/plugins/config/claude-for-legal/employment-legal/CLAUDE.md`. If the Role is **Non-lawyer**:

> Making an offer has legal consequences — the letter is a contract, and restrictive covenants, classification, and jurisdiction-specific terms are difficult to reset once sent. Have you reviewed this offer with an attorney? If yes, proceed. If no, here's a brief to bring to them:
>
> - Candidate, role, jurisdiction (where they'll actually work)
> - Classification call (exempt/non-exempt) and why
> - Restrictive covenants in the offer and the enforceability analysis
> - Jurisdiction-specific requirements that apply (pay transparency, wage notices, salary-history rules)
> - Open questions and what's unresolved
> - What could go wrong (misclassification liability, unenforceable non-compete, missing required notice, conflicting at-will language)
> - What to ask the attorney (is this the right form for this jurisdiction; can we use our standard non-compete here; what notices need to go with the letter)
>
> If you need to find an attorney, solicitor, barrister, or other authorised legal professional: contact your professional regulator (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent) for a referral service.

Do not produce a "Clear to send" output past this gate without an explicit yes. A marked-DRAFT flagged for attorney review is fine.

---

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

## What this skill does not do

- Draft the offer letter — reviews it.
- Make the hire decision — checks the paperwork.
- State restrictive-covenant or exemption rules from memory — every
  jurisdiction-specific call is based on researched, cited sources verified
  for currency.
- Research a new jurisdiction in depth on its own — flags that research is
  needed, and uses `wage-hour-qa` or outside counsel to fill in.
