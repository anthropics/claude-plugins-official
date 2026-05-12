---
name: aia-generation
description: >
  Run an AI impact assessment — structured intake, risk analysis, regulatory
  classification per regime in scope, policy consistency diff, and recommendation
  with conditions. Uses the house-style structure learned from the seed impact
  assessment in `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`.
  Use when user says "impact assessment for", "assess this AI use case", "run an
  AIA", "generate an AIA", "we need to document this AI system", "AI risk
  assessment for X", or follows a conditional triage result.
argument-hint: "[describe the use case or system, or pass a triage result]"
---

# /aia-generation

1. Read `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`. Confirm impact assessment house style is populated.
2. Determine risk track (fast or full) from governance tier and use case characteristics, using the framework below.
3. Run intake — conversational, not a form.
4. Regulatory classification for each regime in the footprint — research tier, prohibited-practice exposure, and applicable obligations; cite primary sources.
5. Write assessment in house style (from seed doc, or default if none captured).
6. Policy diff against `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` AI policy commitments.
7. Output: assessment doc + conditions list + handoff flags (privacy PIA, vendor review if needed).

```
/ai-governance-legal:aia-generation "AI résumé screening for HR"
```

---

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/ai-governance-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Purpose

An AI impact assessment is a documented decision, not a form. It answers: what
does this AI system do, how does it reach its outputs, who's affected if it's
wrong, what's the oversight, and is it okay to deploy. This skill structures that
conversation and writes the output in this team's format — the one learned from the
seed impact assessment during cold-start.

An AI impact assessment is not the same as a PIA. A PIA asks whether personal data
is handled lawfully. An AIA asks whether the AI system is designed and deployed
responsibly. They often need to happen in parallel; they're not substitutes.

## Load house style

Read `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` → `## Impact assessment house style`. That has:
- What triggers an impact assessment at this company
- The structure template extracted from the seed assessment
- Typical depth
- Who signs off

If the seed structure is in `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`, **use it**. The point is that this assessment
looks like the other assessments this team produces.

**Jurisdictional scope.** This assessment applies the regulatory regimes listed in `## Regulatory footprint` in `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`. AI legal rules, risk classifications, and deployment obligations vary materially by jurisdiction and are moving fast. If this system is (or will be) deployed outside that footprint, or if a choice-of-law question is in play, this analysis may not apply as written — re-run or expand the footprint.

---

## Step 0: Is an impact assessment needed?

Check the trigger criteria in `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`.

**Also check these regardless:**
- Does this AI make or materially influence a decision affecting a person (employment,
  credit, access, pricing, content moderation)?
- Does this AI process personal data about individuals?
- Is this a customer-facing AI system rather than purely internal?
- Does this AI use a third-party model where the company is the deployer?
- Is the use case in the elevated or high governance tier per `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`?

If none of the above and the house trigger isn't met:
> "Doesn't look like this needs a full impact assessment. Here's a one-paragraph
> record for the file explaining why — in case anyone asks later."

---

## Step 1: Risk track

Before intake, determine which track to run. The tier definitions and the fast-track criteria come from `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` (`## Use case registry` and `## Governance tiers`), not from any hardcoded regime-specific framework.

Research the applicable risk classification framework for each regime in the user's regulatory footprint. Many regimes distinguish by risk tier, affected population, and decision consequentiality — research the specific criteria. Note that most regimes treat employee data as personal data and employee monitoring as consequential; don't assume internal-only systems are out of scope.

