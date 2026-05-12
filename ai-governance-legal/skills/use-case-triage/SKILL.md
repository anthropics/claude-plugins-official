---
name: use-case-triage
description: >
  Classify a proposed AI use case against your registry — approved, conditional,
  or not approved — and produce required conditions and next steps. Flags
  cross-plugin handoffs to privacy or product counsel. Use when user says "triage
  this use case", "can we use AI for X", "is this approved", "what do we need to
  do to use AI for X".
argument-hint: "[describe the use case, or 'batch' to triage a list]"
---

# /use-case-triage

1. Read `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`. Confirm registry is populated — if not, stop and direct to setup.
2. Use the framework below. Clarify the use case if vague.
3. Registry lookup → red line check → classify.
4. Output: classification, reasoning, conditions table (if conditional), governance tier, cross-plugin handoffs.
5. Propose registry update if use case wasn't already in the registry.

```
/ai-governance-legal:use-case-triage "Sales team wants to score leads with AI automatically"
```

---

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/ai-governance-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Purpose

Stop the conversation that happens in a hallway and starts as "can we just use AI
for this?" Give a fast, calibrated answer from the registry — and if the answer
is conditional, make the conditions concrete and the next step obvious.

The triage skill is a gateway, not a destination. Its job is to classify, flag
what's required, and route. The aia-generation skill does the deep work.

## Read `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` first

Before triaging, always read `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`. The use case registry and red lines there
are authoritative. Generic AI ethics reasoning is not a substitute for what this
company has actually decided.

If `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` contains `[PLACEHOLDER]`, surface this bounce:

> I notice you haven't configured your practice profile yet — that's how I tailor the use case registry, red lines, and governance tiers to your practice.
>
> **Two choices:**
> - Run `/ai-governance-legal:cold-start-interview` (2 minutes) to configure your profile, then I'll triage tailored to YOUR practice.
> - Say **"provisional"** and I'll triage against generic defaults — US jurisdiction, middle risk appetite, lawyer role, no playbook — and tag every output `[PROVISIONAL — configure your profile for tailored output]` so you can see what I do before committing.

### Provisional mode

If the user says "provisional," run triage normally using these generic defaults: middle risk appetite, lawyer role, US jurisdiction, no registry (classify by general AI governance principles rather than matching to a registered entry). Tag the reviewer note and every finding block with `[PROVISIONAL]`. At the end of the output, append:

> "That was a generic run against default assumptions. Run `/ai-governance-legal:cold-start-interview` to get output calibrated to YOUR practice — your registry, your jurisdiction, your risk appetite. 2 minutes."

**Jurisdictional scope.** Triage applies the registry, red lines, and governance tiers configured for the regulatory footprint in `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`. AI rules vary materially by jurisdiction — an APPROVED classification in one footprint may be CONDITIONAL or prohibited in another. If deployment touches a jurisdiction not in the footprint, surface that and re-triage rather than extending by analogy.

---

## Triage process

### Step 1: Understand the use case

Before classifying, make sure you understand what's actually being proposed. If
the description is vague, ask:

- "What is the AI doing, exactly — generating content, making a decision, surfacing
  recommendations, automating a task?"
- "Who or what is the AI acting on — employees, customers, third parties, internal
  data only?"
- "Is a human reviewing the AI output before anything happens, or is it automated?"
- "Which vendor or tool is being proposed?"
- "Is this internal-only, or does it touch customers or other external parties?"

Don't let "we want to use AI for [vague thing]" go untriaged. Get specific enough
to classify accurately.

---

### Step 2: Registry lookup

Check the use case registry in `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` for a direct or close match.

**Direct match:** If the registry has a directly matching entry, apply it.

**Near match:** If the use case is similar to a registry entry but not identical,
flag this: "This looks like [registered use case] — I'm applying that classification,
but if the scope is meaningfully different, it may need its own assessment."

**No match:** If the use case isn't in the registry, default to CONDITIONAL pending an AI impact assessment. Surface the preliminary read on risk and route to the AIA.

> "This use case isn't in your registry yet. Defaulting to CONDITIONAL pending an
> AI impact assessment. Here's my preliminary read on risk: [preliminary read].
> Next step: run the impact assessment, and I'll add the use case to the registry
> once classification is settled."

---

### Source attribution (applies whenever the triage cites regulation)

Triage typically stays high-level, but if the classification depends on citing a regulation, statute, rule, directive, standard, or guidance — tag the citation. Do not output untagged regulatory citations in the triage reasoning, the red-line explanation, or the conditions list. A triage that says "Art. 22(1)" without a tag is exactly where a fabricated pinpoint slips past the reader.

**Source attribution tiering.** For model-knowledge citations, use one of three tiers:

- `[settled]` — stable, well-known statutory and regulatory references unlikely to have changed (e.g., GDPR Art. 22 as a concept, the existence of Regulation (EU) 2024/1689 as the EU AI Act). Still verify before certifying, but lower priority.
- `[verify]` — model-knowledge citations that are real but should be verified: specific delegated / implementing acts, regulator guidance, standards, effective dates, thresholds, post-2023 amendments.
- `[verify-pinpoint]` — pinpoint citations (specific article numbers, annex references, subsection letters, paragraph numbers) carry the highest fabrication risk and should ALWAYS be verified against a primary source. EU AI Act article numbers in particular shifted during consolidation; every pinpoint cite to the Act should be verified against the Official Journal text.

