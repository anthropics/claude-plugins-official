---
name: memo
description: >
  IRAC-scaffolded case analysis memo with research gaps flagged — the
  scaffold, not the analysis. Rule blocks are RESEARCH NEEDED, Application
  is STUDENT ANALYSIS prompts, Conclusion is blank. Use when a student needs
  to scaffold a case analysis memo, write up their analysis, or build an
  IRAC memo for a case.
argument-hint: "[optional: specific issue to focus]"
---

# /memo

1. Load `~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md` → practice areas, jurisdiction.
2. Use the workflow below. Read intake summary / case notes.
3. Frame issues as questions. Scaffold IRAC for each — Rule blocks are RESEARCH NEEDED, Application is STUDENT ANALYSIS prompts, Conclusion is blank.
4. Strengths/weaknesses/open questions. Research gaps summary.
5. Output with prominent "the analysis is yours" label.

```
/legal-clinic:memo
```

---

# Memo: Internal Case Analysis

## Purpose

The case analysis memo is where the student's thinking lives. This skill provides the IRAC scaffolding and flags the research gaps — the student fills in the analysis.

**The analysis is the student's.** This skill structures; it doesn't conclude.

## Load context

`~/.claude/plugins/config/claude-for-legal/legal-clinic/CLAUDE.md` → practice areas, jurisdiction, supervision style.
Intake summary and case notes for facts.

## Pedagogy check

Read the supervisor guide for this practice area at `~/.claude/plugins/config/claude-for-legal/legal-clinic/guides/<practice-area>.md`. Check the `pedagogy_posture` setting:

- **`guide` (default):** Produce the IRAC structure and the research-gap list. Ask the student to draft each rule statement themselves from research, rather than giving them a framework. Give feedback on what they wrote. Offer to fill the framework rule for a section only when the student has tried once.
- **`assist`:** Produce the memo scaffold and fill what can be filled. Flag items for student review. The student edits and learns by reviewing. (Note: this memo skill always leaves the `[STUDENT ANALYSIS]` and `[STUDENT CONCLUSION]` blocks blank by design — `assist` means the skill produces the IRAC scaffold and framework rule statement; it does not produce the application or the conclusion.)
- **`teach`:** Don't produce the framework or the scaffold content. Ask the student to frame the issues, state the rules from their research, and do the application. Give feedback. Ask leading questions when they're stuck. Only show a model rule statement or a model application paragraph after two attempts, and only for the section they're stuck on. Track what they got right and wrong so the supervisor can see progress.

If no guide exists, use `guide`. If the guide exists but doesn't set a posture, use `guide`.

Whatever the posture, the output always includes: "**Pedagogy mode: [assist/guide/teach]** — set by your supervisor's guide. This means I [description of what the student did vs what the skill did]."

## Workflow

### Step 1: Frame the issues

From the intake summary and case notes: what are the legal questions this case presents?

State each as a question. Not "habitability" — "Can the client assert a habitability defense to the eviction based on the broken heater, and if so, does it offset the rent owed?"

If there are multiple issues, each gets its own IRAC block.

### Step 2: Scaffold the IRAC

For each issue:

**Issue:** Stated as a question (from Step 1).

**Rule:** This is a research gap, not a conclusion. State what the student needs to find:

> `[RESEARCH NEEDED: [State] habitability doctrine — warranty of habitability
> elements, what conditions qualify, remedies available including rent offset.
> Start with: [State] landlord-tenant statute, then case law on heater/heat
> specifically. See /research-start for a roadmap.]`

If the skill has high confidence in the general rule framework (e.g., "most states recognize an implied warranty of habitability"), state that as a framework starting point — **but explicitly mark it as unverified**:

> *Framework (unverified — confirm for [State]):* Most jurisdictions recognize
> an implied warranty of habitability requiring landlords to maintain
> conditions fit for human occupation. Breach may give rise to rent withholding,
> repair-and-deduct, or rent abatement.
> `[VERIFY: [State]'s specific elements and remedies]`

**Application:** This is where the student's analysis goes. Scaffold the structure, don't fill it:

> `[STUDENT ANALYSIS: Apply the rule to the facts. Key facts to address:
> - Heater broken since November — how long is "unreasonable"?
> - Client notified landlord [when? how? documented?]
> - Landlord's response or lack thereof
> - [State]-specific: does client need to have given written notice?
>   deposited rent in escrow? other procedural prerequisites?]`

