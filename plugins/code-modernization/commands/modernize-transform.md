---
description: Transform one legacy module to the target stack — idiomatic rewrite with behavior-equivalence tests
argument-hint: <system-dir> <module> <target-stack>
---

Transform `legacy/$1` module **`$2`** into **$3**, with proof of behavioral
equivalence.

This is a surgical, single-module transformation — one vertical slice of the
strangler fig. Output goes to `modernized/$1/$2/`.

## Step 0 — Plan (HITL gate)

Read the source module and any business rules in `analysis/$1/BUSINESS_RULES.md`
that reference it. Then **enter plan mode** and present:
- Which source files are in scope
- The target module structure (packages/classes/files you'll create)
- Which business rules / behaviors this module implements
- How you'll prove equivalence (test strategy)
- Anything ambiguous that needs a human decision NOW

Wait for approval before writing any code.

## Step 1 — Characterization tests FIRST

Before writing target code, spawn the **test-engineer** subagent:

"Write characterization tests for legacy/$1 module $2. Read the source,
identify every observable behavior, and encode each as a test case with
concrete input → expected output pairs derived from the legacy logic.
Target framework: <appropriate for $3>. Write to
`modernized/$1/$2/src/test/`. These tests define 'done' — the new code
must pass all of them."

Show the user the test file. Get a 👍 before proceeding.

## Step 2 — Idiomatic transformation

Write the target implementation in `modernized/$1/$2/src/main/`.

**Critical:** Write code a senior $3 engineer would write from the
*specification*, not from the legacy structure. Do NOT mirror COBOL paragraphs
as methods, do NOT preserve legacy variable names like `WS-TEMP-AMT-X`.
Use the target language's idioms: records/dataclasses, streams, dependency
injection, proper error types, etc.

Include: domain model, service logic, API surface (REST controller or
equivalent), and configuration. Add concise Javadoc/docstrings linking each
class back to the rule IDs it implements.

## Step 3 — Prove it

Run the characterization tests:
```bash
cd modernized/$1/$2 && <appropriate test command for $3>
```
Show the output. If anything fails, fix and re-run until green.

## Step 4 — Side-by-side review

Generate `modernized/$1/$2/TRANSFORMATION_NOTES.md`:
- Mapping table: legacy file:lines → target file:lines, per behavior
- Deliberate deviations from legacy behavior (with rationale)
- What was NOT migrated (dead code, unreachable branches) and why
- Follow-ups for the next module that depends on this one

Then show a visual diff of one representative behavior, legacy vs modern:
```bash
delta --side-by-side <(sed -n '<lines>p' legacy/$1/<file>) modernized/$1/$2/src/main/<file>
```

## Step 5 — Architecture review

Spawn the **architecture-critic** subagent to review the transformed code
against $3 best practices. Apply any HIGH-severity feedback; list the rest
in TRANSFORMATION_NOTES.md.

Report: tests passing, lines of legacy retired, location of artifacts.