Other sources keep their own tags: `[registry]` when drawn from the practice profile's use case registry; `[Westlaw]`, `[EUR-Lex]`, `[regulator site]`, or the MCP tool name when retrieved from a connected legal research tool; `[web search — verify]` for web-search citations; `[user provided]` for user-supplied citations. The tiering surfaces the real verification work — a reader who verifies everything verifies nothing. Never strip or collapse the tags.

**For non-lawyer users, uncertain dates and thresholds go in a confirm-list, not inline.** A `[verify]` tag on "effective February 1, 2026" reads as "effective February 1, 2026" to someone who doesn't know what the tag means. Read `## Who's using this` in `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`. If Role is **Non-lawyer** and an effective date, phase-in, threshold, or deadline is uncertain (would carry `[verify]` or `[verify-pinpoint]` if inline), replace the inline assertion with "effective date: confirm with counsel" (or "threshold: confirm with counsel") and collect all uncertain assertions in a final triage section titled: "**Things I'm not certain about — ask your attorney to confirm before relying on this:**" with each item listed (what I said, what's uncertain, why it matters). Lawyer-role users keep the inline `[verify]` treatment.

---

### Step 3: Red line check

Before going further, check the red lines in `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`.

If the use case triggers a red line — even partially, even in a charitable reading —
say so immediately.

> "This use case touches [red line]. Your red lines treat this as an automatic no.
> If there's something different about this situation, that's a conversation for
> legal sign-off — not a triage call."

Do not soften red line outcomes. If it's a no, it's a no.

---

**Jurisdictional scope.** Ask: "Who's affected, and where are they? (Employees / customers / the general public / specific groups.) Which jurisdictions? (Not just where your company is — where the affected people are.)"

Then check the use case against EVERY regime in the practice profile's `## Regulatory footprint`, not just the primary one. Flag conflicts:
- "APPROVED under US law, but triggers EU AI Act Article 27 FRIA if EU residents are affected — confirm whether any affected individuals are in the EU."
- "Standard tier under your governance framework, but NYC LL144 requires a bias audit if used for hiring decisions affecting NYC residents."
- "Low risk under Australian AI Ethics Framework, but may be high-risk under the Colorado AI Act if Colorado residents are affected."

A use case that crosses jurisdictions gets the strictest applicable treatment, not the most convenient one.

---

### Step 4: Classification and output

The APPROVED / CONDITIONAL / NOT APPROVED buckets, the red-line definitions, and the CONDITIONAL required-controls list all come from `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` → `## AI use case triage criteria` and `## Use case registry`. If the playbook doesn't define a criterion the use case turns on, ask the user: "Your playbook doesn't cover [specific question]. What's your default position? I'll add it to `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` so the next triage is consistent."

**Before issuing an APPROVED classification (approving an AI use case for deployment):** Read `## Who's using this` in `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`. If the Role is Non-lawyer:

> Approving this use case for deployment has legal consequences. Have you reviewed this with an attorney? If yes, proceed. If no, here's a brief to bring to them:
>
> [Generate a 1-page summary: the use case and its scope, how it maps to the registry, what policies or red lines it touches, what could go wrong in deployment, what to ask the attorney before green-lighting.]
>
> If you need to find an attorney, solicitor, barrister, or other authorised legal professional: your professional regulator's referral service is the fastest starting point (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent).

Do not proceed past this gate without an explicit yes. CONDITIONAL outputs do not require the gate.

**Before issuing a NOT APPROVED classification that cuts off a proposed use case:** Read `## Who's using this` in `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`. If the Role is Non-lawyer, a symmetric gate applies — wrongly rejecting a use case is also a consequential error, and the business will push back regardless of the triage call:

> This is a full stop for a business ask. Have you reviewed this with an attorney? If yes, proceed. If no, here's a brief to bring to them:
>
> [Generate a 1-page summary: the use case and its scope, the specific red line or registry entry that blocks it, what a narrower version could look like that might clear elevated tier (if anything), what the business will likely ask the attorney for, and the three questions to ask the attorney before accepting the no.]
>
> If you need to find an attorney, solicitor, barrister, or other authorised legal professional: your professional regulator's referral service is the fastest starting point (state bar in the US, SRA/Bar Standards Board in England & Wales, Law Society in Scotland/NI/Ireland/Canada/Australia, or your jurisdiction's equivalent).

Do not proceed past this gate without an explicit yes. A non-lawyer issuing a hard no on the AI plugin's behalf, without an attorney in the loop, is the mirror failure of a non-lawyer issuing a hard yes.

**Format for each triage output:**

---

