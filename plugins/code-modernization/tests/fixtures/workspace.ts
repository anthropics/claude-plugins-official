/**
 * A small workspace in the shape the plugin's commands write: one system,
 * `billing`, mapped, with rules, a brief, and one transformed module.
 */

export const TOPOLOGY = JSON.stringify({
  system: 'Billing',
  root: {
    id: 'sys',
    name: 'Billing',
    kind: 'system',
    children: [
      {
        id: 'dom:interest',
        name: 'D1 Interest',
        kind: 'domain',
        children: [
          { id: 'INTCALC', name: 'INTCALC', kind: 'module', language: 'cobol', loc: 600, file: 'app/cbl/INTCALC.cbl' },
          { id: 'ds:RATES', name: 'RATES', kind: 'datastore', store: 'vsam' },
        ],
      },
      {
        id: 'dom:accounts',
        name: 'D2 Accounts',
        kind: 'domain',
        children: [
          { id: 'ACCTUPD', name: 'ACCTUPD', kind: 'module', language: 'cobol', loc: 900, file: 'app/cbl/ACCTUPD.cbl' },
          { id: 'ACCTVIEW', name: 'ACCTVIEW', kind: 'module', language: 'cobol', loc: 300, file: 'app/cbl/ACCTVIEW.cbl' },
        ],
      },
    ],
  },
  edges: [
    { source: 'ACCTUPD', target: 'INTCALC', kind: 'call' },
    { source: 'INTCALC', target: 'ds:RATES', kind: 'read' },
    { source: 'INTCALC', target: 'ds:ACCOUNTS', kind: 'write' },
  ],
  entryPoints: ['ACCTUPD'],
  deadEnds: ['ACCTVIEW'],
  flows: [{ name: 'Month-end interest', persona: 'Cardholder', steps: [{ label: 'Interest runs', nodes: ['INTCALC'] }] }],
})

/**
 * The layout the plugin's own command wrote in practice: ids that carry a domain (`BR-D7-09`),
 * the priority in a backticked header line, list-style Given/When/Then, and legend and appendix
 * tables that are not rules.
 */
export const RULES_BR = `# Business Rules — CardDemo

## How to read this

| Element | Meaning |
|---|---|
| **ID** | \`BR-<domain>-<n>\` |
| **Priority** | P0 money movement |

## D7 Interest & Fee Accrual

#### BR-D7-09 · Monthly interest per transaction-category balance

\`P0\` · Calculation · confidence High · \`app/cbl/CBACT04C.cbl:462-470\`

For each balance bucket, monthly interest equals balance times rate divided by 1200.

- **Given** — A balance of 1250.00 at rate 15.00
- **When** — The interest batch processes that row
- **Then** — Interest is 15.62 (truncated, NOT rounded)

**Edge cases**

- COMPUTE has no ROUNDED clause

> ⚠️ **Suspected defect** — Truncation where most products round half-up.

---

#### BR-D7-10 · Interest statement line

\`P2\` · Lifecycle · confidence Medium · \`app/cbl/CBSTM03A.cbl:10-12\`

The statement prints the interest line.

- **Given** — A posted interest amount
- **When** — The statement is produced
- **Then** — The line shows the amount

> ❓ **SME question** — Should zero interest print?

## Appendix A — Suspected defects

| **BR-D7-09** | truncation | \`app/cbl/CBACT04C.cbl:462\` |
`

/**
 * The labelled-fields layout a later model wrote: `### RULE-007: title`, `**Category:**`, `**Priority:**`,
 * `**Source:**`, `**Plain English:**`, a fenced Given/When/Then block, `**Edge cases handled:**`,
 * `**Suspected defect:**`, and the SME question inside the confidence line. A summary table lists every
 * rule up front and is not a set of rules.
 */
export const RULES_LABELLED = `# Business Rules — carddemo

## Summary

| ID | Name | Category | Priority | Source | Confidence |
|---|---|---|---|---|---|
| RULE-007 | Monthly interest per transaction category | Calculation | P0 | \`app/cbl/CBACT04C.cbl:188-222, 415-470\` | High |

## Calculation rules

### RULE-007: Monthly interest per transaction category using disclosure-group rate
**Category:** Calculation  
**Priority:** P0  
**Source:** \`app/cbl/CBACT04C.cbl:188-222, 415-470\`  
**Plain English:** The monthly interest is the balance times the annual rate divided by 1200, truncated to cents.
**Specification:**
\`\`\`
Given Account in group 'GOLD' has TRAN-CAT-BAL $1,250.00 and DIS-INT-RATE 18.50
When  CBACT04C processes that category record
Then  WS-MONTHLY-INT = 1250.00 * 18.50 / 1200 = $19.27 (truncated not rounded)
And   If the group is not in DISCGRP, the rate is read from 'DEFAULT'
\`\`\`
**Parameters:** Divisor 1200  
**Edge cases handled:**
  - No ROUNDED clause on the COMPUTE; result is truncated to cents
  - Negative balances produce negative interest
**Confidence:** High

### RULE-004: Pending authorization summary counters updated per decision
**Category:** Lifecycle  
**Priority:** P0  
**Source:** \`app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:700-720\`  
**Plain English:** Each decision updates the pending-authorization counters.
**Specification:**
\`\`\`
Given A declined authorization
When  The decision is recorded
Then  The declined-amount total is increased
\`\`\`
**Parameters:** none  
**Edge cases handled:**
  - none
**Suspected defect:** Line 821 adds a stale amount to the declined total.  
**Confidence:** Medium — SME question: Should declined-amount accumulate the current request's amount?

### RULE-090: Statement footer prints the page count
**Category:** Policy  
**Priority:** P2  
**Source:** \`app/cbl/CBSTM03A.cbl:10-12\`  
**Plain English:** The footer shows the page count.
**Specification:**
\`\`\`
Given A statement of two pages
When  The footer prints
Then  It reads page 2 of 2
\`\`\`
**Parameters:** none  
**Edge cases handled:**
  - none
**Confidence:** High

## Appendix A — Rejected candidates

### RULE-999: Not a rule
**Priority:** P0
`

