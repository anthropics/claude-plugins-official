---
description: Mine business logic from legacy code into testable, human-readable rule specifications
argument-hint: <system-dir> [module-pattern]
---

Extract the **business rules** embedded in `legacy/$1` into a structured,
testable specification — the institutional knowledge that's currently locked
in code and in the heads of engineers who are about to retire.

Scope: if a module pattern was given (`$2`), focus there; otherwise cover the
entire system. Either way, prioritize calculation, validation, eligibility,
and state-transition logic over plumbing.

## Method

Spawn **three business-rules-extractor subagents in parallel**, each assigned
a different lens. If `$2` is non-empty, include "focusing on files matching
$2" in each prompt.

1. **Calculations** — "Find every formula, rate, threshold, and computed value
   in legacy/$1. For each: what does it compute, what are the inputs, what is
   the exact formula/algorithm, where is it implemented (file:line), and what
   edge cases does the code handle?"

2. **Validations & eligibility** — "Find every business validation, eligibility
   check, and guard condition in legacy/$1. For each: what is being checked,
   what happens on pass/fail, where is it (file:line)?"

3. **State & lifecycle** — "Find every status field, state machine, and
   lifecycle transition in legacy/$1. For each entity: what states exist,
   what triggers transitions, what side-effects fire?"

## Synthesize

Merge the three result sets. Deduplicate. For each distinct rule, write a
**Rule Card** in this exact format:

```
### RULE-NNN: <plain-English name>
**Category:** Calculation | Validation | Lifecycle | Policy
**Priority:** P0 | P1 | P2
**Source:** `path/to/file.ext:line-line`
**Plain English:** One sentence a business analyst would recognize.
**Specification:**
  Given <precondition>
  When  <trigger>
  Then  <outcome>
  [And  <additional outcome>]
**Parameters:** <constants, rates, thresholds with their current values>
**Edge cases handled:** <list>
**Suspected defect:** <optional — legacy behavior that looks wrong; decide preserve-vs-fix during transform>
**Confidence:** High | Medium | Low — <why; if < High, state the exact SME question>
```

Priority heuristic — default to **P1**. Assign **P0** if the rule moves money,
enforces a regulatory/compliance requirement, or guards data integrity (and
flag P0 rules at <High confidence as SME-required). Assign **P2** for
display/formatting/convenience rules. The downstream `/modernize-brief`
behavior contract is built from the P0 rules, so assign deliberately.

Write all rule cards to `analysis/$1/BUSINESS_RULES.md` with:
- A summary table at top (ID, name, category, priority, source, confidence)
- Rule cards grouped by category
- A final **"Rules requiring SME confirmation"** section listing every
  Medium/Low confidence rule with the specific question a human needs to answer

## Generate the DTO catalog

As a companion, create `analysis/$1/DATA_OBJECTS.md` cataloging the core
data transfer objects / records / entities: name, fields with types, which
rules consume/produce them, source location.

## Present

Report: total rules found, breakdown by category, count needing SME review.
Suggest: `glow -p analysis/$1/BUSINESS_RULES.md`
