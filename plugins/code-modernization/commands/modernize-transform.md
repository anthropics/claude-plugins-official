---
description: Transform one legacy module to the target stack — idiomatic rewrite with behavior-equivalence tests
argument-hint: <system-dir> <module> <target-stack>
---

Transform `legacy/$1` module **`$2`** into **$3**, with proof of behavioral
equivalence.

This is a surgical, single-module transformation — one vertical slice of the
strangler fig. Output goes to `modernized/$1/$2/`.

## Step 0a — Toolchain check (fail fast on target, adapt on legacy)

Verify the build environment **before** planning, not when the tests
first run:

- **Target stack ($3) — required.** Runtime, package manager, and test
  framework all respond (`java -version` + `mvn -v`, `node -v` + `npm -v`,
  `python3 -V` + `pytest --version`, …). If any are missing, stop and
  report what to install — the new code and its tests cannot run without
  them, so a plan gate now would just defer the failure an hour. Suggest
  `/modernize-preflight $1 $3` for the full readiness report.
- **Legacy stack — advisory, never a blocker.** Try a syntax-only compile
  of the module being transformed (e.g. `cobc -fsyntax-only`). Legacy
  code often *cannot* build locally by nature, not by misconfiguration —
  CICS/IMS programs have no local translator, and the real runtime may be
  a mainframe you don't have. A failed or impossible legacy compile does
  **not** stop the transform; it changes the equivalence strategy:
  - dual-execution proof is off the table — characterization tests
    assert against **recorded traces / golden-master fixtures** (real
    production outputs, captured reports/screens, SME-confirmed
    examples) instead of live legacy runs
  - say so explicitly in the Step 0b plan and later in
    TRANSFORMATION_NOTES.md ("equivalence is trace-based; legacy was not
    executable in this environment"), so reviewers know the strength of
    the proof they're approving

## Step 0b — Plan (HITL gate)

**The brief is binding — read it first.** If `analysis/$1/MODERNIZATION_BRIEF.md`
exists, this transform is one phase (or one module of a phase) of that plan:
read it before deciding anything below. Find the phase that names this
command with `$2` in scope, and treat that phase's **scope, entry criteria,
exit criteria, and any edits the user made to it** as binding on the plan
you present below. Entry criteria are *gates*, not context: if one is not
met (a prior phase's exit criteria, an SME sign-off the brief requires),
meeting it **is** the next step — do not proceed past it and do not silently
re-plan around it. If the brief exists but no phase covers `$2`, stop and
ask which phase this is. The user steers execution by editing the brief; a
brief the execution command never reads cannot steer anything.

Read the source module and any business rules in `analysis/$1/BUSINESS_RULES.md`
that reference it. Then present the plan and **stop — write no code until
the user explicitly approves** (use plan mode if the session supports it):
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
must pass all of them. Follow your secret-handling rules: no credential
literal from legacy code becomes a fixture; substitute fake same-shape
values and read anything genuinely live from environment variables."

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
(Fall back to `diff -y --width=160` if `delta` isn't installed.) Never
pick a credential-bearing line range for this diff, and mask any
credential-like literal quoted in TRANSFORMATION_NOTES.md — the notes
live in `modernized/` and get committed.

## Step 5 — Architecture review

Spawn the **architecture-critic** subagent to review the transformed code
against $3 best practices. Apply any HIGH-severity feedback; list the rest
in TRANSFORMATION_NOTES.md.

Report: tests passing, lines of legacy retired, location of artifacts.