> **No silent supplement.** If a research query to the configured legal research tool (Westlaw, EUR-Lex, regulator sites, or firm platform) returns few or no results for a regime's risk tiers or triggers, report what was found and stop. Do NOT fill the gap from web search or model knowledge without asking. Say: "The search returned [N] results from [tool]. Coverage appears thin for [regime / topic]. Options: (1) broaden the search query, (2) try a different research tool, (3) search the web — results will be tagged `[web search — verify]` and should be checked against the issuing authority before relying, or (4) flag as unverified and stop. Which would you like?" A lawyer decides whether to accept lower-confidence sources.
>
> **Source attribution tiering.** Tag every citation in the AIA — regulatory text, delegated acts, guidance, standards — with its source. For model-knowledge citations, use one of three tiers rather than a single blanket "verify" tag:
>
> - `[settled]` — stable, well-known statutory and regulatory references unlikely to have changed (e.g., GDPR Art. 22 as a concept, the existence of Regulation (EU) 2024/1689 as the EU AI Act). Still verify before certifying, but lower priority.
> - `[verify]` — model-knowledge citations that are real but should be verified: specific delegated / implementing acts, regulator guidance, NYC DCWP rules, Colorado AI Act provisions, harmonized standards, effective dates, EEOC guidance, and anything post-2023.
> - `[verify-pinpoint]` — pinpoint citations (specific EU AI Act article numbers, annex references, Colorado AI Act subsections, NYC LL 144 rule sections, sub-paragraph letters) carry the highest fabrication risk and should ALWAYS be verified against a primary source. EU AI Act article numbers in particular shifted during consolidation; every pinpoint cite to the Act should be verified against the Official Journal text.
>
> Tool-retrieved citations keep their source tag (`[Westlaw]`, `[EUR-Lex]`, `[regulator site]`, or the MCP tool name); web-search citations remain `[web search — verify]`; user-supplied citations remain `[user provided]`. The tiering surfaces the real verification work — a reader who verifies everything verifies nothing. Never strip or collapse the tags.
>
> **For non-lawyer users, uncertain dates go in a confirm-list, not inline.** A `[verify]` tag on "effective February 1, 2026" reads as "effective February 1, 2026" to a CISO who doesn't know what `[verify]` means. Read `## Who's using this` in `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`. If Role is **Non-lawyer** and a date, deadline, phase-in, threshold, or effective-date assertion is uncertain (would carry `[verify]` or `[verify-pinpoint]` if inline), replace the inline assertion with "effective date: confirm with counsel" (or "threshold: confirm with counsel", etc.) and collect all uncertain assertions in a final AIA section titled:
>
> > **Things I'm not certain about — ask your attorney to confirm before relying on this:**
>
> List each uncertain item there with (1) what I said, (2) what I'm uncertain about, (3) why it matters to the assessment. This prevents a non-lawyer reader from mistaking a flagged best-guess for a checked fact. Lawyer-role users get the inline `[verify]` treatment — they know what the tag means.

**Fast track vs. full assessment:** `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` defines what qualifies for abbreviated treatment. If `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` doesn't define fast-track criteria, default to full assessment and ask the user what criteria they want captured for next time.

If in doubt, run the full assessment. A fast track that turns out to be wrong
is worse than a thorough assessment on something low-risk.

---

## Step 2: Intake

Before writing anything, get answers to these. Conversational is fine — this
is not a form to send them.

### The system

- What does the AI do? Describe it in plain language, not marketing copy.
- Which model or vendor is powering it? Fine-tuned or off-the-shelf?
- Where does it sit in the workflow — is it assistive (human reviews output),
  augmentative (human can override but usually doesn't), or automated (no human
  in the loop)?
- What's the output — generated text, a score, a classification, a recommendation,
  an action?

### Who's affected

- Who does the AI's output act on — employees, customers, third parties?
- If the AI produces an error (false positive, false negative, hallucination), who
  bears the harm and what's the worst realistic case?
- Are any vulnerable groups disproportionately in scope — minors, job applicants,
  people in financial distress, patients?

### Inputs and data

- What data does the AI take in?
- Does it take in personal data? Whose?
- Was the model trained on data from this company, or is it a foundation model
  with no company-specific training?
- Where does input data go — does it leave the perimeter to a third-party model
  API?

### Decisions and oversight

- Does the AI output trigger an action automatically, or does a human decide what
  to do with the output?
- If there's human review: how often does the human actually change the AI's output?
  (If the answer is "rarely" — the human isn't really reviewing; they're rubber-stamping.)
- Is there an appeals or correction process for people affected by the AI's outputs?
- Who is accountable for the AI system's outputs — is there a named owner?

### Accuracy and failure

- What's the known or estimated error rate? What testing has been done?
- What happens when the AI is wrong — is the error surfaced, logged, corrected?
- Has bias testing been done? Against what demographic groups?

### Deployment stage and scale

Ask:
- **Stage:** "Is this system (a) proposed and not yet built, (b) in pilot, (c) live in production, or (d) live and scaled?"
- **Scale:** "Roughly how many individuals are affected per [month/year]? How long has it been running?"
- **History:** "Has it been assessed before? Has it produced decisions that were challenged, appealed, or reversed?"

Stage changes the assessment: a proposed system gets a design review (can we build it safely?). A pilot gets a design review plus a "before you scale" gate. A live system gets a retrospective impact check (has it caused harm?) AND a go-forward review. A live-and-scaled system gets all of the above plus a remediation plan if issues are found, because you can't just turn it off.

---

## Step 3: Regulatory classification

**Step 3 pre-check — footprint freshness.** Before iterating over the captured `## Regulatory footprint`, compare the use case's affected population and decision type (from Step 2) against the footprint as written. The footprint was set at cold-start, based on the company's operating posture at that moment. If the use case introduces an affected population (e.g., children, employees in a new state, EU data subjects) or a decision type (e.g., hiring, creditworthiness, health diagnosis, law enforcement, critical infrastructure) that the footprint does not contemplate, **re-derive the applicable regimes rather than iterating over the stale list.**