export const RULES = `# Business Rules — Billing

# P0 rules

## D1 Interest

### P0-001 · Monthly interest is truncated, not rounded

\`legacy/billing/app/cbl/INTCALC.cbl:462-470\` · Calculation · confidence **High**

Monthly interest equals balance times rate over 1200, truncated to cents.

> **Given** A balance of $1,250.00 at 18.50%
> **When** The interest batch runs
> **Then** Interest is $19.27, not $19.28

**Edge cases**

- A zero rate skips the account

> ⚠️ **Suspected defect** — Truncation where most products round half-up.

### P0-002 · Missing rate row aborts the run

\`legacy/billing/app/cbl/INTCALC.cbl:415-460\` · Calculation · confidence **Medium**

If no rate row exists the whole batch abends.

> **Given** An account with no rate row
> **When** The batch reads the rate file
> **Then** The program abends with code 999

> ❓ **SME** — Should the account be skipped instead?

## D2 Accounts

### P0-003 · Account update checks for concurrent change

\`legacy/billing/app/cbl/ACCTUPD.cbl:100-140\` · Validation · confidence **High**

An update is refused when the record changed since it was read.

> **Given** Two operators on one account
> **When** The second saves
> **Then** The save is refused

# P1 rules

## D2 Accounts

| Rule | Given / When / Then | Source | Flags |
|---|---|---|---|
| **View shows masked id**<br/>Policy | **G** An operator opens an account **W** The screen draws **T** The id is masked | \`legacy/billing/app/cbl/ACCTVIEW.cbl:50-60\` | |

# Appendix — rules rejected at citation verification

| Rule | Why |
|---|---|
| **Not a rule** | rejected |
`

export const BRIEF_UNSIGNED = `# Modernization Brief — Billing → Java / Spring

## 3. Phased Sequence

### Phase 1 — Interest pilot (D1) · **Size M** · Risk **Medium**

Scope: INTCALC.

Exit criteria:

- [ ] All P0 interest rules proven equivalent against recorded traces.
- [ ] Golden-master diff is clean on the full fixture set.

### Phase 2 — Accounts (D2) · **Size L** · Risk **High**

Scope: ACCTUPD and ACCTVIEW.

Exit criteria:

- [ ] Concurrency rule proven under load.

## 7. Open Questions

- [ ] Who owns the rate table?

## 8. Approval Block

\`\`\`
Approved by: ________________
Date:        __________

Approval covers:   [ ] Phase 1 only      [ ] Full plan
\`\`\`
`

export const BRIEF_SIGNED = BRIEF_UNSIGNED.replace('Approved by: ________________', 'Approved by: VP Engineering')
  .replace('Date:        __________', 'Date:        2026-09-15')
  .replace('[ ] Phase 1 only', '[X] Phase 1 only')

export const NOTES_REVIEWED = `# Transformation Notes — INTCALC

## Behaviour mapping

...

## Follow-ups for Phase 2

- Rate cache

## Architecture review

Reviewed 2026-09-15. HIGH-1 applied.
`

export const surefire = (tests: number, failures = 0, skipped = 0) =>
  `<?xml version="1.0"?>\n<testsuite name="x" tests="${tests}" errors="0" skipped="${skipped}" failures="${failures}"></testsuite>`

/** Discovery done, brief signed, INTCALC transformed and reviewed. */
export const FULL: Record<string, string> = {
  'analysis/billing/PREFLIGHT.md': '# Preflight',
  'analysis/billing/ASSESSMENT.md': '# Assessment',
  'analysis/billing/topology.json': TOPOLOGY,
  'analysis/billing/BUSINESS_RULES.md': RULES,
  'analysis/billing/MODERNIZATION_BRIEF.md': BRIEF_SIGNED,
  'legacy/billing/app/cbl/INTCALC.cbl': Array.from({ length: 600 }, (_, i) => `       LINE ${i + 1}.`).join('\n'),
  'legacy/billing/app/cbl/ACCTUPD.cbl': '       IDENTIFICATION DIVISION.',
  'legacy/billing/app/cbl/ACCTVIEW.cbl': '       IDENTIFICATION DIVISION.',
  'modernized/billing/INTCALC/src/main/java/Interest.java': 'class Interest {}',
  'modernized/billing/INTCALC/src/test/java/InterestTest.java': 'class InterestTest {}',
  'modernized/billing/INTCALC/TRANSFORMATION_NOTES.md': NOTES_REVIEWED,
  'modernized/billing/INTCALC/target/surefire-reports/TEST-InterestTest.xml': surefire(12),
}

/** Discovery done and a brief written, not yet signed; nothing transformed. */
export const UNSIGNED: Record<string, string> = Object.fromEntries(
  Object.entries({ ...FULL, 'analysis/billing/MODERNIZATION_BRIEF.md': BRIEF_UNSIGNED }).filter(
    ([path]) => !path.startsWith('modernized/'),
  ),
)
