---
name: ai-inventory
description: >
  EU AI Act per-system inventory — track each AI system's role (provider,
  deployer, importer, distributor, authorized representative, product
  manufacturer) and risk tier (prohibited, high-risk, limited, minimal,
  GPAI, GPAI+systemic). Role and tier are assessed per system, not per
  company. Use when the user says "ai inventory", "add an ai system",
  "what systems do we have", "classify this ai system", "eu ai act
  register", or "ai system registry".
argument-hint: "[list | add | edit <id> | classify <id> | show <id>]"
---

# /ai-inventory

## When this runs

The user wants to manage their AI system inventory under the EU AI Act. The
core idea the skill exists to enforce: **role and tier are per-system, not
per-company.** A single organization can be a *provider* of System A, a
*deployer* of System B, and an *importer* of System C. Each combination
triggers a different set of obligations under the AI Act. The inventory
exists so those assessments are tracked where you can find them — the
obligations themselves are derived in conversation, not from a table.

## What to do

1. **Read the config.** Read
   `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/CLAUDE.md`.
   If it doesn't exist or still has `[PLACEHOLDER]` markers, direct the user
   to `/ai-governance-legal:cold-start-interview` first.

2. **Read the inventory.** Inventory lives at
   `~/.claude/plugins/config/claude-for-legal/ai-governance-legal/ai-systems.yaml`.
   If it doesn't exist, create it with an empty `systems:` list when the
   first `add` runs.

3. **Dispatch on the argument:**

   - No argument, or `list` → show the inventory table (see **List** below).
   - `add` → run the **Add** flow.
   - `edit <id>` → show the current record, ask what to change, update one
     field, confirm, write.
   - `classify <id>` → run the **Classification walk-through** on an
     existing record, updating role, tier, role_basis, and tier_basis.
   - `show <id>` → show the full record.

4. **On list, offer the dashboard:**
   "Want the full dashboard? Filter by status / tier / EU nexus / owner.
   Say the word."

5. **Close every action with a hook into the lawyer's work.**
   After any write, say:
   > Recorded. When you're ready to walk through obligations for this
   > system, just ask — I'll do it in-conversation and flag where the AI
   > Act article mapping needs your verification. I don't derive
   > obligations from a table because the mapping is complex and changing.

## List format

Render as a compact table:

| ID | Name | Owner | Status | EU nexus | Role | Tier | Next review |
|----|------|-------|--------|----------|------|------|-------------|
| sys-001 | Resume screening | HR / Jamie | in_production | yes | deployer | high_risk | 2026-08-01 |
| sys-002 | Email drafting assistant | IT / Priya | in_production | no | deployer | limited | 2026-12-01 |

Under the table, show counts by tier and a line: "N systems flagged for
review within 30 days."

## Add flow (interview)

Ask, one field at a time (or accept a paste). The required fields are
`name`, `owner`, `description`, `status`, `eu_nexus`. The rest can be
deferred — say so explicitly: "you can come back to classification with
`/ai-governance-legal:ai-inventory classify <id>`."

1. **Name.** Short label for the system.
2. **Owner.** Person or team accountable for it day-to-day.
3. **Description.** One or two sentences. What does it do, and against
   what data?
4. **Status.** `planned | in_development | in_production | deprecated`.
5. **EU nexus.** Is the system deployed in the EU/EEA, offered to users in
   the EU/EEA, or used to produce outputs that affect people in the
   EU/EEA? If any of these are true, EU AI Act analysis applies.
6. **Proceed to classification?** Offer to run the walk-through now, or
   skip and come back later.

Assign an ID: `sys-NNN` where NNN is the next integer in the file.

## Classification walk-through

The walk-through produces `role`, `role_basis`, `tier`, `tier_basis`. Both
bases are tagged `[verify against current AI Act text]` — not because the
skill is hedging, but because the article mapping is complex and the AI
Act is still phasing in. The lawyer owns verification.

### Step 1: Role

> **Who does what to this system?**

Options, with the distinguishing test:

- **Provider** — you develop it (or have it developed) and place it on the
  EU market or put it into service under your own name or trademark.
- **Deployer** — you use it under your own authority, not for personal
  non-professional use. (Most common inside companies.)
- **Importer** — you bring an AI system into the EU from a provider
  established outside the EU.
- **Distributor** — you make an AI system available on the EU market
  without being the provider or importer.
- **Authorized representative** — you act on behalf of a non-EU provider
  and are established in the EU.
- **Product manufacturer** — you put a general-purpose AI system (or
  another AI system) into a product under your own name/trademark. Treated
  as provider for the product.

**Dual-role flag.** If the user substantially modifies a vendor system
(fine-tunes on their own data, changes the intended purpose, rebrands),
they may become a **provider** of the modified system even if they started
as a deployer. Call this out when they describe any modification beyond
configuration. `[verify against current AI Act text — Article 25, provider
obligations and substantial modification]`

Write the role. Write `role_basis` in one sentence.

### Step 2: Tier

