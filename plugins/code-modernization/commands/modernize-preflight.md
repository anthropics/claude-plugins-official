---
description: Environment readiness check — analysis tools, build toolchain, source completeness, telemetry access
argument-hint: <system-dir> [target-stack]
---

Check whether this environment is ready to analyze — and eventually
transform — `legacy/$1`, and tell the user exactly what to fix before the
other commands run into it. Modernization sessions fail late and
confusingly when this isn't done: assessment metrics silently degrade
without analysis tools, characterization tests can't run without a build
toolchain, and dependency maps come out wrong when half the source isn't
in the tree.

Run every check even when an early one fails — the point is one complete
readiness report, not the first error.

## Check 1 — Detect the stack

Fingerprint `legacy/$1` from file extensions and manifests: languages,
build system, deployment/config descriptors. This drives which checks
below apply. Report what was detected and the rough file split.

## Check 2 — Analysis tooling

For each, check availability (`command -v`) and report version, what it's
used for, and what degrades without it:

| Tool | Used by | Without it |
|---|---|---|
| `scc` (or `cloc`) | assess | LOC/complexity fall back to `find`+`wc`; the COCOMO complexity index gets coarser |
| `lizard` | assess --portfolio | complexity estimated from decision-keyword counts |
| `glow` | all | markdown artifacts render as plain text |
| `delta` | transform | side-by-side diffs fall back to `diff -y` |

Include the platform's install one-liner for anything missing
(`brew install scc`, `apt install cloc`, `pip install lizard`, …).

## Check 3 — Build toolchain (smoke test, not just presence)

Identify the compiler/interpreter for the detected legacy stack — e.g.
GnuCOBOL (`cobc`) for COBOL, JDK + Maven/Gradle for Java, `cc`/`make` for
C, `dotnet` for .NET. Then **prove it works on this codebase**: pick one
representative source file and run a syntax-only compile
(`cobc -fsyntax-only`, `javac`, `gcc -fsyntax-only`, …).

A failed smoke test is the most valuable output of this command — report
the actual error and diagnose it: missing copybook/include path, missing
dialect flag (`-std=ibm` etc.), fixed vs free format, missing dependency
jar. These are the errors that otherwise surface mid-`/modernize-transform`
with much less context.

If the user passed a `[target-stack]`, do the same for it: runtime,
package manager, test framework (`mvn -v`, `npm -v`, `pytest --version`, …).

## Check 4 — Source completeness

The dependency map is only as good as what's in the tree. Check for the
detected stack's equivalents of:

- **Referenced-but-missing includes** — copybooks (`COPY X` with no
  `X.cpy`), headers, imports that resolve nowhere. Count and list the top
  missing names.
- **Deployment/config descriptors** — JCL for batch COBOL, CICS CSD
  definitions, `web.xml`/route configs, cron/scheduler definitions.
  Without these, entry-point detection and the code↔storage join in
  `/modernize-map` are guesswork.
- **Data definitions** — DDL, schemas, copybook record layouts, ORM
  mappings.
- **Binary-only artifacts** — load modules, jars, DLLs with no matching
  source. These become unmappable black boxes; flag them now.

## Check 5 — Optional context

- **Production telemetry** — is an observability/APM MCP server connected,
  or are batch job logs / runtime exports available? (Enables the runtime
  overlay in `/modernize-assess` Step 4 and timing annotations in
  `/modernize-map`.)
- **Version control history** — is `legacy/$1` under git with meaningful
  history? (Change-frequency data sharpens risk ranking.)

## Report

Write `analysis/$1/PREFLIGHT.md`: a status table — one row per check,
status ✅ / ⚠️ / ❌, what was found, and the fix for anything not green —
followed by a **Ready / Ready-with-gaps / Not ready** verdict per command:

- `assess` + `map` + `extract-rules` — need Checks 1–2 green-ish and
  Check 4's missing-include count low
- `brief` — needs only the three discovery artifacts; no tooling
- `transform` + `reimagine` — additionally need Check 3 green for the
  **target** stack. A red legacy toolchain downgrades these to
  Ready-with-gaps, not Not-ready: equivalence testing falls back to
  recorded traces / golden-master fixtures instead of dual execution
  (common and expected for CICS/IMS code that has no local runtime)
- `harden` — needs Check 2 plus any stack-specific SAST tooling found
- `uplift` (same-stack version bump) — needs Check 3 green for the **target**
  version. Two uplift-specific signals to report when a `[target-stack]` that
  looks like a version bump was passed: (a) is the **source** runtime also
  available here? Both present = a true dual-run is possible; target-only =
  equivalence degrades to characterization tests against recorded outputs (say
  which). (b) Is the stack's **migration tool** installed (`dotnet tool list`
  for `upgrade-assistant`, `apiport`, OpenRewrite, `pyupgrade`, `ng`)? Missing
  is Ready-with-gaps, not Not-ready — the delta catalog is then fully
  Claude-derived and loses the tool's coverage; note that.

Print the table in the session too, and end with the single most
important fix if anything is red.
