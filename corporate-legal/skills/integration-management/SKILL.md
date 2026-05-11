---
name: integration-management
description: >
  Post-closing M&A integration tracker — phased workplan, consent tracking,
  contract assignment at scale, weekly status reports. Initializes from whatever
  deal artifacts are available (purchase agreement, deal summary, closing
  checklist) and connects to deal-context.md and closing-checklist.yaml from the
  M&A cold-start. Use when user says "integration", "post-close", "post-closing",
  "consents outstanding", "contract assignment", "integration status", or
  "what's left on the deal".
argument-hint: "[--init | --contracts | --report | --update | --export [--format csv|table] [--section all|consents|contracts|workplan]] [--deal [code]]"
---

# /integration-management

1. Load `deal-context.md` for deal code, target, close date, deal lead.
2. Load `integration-tracker.yaml` if it exists (or create on --init).
3. Use the workflow below.
4. Route by flag:
   - `--init`: Mode 1 — read PA, build phased workplan, consent tracker
   - `--contracts`: Mode 2 — import contract list (repository or upload), tier and classify
   - `--report`: Mode 3 — generate status report
   - `--update`: Mode 4 — manual update or parse uploaded status document
   - `--export`: Mode 5 — CSV or table export
5. Read/write `~/.claude/plugins/config/claude-for-legal/corporate-legal/deals/[code]/integration-tracker.yaml`.
6. After any write: show summary of changes and surface any new flags.

---

## Matter context

**Matter context.** Check `## Matter workspaces` in the practice-level CLAUDE.md. If `Enabled` is `✗` (the default for in-house users), skip the rest of this paragraph — skills use practice-level context and the matter machinery is invisible. If enabled and there is no active matter, ask: "Which matter is this for? Run `/corporate-legal:matter-workspace switch <slug>` or say `practice-level`." Load the active matter's `matter.md` for matter-specific context and overrides. Write outputs to the matter folder at `~/.claude/plugins/config/claude-for-legal/corporate-legal/matters/<matter-slug>/`. Never read another matter's files unless `Cross-matter context` is `on`.

---

## Purpose

Outside counsel closes the deal. Legal inherits the mess. This skill is the
program management layer for post-closing integration — not the business
integration, not IT systems, not HR org design. The legal workstream: consents,
contract assignments, entity rationalization, IP recordals, PA obligations.
It tracks what's done, what's due, what's blocked, and what needs a decision.

---

## Tracker file

Lives at `~/.claude/plugins/config/claude-for-legal/corporate-legal/deals/[code]/integration-tracker.yaml`. Read `deal-context.md` for
the deal code, target name, close date, and deal lead. Inherit any post-close
items from `closing-checklist.yaml` if it exists.

```yaml
# integration-tracker.yaml

metadata:
  deal_code: "[code]"
  target: "[company name]"
  close_date: "[YYYY-MM-DD]"
  deal_lead: "[name]"
  outside_counsel: "[firm and lead attorney]"
  last_updated: "[date]"
  last_status_report: "[date or null]"

pa_dates:
  required_consents_deadline: "[YYYY-MM-DD — extract from PA]"
  rep_survival_expires: "[YYYY-MM-DD]"
  escrow_release: "[YYYY-MM-DD or null]"
  earnout_milestones:
    - description: "[milestone]"
      measurement_date: "[YYYY-MM-DD]"
      payment_date: "[YYYY-MM-DD]"
      owner: "finance"   # always finance — legal tracks date only

workplan:
  day_1:
    target_date: "[close_date + 7 days]"
    items: []
  day_30:
    target_date: "[close_date + 30 days]"
    items: []
  day_90:
    target_date: "[close_date + 90 days]"
    items: []
  day_180:
    target_date: "[close_date + 180 days]"
    items: []

required_consents: []
desired_consents: []

contracts:
  source: "[repository / manual-upload / disclosure-schedule]"
  repository_path: "[path or null]"
  last_imported: "[date]"
  total: 0
  tier_1: []
  tier_2: []
  tier_3: []
  tier_4: []
```

