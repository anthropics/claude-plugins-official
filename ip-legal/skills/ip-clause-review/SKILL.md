---
name: ip-clause-review
description: >
  Review the IP clauses in an agreement — assignment, ownership, license
  grants, warranties, indemnities. Use when reviewing IP terms in employment,
  consulting, SOW, vendor, or licensing agreements, when asked to check the
  assignment language or license scope, or when an agreement with IP
  provisions is pasted or attached.
argument-hint: "[file path | Drive link | paste text]"
---

# /ip-clause-review

Reviews the IP clauses in an agreement against the practice profile in `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md`. Flags assignment gaps, ownership ambiguity, license-scope issues, and IP warranty/indemnity problems. Produces a memo with per-clause findings, prioritized by risk, with suggested redline language where appropriate.

## Instructions

1. **Load `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md`.** If placeholders present, stop and prompt: "Run `/ip-legal:cold-start-interview` first — I need to learn your practice profile before I can review IP clauses against it."

2. **Get the agreement:** From file path, Drive link, or pasted text. If none provided, ask.

3. **Follow the workflow below.** In particular:
   - Establish the agreement type and which side the company is on for IP (granting / receiving / both). The side question is per-document, not a one-time setup answer.
   - Run the assignment gap check first if the agreement is an employment, consulting, SOW, or work-for-hire document.
   - Produce per-clause findings prioritized by risk.
   - Check cross-clause consistency, not just clause-by-clause.
   - Note jurisdiction implications (moral rights, work-for-hire, implied license, patent indemnity).

4. **Output the memo** per the template below — work-product header first, bottom line, assignment gap check, clauses by severity, consistency flags, jurisdiction note, approval routing.

5. **Respect the decision posture.** When a clause could be read to allocate IP either way, flag for attorney review and surface the factors cutting both ways. Never silently decide a subjective allocation question.

## Examples

```
/ip-legal:ip-clause-review ~/Documents/vendor-sow.pdf
/ip-legal:ip-clause-review https://docs.google.com/document/d/...
/ip-legal:ip-clause-review
```

---

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/ip-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/ip-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Purpose

Read the IP clauses in an agreement and tell the lawyer what each one does, how it deviates from market or from the team's standard position, what the risk is, and — where appropriate — the specific redline to propose. The goal is a memo the lawyer can act on in one pass.

**The highest-stakes clauses in most agreements are IP ownership and assignment.** They are hard to fix later. A failure to get a clean assignment on an employment or consulting agreement surfaces in M&A diligence, in financing, and in litigation, sometimes years after the agreement was signed. If assignment language is weak or missing in a document that should have it, flag it loudly at the top of the memo — not buried as one line item among many.

## Precondition: load the practice profile

**Before reading the agreement, read `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md`.** If it is missing or still contains placeholders, stop and run `/ip-legal:cold-start-interview`. The practice profile tells you:

- The jurisdiction footprint — which affects whether moral rights waivers are enforceable, whether work-for-hire applies, whether implied assignment fills a gap, how broad license grants can be
- Who approves deviations and at what severity
- The work-product header to prepend to outputs

## Workflow

### Step 1: Orient

Read the whole agreement once, fast. Answer:

| Question | Answer |
|---|---|
| What kind of agreement is this? | Employment / consulting or SOW / vendor MSA / in-license / out-license / collaboration or JDA / settlement / acquisition or asset purchase / other |
| Which side are we on for IP? | Granting rights or receiving them / assigning IP or acquiring it / licensor or licensee |
| Who is the counterparty? | Name, and sophistication — individual, startup, BigCo |
| Is there consideration flowing for the IP specifically? | Salary, fee, royalty, upfront payment, equity, none |
| Governing law and venue | What does it say — and does our practice profile flag that jurisdiction as escalate/never? |

The side question is per-document, not a one-time setup answer. An in-house counsel reviewing an employment agreement is on the "receiving" side; reviewing an out-license the same day, on the "granting" side. The posture inverts.

