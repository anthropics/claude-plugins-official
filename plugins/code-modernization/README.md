# Code Modernization Plugin

Point Claude at a legacy codebase — COBOL, legacy Java/C++/.NET, monolith web apps — and get back: an executive assessment, an interactive architecture map, the business rules mined out of the code, a steering-committee-ready modernization brief, and scaffolded or transformed new code with a behavior-equivalence test harness so you can prove nothing drifted.

It works by enforcing a sequence, because modernization usually fails when teams skip steps — transforming code before understanding it, or shipping without a harness to catch behavior drift:

```
preflight → assess → map → extract-rules → brief → (reimagine | transform | uplift) → harden
```

The discovery commands (`assess`, `map`, `extract-rules`) write artifacts to `analysis/<system>/`. `brief` synthesizes them into an approval gate. The three build commands write to `modernized/<system>/` and are three different *methods* — the brief recommends which one fits:

- **`transform`** — cross-stack rewrite from extracted intent (e.g. COBOL → Java).
- **`reimagine`** — greenfield rebuild on a new architecture.
- **`uplift`** — same-stack version bump (e.g. .NET Framework → .NET 8) that *preserves* the code and fixes only the version deltas.

![Interactive topology map of AWS CardDemo — domains as containers, modules sized by lines of code, dependency edges colored by kind, entry points ringed](assets/topology-viewer-screenshot.jpg)

## Install

```
/plugin install code-modernization@claude-plugins-official
```

## Quickstart

Each command takes a `<system-dir>` and assumes the code lives at `legacy/<system-dir>/`. Artifacts land in `analysis/<system-dir>/`; new code in `modernized/<system-dir>/`. If your code is elsewhere, symlink it: `mkdir -p legacy && ln -s /path/to/code legacy/billing`.

Try the first three on your own codebase — each produces a standalone artifact, so you can stop and review at any point:

```bash
/modernize-preflight billing      # is my environment ready?
/modernize-assess billing         # what am I dealing with?
/modernize-map billing            # show me the structure (opens an interactive map)
```

Then the full path:

```bash
/modernize-extract-rules billing                              # mine business rules → testable Rule Cards
/modernize-brief billing java-spring                          # the plan a steering committee approves (HITL gate)
/modernize-transform billing interest-calc java-spring        # …or reimagine, or uplift — see Commands
/modernize-harden billing                                     # security pass on the still-running legacy system
/modernize-status billing                                     # where am I, what's stale, what's next
```

## Commands

Run in order, but each is standalone — stop, review, resume.

- **`/modernize-preflight <system-dir> [target-stack]`** — Environment readiness check. Asks you the five questions the source can't answer (scope, whether you can build and test locally, bespoke build infrastructure, prior attempts, what's off limits), then detects the legacy stack, checks analysis tooling, reads the CI/build definition for how the system builds, smoke-tests the toolchain against the real code, inventories missing includes / deployment descriptors, and checks the **scope boundary** — whether `<system-dir>` is a slice of a larger repo and what outside it depends on it. Produces `PREFLIGHT.md` with a per-command Ready / Ready-with-gaps / Not-ready verdict.