**Workplan item structure:**
```yaml
- id: "W-001"
  description: "[action item]"
  phase: "[day_1 / day_30 / day_90 / day_180]"
  owner: "[legal-owns / legal-supports]"
  workstream: "[legal / hr / it / finance / real-estate / other]"
  priority: "[critical / high / medium / low]"
  deadline: "[YYYY-MM-DD or null]"
  deadline_basis: "[pa-obligation / regulatory / best-practice]"
  status: "[not_started / in_progress / complete / blocked / deferred]"
  blocker: "[description or null]"
  depends_on: "[item id or null]"
  notes: ""
```

**Consent entry structure:**
```yaml
- id: "CON-001"
  counterparty: "[name]"
  contract_type: "[customer / vendor / lease / IP-license / financial / other]"
  required_consent: true        # true = named in PA Required Consents schedule
  pa_deadline: "[YYYY-MM-DD]"   # only for required_consent: true
  status: "[not_started / outreach_sent / in_negotiation / obtained / waived / refused]"
  assigned_to: "[name or null]"
  outreach_date: "[date or null]"
  obtained_date: "[date or null]"
  notes: ""
```

**Contract entry structure:**
```yaml
- id: "C-001"
  name: "[contract name or filename]"
  counterparty: "[party name]"
  contract_type: "[MSA / SaaS / lease / IP-license / employment / NDA / other]"
  annual_value: "[amount or unknown]"
  assignment_mechanism: "[auto-assign / consent-required / coc-provision / silent]"
  tier: 1   # 1=Required Consent, 2=material+consent-required, 3=CoC, 4=auto-assign
  required_consent: false
  pa_deadline: "[YYYY-MM-DD or null]"
  status: "[not_reviewed / no_action / consent_pending / outreach_sent / in_negotiation / consent_obtained / assignment_complete / waived / refused / coc_triggered]"
  assigned_to: "[name or null]"
  notes: ""
  last_updated: "[date]"
```

---

## Mode 1: Initialize

```
/corporate-legal:integration-management --init [--deal [code]]
```

### Step 1: Load deal context

Read `~/.claude/plugins/config/claude-for-legal/corporate-legal/deals/[code]/deal-context.md`. If not found: ask for deal code name,
target company, close date, deal lead, and outside counsel. Write to
deal-context.md if it doesn't exist.

Read `~/.claude/plugins/config/claude-for-legal/corporate-legal/deals/[code]/closing-checklist.yaml` if it exists. Any items marked as
post-closing become Day 1 or Day 30 workplan items (inherit status from
closing-checklist).

### Step 2: Read deal inputs

**A full purchase agreement produces the most complete tracker.** The PA's Required
Consents schedule and post-closing covenants section are the authoritative source
for hard deadlines and legal obligations. But the skill can initialize usefully
from whatever is available — partial inputs produce a starter tracker the attorney
fills in rather than an empty page.

