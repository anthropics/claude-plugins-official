---
name: subpoena-triage
description: Triage a subpoena served on the company — classify it, analyze scope/burden/privilege, cross-check the portfolio, and produce an objections framework, compliance plan, and deadline calendar. Use when the user says "we got a subpoena", "served with a subpoena", or shares a subpoena, CID, or third-party document request to evaluate.
argument-hint: "[path-to-subpoena] [--slug=custom-slug]"
---

# /subpoena-triage

1. Read the subpoena from provided path.
2. Classify (third-party-docs / third-party-depo / party / CID / grand-jury).
3. If grand jury → stop, escalate per `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md`. Otherwise continue.
4. Load `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/_log.yaml` for cross-check. Load `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` → landscape, privilege conventions, escalation norms.
5. Follow the workflow and reference below.
6. Extract key fields, analyze scope/burden/privilege, produce objections framework + compliance plan + deadline calendar.
7. Write `~/.claude/plugins/config/claude-for-legal/litigation-legal/inbound/[slug]/triage.md`. Copy or link subpoena to `~/.claude/plugins/config/claude-for-legal/litigation-legal/inbound/[slug]/incoming.[ext]`.
8. Hand off: `/legal-hold --issue` if hold not in place; `/matter-intake` if materiality warrants; `/matter-briefing [slug]` if party subpoena in existing matter.

---

# Subpoena Triage

## Purpose

Subpoenas arrive with deadlines. The failure modes: missing the deadline, over-producing (privilege waiver, burden we should have objected to), under-producing (contempt exposure), or missing a motion-to-quash window. This skill classifies, analyzes, and produces a compliance plan with objections framework.

## Jurisdiction assumption

The rule cited in Step 0 is the operative one for this subpoena in this forum. Subpoena practice varies materially: federal (FRCP 45) vs. state equivalents, state-to-state variants, local rules, court-specific standing orders, and the subpoena type (trial, deposition, document production) all change objection deadlines, place-of-compliance limits, privilege-log requirements, and cost-shifting. Every rule output here is a starting-point heuristic — confirm currency and the local variant before asserting in writing.

## Side context

