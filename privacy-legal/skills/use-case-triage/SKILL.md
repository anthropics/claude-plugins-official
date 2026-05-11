---
name: use-case-triage
description: >
  Quickly determine whether a processing activity needs a PIA, a mandatory GDPR
  DPIA, or can proceed — surfaces privacy policy conflicts and routes to the right
  next step. Use when the user asks "does this need a PIA", "triage this feature",
  "privacy check on X", "is this okay from a privacy perspective", or describes a
  new data processing activity, product feature, or vendor relationship.
argument-hint: "[describe the data processing activity or feature]"
---

# /use-case-triage

1. Read `~/.claude/plugins/config/claude-for-legal/privacy-legal/CLAUDE.md`. Confirm privacy practice is configured — if not, stop and direct to setup.
2. Run the workflow below. Clarify the activity if vague.
3. House trigger check → mandatory DPIA check (if GDPR in footprint) → privacy policy conflict check.
4. Output: classification (PROCEED / PIA REQUIRED / DPIA MANDATORY / STOP), reasoning, conditions table if required, cross-plugin handoffs.
5. Offer to continue into PIA generation if assessment is required.

```
/privacy-legal:use-case-triage "New feature that uses behavioral data to personalize content recommendations"
```

---

# Privacy Use Case Triage

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/privacy-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/privacy-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Destination check

Before producing output, check where it's going. If the user has named a destination (a channel, a distribution list, a counterparty, "everyone"), ask whether it's inside the privilege circle. Public channels, company-wide lists, counterparty/opposing counsel, vendors, and clients (for work product) waive the protection. When the destination looks outside the circle, flag it and offer (a) the privileged version for legal only, (b) a sanitized version for the broader channel, or (c) both — don't silently apply a privileged header and then help paste it somewhere the header won't protect it. See the canonical `## Shared guardrails → Destination check` in this plugin's CLAUDE.md.

## Purpose

Answer the question that comes up before anyone runs a PIA: "does this thing even
need one?" And if it does, what kind, and what's blocking the way?

Privacy triage is faster than PIA generation but upstream of it. It doesn't write
the assessment — it determines whether one is needed and on what terms. The PIA
generation skill does the deep work.

