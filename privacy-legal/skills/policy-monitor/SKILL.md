---
name: policy-monitor
description: >
  Keep the privacy policy current with practice. Two modes: weekly sweep of saved
  PIAs, DPA reviews, and triage results to find policy drift; or direct query for
  a proposed new practice. Use when the user asks "does our policy cover this",
  "we want to start doing X — does the policy need updating", "run the policy
  monitor", "policy sweep", or wants to find where the privacy policy no longer
  matches what the team actually does.
argument-hint: "[describe a proposed new practice — or omit / use --sweep for crawl mode]"
---

# /policy-monitor

**Sweep mode** (no argument or `--sweep`):
1. Read `~/.claude/plugins/config/claude-for-legal/privacy-legal/CLAUDE.md` → outputs folder path, policy document, last sweep date.
2. Run the workflow below. Scan outputs folder for files since last sweep.
3. For each output: extract approved practices → diff against current policy commitments.
4. Classify gaps: REQUIRED (policy misrepresents current practice) vs ADVISABLE (policy silent).
5. For each gap: quote current policy, describe gap, draft suggested language.
6. Update Last policy sweep date in `~/.claude/plugins/config/claude-for-legal/privacy-legal/CLAUDE.md`.

**Direct query mode** (with description argument):
1. Read `~/.claude/plugins/config/claude-for-legal/privacy-legal/CLAUDE.md` → current policy commitments + actual policy document.
2. Parse proposed practice. Diff against policy: data categories, purposes, third parties, retention, user rights, disclosure.
3. Output: covered / missing / conflicting + suggested language for each gap + timing recommendation.

**Schedule:** Set up a recurring reminder in your own scheduler (calendar, task manager, or CI) to run `/privacy-legal:policy-monitor` weekly. Scheduled execution requires a scheduled-tasks integration, which is not bundled with this plugin.

```
/privacy-legal:policy-monitor
/privacy-legal:policy-monitor "We want to start using behavioral data to personalize onboarding emails"
```

---

# Privacy Policy Monitor

## Purpose

Privacy policies drift from practice in one direction: practice moves forward,
policy stays behind. A PIA approves a new data category. A DPA is signed with a
subprocessor not listed anywhere. A triage result marks a new use case conditional
with a disclosure requirement that the policy doesn't yet make. Months later,
someone reads the policy and it doesn't reflect what actually happens.

This skill catches the drift before it becomes a problem — either by crawling the
outputs folder weekly, or by answering the direct question: "we're about to start
doing X, what does that mean for the policy?"

The output is always the same: here's the gap, here's the suggested language.

---

## Load current state

Read `~/.claude/plugins/config/claude-for-legal/privacy-legal/CLAUDE.md`:
- `## Who we are` → `## Regulatory footprint` — the regimes in scope (GDPR, CCPA / CPRA / other state consumer privacy, GLBA, HIPAA, FERPA, COPPA, VPPA, CPNI, etc.)
- `## Privacy policy commitments` — the commitments extracted from the published policy
- `## Outputs` — outputs folder path, policy document location, last sweep date

If `## Outputs` contains `[PLACEHOLDER]`:
> "Outputs aren't configured yet. I can still run a direct-query check — describe
> what you're planning to do and I'll diff it against your current policy. To enable
> the crawl sweep, run `/privacy-legal:cold-start-interview` and provide the outputs
> folder path."

Read the actual privacy policy document from the path in `## Outputs` → **Privacy
policy document**. The commitments in the config CLAUDE.md are a summary; the actual document
is authoritative for suggesting edits.

### Privacy commitments live on multiple surfaces — sweep all of them

The website privacy policy is one surface. Modern privacy programs make binding commitments in at least four more places that regulators actively scrutinize for inconsistencies:

1. **Cookie consent banners / CMPs.** The consent management platform promises specific cookie categories and purposes. If the privacy policy says "we use analytics cookies" and the CMP offers "strictly necessary only," there's a conflict. EU DPAs and the FTC have both enforced against CMP misconfigurations.
2. **App store privacy labels.** Apple App Privacy (the "nutrition label") and Google Data Safety are self-declared and FTC-enforceable. A company that updates its privacy policy but doesn't update its App Store label has a material, regulator-visible inconsistency. Check: when was the label last updated? Does it match the current policy's data categories, purposes, and sharing?
3. **In-product consent flows.** The actual screens where users make data-use choices (onboarding consents, settings toggles, "we've updated our policy" dialogs). The policy says what you do; the consent flow says what the user agreed to. They should match.
4. **Sector-specific notices.** GLBA privacy notices, HIPAA NPPs, FERPA directory notices, COPPA direct notices. These have their own update obligations and their own consistency requirements with the general privacy policy. (Detail below under "Sectoral notices.")

**Add fields to the practice profile for each surface's location and last-updated date.** The sweep checks each against the current policy and flags divergence: "Privacy policy updated [date]. App Store label last updated [earlier date] — may not reflect the new data category. CMP last configured [date] — verify cookie purposes match the policy."

A company with a clean privacy policy and a stale App Store label is a company with an FTC complaint waiting to happen. Sweep the surfaces, not just the document.

### Sectoral notices are in scope for this sweep

The website privacy policy is one notice. Federally-regulated practices require a separate, sector-specific notice that the website policy does not substitute for. If `## Regulatory footprint` includes any of the following, the sweep diffs practice against that notice in addition to the website policy — or flags its absence if no such notice has been configured:

| Footprint entry | Sectoral notice to diff against | What to flag |
|---|---|---|
| **GLBA / Reg P** (financial institution handling NPI) | GLBA initial + annual privacy notice (12 C.F.R. Part 1016, or the functional regulator's equivalent) | Outputs implying new NPI categories, sharing with non-affiliated third parties, or changes to opt-out mechanics that the Reg P notice doesn't reflect. A DPA signed with an analytics vendor receiving NPI with no matching Reg P notice update is a gap. |
| **HIPAA** (covered entity or BA) | Notice of Privacy Practices (45 C.F.R. § 164.520) | Outputs implying new uses or disclosures, new routine categories, or changes to patient-rights mechanics. A BAA signed with a new subcontractor flowing PHI with no matching NPP refresh is a gap. |
| **FERPA** (school or school service provider) | Annual directory-information / rights notice (34 C.F.R. § 99.37) | Outputs implying new disclosure categories to service providers under the school-official exception, new directory-information elements, or changes that implicate parental-consent flow-through. |
| **COPPA** (operator of service directed to children <13) | Direct notice to parents + online notice (16 C.F.R. § 312.4) | Outputs implying new data categories collected from children, new third-party disclosures, or changes to the verifiable-parental-consent mechanic. |
| **VPPA / CPNI / DPPA / other sectoral** | The regime's specific notice or consent regime | Processing activities the regime restricts that aren't reflected in the configured notice. |

**If no sectoral notice is configured for a regime in the footprint**, surface this as a standing gap on every sweep, not a one-time finding. The sweep output should include:

> **Sectoral notice coverage:**
> - [regime]: [configured notice path + last updated, or "NOT CONFIGURED — flag each sweep until resolved"]

**If the sweep cannot locate the sectoral notice**, say so explicitly — do not silently default to diffing only against the website policy. A fintech DPO relying on a policy-monitor sweep that ignored GLBA would ship with an outdated regulator-facing notice and no warning. Surface the gap loudly.

**Ask the user if the footprint is ambiguous.** If `## Regulatory footprint` says "GDPR / CCPA" but the outputs scan surfaces PHI, NPI, or student data categories, surface the footprint-vs-practice mismatch before proceeding: "Your footprint doesn't list [GLBA / HIPAA / FERPA / COPPA] but this sweep is looking at outputs that involve [category]. Should this regime be added to the footprint, and is there a sectoral notice to diff against?"

---

## Mode detection

**Sweep mode:** No argument, `--sweep`, or triggered by schedule.
→ Scan the outputs folder. Diff all outputs since last sweep against current policy.

**Direct query mode:** User provides a description of a proposed new practice.
→ Diff that practice against current policy. Suggest updates.

---

## Mode 1: Sweep

### Determine scope

Read `## Outputs` → **Last policy sweep** date. Scan for output files in the
outputs folder that are dated after that date. If no date is recorded, scan all
files and note: "First sweep — scanning all outputs."

If the outputs folder is empty or has no new files since the last sweep:
> "No new outputs since [last sweep date]. Policy appears current with recent
> practice. Next scheduled sweep: [date]."

Update **Last policy sweep** in `~/.claude/plugins/config/claude-for-legal/privacy-legal/CLAUDE.md` to today's date after completing the sweep.

### What to read in each output type

**PIAs (Privacy Impact Assessments):**
- Extract: data categories processed, purposes, third parties / subprocessors involved,
  retention periods, user rights implications, any conditions placed on the processing
- Flag: anything in that list not present in the current privacy policy commitments

**DPA reviews (signed or approved):**
- Extract: subprocessors added, data locations agreed to, processing purposes covered,
  any obligations to data subjects created by the DPA terms
- Flag: subprocessors not listed in the policy (if policy names them), new processing
  categories, new data locations, obligations inconsistent with policy

**Triage results (PIA REQUIRED / PROCEED outcomes):**
- Extract: what was approved, any conditions imposed that imply a public commitment
  (e.g., "disclosure to affected parties required before launch")
- Flag: approved practices not covered by policy, conditions that require policy language

**DSAR responses:**
- Extract: any new data categories surfaced that weren't in previous DSAR responses,
  any systems added to the systems list
- Flag: data categories collected but not stated in policy

### Gap identification

For each flagged item, assess:

**REQUIRED update** — the policy makes a commitment that this output contradicts, or
the processing is occurring and the policy has no coverage at all. Not updating creates
a material misrepresentation.

> Example: Policy says "we collect name, email, and payment information." A PIA
> approved collection of location data. Policy says nothing about location. That's
> a REQUIRED update — you're collecting data you haven't disclosed.

**ADVISABLE update** — the policy is silent but not in conflict. The processing is
defensible without updating, but cleaner with it.

> Example: Policy says "we may share data with service providers." A DPA was signed
> with a new analytics vendor. Policy doesn't name the vendor but doesn't exclude
> them either. Advisable to add to a named subprocessor list if one is maintained.

### Sweep output format

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

# Privacy Policy Monitor — Sweep Report

**Date:** [date]
**Outputs scanned:** [N files] | **New since last sweep:** [N files]
**Gaps found:** [N] REQUIRED | [N] ADVISABLE

---

## REQUIRED updates

### [Gap 1 short name]

**Source:** [filename / output type that triggered this]
**What's happening:** [plain description of the new practice]
**Current policy:** [quote the relevant section — or "No coverage"]
**Gap:** [what's missing or inconsistent]

**Suggested language:**
> *Add to [section name]:*
> "[Drafted policy text — specific, consistent with house style of the actual policy]"

---

[repeat for each REQUIRED gap]

---

## ADVISABLE updates

### [Gap name]

**Source:** [filename]
**What's happening:** [description]
**Current policy:** [quote or "Silent"]
**Suggested language:**
> *Add to / update [section]:*
> "[Drafted text]"

---

## No action needed

[List outputs scanned where no gaps were found — confirms they were reviewed]

---

## Next steps

- [ ] Review REQUIRED updates — each needs a decision before the associated
  feature/processing goes live (or immediately if already live)
- [ ] Review ADVISABLE updates — lower urgency but worth addressing at next
  policy refresh
- [ ] Next scheduled sweep: [date]
```

---

## Mode 2: Direct query

### Parse the proposed practice

Extract from the user's description:
- What data is being collected or processed?
- What's the purpose?
- Who else is involved (vendors, partners, third parties)?
- Who are the data subjects?
- Is there any automated decision-making?
- Any new disclosure to data subjects required?

If the description is vague, ask one clarifying question before proceeding. Don't
run a long intake — this mode should be fast.

### Policy diff

Check the proposed practice against every relevant section of the current policy:

| Check | Current policy says | Proposed practice | Verdict |
|---|---|---|---|
| Data categories | [what policy lists] | [new category if any] | 🟢 Covered / 🟡 Gap / 🔴 Conflict |
| Purposes | [stated purposes] | [new purpose] | |
| Third parties / subprocessors | [stated parties] | [new party if any] | |
| Retention | [retention commitment] | [implied retention] | |
| User rights | [rights offered] | [any new rights implications] | |
| Disclosure / notice | [what policy says about telling users] | [what this practice requires] | |

### Direct query output format

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

# Privacy Policy Check: [Proposed practice in one line]

**Bottom line:** [POLICY UPDATE REQUIRED / ADVISABLE / NO UPDATE NEEDED]

---

## What's covered

[List aspects of the proposed practice already addressed by the current policy —
brief, confirms they don't need to change]

## What's missing

### [Gap 1]

**Current policy:** [quote or "Silent"]
**What's needed:** [why this gap matters — legal, reputational, or consistency reason]

**Suggested language:**
> *Add to [section]:*
> "[Drafted text]"

### [Gap 2]
[same format]

## What conflicts

### [Conflict 1 — if any]

**Current policy says:** [quote]
**Proposed practice does:** [what conflicts]
**Resolution:** [which one needs to change and why — usually the practice adjusts
to match the policy, or the policy gets updated to a defensible new position]

---

## Timing

[If any gap is REQUIRED: "Policy update should happen before this goes live."
If ADVISABLE: "Can proceed; update at next policy refresh."]
```

---

## Suggested language quality standards

Policy language should:
- Match the voice and style of the existing policy (read the actual document, not
  just the config CLAUDE.md summary, before drafting)
- Be specific enough to be meaningful but not so specific that routine changes
  break it ("service providers who assist us in operating our business" ages better
  than naming every vendor)
- Not make commitments the team can't keep (e.g., don't draft "we will never share
  location data" if the architecture has that data flowing to an analytics vendor)
- Flag where a broader policy position change might be needed, not just a
  sentence addition

When drafting, always say which section to add to. If the right section doesn't
exist, say so and suggest creating it.

---

## Schedule integration

Set up a recurring reminder in your own scheduler (calendar, task manager, or CI)
to run `/privacy-legal:policy-monitor` weekly. Scheduled execution requires a
scheduled-tasks integration, which is not bundled with this plugin.

Whenever the sweep runs, it updates `## Outputs` → **Last policy sweep** in
`~/.claude/plugins/config/claude-for-legal/privacy-legal/CLAUDE.md`, so the next sweep only looks at new files.

---

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

If the sweep surfaced more than ~10 drift findings, or any time the user asks: offer the dashboard (see CLAUDE.md `## Outputs → Dashboard offer for data-heavy outputs`). Shape the offer for this output — counts by surface (policy clause / PIA / DPA / triage), counts by severity, and a sortable grid of findings with source artifact and recommended remediation.

## What this skill does not do

- It doesn't update the policy itself — it drafts suggested language and flags
  decisions, but a human reviews and approves every change.
- It doesn't catch regulatory changes — that's `reg-gap-analysis`. This skill
  monitors internal practice drift, not external legal changes.
- It doesn't enforce that outputs are saved — if the team isn't saving PIAs to the
  configured folder, the sweep won't find them. The direct-query mode works without
  saved outputs.
- It doesn't read email or Slack for informal decisions — only structured outputs
  saved to the configured folder.
