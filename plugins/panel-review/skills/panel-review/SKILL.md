---
name: panel-review
description: >
  Run the 2-pass code review system on staged changes or a diff. Invoke when the user
  says "run panels", "panel review", "review my changes", "run the passes", "defense pass",
  "adversary pass", or "/panel-review". Also invoke proactively after writing or editing
  security-critical code (auth, permissions, DB writes, MCP tools) before the user commits —
  don't wait to be asked. Classifies the risk tier, spawns a Defense pass (Sonnet) for all
  non-trivial changes and an Adversary pass (Opus) for high-risk T1 changes, then returns
  structured findings with exact file:line references and test signatures.
---

# Panel Review — 2-Pass Code Review

Two passes replace the old five-panel system. Classify the risk tier, run the right
passes as separate Agent spawns, then synthesize findings.

---

## Step 1 — Get the diff

If the user provided a diff or pasted code: use it.

Otherwise, get it:
```bash
git diff HEAD          # staged + unstaged changes
# or for a branch review:
git diff main...HEAD
```

Also ask (or infer from context): one sentence describing what this change is supposed to do.

---

## Step 2 — Classify the tier

Read the diff and pick the highest matching tier. State your choice and reasoning in one line.

| Tier | Triggers |
|------|----------|
| **T1** | Touches auth, RLS, permissions, secrets, or MCP tool schemas; major rewrite (>50% of a module); new service/route/data boundary |
| **T2** | Touches DB writes or external API calls, but not auth/permissions; new MCP write tool handler |
| **T3** | Logic or behavior change with no security surface |
| **T4** | Purely cosmetic — typo, log wording, comment, test-only with zero auth/db-path |

When in doubt, go up one tier.

---

## Step 3 — Spawn the passes

| Tier | Passes |
|------|--------|
| T1 | Defense pass (model: Sonnet) + Adversary pass (model: Opus) — run both; enable §7 if DB-touching |
| T2 | Defense pass only — §7 Performance enabled |
| T3 | Defense pass only — §7 omitted |
| T4 | Skip — state "T4: no review needed" and stop |

Spawn each pass as a **separate Agent call**. Do not combine them. Pass the full diff and
feature context verbatim into each prompt.

---

## Defense Pass Prompt

Fill in DIFF and FEATURE_CONTEXT, then use as the Agent prompt verbatim.

---
You are a senior engineer doing a blocking code review. Find real defects — broken
behavior, unverified wiring, exploitable input handling, or a test that passes when
the bug is present.

**Diff under review:**
DIFF

**Feature context:** FEATURE_CONTEXT

**1. EXECUTION PATH** — Trace the full call chain from the public entry point (HTTP
route / CLI / MCP dispatcher) to the final I/O. List every hop. Flag any function
defined and tested but not in this chain — dead code is not a safety gate.

**2. WIRING GAPS** — For every new enforcement function, gate, or validator: is there
a test entering at the public entry point, triggering the condition, and asserting the
gate fired? Unit tests on the function itself do not verify wiring.

**3. LOCKED CONTRACTS** — List every locked spec this diff is supposed to implement.
For each: identify the exact line of code that implements it. "Gated by X so Y is
unnecessary" is not an implementation.

**4. SIBLING INSTANCES** — For every guard added: list every other route/function
performing a similar operation that may be missing the equivalent guard. State which
siblings were checked and their status.

**5. TESTS**
- Every test enters at the public entry point, not the function directly?
- Every test asserting a state label also asserts a behavioral side effect (method
  called, object replaced, output written)?
- Every new ID format / enum variant tested through the full output pipeline
  (load → process → output), not just the parser?
- Every existing test asserting a value this diff changes — updated to assert the
  new correct behavior?
- MOCK DISCIPLINE: create_autospec(real_fn, return_value=...) for every DB/external
  mock? List any that are not.
- HTTP BOUNDARY: TestClient/AsyncClient test entering at the HTTP route for every
  security gate?

**6. SECURITY**
- CONDITIONAL GUARD COMPLETENESS: does every else: branch also have an
  ownership/identity check?
- OUTPUT FORMAT INJECTION: for each user-controlled string in the output — is
  escaping format-specific (html.escape, parameterized SQL, shlex.quote)?
- SANITIZATION COMPLETENESS: every sibling sanitizer also updated?
- INFO DISCLOSURE: no error message leaks table names, column names, constraint
  names, org IDs?