> What deal artifacts do you have available? Share whatever exists:
>
> **Ideal:** The purchase agreement (upload or connected document path). I'll read
> the post-closing covenants, Required Consents schedule, survival periods, escrow
> terms, and earn-out provisions.
>
> **Also useful — share any combination of:**
> - Deal summary or term sheet (gives me the key economics and timeline)
> - Integration to-do list or post-close checklist from outside counsel
> - Existing workplan or integration tracker (I'll import and continue from it)
> - Closing checklist — if generated by the M&A cold-start skill, I'll inherit it
>   automatically from `~/.claude/plugins/config/claude-for-legal/corporate-legal/deals/[code]/closing-checklist.yaml`
> - Required Consents list alone (if the PA is held by outside counsel)
>
> **If you have nothing written down:** Tell me the deal in plain terms — who was
> acquired, when it closed, what the main open items are — and I'll build a
> starter tracker from the standard Day 1/30/90/180 workplan that you edit.

**What changes based on what's provided:**

| Input | What you get |
|---|---|
| Full PA | Complete workplan + Required Consents with deadlines + PA dates |
| PA + contract list | Full tracker + contract assignment tier list |
| Deal summary / to-do list | Standard workplan skeleton, Required Consents as placeholders |
| Nothing | Standard workplan scaffold; attorney fills in consents and contract lists |

The tracker is designed to be built out progressively — a skeleton today, filled
in as more information becomes available.

**From the PA extract:**

*Required Consents schedule:*
- For each consent: counterparty name, contract type, and the contractual
  deadline. Set as required_consent: true with pa_deadline populated.

*Post-closing obligations:*
- Map each obligation to a workplan item. Assign to the correct phase based
  on the deadline. Tag as pa-obligation in deadline_basis.

*Key dates:*
- Required Consents deadline — extract from the PA
- Rep and warranty survival expiry — pull the specific survival periods from the PA.
  General, fundamental, and tax reps typically have different survival periods; pull
  each one the PA defines and record them separately. Do not assume a default.
- Escrow release date(s) — extract from the PA
- Any earn-out measurement and payment dates — add to pa_dates.earnout_milestones,
  owner always set to "finance"

### Step 3: Build the phased workplan

Generate standard workplan items for each phase. Add PA obligations extracted
in Step 2. Items inherited from the closing checklist are pre-populated.

**Day 1 — legal-owns:**
- Entity name change filing (if acquired entity is being renamed) [priority: critical]
- Bank account signatory updates — notify bank with closing documentation [priority: critical]
- Registered agent notification of ownership change [priority: high]
- Key IP assignment execution — if any IP assignments were deferred from closing [priority: critical]
- Domain name and social media account transfer [priority: high]
- D&O insurance — confirm tail policy is bound for acquired entity directors [priority: critical]
- Secretary of State ownership notifications where required by state law [priority: high]

**Day 1 — legal-supports:**
- Employee announcement and communications (HR owns, legal reviews) [priority: critical]
- Benefits day-1 coverage confirmation (HR owns, legal advises on COBRA and plan terms)
- Customer communication letters (business owns, legal reviews for accuracy)

**Day 30 — legal-owns:**
- Required Consents initial push — contact all counterparties, document outreach [priority: critical]
- IP assignment recordal at USPTO (patents, trademarks) [priority: high]
- Copyright assignment filing [priority: medium]
- Trademark assignment recording [priority: high]
- Material contract review — complete tier 1 and tier 2 contract assignment analysis [priority: high]
- Insurance tail policy final confirmation [priority: high]

**Day 30 — legal-supports:**
- Data migration privacy review (IT owns, legal advises on data transfer mechanisms)
- Real estate lease review for assignment provisions (facilities owns, legal advises)

**Day 90 — legal-owns:**
- Required Consents deadline — all Required Consents must be obtained or escalated [priority: critical, deadline: pa_dates.required_consents_deadline]
- Entity rationalization decision — recommend keep separate / merge / dissolve [priority: high]
- Benefits plan assumption or termination documentation [priority: high]
- Secondary consent push — remaining outstanding consents [priority: high]
- Tier 3 change of control contract resolution [priority: critical]

**Day 90 — legal-supports:**
- Full HR harmonization documentation (HR owns, legal advises on employment law)

**Day 180 — legal-owns:**
- Entity merger filing — if rationalization decision is to merge [priority: high]
- Entity dissolution filing — if rationalization decision is to wind down [priority: high]
- Full contract novation — contracts requiring acquiror's name [priority: high]
- Rep survival tracking — note upcoming expiry date [priority: medium]

Show summary after generating:

```
Integration tracker initialized — [Deal code] / [Target]

Close date: [date]
Required Consents deadline: [date] ([N] days from today)
Rep survival expires: [date]

Workplan items: [N] ([N] legal-owns, [N] legal-supports)
Required Consents: [N] (from PA schedule)
Desired Consents: [N] (from diligence — no PA deadline)

Contract assignment: not yet imported — run --contracts to populate

Next step: run /corporate-legal:integration-management --contracts to import the
contract list, then --report to see your first status summary.
```

---

## Mode 2: Contract Assignment

```
/corporate-legal:integration-management --contracts [--deal [code]]
```

This is the dedicated contract assignment initialization. Separate from the
main init so it can be run independently and re-run when the contract list
changes.

### Step 1: Get the contract list

Two paths — use whichever applies:

**Path A: Connected repository**

> Is your contract repository connected? (Google Drive, Box, SharePoint,
> or a VDR that's still accessible post-close?)
>
> If yes: give me the folder path or folder name for the acquired company's
> contracts. I'll pull a list of what's there and read each contract for the
> assignment clause and counterparty.

Search the connected repository. For each document found:
- Extract filename and file path
- Read the document — identify: contract party (counterparty name), contract
  type (from header or subject matter), assignment clause text, change of
  control clause text if present, and annual value if stated.

**Path B: Manual list upload**

> Upload a contract list. This can be:
> - The Material Contracts schedule from the PA disclosure schedules
> - A CSV or Excel export from their contract management system
> - A manually prepared list
>
> Minimum required columns: Contract Name, Counterparty. Helpful but optional:
> Contract Type, Annual Value, Assignment Clause text.

Read the uploaded list. For contracts where no assignment clause text is
provided, set assignment_mechanism to "not_reviewed" and flag for follow-up.

**Path C: Disclosure schedule**

If neither repository nor list is available, read the Material Contracts
schedule from the PA disclosure schedules (from the PA uploaded in --init).
This gives the minimum required list — parties and contract types. Assignment
clauses will need manual review.

### Step 2: Determine assignment mechanism

For each contract, classify the assignment mechanism:

| Mechanism | Definition | Tier |
|---|---|---|
| `consent-required` | Explicit clause prohibiting assignment without counterparty consent | 1 or 2 |
| `coc-provision` | Change of control clause giving counterparty termination or consent right triggered by the deal | 3 |
| `auto-assign` | No restriction, or explicit permission to assign to affiliates or successors | 4 |
| `silent` | No assignment clause — default to governing law. Research the governing-law default for contract assignment when the contract is silent and cite the controlling rule. Flag for attorney review. | 2 |
| `not_reviewed` | Could not read or locate assignment clause | Flag for manual review |

For contracts flagged in the Required Consents PA schedule: override tier to 1
regardless of assignment mechanism classification.

### Step 3: Tier assignment

```
Tier 1 — Required Consents: [N] contracts
  Named in PA schedule, hard deadline [date], must obtain consent

Tier 2 — Material, consent required: [N] contracts
  Assignment restriction present, not in PA schedule
  Recommended timeline: obtain within Day 90

Tier 3 — Change of control provisions: [N] contracts ⚠️
  Counterparty has termination or consent right triggered by close
  ACTION REQUIRED: contact counterparty immediately — CoC may already be triggered

Tier 4 — Auto-assign / no action: [N] contracts
  Assigns automatically or by affiliate/successor provision
  Tracking only — no outreach needed

Not reviewed: [N] contracts
  Could not determine assignment mechanism — manual review required
```

Show tier 3 separately and prominently. A change of control clause may have
already triggered on the close date — counterparty may have a right to terminate
that is running right now.

### Step 4: Generate status entries

For each contract, create a tracker entry with:
- All extracted fields (counterparty, type, value, mechanism, tier)
- Initial status: tier 4 → `no_action`; tier 3 → `coc_triggered`; tiers 1/2 → `consent_pending`; not_reviewed → `not_reviewed`
- pa_deadline populated for tier 1 from Required Consents schedule

---

## Mode 3: Status Report

```
/corporate-legal:integration-management --report [--deal [code]]
```

Reads current tracker state. Produces:

```
[WORK-PRODUCT HEADER — per plugin config ## Outputs — differs by role; see `## Who's using this`]

> This status report is derived from the purchase agreement, diligence findings, and post-closing integration records. It inherits their privilege and confidentiality status — distribution beyond the privilege circle can waive privilege. Confirm the recipient list before sending.

INTEGRATION STATUS — [Deal code] / [Target]
[Date] — Day [N] post-close

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXECUTIVE SUMMARY
[2-3 sentence paragraph: overall status, biggest risk, key win since last report]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REQUIRED CONSENTS  [deadline: DATE — N days remaining]
  Obtained:        [N] of [total]  ████████░░  [%]
  In negotiation:  [N]
  Outreach sent:   [N]
  Not started:     [N]
  Refused:         [N] ⚠️

⚠️ AT RISK: [counterparty] — deadline in [N] days, no response to outreach
⚠️ REFUSED: [counterparty] — PA obligation not met; escalate to outside counsel

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONTRACT ASSIGNMENT
  Tier 1 (Required Consents):   [N] complete / [N] in progress / [N] pending
  Tier 2 (Material contracts):  [N] complete / [N] in progress / [N] pending
  Tier 3 (CoC provisions):      [N] resolved / [N] outstanding ⚠️
  Tier 4 (Auto-assign):         [N] — no action required

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WORKPLAN — LEGAL OWNS
  🔴 OVERDUE ([N]):
    [item] — was due [date]

  ⏰ DUE THIS WEEK ([N]):
    [item] — due [date]

  ✅ COMPLETED SINCE LAST REPORT ([N]):
    [item] — completed [date]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BLOCKERS & DECISIONS NEEDED
  [item] — blocked on: [description] — owner: [name]
  [item] — decision needed: [description] — recommend: [option]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

KEY DATES COMING UP
  [date] — [milestone / deadline]
  [date] — Rep survival expires — confirm no pending indemnification claims

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Mode 4: Update

```
/corporate-legal:integration-management --update [--deal [code]]
```

**Manual update:** Attorney tells Claude what changed.

> "We got the Salesforce consent. Mark it obtained, assigned to [name], date today."
> "The entity rationalization decision is to merge. Update status and add the merger
> filing to Day 180."
> "[Counterparty] refused consent. Flag it and note we need outside counsel on
> whether this triggers a PA indemnification claim."

Claude updates the relevant tracker entry, recalculates any downstream status
(e.g., if all tier 1 consents are now obtained, flag the PA obligation as met),
and shows what changed.

**Upload update:** Workstream owner or outside counsel sends a status document.

> Upload the status update from [outside counsel / HR lead / corp dev team].
> I'll parse it and update the tracker.

Read the uploaded document. Match described items to tracker entries by
counterparty name or workplan item description. Update status fields.
Flag any items in the update that don't match an existing tracker entry —
may be new items to add.

After any update, show:
```
Updated [N] items.

Changes:
  CON-003 Salesforce: not_started → obtained
  W-014 Entity rationalization: in_progress → complete

New flags:
  CON-007 [Counterparty]: refused — PA obligation may be unmet. Consider:
  outside counsel review of indemnification claim. ⚠️
```

---

## Mode 5: Export

```
/corporate-legal:integration-management --export [--format csv|table] [--section all|consents|contracts|workplan]
```

Produces a flat CSV or markdown table. Default: all sections, CSV.

CSV format — one row per item, section indicated by a `section` column.
Columns vary by section:

*Workplan:* id, phase, description, owner, workstream, priority, deadline, status, blocker

*Consents:* id, counterparty, contract_type, required_consent, pa_deadline, status, assigned_to, obtained_date, notes

*Contracts:* id, name, counterparty, contract_type, annual_value, assignment_mechanism, tier, required_consent, pa_deadline, status, assigned_to, notes

Export is the shareable format — suitable for outside counsel, corp dev, or a
board integration update.

---

## What this skill does not do

- It does not manage business integration workstreams (IT, HR, finance, real
  estate). It tracks legal's touchpoints in those workstreams and flags when
  legal input is needed. Ownership stays with the business function.
- It does not draft the consent request letters or novation agreements — those
  are produced by the written-consent skill or by outside counsel.
- It does not advise on indemnification claims or PA breach. When a consent is
  refused or a deadline is missed, it flags the situation — the legal analysis
  of consequences is the attorney's call.
- It does not track earn-out performance. Earn-out milestones and payment dates
  appear in the tracker as reference dates with owner set to finance. The
  business drives the numbers.
- It does not read contracts in real time during status reporting. Contract
  status is what the attorney has updated in the tracker. The skill reads the
  tracker, not the contracts, at report time.


## Formula injection defense

Before writing any cell in Excel, Sheets, or CSV output, neutralize formula injection. Counterparty-sourced text (contract quotes, party names, registered agent data, CLM exports) is attacker-controlled. A cell starting with `=`, `+`, `-`, `@`, `	`, `
`, or `
` will be interpreted as a formula or break the row structure.

- **Prefix with a single quote:** `'=SUM(A1:A10)` → `=SUM(A1:A10)` (displayed as text, not executed)
- **Applies to every cell that contains text sourced from a document, a tool result, or a user paste.** Column headers you control and computed values you produce are safe.
- **CSV: also escape embedded commas, double quotes, newlines** (RFC 4180 quoting).
- This is not optional. A spreadsheet your user opens in Excel that triggers a macro or exfiltrates data via DDE is a supply-chain attack on your user.