If the side is ambiguous (a collaboration agreement where both parties contribute and both receive rights, a reseller agreement with flow-through IP), ask:

> Which side is [company] on for this agreement's IP? Granting rights, receiving rights, or both? If both, I'll review each direction separately.

### Step 2: Assignment gap check (highest priority)

If the agreement is an employment agreement, consulting agreement, SOW, work-for-hire contract, or anything else where the company should be receiving an assignment of the counterparty's IP in work product — check the assignment language first.

Look for:

- **Present-tense assignment** ("hereby assigns" or "hereby irrevocably assigns and agrees to assign"). A bare "agrees to assign" is a promise to assign, not an assignment, and can require a second document to perfect.
- **Scope** — does it cover all IP created in the course of engagement, or only IP related to the company's business, or only IP created using company resources? Narrow scope is a gap if work product is expected to range broadly.
- **Moral rights waiver** (for jurisdictions that recognize moral rights — EU member states, Canada, many others — the US recognizes a narrow version for visual art). If the agreement is governed by or has counterparties in a moral-rights jurisdiction, a waiver or non-assertion covenant matters.
- **Further assurances** clause — counterparty agrees to sign whatever else is needed to perfect the assignment later.
- **Pre-existing IP carveout** — what does the counterparty exclude from the assignment, and is that list specific or open-ended?

If any of the above is missing or weak, flag at the top of the memo with a 🔴 or 🟠 severity and a specific redline.

```markdown
## ⚠️ ASSIGNMENT GAP

**Section [X]** assigns IP in the work product, but: [specific issue — e.g.,
"'agrees to assign' rather than 'hereby assigns,'" or "no moral rights waiver
and governing law is France," or "no carveout list is provided and the
counterparty has pre-existing platform IP"].

**Risk:** This is the kind of gap that surfaces in M&A diligence years later.
The counterparty (or a successor) may have residual rights in work product we
thought we owned.

**Proposed redline:**
> "[specific replacement language]"

**Escalation:** Per `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md`, assignment-scope gaps escalate to [approver].
```

> **Can the assignment convey AI-generated content?** *Thaler v. Perlmutter* and the Copyright Office's 2023 AI registration guidance suggest that AI-generated works without any human authorship may not be copyrightable, though the boundaries remain unclear and this area is evolving. If the contractor uses AI for substantial portions of the deliverables, the copyright status of those portions is uncertain — and an assignment clause can only convey rights that exist.
>
> Check: does the agreement have an AI-use disclosure obligation? A representation about the role of AI in the deliverables? A mechanism to identify which portions are AI-assisted vs. human-authored?
>
> If absent and AI-assisted creation is foreseeable (consulting, development, content creation, design): 🟠 High. "The assignment clause is well-drafted but there's no AI-use disclosure. The copyright status of AI-generated content is unsettled, and without a disclosure obligation you won't know which portions are affected. Add an AI-use representation and a disclosure obligation." `[review — copyright status of AI-generated works is an evolving area; verify against current Copyright Office guidance and case law]`

> **AI-assisted inventorship.** A patent filed with incorrect inventorship is unenforceable. If a consultant uses AI tools that contribute to an inventive concept, the inventorship question is unsettled and the patent is at risk. For any agreement with patent assignment provisions covering potentially patentable work product:
>
> Check: does the agreement have an AI-use representation? A process for determining inventorship where AI contributed? A disclosure obligation about AI use in the inventive process?
>
> If absent: flag. "Patent assignment without an AI-use representation. If AI tools contributed to the inventive concept, inventorship determination is complicated and an incorrectly-attributed patent is unenforceable. Add an AI-use representation and inventorship protocol."

### Step 3: Clause-by-clause review

For every IP-relevant clause, produce a block. The clauses to look for:

- **Assignment / work-for-hire** — who owns what's created under the agreement
- **Ownership of deliverables** — distinct from assignment; often states the output of the engagement
- **Improvements and derivatives** — who owns improvements to pre-existing IP, who owns derivative works
- **Background IP vs. foreground IP** — does the agreement define pre-existing IP and newly-created IP separately, and license the background IP to the extent needed?
- **License grants** — scope, exclusivity, territory, field of use, sublicensability, term, termination triggers, royalty or fee structure
- **IP warranties** — non-infringement of third-party rights, authority to grant, original work
- **IP indemnities** — scope, cap, procedure, exclusions (user modifications, combinations, unauthorized use)
- **Moral rights waiver** — jurisdiction-dependent
- **Open source representations** — representations about what OSS is and is not embedded in deliverables
- **Trademark use** — any grant or restriction on use of the other party's marks; brand guidelines; quality control for licensor
- **Confidentiality / trade secrets** — treatment of trade secret material, reasonable measures, return or destruction, post-term obligations

For each clause present, produce:

```markdown
### [Section X.X]: [Clause name]

**What it says:** [plain-English summary, one or two sentences]

**What's market (for this agreement type, this side, this jurisdiction):**
[brief reference point]

**Risk:** 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low

**Why it matters:** [one or two sentences — what goes wrong for the business
if this stays as-is]

**Proposed redline (if needed):**
> "[specific replacement language]"

**Decision call:** [If uncertain whether the clause achieves the intended IP
allocation, flag for attorney review and state the factors cutting both
ways. Do not silently decide a subjective allocation question.]
```

**Severity calibration:**

| Level | Means |
|---|---|
| 🔴 Critical | Don't sign without fixing. Assignment gap in a document that should have one. Unlimited license where a narrow one was intended. Exclusive grant where non-exclusive was intended. |
| 🟠 High | Strongly push; escalate if they won't move. Ambiguous scope, missing moral rights waiver in a moral rights jurisdiction, missing further assurances, narrow indemnity. |
| 🟡 Medium | Push in first round; accept if it's the last open item. Cosmetic but imprecise language, survival periods shorter than standard. |
| 🟢 Low | Note it, don't spend capital. A stylistic deviation that doesn't change the allocation. |

### Step 4: Cross-clause consistency

IP clauses fail as a system. Check:

- **Does the license grant match the scope of what's being licensed?** (A license to "use" the deliverable is narrower than a license to "use, modify, and create derivative works.")
- **Do the warranties cover everything the grant covers?** (A warranty of non-infringement limited to patents, in a license that also covers copyrights and trade secrets, leaves gaps.)
- **Does the indemnity cover what the warranty promises?** (A warranty without indemnity is a promise without a remedy.)
- **Does termination pull the license back?** (Or does a paid-up license survive termination? Either is defensible — the question is whether it matches intent.)
- **Is the IP allocation between this agreement and any related SOW, order form, or related side letter consistent?** Flag conflicts.

### Step 5: Jurisdiction note

IP rules are jurisdiction-specific in ways that change the outcome. Flag if the agreement implicates any of these:

- **Moral rights** — EU member states, Canada, much of the civil-law world recognize moral rights (paternity, integrity) that may not be fully assignable or waivable. US recognition is narrow (VARA, for visual art).
- **Work-for-hire** — US doctrine is statutory (17 U.S.C. § 101) and only applies to enumerated categories for independent contractors. UK implies assignment in the employment context but not always for contractors. Civil-law jurisdictions handle this differently again.
- **Implied license** — common-law jurisdictions may read in an implied license where the written grant is silent. Civil-law jurisdictions tend not to.
- **Patent indemnity exclusions** — combinations, modifications, and user supply of accused features are standard US exclusions; the interaction with EU patent and UPC is still developing.

State what jurisdiction the agreement is governed by, and whether the practice profile flags that jurisdiction as standard, escalate, or never.

## Redline granularity

**Edit at the smallest possible granularity.** A redline is a negotiation artifact, not a rewrite. Wholesale clause replacement signals "we threw out your drafting" — it's aggressive, it forces the counterparty to re-read the whole clause, and it discards the parts of their drafting that were fine. Surgical redlines — strike a word, insert a phrase, restructure a subclause — signal "we have specific asks" and are faster to read, understand, and accept.