[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

**USE CASE:** [State the use case as you understand it]

**CLASSIFICATION:** [APPROVED / CONDITIONAL / NOT APPROVED]

**Registry match:** [Direct match / Near match — [name] / No match]

**Reasoning:**
[1-3 sentences on why this classification. If approved, what makes it safe. If
conditional, what creates the risk that conditions are managing. If not approved,
what red line or policy position applies.]

**Red lines triggered:** [None / List any that apply]

---

*If CONDITIONAL — required before proceeding:*

| Requirement | Owner | Done? |
|---|---|---|
| [e.g., AI impact assessment] | [AI governance counsel] | ☐ |
| [e.g., Privacy review / PIA] | [Privacy counsel] | ☐ |
| [e.g., Human-in-the-loop requirement — no automated decisions] | [Product] | ☐ |
| [e.g., Disclosure to affected parties] | [Product / Legal] | ☐ |
| [e.g., Specific vendor only — [approved vendor name]] | [Procurement] | ☐ |
| [e.g., Legal sign-off] | [GC] | ☐ |

**Governance tier:** [Standard / Elevated / High — per `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`]

**Approval path:** [Who needs to sign off, per tier]

**Next step — offer to continue:**

After presenting a CONDITIONAL result, always end with:

> "Want me to start the impact assessment now? I can run the intake questions
> and produce the assessment document without you needing to run a separate command."

If they say yes, load the `aia-generation` skill and continue in the same
conversation — no need to restart. Pass the use case description and governance
tier already determined.

If they say no (or don't respond), the triage result stands as a standalone output.
The AIA can be run any time with:
`/ai-governance-legal:aia-generation [use case]`

---

*If NOT APPROVED:*

**Reason:** [Specific red line, policy prohibition, or registry entry]

**If there's a version of this that could work:** [Optional — "A narrower version
that keeps a human in the loop for every adverse decision might clear the elevated
tier. That would require..."] Only include if genuinely true. Don't offer a workaround
for every no.

---

### Step 5: Cross-plugin handoffs

**Privacy handoff:** If the use case involves personal data — employee data,
customer data, behavioral data — flag it:

> "This use case involves personal data. A PIA is likely required in addition to
> an AI impact assessment. Use `/privacy-legal:pia-generation [use case]`, if the
> plugin is installed, to run that in parallel."

**Product counsel handoff:** If this is a new product feature involving AI:

> "If this use case is part of a product launch, loop in product counsel.
> Use `/product-legal:launch-review`, if the plugin is installed — it will detect
> the AI component and route to this plugin."

Only flag handoffs that are actually relevant. Don't append both as boilerplate
to every triage.

---

### Step 6: Registry update suggestion

If this triage resulted in a classification that isn't in the registry yet — either
a no-match or a near-match that revealed a gap:

> "I'd suggest adding this to your use case registry. Proposed entry:"

```
| [Use case description] | [Approved/Conditional/Never] | [Conditions if any] | [Reason if Never] |
```

> "Add to `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md` → Use case registry. This means next time the same request
> comes up, the answer is documented and consistent."

---

## Batch triage

If the user presents multiple use cases at once — a list, a backlog, a product
roadmap — run through each one and output a summary table first, then expand
each conditional or not-approved entry:

| # | Use case | Classification | Key condition / blocker |
|---|---|---|---|
| 1 | [use case] | 🟢 Approved | — |
| 2 | [use case] | 🟡 Conditional | Impact assessment required |
| 3 | [use case] | 🔴 Not approved | Automated adverse decision — red line |

Then expand each row that isn't a clean approved.

---

## Edge cases and failure modes

**"We're already doing this" triage:**
If someone is asking for retroactive triage — the use case is already deployed —
say so plainly, and before classifying from scratch, search the registry for an
existing entry covering the deployed version. Retroactive triages often surface a
superseded registry entry whose conditions have drifted from current practice;
updating that entry is usually the right follow-up rather than adding a new row.
> "This looks like retroactive triage. If this is already running without an
> assessment, that's a gap to document, not to wave through. I'm searching the
> registry for any existing entry covering this deployment before running the
> triage fresh. Here's the classification: [run normal triage]. If it's
> conditional, those conditions should be confirmed in place now, not assumed.
> If the registry has an existing entry and the deployed version has drifted,
> the right follow-up is updating that entry rather than adding a new one."

**"It's just internal" doesn't change the analysis:**
Internal AI use affecting employees (screening, monitoring, evaluation) is often
higher-risk than customer-facing AI. Flag this if the user implies internal scope
reduces risk.

**"The vendor says it's safe":**
Vendor representations don't substitute for your own impact assessment. Flag it:
> "The vendor's position doesn't substitute for your own assessment — especially
> for anything in the elevated or high tier."

**"We're just piloting":**
A pilot that touches real employee or customer data is not exempt from triage or
impact assessment. Apply the same classification; if conditions include an impact
assessment, the pilot should have one too.

## Close with the next-steps decision tree

End with the next-steps decision tree per CLAUDE.md `## Outputs`. Customize the options to what this skill just produced — the five default branches (draft the X, escalate, get more facts, watch and wait, something else) are a starting point, not a lock-in. The tree is the output; the lawyer picks.