Say to the user:

> "The practice profile's regulatory footprint was set for [affected populations / decision types captured at cold-start]. This use case affects **[new population or decision type — e.g., employees in Colorado, minors under 13, credit decisions, biometric identification]**, which is not in the captured footprint. I'm going to re-derive the applicable regimes from the company's operating jurisdictions ([list from `## Company profile`]) and this use case's decision type ([Y]), rather than use the stale footprint. If this use case is representative of work you expect to see more of, update `## Regulatory footprint` at the end of this run so the next AIA doesn't have to re-derive."

A common failure mode: the footprint lists EU AI Act + GDPR + NYC Local Law 144, and the use case is a hiring system being deployed into Illinois and Colorado. The footprint has no Illinois or Colorado entry, so iterating over it silently misses IL AIVIA, the new Colorado AI Act deployer obligations, and BIPA implications of any biometric component. Re-derive.

A second failure mode: the footprint was set before a regime that now matters existed (or took effect). If re-derivation surfaces a regime not in the footprint, flag it in the output's recommendation section, cite the authority, and recommend updating the footprint.

For each regime in `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` → `## Regulatory footprint` that applies to this system — **plus any regime surfaced by the re-derivation above** — research the currently operative risk classification framework and determine where the system lands.

Research tasks:
- What is the regime's own tier taxonomy (e.g., prohibited / high-risk / limited / minimal, or the regime's equivalent)?
- What are the criteria for each tier? Cite primary sources with pinpoint references.
- Which tier does this system fall into given its function, affected parties, and decision consequentiality?
- Are there prohibited practices the system might touch? Treat any possible match as critical — flag immediately.
- Are there transparency obligations that apply regardless of tier (disclosure that a user is interacting with AI, labeling of AI-generated content, notice to people subject to automated decisions)?
- If the company is a builder providing a general-purpose or foundation model, what provider-level obligations apply (technical documentation, training data transparency, copyright compliance, systemic-risk testing)?
- **Does any regime in the footprint require a separate fundamental-rights impact assessment (FRIA)?** EU AI Act Art. 27 requires a FRIA for certain deployers of high-risk AI systems (public bodies and private entities providing public services, plus certain creditworthiness and insurance-risk-assessment use cases). Check each regime for an equivalent fundamental-rights or human-rights impact assessment that is a distinct deliverable from this AIA. If a FRIA (or regime equivalent) is required, flag it as a separate deliverable in the recommendation and conditions — do not treat this AIA as a substitute.

Don't assume internal-only systems are out of scope — most regimes treat employee data as personal data and employee monitoring as consequential. Verify the specific rule.

**Provider-vs-deployer split (when `AI role: Both`).** If `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` → `## Company profile` → `AI role` is `Both` (the company is both a provider/builder and a deployer), Section 6 MUST include a provider-vs-deployer mapping table per regime. Most regimes impose materially different obligations on providers (or builders) versus deployers (or users) — collapsing them into one undifferentiated list misses obligations and conflates risks. Do not combine provider and deployer obligations into a single section. Produce, per regime:

| Obligation | As provider | As deployer |
|---|---|---|
| [specific obligation, pinpoint cite] | [what applies / does not apply / with what carve-outs] | [what applies / does not apply / with what carve-outs] |

**If a high-risk or equivalent classification applies:**
Flag in the assessment, citing the specific provision and regime. Note that this AIA documents the internal review but does not substitute for any formal conformity assessment the regime requires. Recommend external legal review before deployment in the affected jurisdiction.

Capture the classification and the cited authority in the assessment output.

---

## Step 4: Write the assessment

**Use the seed structure from `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`.** If none was captured, use this default:

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

# AI Impact Assessment: [System/Feature Name]

**Prepared by:** [name] | **Date:** [date] | **Status:** DRAFT / APPROVED
**System owner:** [name] | **AI governance reviewer:** [name]
**Governance tier:** [Standard / Elevated / High]
**Track:** [Fast track / Full assessment]

---

## Executive summary

[Two sentences: what this AI does and whether it's okay to deploy. E.g., "This
system uses a third-party LLM to draft initial responses to customer support tickets
before human agent review. Processing is consistent with the company's AI policy;
three conditions required before production deployment."]

**Overall risk:** 🟢 Low / 🟡 Medium / 🟠 High / 🔴 Very high

---

## 1. System description

**What it does:** [plain English — not marketing]
**Model / vendor:** [who's providing the AI]
**Deployment mode:** [Assistive / Augmentative / Automated]
**Output type:** [text / score / classification / recommendation / action]
**Status:** [Not started / Pilot / Production]

---

## 2. Affected parties

**Who it acts on:** [employees / customers / third parties]
**Scale:** [how many people, how often]
**Harm if wrong:** [most realistic worst case — specific, not generic]
**Vulnerable groups in scope:** [yes — [who] / no]

---

## 3. Data inputs

**Data categories used:** [specific fields, not "user data"]
**Personal data:** [yes — [whose] / no]
**Data leaves perimeter?** [yes — to [vendor] / no]
**Model training:** [company data used / foundation model / fine-tuned on [dataset]]

---

## 4. Decision-making and oversight

**Human in the loop:** [Always / Nominally (rubber-stamp risk) / No]
**Override mechanism:** [how a human can intervene or correct]
**Appeals / correction for affected parties:** [yes — [how] / no]
**Named owner:** [name or role]

---

## 5. Accuracy and bias

**Error rate:** [known / estimated / untested]
**Failure mode:** [what happens when it's wrong — surfaced? logged? corrected?]
**Bias testing:** [done — [results] / not done / not applicable]

---

## 6. Regulatory classification

*[One subsection per regime in the regulatory footprint that applies to this system.]*

**Regime:** [name]
**Classification under this regime:** [tier, with pinpoint citation to the controlling provision]
**Prohibited practices triggered:** [none identified / [specific provision and why]]
**Applicable obligations:** [researched list with citations — transparency, documentation, human oversight, testing, registration, etc.]
**Fundamental-rights impact assessment required?** [Yes — e.g., EU AI Act Art. 27 FRIA applies / regime equivalent / No / Not applicable. If yes, this is a separate deliverable, not subsumed by this AIA.]
**Effective / enforcement date:** [date(s)]
**Ambiguity or open interpretation:** [flag anything not yet settled]

**Provider-vs-deployer obligation split (required if `AI role: Both`):**

| Obligation | As provider | As deployer |
|---|---|---|
| [specific obligation + pinpoint cite] | [what applies / does not apply] | [what applies / does not apply] |

---

## 7. AI policy consistency

| Policy commitment | Consistent? | Notes |
|---|---|---|
| [commitment from `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` AI policy section] | 🟢 / 🟡 / 🟠 / 🔴 | |

[If any item is 🟡 or worse: policy update needed before deployment, or design needs to change.
One of them has to change — not both flagged and left open.]

---

## 8. Risks and mitigations

| # | Risk | Likelihood | Impact | Mitigation | Status | Owner |
|---|---|---|---|---|---|---|
| 1 | [specific risk tied to this design — not "AI hallucination" generically] | L/M/H | L/M/H | [specific control] | Done / Planned / Gap | [name] |

**Residual risk after mitigations:** [assessment]

---

## 9. Recommendation

**[APPROVED / APPROVED WITH CONDITIONS / CHANGES REQUIRED / NOT APPROVED]**

**Conditions (if any):**
- [ ] [specific action before deployment — owner, deadline]

**Privacy review required?** [Yes — run `/privacy-legal:pia-generation`, if the plugin is installed /
No]

**Sign-off:** [name, date]

---

## Cite check

Regulatory citations in Section 6 (and anywhere else) were generated by an AI model and have not been verified against primary sources. Before the assessment is certified or relied on, run a verification pass against a legal research tool (Westlaw, EUR-Lex, or your firm's platform) for each cited provision — confirm the pinpoint, currency, and any delegated or implementing acts. The AI regulatory landscape shifts quickly; verify before advising. Source tags on each citation (e.g., `[EUR-Lex]`, `[web search — verify]`) show where it came from; `verify` tags carry higher fabrication risk and should be checked first.
```

**Before certifying the AIA (the Sign-off step, marking Status: APPROVED):** Read `## Who's using this` in `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`. If the Role is Non-lawyer:

> Certifying this AIA has legal consequences — it becomes the record the company relies on if a regulator or affected party asks how this use case was assessed. Have you reviewed this with an attorney? If yes, proceed. If no, here's a brief to bring to them:
>
> [Generate a 1-page summary: the system, the regulatory classification, the risks identified, the mitigations in place, residual risk, open questions, what to ask the attorney before certifying.]
>
> If you need to find an attorney, solicitor, barrister, or other authorised legal professional: your professional regulator's referral service is the fastest starting point (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent).

Do not proceed past this gate without an explicit yes. DRAFT assessments for attorney review do not require the gate — certification does.

---

## Risk quality standards

Same standard as the PIA skill — risks must be **specific and tied to the design**.

| Bad risk | Why bad | Better |
|---|---|---|
| "AI hallucination" | Applies to every LLM; says nothing | "Model may generate plausible but incorrect legal citations — support agents have no current verification step before sending to customers" |
| "Bias" | Too vague | "Résumé scoring model trained on historical hires; if historical cohort was demographically homogeneous, underrepresented candidates may be systematically scored lower" |
| "Vendor risk" | Circular | "OpenAI's terms permit training on API inputs by default; unless the opt-out is confirmed in the agreement, customer support messages may be used to train the model" |

Aim for 2-5 real risks, not 12 padded ones.

---

## AI policy diff

Every assessment should cross-check against the AI policy commitments in `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`.
Common drift:

- Policy prohibits AI use in [category] — this use case is that category. Stop.
- Policy requires human review — this deployment has no human step. Design needs to change.
- Policy requires disclosure to affected parties — disclosure mechanism hasn't been built.
- Approved vendor list exists — this vendor isn't on it. Procurement step required.

Flag every mismatch. One of them has to change before deployment.

---

## Handoffs

- **To product / engineering:** Conditions list with owners and deadlines. Not
  "add oversight" — "add a human review step before any automated email is sent,
  owner: [product lead], before launch."
- **To privacy:** If personal data is involved, flag: "Run `/privacy-legal:pia-generation [system name]` in parallel, if the plugin is installed — the AIA doesn't substitute for a PIA."
- **To vendor-ai-review:** If a new vendor is involved, flag: "If there's no AI addendum reviewed for [vendor], run `/ai-governance-legal:vendor-ai-review` before production."
- **To reg-gap-analysis:** If new regulatory obligations emerged (EU AI Act high-risk, new sector rule), that skill tracks the gap.

---

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

## What this skill does not do

- It doesn't approve the deployment. A human signs the assessment.
- It doesn't constitute any regulatory conformity assessment — where a regime (e.g., EU AI Act) requires a formal conformity assessment, that is a separate exercise requiring external legal review and technical documentation beyond what's here.
- It doesn't design the mitigations. It describes what needs mitigating; engineering
  designs the fix.
- It doesn't substitute for a PIA when personal data is involved. Run both.