Default to the smallest edit that achieves the playbook position:
- Replace a **word** before a phrase. ("twelve (12)" → "twenty-four (24)")
- Replace a **phrase** before a sentence. ("paid by the Buyer" → "paid and payable by the Buyer")
- Restructure a **subclause** before replacing the sentence. (Add "(a)" and "(b)" to split a compound condition.)
- Replace a **sentence** before replacing the clause.
- Only replace a **whole clause** when the counterparty's version is so far from your position that surgical edits would be harder to read than a fresh draft — and when you do, say so in the transmittal: "We've replaced §8.2 rather than marking it up because the changes were extensive. Happy to walk you through the delta."

When in doubt, smaller. A client who receives a surgical redline trusts that you read carefully. A client who receives a wholesale replacement wonders whether you read at all.

### Step 6: Assemble the memo

Prepend the work-product header from `~/.claude/plugins/config/claude-for-legal/ip-legal/CLAUDE.md` → `## Outputs` (it differs by user role — see `## Who's using this`).

This memo and the underlying agreement may be privileged, confidential, or both. The output inherits that status from the source. Distribute only within the privilege circle; mark and store it where privileged materials live; strip the work-product header before any external delivery.

> **No silent supplement.** If a research query to the configured legal research tool returns few or no results for a rule the memo needs (enforceability of a moral rights waiver in a given jurisdiction, scope of an implied license, standard for an IP warranty survival period), report what was found and stop. Do NOT fill the gap from web search or model knowledge without asking. Say: "The search returned [N] results from [tool]. Coverage appears thin for [rule / jurisdiction]. Options: (1) broaden the search query, (2) try a different research tool, (3) search the web — results will be tagged `[web search — verify]` and should be checked against a primary source before relying, or (4) flag as unverified and stop. Which would you like?" A lawyer decides whether to accept lower-confidence sources.
>
> **Source attribution.** Where the memo cites a statute, regulation, case, or treatise, tag the citation: `[Westlaw]`, `[statute / regulator site]`, or the MCP tool name for citations retrieved from a legal research connector; `[web search — verify]` for web-search citations; `[model knowledge — verify]` for citations recalled from training data; `[user provided]` for citations from the counterparty draft or house files. Citations tagged `verify` carry higher fabrication risk and should be checked first. Never strip or collapse the tags.

```markdown
[WORK-PRODUCT HEADER — per plugin config ## Outputs]

# IP Clause Review: [Counterparty] [Agreement Type]

**Reviewed:** [date]
**Our side for IP:** [Granting / Receiving / Both]
**Governing law:** [jurisdiction]

---

## Bottom line

[Two sentences. Can the IP allocation stand? What has to change first?]

**Issues:** [N]🔴 [N]🟠 [N]🟡 [N]🟢

**Approval needed from:** [name, per practice profile]

---

## Assignment gap check

[✅ Clear | ⚠️ Gap present — see above]

---

## Clauses by severity

[All clause blocks from Step 3, grouped Critical → Low]

---

## Cross-clause consistency

[Flags from Step 4]

---

## Jurisdiction note

[Flags from Step 5]

---

## Approval routing

[From practice profile — who approves, what triggers automatic escalation]
```

## Decision posture

When a clause could be read to allocate IP either way, or when it is unclear whether the drafter's chosen words achieve the stated intent, **flag it for attorney review and surface the factors cutting both ways**. Do not silently decide a subjective allocation question. An unresolved IP allocation that gets signed is a one-way door — the error surfaces in diligence, financing, or litigation. Flagging an ambiguous clause that turns out to be fine is a two-way door.

## Quality checks before delivering

- [ ] Practice profile was loaded and the jurisdiction note reflects what's there
- [ ] Assignment gap checked first (for employment/consulting/SOW/WFH)
- [ ] Every 🔴 and 🟠 issue has specific replacement language
- [ ] Cross-clause consistency checked, not just clause-by-clause
- [ ] Source tags applied to citations; no stripped `verify` tags
- [ ] Approver named per practice profile, not "escalate to legal"
- [ ] Output marked with the work-product header

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