This skill is inherently defensive — a subpoena has been served on the recipient and the posture is respond/object/comply. Read `## Side` in the practice profile. If the user's default side is **plaintiff**, note that receiving a subpoena is common for plaintiffs too (witness subpoenas, third-party requests directed at the plaintiff's own records) but the framing here is always "subpoena served on us, how do we respond." If the user is **defense** (typical), the framing aligns with the default. If the matter has a different posture than the default (e.g., defense practitioner receiving a subpoena in a matter where they're pro se for a family member), prompt the user to confirm posture before proceeding.

## Load context

- The subpoena document (user provides path or drops it in-session)
- `~/.claude/plugins/config/claude-for-legal/litigation-legal/matters/_log.yaml` — for related matter lookup and legal hold status
- `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md` → landscape (regulators we deal with), house privilege conventions, escalation norms

## Workflow

### Step 0: Research the applicable rule

**Before analyzing this subpoena, research the applicable rule of civil procedure for the forum (FRCP 45 for federal, the state equivalent otherwise) and the subpoena type (trial, deposition, document production). Identify: place-of-compliance limits, objection deadlines (these often run from the EARLIER of the compliance date or a fixed number of days after service), privilege-log requirements, and who bears costs. Cite with pinpoint references. Verify currency — rules and local variants change. Flag grand-jury subpoenas for immediate criminal-counsel escalation.**

**No silent supplement.** If a research query to the configured legal research tool (Westlaw, CourtListener, Trellis, Descrybe, or firm platform) returns few or no results for the forum's rule, variant, or pinpoint, report what was found and stop. Do NOT fill the gap from web search or model knowledge without asking. Say: "The search returned [N] results from [tool]. Coverage appears thin for [rule / forum / variant]. Options: (1) broaden the search query, (2) try a different research tool, (3) search the web — results will be tagged `[web search — verify]` and should be checked against a primary source before relying, or (4) stop here. Which would you like?" A lawyer decides whether to accept lower-confidence sources; the skill does not decide for them.

**Source attribution.** Tag every rule reference, case, statute, and regulation in the triage output with where it came from: `[Westlaw]`, `[CourtListener]`, `[Trellis]`, `[Descrybe]`, or the MCP tool name for citations retrieved from a legal research connector; `[web search — verify]` for citations from web search; `[model knowledge — verify]` for citations recalled from training data; `[user provided]` for citations the user supplied (e.g., from the subpoena or prior matter work). Citations tagged `verify` carry higher fabrication risk and should be checked first. Never strip or collapse the tags — they are counsel's fastest signal about which citations to verify before asserting in objections or filings.

### Step 1: Classify

Subpoenas come in flavors with different rules; confirm the specifics against the rule you just researched:

- **Third-party document subpoena (civil)** — we're not a party to the litigation; someone wants our documents. Usual objection categories: relevance, burden, privilege, place-of-compliance / geographic reach.
- **Third-party deposition subpoena** — someone wants an employee to testify. Scope, relevance, burden; possible motion to quash; witness prep required.
- **Party subpoena** — we ARE a party; this is discovery in a litigation we're tracking. Treat as discovery, not inbound — it should map to an existing matter.
- **Regulatory civil investigative demand (CID)** — FTC, SEC, DOJ, state AG. Different rules, different posture; often more deferential but also more consequential.
- **Grand jury subpoena** — criminal. Escalate immediately to criminal counsel; different skill path (outside this skill's scope — flag for escalation).

### Step 2: Extract key fields

- **Issuing authority** — court (which), agency (which), counsel (if civil)
- **Issuing party** — who requested (if civil)
- **Case / matter caption** — the litigation we're being asked about
- **Document categories sought** — numbered list
- **Testimony topics** (if depo) — Rule 30(b)(6) designations
- **Deadline for response/objection** — date served + computing the response window per applicable rule
- **Production date** — date by which documents must be produced
- **Geographic scope** — custodians, locations, systems implicated
- **Custodian of record designation** — who at the company is the witness/signatory

### Step 3: Portfolio cross-check

- **Party subpoena → related to existing matter:** verify the caption matches a matter in `_log.yaml`. If yes, route to that matter's workflow; this triage is informational.
- **Third-party subpoena → caption we don't recognize:** capture the parties; log as standalone inbound.
- **Multiple subpoenas from same case:** flag coordinated issuance; a single response strategy may apply.

### Step 4: Analyze scope, burden, privilege

**Scope / relevance**
- Do the categories map to actual documents we plausibly have?
- Is any category a fishing expedition (overbroad, untethered to claims/defenses of the underlying case)?
- Place of compliance / geographic reach — apply the researched rule; limits differ by subpoena type (trial vs. document vs. deposition).

**Burden**
- Custodians implicated, systems searched, time period
- Estimated volume (rough: small / medium / large / extreme)
- Cost — third-party responders may have cost-shifting available; check the researched rule.

**Privilege**
- Attorney-client or work product likely implicated? (Almost always yes for anything legal-related; often yes for communications involving in-house or outside counsel.)
- Other privileges — trade secret, HIPAA (if applicable), state privilege, common interest
- Privilege log will be required — flag the format per `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md`

**Other objection grounds**
- Confidentiality — protective order needed?
- Duplicative — do they already have this from another party?
- Not possessed — we don't have what they're asking for (document with specificity)
- Improperly served — check the researched rule's service requirements

### Step 5: Objections framework

Draft a structured objections outline — not the final objections letter, but the outline of what objections apply and why. The user (often with outside counsel) finalizes.

Each objection:
- Legal basis — cite the pinpoint from the rule researched in Step 0
- Specific application to this subpoena (which categories, which custodians)
- Strength (strong / reasonable / weak)

### Step 6: Compliance plan

Even when objecting, we often produce some of what's requested. Plan:

- **Scope of likely production** — after objections, what we'd produce
- **Custodians to search** — names and systems
- **Date range**
- **Review protocol** — who reviews for privilege (us, outside counsel, contract reviewers)
- **Production format** — per the subpoena or per negotiated protocol (TIFF+load file, native, PDF)
- **Privilege log requirements** — format, fields

### Step 7: Deadlines

Use the deadlines identified in the Step 0 research. Note that objection deadlines often run from the EARLIER of the compliance date or a fixed number of days after service — do not default to a single number without checking the applicable rule and local variant.

- **Response deadline** — per researched rule; note if user needs more time (meet-and-confer to extend is standard)
- **Objection deadline** — per researched rule (federal / state rule + any local variant)
- **Production date** — if no objections succeed
- **Motion to quash window** — if pursuing that path, timing is critical

Calendar all of them. Immediate action item.

### Step 8: Write triage

Output: `~/.claude/plugins/config/claude-for-legal/litigation-legal/inbound/[slug]/triage.md`.

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

# Subpoena Triage

> **NOT A SUBSTITUTE FOR OUTSIDE COUNSEL.** This is a structured classification and scoping read to support fast decisions on deadlines, holds, and engagement. Every rule reference is a starting-point heuristic; jurisdiction-specific analysis, objections finalization, motions practice, and merit calls on privilege require licensed counsel familiar with the forum. Engage outside counsel for any subpoena above routine third-party document scope.

**Slug:** [slug]
**Served:** [YYYY-MM-DD]
**Served on:** [entity / registered agent]
**Incoming file:** [path]
**Classification:** [third-party-docs / third-party-depo / party / CID / grand-jury]

---

## Key fields

- **Issuing authority:** [court/agency]
- **Issuing party:** [name]
- **Case caption:** [caption]
- **Response deadline:** [date]
- **Production date:** [date]
- **Motion-to-quash window:** [date range]

## Categories sought (summary)

[numbered list, concise]

## Custodians / systems likely implicated

[list]

---

## Portfolio cross-check

**Related matter:** [slug or "none"]
**If party subpoena:** [routed to existing matter or new matter?]
**If third-party:** [standalone inbound]

---

## Scope & burden analysis

**Scope:** [relevance assessment by category]
**Burden estimate:** [small / medium / large / extreme — with reasoning]
**Geographic reach issues:** [any]

## Privilege analysis

*Privilege scoping is a first-pass read; final call is counsel's, not this skill's.*

**Attorney-client / work product likely implicated:** [yes/no + which categories] `[SME VERIFY]`
**Other privileges:** [trade secret, HIPAA, state, common interest] `[SME VERIFY]`
**Privilege log format required:** [per `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md`]

---

## Objections framework

*Every row below requires `[SME VERIFY]` before asserting in writing — jurisdiction, rule currency, waiver risk.*

| Objection | Legal basis | Applies to | Strength | SME verified? |
|---|---|---|---|---|
| Relevance | [rule] | [categories] | [strong/reasonable/weak] | [ ] |
| Burden | [rule] | [categories] | | [ ] |
| Privilege | A/C, WP | [all producing docs] | strong (always) | [ ] |
| Duplicative | [rule/doctrine] | [if applicable] | | [ ] |
| [other] | | | | [ ] |

---

## Compliance plan (if responding)

- **Scope of likely production:** [after objections]
- **Custodians / systems:** [list]
- **Date range:** [range]
- **Review protocol:** [who, how]
- **Production format:** [format]
- **Privilege log:** [format, est. entries]

---

## Deadlines (calendar these)

*All deadlines below come from the Step 0 rule research. `[SME VERIFY]` confirms the rule, variant, and computation for this forum and this subpoena type — state variants and local rules differ.*

- **Response deadline:** [date] `[SME VERIFY]`
- **Objection deadline:** [date] — cite: [rule + pinpoint] `[SME VERIFY]`
- **Meet-and-confer by:** [date] (typically before objection deadline) `[SME VERIFY]`
- **Production date:** [date]

---

## Immediate actions

- [ ] Legal hold issued — [yes/no] — if no, run `/legal-hold [slug] --issue` with subpoena scope
- [ ] Outside counsel engaged — [yes/who/TBD]
- [ ] Meet-and-confer scheduled — [date]
- [ ] Matter created in log — [yes/no/TBD — usually yes for anything above the smallest third-party docs subpoena]
- [ ] Insurance / cost-shifting analysis — [if burden is large]
- [ ] Internal escalation — [who]

---

## Recommendation

[Two paragraphs: what to do. Objection posture. Production posture. Whether outside counsel handles objections or we do. Whether to move to quash.]

---

## Citation verification

Every rule reference, case, statute, and regulation in this triage — including the Step 0 research citations, objection bases, and the privilege-log format pointer — is AI-generated and unverified. Before relying on any cite (especially in objections, a motion to quash, or correspondence with the issuing party), run a verification pass against a legal research tool (Westlaw, CourtListener, Trellis, Descrybe, or your firm's platform) for accuracy, good law status, and local variants. Fabricated or misquoted citations in filed documents have resulted in sanctions. Source tags on each citation (e.g., `[Westlaw]`, `[web search — verify]`) show where it came from; `verify` tags carry higher fabrication risk and should be checked first.
```

### Step 9: Hand off

**Before responding to the subpoena (serving objections, producing documents, appearing for deposition, or filing a motion to quash — any substantive response to the issuing party or court):** Read `## Who's using this` in `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md`. If the Role is Non-lawyer:

> Responding to a subpoena has legal consequences — missing a deadline risks contempt, over-producing waives privilege, under-producing risks sanctions. Have you reviewed this with an attorney? If yes, proceed. If no, here's a brief to bring to them:
>
> [Generate a 1-page summary: the subpoena type, issuing authority, deadlines, scope of what's sought, objections framework and strength, privilege and burden issues, proposed response posture, what could go wrong, what to ask the attorney.]
>
> If you need to find a licensed attorney, solicitor, barrister, or other authorised legal professional in your jurisdiction: your professional regulator's referral service is the fastest starting point (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent).

Do not proceed past this gate without an explicit yes. Triage, scoping, and internal calendaring do not require the gate — the response to the issuing authority does.

- If classified as **grand jury subpoena** → stop, flag for escalation per `~/.claude/plugins/config/claude-for-legal/litigation-legal/CLAUDE.md`, do not proceed with standard triage.
- If classified as **CID**: flag that regulator-specific norms apply; recommend outside regulatory counsel.
- Otherwise: offer to create a matter (usually yes — subpoenas are almost always material enough to track).
- If a legal hold isn't issued with subpoena scope, hand off to `/legal-hold --issue` immediately.

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

## What this skill does not do

- **Draft the final objections letter.** Produces the framework; the letter is drafted by user + outside counsel (future: a dedicated objections-draft skill).
- **Move to quash.** Surfaces the option; the motion is legal work that requires jurisdiction-specific analysis.
- **Validate rules across jurisdictions.** The Step 0 research produces the operative rule for this subpoena; the skill doesn't independently confirm currency or local variants. Flag for counsel verification before acting.
- **Handle grand jury subpoenas.** Escalates. This is outside the triage scope.