The output is one of four classifications:
- **PROCEED** — No PIA needed. Standard safeguards apply.
- **PIA REQUIRED** — Assessment needed before or alongside deployment.
- **DPIA MANDATORY** — A regime-mandated data protection impact assessment is
  required (research the applicable regime's trigger and cite primary sources).
  Harder bar, DPO/GC involvement likely.
- **STOP** — Processing activity conflicts with the privacy policy or has no
  lawful basis as described. Needs redesign before proceeding.

## Jurisdiction assumption

This triage assumes the jurisdictional scope specified in your configuration. Privacy rules, assessment triggers, and lawful bases vary materially by jurisdiction (GDPR vs. state consumer privacy laws vs. sectoral). If the processing activity, controller, or affected data subjects fall under a different jurisdiction, this classification may not apply as written.

## Read the config first

Before triaging, always read `~/.claude/plugins/config/claude-for-legal/privacy-legal/CLAUDE.md`. The PIA trigger criteria, regulatory
footprint, and privacy policy commitments there are authoritative. Generic privacy
law reasoning is not a substitute for what this company has actually committed to.

If the file is missing or contains `[PLACEHOLDER]`, surface this bounce:

> I notice you haven't configured your practice profile yet — that's how I tailor the PIA trigger criteria, regulatory footprint, and privacy policy commitments to your practice.
>
> **Two choices:**
> - Run `/privacy-legal:cold-start-interview` (2 minutes) to configure your profile, then I'll triage tailored to YOUR practice.
> - Say **"provisional"** and I'll triage against generic defaults — US jurisdiction, middle risk appetite, lawyer role, no playbook — and tag every output `[PROVISIONAL — configure your profile for tailored output]` so you can see what I do before committing.

### Provisional mode

If the user says "provisional," run triage normally using these generic defaults: middle risk appetite, lawyer role, US jurisdiction (CCPA + common federal sectoral baselines), no playbook (classify from general privacy-law principles rather than matching to configured commitments). Tag the reviewer note and every finding block with `[PROVISIONAL]`. At the end of the output, append:

> "That was a generic run against default assumptions. Run `/privacy-legal:cold-start-interview` to get output calibrated to YOUR practice — your regulatory footprint, your privacy policy commitments, your risk appetite. 2 minutes."

---

## Triage process

### Step 1: Understand the activity

If the description is vague, ask before classifying. Get specific on:

- What data is being collected or processed? Which categories?
- Who are the data subjects — customers, employees, third parties?
- What's the purpose? What problem is this solving?
- Is this new data collection, or repurposing data you already have?
- Is a third-party vendor involved? New vendor or existing?
- Is any automated decision-making involved — does the output affect anyone?
- What's the deployment context — internal only, customer-facing, public?

"New feature" and "data processing activity" are not enough to triage accurately.

---

### Step 2: Check house triggers

Read `~/.claude/plugins/config/claude-for-legal/privacy-legal/CLAUDE.md` → `## PIA house style` → Trigger criteria. Apply them.

If the house trigger is met → at minimum **PIA REQUIRED**.

If house trigger is not met, continue to Step 3 before concluding PROCEED. Some
activities need a PIA regardless of internal policy.

---

### Step 3: Mandatory assessment check

**Before researching regime-specific triggers, ask the activity-based federal overlay question first.** If the processing touches a federally-regulated data category, the federal overlay is usually the controlling framework, not state privacy law, and the triage needs to surface that early rather than as an afterthought.

> **Activity-based federal overlays — ask first:**
>
> Does this processing touch:
> - **Financial account data or "nonpublic personal information" about consumers** (GLBA / Reg P — applies to financial institutions and their non-affiliated third parties; imposes substantive restrictions on sharing NPI for marketing, separate from and on top of any state privacy-law exemption)?
> - **Protected health information held by a covered entity or business associate** (HIPAA Privacy / Security Rules — substantive restrictions on use and disclosure, breach notification at 500+ records, BAA required for any vendor)?
> - **Education records held by a school or a service provider acting for a school** (FERPA — consent requirements for disclosure, directory-information carve-outs)?
> - **Data from children under 13 collected by an operator of an online service directed to children or with actual knowledge** (COPPA — parental consent, notice, deletion rights, strict limits on retention and sharing)?
> - **Another sectoral federal regime** (e.g., VPPA for video-viewing records, CPNI for carrier data, DPPA for DMV records, TCPA for SMS/call consent)?
>
> If yes to any: the federal overlay usually supplies the controlling substantive restriction, not just an exemption from a state consumer privacy law. Research and cite the specific provision before continuing. An activity that is "exempt" from CCPA under § 1798.145(e) because it is GLBA-covered is still subject to the GLBA restrictions (e.g., § 6802(a)-(c) on NPI sharing) — the CCPA exemption does not make the activity lawful; it just moves the governing framework to GLBA.

For each regime in `~/.claude/plugins/config/claude-for-legal/privacy-legal/CLAUDE.md` → `## Regulatory footprint`, **research the currently operative mandatory privacy/data-protection assessment triggers**. Cite controlling statute, regulation, or regulator guidance with pinpoint references. Note effective dates — national and state regulators publish and update trigger lists regularly; do not rely on a static checklist. Flag uncertainty for attorney verification rather than guess.

If **any** applicable regime's mandatory trigger is met → **DPIA MANDATORY** (or the equivalent regime-specific mandate), regardless of house trigger.

**Strong indicators (not necessarily mandatory but do one anyway):**
- New technology or novel use of existing technology
- Children's data
- Combining datasets that weren't collected together
- Data that could enable discrimination
- Processing users would not expect
- Lookalike audiences, cross-context behavioral advertising, or other tracking-based ad-tech activity (recurring question for consumer-facing companies; surfaces policy-commitment conflicts and federal sectoral overlays reliably)

One or more strong indicators with no researched mandatory trigger → escalate to **PIA REQUIRED**
(not DPIA mandatory, but flag in the output).

---

### Step 4: Privacy policy conflict check

Read `~/.claude/plugins/config/claude-for-legal/privacy-legal/CLAUDE.md` → `## Privacy policy commitments`. Check the proposed activity
against every stated commitment.

**Common conflicts to catch:**
- Policy says "we collect X, Y, Z" — this activity collects W. Policy update
  needed before launch, or stop collecting W.
- Policy says "we don't sell or share data with third parties" — this activity
  passes data to a vendor for their own purposes. Research whether the flow falls
  within a regulated "sale," "share," or other disclosure category under each
  applicable regime.
- Policy states retention limits — this activity retains data longer.
- Policy says "we use data only for [purpose]" — this activity uses it for a new
  purpose without fresh consent or legitimate interest assessment.
- Policy specifies user rights offered — this activity creates a new data category
  the rights process wasn't built for.

If a direct conflict exists → **STOP**. Not "proceed with caution" — the policy
conflict has to be resolved (policy update or activity redesign) before this
proceeds.

---

### Step 5: Classification and output

---

### Bottom line
[PIA required / Mandatory DPIA required / Proceed — one-sentence why]

---

**ACTIVITY:** [State the processing activity as you understand it]

**CLASSIFICATION:** [PROCEED / PIA REQUIRED / DPIA MANDATORY / STOP]

**House trigger met?** [Yes / No]
**GDPR mandatory DPIA trigger?** [Yes — [trigger] / No / N/A (GDPR not in footprint)]
**Privacy policy conflict?** [None / Yes — [specific conflict]]

**Reasoning:**
[1-3 sentences. For PROCEED: what makes it safe under current policy. For PIA/DPIA:
what creates the obligation. For STOP: which specific policy commitment or principle
is in conflict.]

---

*If PIA REQUIRED or DPIA MANDATORY — conditions before proceeding:*

| Requirement | Owner | Done? |
|---|---|---|
| [e.g., Privacy Impact Assessment — full DPIA format] | [Privacy counsel] | ☐ |
| [e.g., Legitimate interest assessment (if LI basis)] | [Privacy counsel] | ☐ |
| [e.g., DPO consultation (DPIA mandatory track)] | [DPO] | ☐ |
| [e.g., Vendor DPA in place] | [Privacy / Legal] | ☐ |
| [e.g., Privacy policy update before launch] | [Privacy counsel] | ☐ |
| [e.g., Consent mechanism built and tested] | [Product] | ☐ |
| [e.g., Data subject rights process covers new data category] | [Privacy / Product] | ☐ |

**Lawful basis (if GDPR in footprint):** [Consent / Contract / Legitimate Interest /
Legal Obligation — or "unclear — needs determination in PIA"]

**Next step — offer to continue:**

After presenting a PIA REQUIRED or DPIA MANDATORY result, always end with:

> "Want me to start the PIA now? I can run the intake questions and produce the
> assessment document without you needing to run a separate command."

If they say yes, load the `pia-generation` skill and continue in the same
conversation — pass the activity description and any triggers already identified.

If they say no, the triage result stands. The PIA can be run any time with:
`/privacy-legal:pia-generation [activity]`

---

*If STOP:*

**Conflict:** [Specific privacy policy commitment or principle in conflict]

**To proceed, one of these has to change:**
- [Option A — redesign the activity so it doesn't create the conflict]
- [Option B — update the privacy policy to cover this processing (requires review
  of whether the update is itself consistent with lawful basis)]

Don't offer a path forward if there isn't one. If the processing simply can't be
reconciled with stated commitments or lawful basis, say so.

---

### Step 6: Cross-plugin handoffs

**AI governance handoff:** If the activity involves an AI system making or
influencing decisions about individuals:

> "This activity involves AI decision-making. An AI impact assessment is likely
> required in addition to a PIA. Use `/ai-governance-legal:aia-generation [activity]`
> to run that in parallel — they're not substitutes."

**Product counsel handoff:** If this is a new product feature or launch:

> "If this is part of a product launch, loop in product counsel.
> Use `/product-legal:launch-review` — it will detect the privacy component
> and route to this plugin."

Only flag handoffs that are actually relevant. Don't append both as boilerplate.

---

## Batch triage

If the user presents a feature list, roadmap, or backlog — summary table first,
then expand each non-PROCEED entry:

| # | Activity | Classification | Key condition / blocker |
|---|---|---|---|
| 1 | [activity] | 🟢 Proceed | — |
| 2 | [activity] | 🟡 PIA required | Lawful-basis assessment needed; vendor DPA not in place |
| 3 | [activity] | 🟠 DPIA mandatory | Large-scale special category data |
| 4 | [activity] | 🔴 Stop | Privacy policy conflict — purpose limitation |

---

## Edge cases and failure modes

**"It's anonymized" doesn't automatically mean PROCEED.**
Ask how it's anonymized and whether re-identification is realistically possible
given the data set. Pseudonymized data is still personal data under GDPR.

**"We already do something similar" isn't a triage.**
Existing processing that was never assessed doesn't grandfather new processing.
If the new activity is materially different in scale, purpose, or data category,
triage it fresh.

**"Just a pilot" doesn't skip triage.**
A pilot that touches real user or employee data is subject to the same triggers.
Apply the same classification; if a PIA is required, the pilot should have one.

**"The vendor handles all the privacy."**
Vendor handles the infrastructure. You're still the controller determining the
purposes. If personal data flows to the vendor, a DPA is required and triage still
applies to the purpose.

**Inferred data and derived attributes count.**
If the activity generates inferred data about individuals (e.g., a behavioral score,
a predicted preference), treat the inferred attribute as personal data for triage
purposes. Don't let "we're just computing a score" obscure what the score represents.

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.