> **What does the system do, and does the use case fall into a regulated
> category?**

Check in order:

**A. Article 5 prohibited practices.** `[verify against current AI Act
text — Article 5]`

Summaries, not definitive text:
- Subliminal or deceptive techniques materially distorting behavior
- Exploiting vulnerabilities (age, disability, socio-economic status) to
  materially distort behavior
- Social scoring by public authorities leading to detrimental treatment
- Real-time remote biometric ID in publicly accessible spaces for law
  enforcement (narrow exceptions)
- Biometric categorization inferring race, political opinions, union
  membership, religious or philosophical beliefs, sex life, or sexual
  orientation
- Emotion recognition in the workplace or education (medical and safety
  exceptions)
- Facial image database scraping from the internet or CCTV
- Predictive policing based solely on personality traits

If matched → tier is `prohibited`. Flag the use case as stop and route to
the governance team's prohibited-practice workflow.

**B. Annex III high-risk areas.** `[verify against current AI Act text —
Annex III]`

Summaries:
1. Biometric identification and categorization
2. Critical infrastructure (digital infrastructure, road traffic, supply of
   water / gas / heating / electricity)
3. Education and vocational training (access, evaluation, proctoring,
   monitoring prohibited behavior)
4. Employment, worker management, self-employment access — recruitment,
   selection, promotion, termination, task allocation, monitoring, performance
5. Essential private and public services (public benefits, credit scoring
   for individuals, risk assessment and pricing for life/health insurance,
   emergency dispatch)
6. Law enforcement (risk assessment, polygraphs, deepfake detection,
   reliability of evidence, profiling)
7. Migration, asylum, border control (risk assessment, travel document
   verification, examination of applications)
8. Administration of justice and democratic processes (research and
   interpretation, influencing elections)

If matched → tier is `high_risk`. Note the Annex III area and subsection.

**C. GPAI.** `[verify against current AI Act text — Article 51 and
surrounding]`

- **GPAI:** model trained on broad data at scale, designed for generality,
  capable of competently performing a wide range of distinct tasks.
- **GPAI + systemic risk:** cumulative compute > 10^25 FLOPs, or designated
  by the Commission.

**D. Limited risk.** Chatbots interacting with natural persons, deepfakes,
emotion recognition and biometric categorization systems outside Article 5
scope — transparency obligations apply.

**E. Minimal risk.** Everything else.

Write the tier. Write `tier_basis` in one sentence, citing the article or
Annex entry that matched, tagged `[verify against current AI Act text]`.

### Step 3: Recommendations

Offer three next steps:
1. "Want me to walk through obligations for this system? I'll do it in
   conversation — I don't derive them from a table."
2. "Want to run `/ai-governance-legal:aia-generation` to produce a full
   impact assessment?"
3. "Want to set a next review date? I'll add it to the inventory."

## Record format

```yaml
systems:
  - id: sys-001
    name: "Resume screening tool"
    owner: "HR / Jamie"
    description: "Filters inbound CVs against job criteria"
    status: in_production          # planned | in_development | in_production | deprecated
    eu_nexus: true                 # deployed, offered, or affects people in the EU/EEA
    role: deployer                 # provider | deployer | importer | distributor | authorized_rep | product_manufacturer
    role_basis: "We license from VendorX and deploy internally [verify against current AI Act text]"
    tier: high_risk                # prohibited | high_risk | limited | minimal | gpai | gpai_systemic
    tier_basis: "Annex III(4)(a) — employment, recruitment selection [verify against current AI Act text]"
    obligations_assessed: false
    obligations_note: "To assess: as deployer of a high-risk system — human oversight, input data quality, monitoring, record-keeping, informing workers, FRIA if public body/service — see Article 26 [verify against current AI Act text]"
    next_review: "2026-08-01"
    review_trigger: "on substantial modification or annually"
    created: "2026-05-11"
    updated: "2026-05-11"
```

## Why this skill does NOT auto-derive obligations

The inventory stores role, tier, and the basis for each. It does NOT
contain a hardcoded role × tier → obligations table.

When the user asks "what are my obligations for System X?", the skill
does the analysis **in conversation**, tagged `[verify]`, and routes to
`/ai-governance-legal:aia-generation` for the formal impact assessment
if needed.

This is deliberate:
- Article mapping is complex and the AI Act is phasing in through 2027.
- Confident-and-wrong on a compliance obligation ends up in a board memo.
- The inventory is a registry for the lawyer. The lawyer owns the
  obligation analysis.

## Guardrails

- **Never classify silently.** The classification walk-through must be
  visible; do not auto-classify from a system description.
- **`[verify]` tags stay.** They are not hedging — they are the point.
  Do not strip them in outputs.
- **Flag substantial modification.** Whenever a system is modified beyond
  configuration, prompt the user to re-run `/ai-inventory classify` —
  modification can change role.
- **Don't declare obligations from a table.** If asked, do the analysis
  in conversation and route to `/aia-generation` for anything that needs
  a formal record.
