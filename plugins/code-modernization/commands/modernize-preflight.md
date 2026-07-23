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

## Check 0 — Ask the human (these answers are not in the source)

Before any automated check, ask the person running this command the five
questions below. The most expensive modernization mistakes are things a
person who knows the system answers in seconds and that cost real money to
discover wrong from the source alone. Ask **only** these — add none —
and accept "don't know" for any of them.

**Ask, then do not block on the answers.** None of Checks 1–6 needs one
(Check 6 verifies the scope boundary from the source *independently* — the
human's answer says whether a crossing *matters*, not whether it exists), so
proceed to the checks immediately after asking and write the report with
whatever answers exist by then. Any question still unanswered goes in the
report **verbatim, marked as an open item the human must fill in** — it is
not dropped. This way an interactive user answers while the checks run, a
headless or scripted run still produces a complete `PREFLIGHT.md`, and the
one thing that never happens is a readiness report silently missing the
questions.

1. **Scope** — Is `legacy/$1` the complete system, or one slice of a
   larger codebase? If a slice: what *outside* it depends on code *inside*
   it, and is breaking those consumers acceptable? (Check 6 verifies this
   from the source independently; the human's answer says whether it
   *matters*.)
2. **Build & test locally** — Can this environment restore, build, and run
   the tests? Roughly how long does the full CI pipeline take? (A pipeline
   measured in hours changes the whole validation strategy: you cannot
   afford to first learn you were wrong from CI.)
3. **Bespoke build infrastructure** — Is there organization-specific build
   or dependency-resolution machinery (an internal package feed, a custom
   binary store, a code generator, a wrapper around the standard build
   tool) that someone new to this codebase would not guess? Where is it
   documented?
4. **Prior attempts** — Has anyone tried to modernize any of this before?
   What went wrong?
5. **Off limits** — Is anything under `legacy/$1` not allowed to change in
   this pass (a component another team owns, a frozen branch, generated
   code)?

Record every answer **verbatim** in the report — downstream commands, and
`/modernize-brief` most of all, read them from there. Do not paraphrase
away a caveat the human gave you.

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

## Check 3 — Build toolchain (prove it on THIS codebase, not just presence)

**3a — The build definition is the ground truth. Find it and read it
before guessing.** Something already builds this system; go find out how.
Look for the CI/pipeline definition (`azure-pipelines.yml`, `Jenkinsfile`,
`.github/workflows/`, `.gitlab-ci.yml`, `bitbucket-pipelines.yml`, build
JCL procs, a `Makefile`) and any organization-level build configuration
above or beside the source (`Directory.Build.props`/`.targets` and
`nuget.config` in .NET; a parent POM, a `settings.xml` mirror, or a
`.mvn/` directory in Java; a private-registry `.npmrc`/`pip.conf`; a root
`build/`, `eng/`, `tools/`, or `scripts/` directory). These files are the
single most honest document about how the system *actually* builds: the
exact toolchain version it pins, where dependency binaries really come
from, and which steps a naive build invocation skips. Every mid-migration
"wait, how do dependencies resolve here?" surprise is already written down
in one of them. Report what you found (or that none exists), quote the
pinned toolchain version and the dependency source, and flag anything
bespoke — a homegrown binary-resolution scheme is exactly the thing a
transformation must not have to discover halfway through.

**3b — Smoke test, escalating.** Identify the compiler/interpreter for the
detected legacy stack — e.g. GnuCOBOL (`cobc`) for COBOL, a JDK +
Maven/Gradle for Java, `cc`/`make` for C, `dotnet` for .NET — then **prove
it works on this codebase**, at the strongest level available:

- **Level 1 (any stack) — syntax-compile one representative source file**
  (`cobc -fsyntax-only`, `javac`, `gcc -fsyntax-only`, …). This catches
  missing copybooks/includes, dialect flags, fixed-vs-free format.
- **Level 2 (any stack with a build system) — restore + build ONE whole
  project/module the way 3a says the CI does.** A single file
  syntax-compiling proves almost nothing about a real build system: a
  restore that hits a private feed, a code-generation step, a shared props
  file, a pinned SDK are all invisible to a one-file compile — and are
  exactly where large codebases hide their surprises. Pick one small
  *real* unit and take it all the way through.

A failed smoke test at either level is the most valuable output of this
whole command — report the actual error and diagnose it: missing
copybook/include path, missing dialect flag (`-std=ibm` etc.), fixed vs
free format, a dependency the standard feed cannot resolve. These are the
errors that otherwise surface mid-transformation with far less context.
Level 2 being *impossible* (no build system in the tree, a mainframe stack
with no local runtime) is normal for some legacy code: report it as a
fact, not a failure — equivalence then degrades to recorded traces, which
the other commands already handle.

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

## Check 6 — Scope boundary (is `$1` the whole world, or a slice of one?)

Every downstream command assumes `legacy/$1` *is* the system. When it is
actually **one directory inside a larger source repository** — a module in
a monorepo, one solution folder inside a much bigger solution, a subsystem
sharing copybooks or includes with siblings — that assumption is the most
dangerous thing in the whole run, and nothing else checks it.

Detect it: after resolving the `legacy/$1` symlink (the recommended setup
symlinks real code in), is there a repository / solution / workspace /
reactor root *above* it? Do manifests or includes *inside* `$1` reference
paths *outside* it? If either is true, report **both directions** of the
boundary crossing:

- **Outbound** — things inside `$1` that depend on source *outside* it
  (project/module references, shared includes, a parent build file). The
  `/modernize-map` topology and any delta catalog only see what is under
  `$1`, so every outbound reference is a dependency they will silently
  miss. List them.
- **Inbound** — things *outside* `$1` that depend on things *inside* it.
  This is the **blast radius**: an in-place migration (`/modernize-uplift`)
  of a node with external consumers breaks every one of them. Grep the
  sibling manifests for references into `$1`, enumerate the
  inbound-referenced nodes, and say plainly that each needs an explicit
  decision *before* any in-place change — keep it buildable for both old
  and new consumers during the transition, expand the scope to include the
  consumers, or accept and schedule the break. Never let this be
  discovered by a broken build in a directory nobody was looking at.

If `$1` really is a standalone repository, one line saying so is the whole
check — it is cheap when it does not apply.

## Report

Write `analysis/$1/PREFLIGHT.md`. It **leads with the Check 0 answers,
verbatim, and the Check 6 scope-boundary finding** — those two are read by
every downstream command (`/modernize-brief` above all) and are worth
nothing paraphrased. Then a status table — one row per check, status
✅ / ⚠️ / ❌, what was found, and the fix for anything not green — followed
by a **Ready / Ready-with-gaps / Not ready** verdict per command:

- `assess` + `map` + `extract-rules` — need Checks 1–2 green-ish and
  Check 4's missing-include count low
- `brief` — needs only the three discovery artifacts (plus
  `DELTA_CATALOG.md` when the plan is a same-stack uplift); no tooling
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
  Claude-derived and loses the tool's coverage; note that. (c) Did Check 6
  find **inbound external consumers** of `$1`? That is **Ready-with-gaps**,
  not Not-ready — preflight runs before any plan exists, so there is nowhere
  yet to record a decision — but it is the gap that matters most: name the
  inbound-referenced shared nodes and say that `/modernize-brief` must give
  each one an explicit transition decision as its own line item (Check 6
  lists the options), and that `/modernize-uplift` Step 1 will not migrate a
  shared node in place without one. Never let this be discovered from a
  sibling's broken build.

Print the table in the session too, and end with the single most
important fix if anything is red.