List the facts that matter. Let the student do the applying.

**Conclusion:** Explicitly blank:

> `[STUDENT CONCLUSION: Based on your research and analysis above, what's the
> likely outcome? How strong is this defense? What are the weaknesses?]`

### Step 3: Identify strengths, weaknesses, open questions

Separate section, after the IRAC blocks:

**Strengths (apparent from facts — student should test these):**
- [Fact that seems helpful and why]

**Weaknesses (apparent from facts — student should assess how serious):**
- [Fact that seems harmful and why]
- `[UNCERTAIN: whether [X] is actually a weakness — depends on [State] rule on [Y]]`

**Open questions (things the memo can't answer without more info):**
- Factual: [what we don't know from the client]
- Legal: [what needs research]
- Strategic: [judgment calls for the student/professor]

## Output

```markdown
═══════════════════════════════════════════════════════════════════════
  AI-ASSISTED SCAFFOLD — THE ANALYSIS IS YOURS TO WRITE
  Every [RESEARCH NEEDED] and [STUDENT ANALYSIS] block is a prompt, not
  a placeholder to delete. The thinking happens when you fill them in.
═══════════════════════════════════════════════════════════════════════

# Case Analysis Memo: [Client] — [Matter]

**Date:** [date] | **By:** [student] | **For:** [Professor]

---

## Bottom line

[Take the case / Decline because X / Need more info on Y — next step is Z]

---

## Issues Presented

1. [Issue as question]
2. [Issue as question]

---

## Issue 1: [Issue]

### Rule

[Framework starting point with VERIFY flags, and RESEARCH NEEDED blocks]

### Application

[STUDENT ANALYSIS scaffold with the facts that matter]

### Conclusion

[STUDENT CONCLUSION — blank]

---

[repeat for each issue]

---

## Strengths

[list with caveats]

## Weaknesses

[list with UNCERTAIN flags where applicable]

## Open Questions

**Factual:** [list]
**Legal:** [list — these feed /research-start]
**Strategic:** [list — these are for discussion with Professor]

---

## Research gaps summary

[Every RESEARCH NEEDED block pulled out into one list, so the student can
work through them systematically — and can run /research-start on each]

═══════════════════════════════════════════════════════════════════════

## What this memo is NOT

This is a scaffold, not an analysis. The [STUDENT ANALYSIS] blocks are where
the educational value lives — filling them in is the work. A memo where those
blocks are still empty is a memo that hasn't been written yet.

---

**Cite verification — required before use.** Any framework rules, cases, or statutes suggested above were generated by an AI model and have not been verified. Before relying on any citation — or including it in client work — run it through Westlaw, Fastcase, CourtListener, or your clinic's research platform for accuracy and current good-law status. Flag unverified citations to your supervisor.

**Source attribution.** Tag every suggested citation in the scaffold with where it came from: `[Westlaw]`, `[CourtListener]`, `[Fastcase]`, or the MCP tool name for citations retrieved from a legal research connector; `[web search — verify]` for web-search citations; `[model knowledge — verify]` for citations recalled from training data; `[user provided]` for citations the supervising attorney or case file supplied. Citations tagged `verify` carry higher fabrication risk than tool-retrieved citations and should be checked first. Never strip or collapse the tags — they are the supervisor's fastest signal about which citations to verify.

**No silent supplement.** If a query to a configured research tool returns few or no results for a rule the memo needs, say so and stop. Do NOT fill the gap from web search or model knowledge without asking. Say: "The search returned [N] results from [tool]. Coverage appears thin for [rule / issue]. Options: (1) broaden the search query, (2) try a different research tool, (3) search the web — results will be tagged `[web search — verify]` and should be checked against a primary source before relying, or (4) leave `[RULE TO VERIFY]` and stop. Which would you like?" The supervising attorney decides whether to accept lower-confidence sources.
```

## What this skill does NOT do

- **Write the analysis.** It scaffolds the IRAC and flags the gaps. The student reasons through the application.
- **Provide verified rules.** Every rule statement is explicitly unverified until the student researches it.
- **Reach conclusions.** The C in IRAC is blank on purpose.
- **Replace the conversation with the professor.** The Open Questions / Strategic section is the agenda for that conversation, not a substitute.

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