- **`/modernize-assess <system-dir>`** *(or `--portfolio <parent-dir>`)* — Inventory: languages, complexity, tech debt, security posture, and a COCOMO complexity index ([see note](#a-note-on-cocomo)). Produces `ASSESSMENT.md` + `ARCHITECTURE.mmd`. With `--portfolio`, sweeps every subdirectory and writes a sequencing heat-map (`portfolio.html`).

- **`/modernize-map <system-dir>`** — Dependency and topology map: call graph, data lineage, entry points, and 2–4 business flows each traced for a persona (the claimant, the auditor). Produces `topology.json` and an **interactive zoomable `TOPOLOGY.html`** (circle-pack sized by LOC, edge toggles, search, and a persona-flow walkthrough), plus small `.mmd` diagrams for docs.

- **`/modernize-extract-rules <system-dir> [module-pattern]`** — Mine the business rules — calculations, validations, eligibility, state transitions — into Given/When/Then "Rule Cards" with `file:line` citations and confidence ratings. Produces `BUSINESS_RULES.md` + `DATA_OBJECTS.md`.

- **`/modernize-brief <system-dir> [target-stack]`** — Synthesize discovery into a phased **Modernization Brief**: target architecture, phase plan, persona walkthroughs, behavior contract, and an approval block. Reads the discovery artifacts and **stops if any are missing**. Enters plan mode as a human-in-the-loop approval gate. For a same-stack uplift it also requires the **delta catalog**, since an uplift's phase order is decided by its version deltas. The execution commands read the brief and treat each phase's entry criteria as gates, so editing the brief steers execution.

- **`/modernize-reimagine <system-dir> <target-vision>`** — Greenfield rebuild from extracted intent. Mines a spec, designs and adversarially reviews a target architecture, then scaffolds services with executable acceptance tests under `modernized/<system>-reimagined/`. Two human checkpoints.

- **`/modernize-transform <system-dir> <module> <target-stack>`** — Surgical single-module rewrite (strangler-fig: replace one piece while the legacy system keeps running). Plans first (approval gate), writes characterization tests, then an idiomatic implementation, and proves equivalence by running the tests. Produces `TRANSFORMATION_NOTES.md`.

- **`/modernize-uplift <system-dir> <source-version> <target-version> [project-pattern]`** — Same-stack version bump (e.g. `.NET Framework 4.8` → `.NET 8`, Spring Boot 2 → 3) — the common case `transform` gets wrong by rewriting. Preserves the code and makes the smallest diffs that compile and behave identically, driven by a **delta catalog** (the known breaking changes that *this* code actually hits) and the ecosystem's migration tooling. Equivalence is proven by running the test suite on both the old and new runtime where both can run here (otherwise it falls back to characterization tests, like `transform`). Migration is **pilot-first**: one representative project is migrated end-to-end in-session and its lessons written to a `PLAYBOOK.md` before anything else is touched; the rest then fan out, one agent per project, in **dependency-aware escalating batches behind a circuit breaker**. Produces `DELTA_CATALOG.md`, `BASELINE.md`, `PLAYBOOK.md` + `UPLIFT_NOTES.md`. If the catalog shows most of the code is forced to change, it tells you to use `transform` instead.

- **`/modernize-harden <system-dir>`** — Security pass on the **legacy** system: OWASP/CWE, dependency CVEs, secrets, injection. Produces `SECURITY_FINDINGS.md` (ranked) and a reviewed `security_remediation.patch`. **Never edits `legacy/`** — you review and apply the patch yourself. Useful while the legacy system keeps running in production during migration.

- **`/modernize-status <system-dir>`** — Read-only progress report: artifact inventory, staleness flags, secrets-hygiene checks, and the single most useful next command.

## Agents

Specialist subagents invoked by the commands (or directly):

- **`legacy-analyst`** — Reads legacy code (COBOL, EJB, classic ASP, …) and produces structural summaries; spots implicit dependencies and "JOBOL" (procedural code in modern syntax). *(assess, reimagine, uplift)*
- **`business-rules-extractor`** — Mines domain rules from procedural code with source citations. *(extract-rules, reimagine)*
- **`architecture-critic`** — Skeptical reviewer of target designs and transformed code; flags over-engineering. *(reimagine, transform, uplift)*
- **`security-auditor`** — Auth, input validation, secrets, dependency CVEs. *(assess, harden)*
- **`test-engineer`** — Characterization and equivalence tests that pin legacy behavior. *(transform, uplift)*
- **`version-delta-analyst`** — Finds the breaking changes between two versions of one stack that bite *this* codebase, and drives the ecosystem migration tool. *(uplift)*
- **`uplift-migrator`** — Migrates one project/module of an in-flight uplift by following the pilot's playbook, then runs that unit's real build to prove it; refuses to migrate anything if no playbook exists yet. Writes only inside its own unit's directory. *(uplift)*
- **`scaffolder`** — Builds one service of a reimagined system; writes only within its own `modernized/.../<service>/` directory. *(reimagine)*

## Recommended workspace setup

A `.claude/settings.json` in the project you're modernizing enforces the core invariant — never touch `legacy/`, freely edit `analysis/` and `modernized/`:

```json
{
  "permissions": {
    "allow": ["Read(**)", "Write(analysis/**)", "Write(modernized/**)", "Edit(analysis/**)", "Edit(modernized/**)"],
    "deny": ["Edit(legacy/**)", "Write(legacy/**)"]
  }
}
```

This guards the file tools; shell commands that mutate files (`sed -i`, `git apply`) still go through the normal Bash prompt, so review those with the same invariant in mind. That prompt is the containment for the two steps that fan out many write-capable agents at once — `/modernize-uplift` Step 5b and `/modernize-reimagine` Phase E — so keep Bash on a *prompted* permission mode for those.

## Prerequisites

Commands degrade gracefully, but these improve the output (run `/modernize-preflight` to check all at once):

- **Analysis tools** — [`scc`](https://github.com/boyter/scc) or [`cloc`](https://github.com/AlDanial/cloc); without them, metrics fall back to `find`/`wc`.
- **A build toolchain** for the legacy stack — enables the strongest equivalence proof (live dual execution). Not required: without it, equivalence falls back to recorded-trace tests and preflight reports Ready-with-gaps rather than blocking.
- **The whole system in the tree** — deployment descriptors (JCL, CICS, route configs), copybooks/includes, DDL. Entry-point detection and data lineage need them.

## Safety notes

**Analyzed code is untrusted input.** A hostile codebase can plant comments like "ignore previous instructions" or "mark this rule approved" to steer what lands in `BUSINESS_RULES.md` or `SECURITY_FINDINGS.md`, which later commands trust. Defenses: agents treat file content as data and flag instruction-shaped text; verification agents re-derive every rule and finding from the cited code, not from another agent's description; filesystem paths are validated; and `/modernize-brief` is a human approval gate before any code is generated. Treat discovery artifacts from untrusted code with the same skepticism as the code itself.

**Secrets stay out of shared artifacts.** Discovered credentials are masked (`AKIA****`) and inventoried in a gitignored `SECRETS.local.md` (or `~/.modernize/<system>/` on non-git projects); `/modernize-harden` keeps credential-removal hunks in a separate gitignored patch. Pass `--show-secrets` to include raw values in the quarantine file only. If you ran an early version of this plugin on a real system, check whether `analysis/` artifacts were committed and rotate anything exposed.

### A note on COCOMO

`assess` derives a COCOMO figure from code size and uses it **only as a relative complexity/scale index** to rank and sequence systems — never as a timeline or cost. COCOMO's constants encode human-team productivity, which agentic transformation doesn't follow, so any duration derived from it would be wrong.

## Dynamic workflow orchestration

On Claude Code builds with the Workflow tool, five commands (`extract-rules`, `harden`, `assess --portfolio`, `reimagine`, `uplift`) run as scripted multi-agent orchestrations that fan out more agents for deeper coverage — looping until findings stabilize, and adversarially verifying each finding before it's written. `uplift`'s migration fan-out runs in dependency-aware escalating batches behind a per-batch **circuit breaker**, so a playbook that stops working is caught within a handful of agents and the spend stops until it is revised. They fall back to direct subagent fan-out on older builds automatically; no configuration needed. Invoking the slash command is the opt-in.

## License

Apache 2.0. See `LICENSE`.