- NULL/ZERO SUBSTITUTION: substitute None, 0, '', and False for every conditional.
  Does the condition still reject the dangerous case?
- EXCEPTION HANDLING: does any DB call surface raw error messages (asyncpg DataError,
  constraint names, column details) in the HTTP response? All DB exceptions must be
  caught, logged server-side, and return a generic detail string.
- INPUT BOUNDS: for any list/array parameter — is there an explicit max_items guard?
  An unbounded list + N+1 query is a pool-exhaustion DoS vector.
- Industry-standard approach? Name it.

**7. PERFORMANCE** *(include only when diff touches DB hot path — required for T1/T2)*
- DB ROUND-TRIPS: list every sequential DB await (file:line). More than 1 per
  request = pool-exhaustion risk. Can each be collapsed to a CTE?
- AUTH CACHE: token verification hits in-memory cache before pool.acquire()?
  Name cache and TTL.
- N+1 QUERIES: every loop with a per-iteration DB call — max iteration count?
  Collapsible to IN-clause or JOIN?
- UNBOUNDED QUERIES: every SELECT without LIMIT — max rows returnable?
- TRANSACTION SCOPE: no external calls (HTTP, file I/O, sleep) inside any
  transaction?

Output — for each finding:
  FIX [N]: <file>:<line>
  Change: <exact description>
  Test: test_regression_<name> — asserts <what>
Omit sections with no findings. End: PASS or BLOCK, finding count.

---

## Adversary Pass Prompt (T1 only — spawn as separate Opus Agent)

Fill in DIFF and FEATURE_CONTEXT, then use as the Agent prompt verbatim.

---
You are an attacker reviewing this diff, not an auditor. Find the exploit, not the
compliance gap. Assume the developer is competent — any gap is something they convinced
themselves was safe.

**Diff under review:**
DIFF

**Feature context:** FEATURE_CONTEXT

**1. RATIONALIZATIONS** — Every comment or design decision saying a check is
unnecessary because of X: is X actually sufficient? "We check Y upstream so Z is safe"
is your first target. Name the rationalization and the exploit.

**2. THE SIBLING THAT WASN'T FIXED** — For every function patched: grep for functions
with the same purpose elsewhere. The developer fixed the one they were looking at. List
the ones they weren't, and state whether each is exploitable.

**3. MALICIOUS INPUT — FULL DATA FLOW** — Pick the most dangerous user-controlled
input. Trace it from API boundary through every transformation to final output or
storage. Can each transformation be bypassed, reversed, or circumvented?

**4. REGRESSION INTRODUCTION** — Does this fix redirect an attack to a sibling route
that is now comparatively less protected?

**5. ENUMERATION ORACLE** — Do error messages, timing, or response shapes differ
between "not found", "wrong org", "wrong user", "personal vs org" cases? All must
return identical responses with identical timing.

**6. NEW FORMAT / VARIANT AUDIT** — If a new ID format, enum variant, or schema
extension was introduced: every place the codebase pattern-matches the old format
(regex, match, conditional) — all updated?

**7. WRONG MECHANISM CLASS** — Is this the right class of solution for this threat?
Name the stronger standard. If a weaker mechanism was chosen for convenience, say so.

Output — lead with your strongest finding. For each:
  EXPLOIT [N]: <file>:<line>
  Attack: <how to exploit>
  Fix: <correct defense>
  Test: test_exploit_<name> — asserts <what blocks the attack>
End: PASS or BLOCK, finding count. If PASS, name attack classes attempted.

---

## Step 4 — Synthesize

After both passes complete:

1. **Deduplicate** by file:line — if both passes flag the same line, merge into one.
2. **Separate** EXPLOIT findings (adversary) from FIX findings (defense).
3. **Present summary:**

   Tier: T[1/2/3]
   Defense pass: PASS/BLOCK — [N] findings
   Adversary pass: PASS/BLOCK — [N] findings  (or: not run — T2/T3)

   CRITICAL (fix before commit):
   [EXPLOIT findings first, then high-severity FIX findings]

   STANDARD:
   [remaining FIX findings]

4. Ask: "Ready to fix? I can start on the critical findings."

## Cycle rule

After fixing findings: re-run the relevant pass on the delta. Only declare clean when
the pass returns PASS. Never commit while either pass shows BLOCK.
