---
description: Full discovery & portfolio analysis of a legacy system — inventory, complexity, debt, relative scale
argument-hint: <system-dir> [--show-secrets] | --portfolio <parent-dir>
---

**Mode select.** If `$ARGUMENTS` starts with `--portfolio`, run **Portfolio
mode** against the directory that follows. Otherwise run **Single-system
mode** against the system dir. Parse flags positionally-independently:
`--show-secrets` may appear before or after the system dir — the system
dir is the first non-flag token.

---

# Portfolio mode (`--portfolio <parent-dir>`)

Sweep every immediate subdirectory of the parent dir and produce a
heat-map a steering committee can use to sequence a multi-year program.

**Preferred — Workflow orchestration.** If the **Workflow tool** is available
in this session (this command invocation is your authorization), enumerate
the immediate subdirectories first — the workflow script has no filesystem
access — then launch one survey agent per system, all independent:

```bash
ls -d <parent-dir>/*/ | xargs -n1 basename   # bare subdir names, not paths
```

```
Workflow({
  scriptPath: "${CLAUDE_PLUGIN_ROOT}/workflows/portfolio-assess.js",
  args: { parentDir: "<parent-dir>", systems: ["<sub1>", "<sub2>", ...] }
})
```

This is one agent per system (a 30-system estate = 30 agents — tell the user
the count before launching; the runtime queues them against its concurrency
cap). Each agent returns a structured metrics row and the workflow computes
COCOMO-II uniformly in code, so every row uses the identical formula. On
return, render `rows` (plus an "unmeasured" marker row for anything in
`unmeasured`) into the Step P4 heat-map, add the sequencing recommendation
yourself, and skip Steps P1–P3. For very long sweeps, note the workflow's
`runId` — if the session dies mid-sweep, relaunch with `resumeFromRunId` and
completed systems return instantly from cache.

**Fallback** (no Workflow tool): run Steps P1–P3 per system yourself, then P4.

## Step P1 — Per-system metrics

For each subdirectory `<sys>`:

```bash
cloc --quiet --csv <parent>/<sys>          # LOC by language
lizard -s cyclomatic_complexity <parent>/<sys> 2>/dev/null | tail -1
```

If `cloc`/`lizard` are not installed, fall back to `scc <parent>/<sys>`
(LOC + complexity) or `find` + `wc -l` grouped by extension, and estimate
complexity by counting decision keywords per file. Note which tool you used.

Capture: total SLOC, dominant language, file count, mean & max
cyclomatic complexity (CCN). For dependency freshness, locate the
manifest (`package.json`, `pom.xml`, `*.csproj`, `requirements*.txt`,
copybook dir) and note its age / pinned-version count.

## Step P2 — COCOMO-II complexity index

Compute the COCOMO-II basic figure per system: `2.94 × (KSLOC)^1.10`
(nominal scale factors). Show the formula and inputs so it is defensible,
not a guess.

**Use this only as a relative complexity/scale index** for ranking and
sequencing systems — bigger number = bigger, more complex estate. **It is
not a modernization timeline or cost.** The COCOMO person-month figure
assumes traditional human-team productivity; agentic transformation does
not follow those productivity curves, so do not present it (or convert it)
as how long the work will take or what it will cost. Label the column as an
index, not "person-months", and never attach a date or duration to it.

## Step P3 — Documentation coverage

For each system, count source files with vs without a header comment
block, and list architecture docs present (`README`, `docs/`, ADRs).
Report coverage % and the top undocumented subsystems.

## Step P4 — Render the heat-map

Write `analysis/portfolio.html` (dark `#1e1e1e` bg, `#d4d4d4` text,
`#cc785c` accent, system-ui font, all CSS inline). One row per system;
columns: **System · Lang · KSLOC · Files · Mean CCN · Max CCN · Dep
Freshness · Doc Coverage % · Complexity (COCOMO index) · Risk**. Color-grade the index and
Risk cells (green→amber→red). Below the table, a 2-3 sentence
sequencing recommendation: which system first and why.

Then stop. Tell the user to open `analysis/portfolio.html`.

---

# Single-system mode

Perform a complete **modernization assessment** of `legacy/$1`.

This is the discovery phase — the goal is a fact-grounded executive brief that
a VP of Engineering could take into a budget meeting. Work in this order:

## Step 1 — Quantitative inventory

Run and show the output of:
```bash
scc legacy/$1
```
Then run `scc --by-file -s complexity legacy/$1 | head -25` to identify the
highest-complexity files. Capture scc's COCOMO figure **only as a relative
complexity/scale index** — and **ignore scc's "Estimated Schedule Effort"
and cost-in-dollars lines**: those project a human-team timeline and budget,
which are invalid for agentic modernization (see the not-a-timeline note in
Step 6).

If `scc` is not installed, fall back in order:
1. `cloc legacy/$1` for the LOC table, then compute the COCOMO-II index
   yourself: `2.94 × (KSLOC)^1.10` (nominal scale factors). Show the
   inputs.
2. If `cloc` is also missing, use `find` + `wc -l` grouped by extension
   for LOC, and rank file complexity by counting decision keywords
   (`IF`/`EVALUATE`/`WHEN`/`PERFORM` for COBOL; `if`/`for`/`while`/`case`/
   `catch` for C-family). Compute COCOMO from KSLOC as above.

Note in the assessment which tool was used so the figures are reproducible.

## Step 2 — Technology fingerprint

Identify, with file evidence:
- Languages, frameworks, and runtime versions in use
- Build system and dependency manifest locations
- Data stores (schemas, copybooks, DDL, ORM configs)
- Integration points (queues, APIs, batch interfaces, screen maps)
- Test presence and approximate coverage signal

## Step 3 — Parallel deep analysis

Spawn three subagents **in parallel**:

1. **legacy-analyst** — "Build a structural map of legacy/$1: what are the
   5-12 major functional domains (group optional/feature-gated subsystems
   under one umbrella), which source files belong to each, and how do they
   depend on each other (control flow + shared data)? Return a markdown
   table + a Mermaid `graph TD` of domain-level dependencies — use
   `subgraph` to cluster and cap at ~40 edges. Cite repo-relative file
   paths. Flag dangling references (defined but no source, or unused)."

2. **legacy-analyst** — "Identify technical debt in legacy/$1: dead code,
   deprecated APIs, copy-paste duplication, god objects/programs, missing
   error handling, hardcoded config. Return the top 10 findings ranked by
   remediation value, each with file:line evidence. If evidence contains a
   credential value, mask it per your secret-handling rules — never quote
   it."

3. **security-auditor** — "Scan legacy/$1 for security vulnerabilities:
   injection, auth weaknesses, hardcoded secrets, vulnerable dependencies,
   missing input validation. Return findings in CWE-tagged table form with
   file:line evidence and severity. Mask every discovered credential value
   per your secret-handling rules — file:line plus a 2–4 character masked
   preview, never the value itself."

Wait for all three. Synthesize their findings.

## Step 4 — Production runtime overlay (optional)

If production telemetry is available — an observability/APM MCP server, batch
job logs, or runtime exports the user can supply — gather p50/p95/p99
wall-clock for the system's key jobs/transactions (e.g. JCL members under
`legacy/$1/jcl/`, scheduled batches, top API routes). Use it to:

- Tag each functional domain from Step 3 with its production wall-clock
  cost and **p99 variance** (p99/p50 ratio).
- Flag the highest-variance domain as the highest operational risk —
  this is telemetry-grounded, not a static-analysis opinion.

Include a small **Runtime Profile** table (Job/Route · Domain · p50 · p95 ·
p99 · p99/p50) in the assessment. If no telemetry is available, skip this
step and note the gap in the assessment.

## Step 5 — Documentation gap analysis

Compare what the code *does* against what README/docs/comments *say*. List
the top 5 undocumented behaviors or subsystems that a new engineer would
need explained.

## Step 6 — Write the assessment

**Secrets quarantine first.** The assessment gets shared and committed —
discovered credential values must never appear in it. If the
security-auditor found any hardcoded credentials:

1. Ensure `analysis/.gitignore` exists and contains the lines
   `SECRETS.local.md` and `*.local.patch` (create or append as needed —
   the patch pattern is used by `/modernize-harden`; writing both now
   means the ignore set is complete from first contact). If the project is a
   git repo, verify with `git check-ignore -q analysis/$1/SECRETS.local.md`
   — do not write any findings until the check passes. If there is **no
   git repo** (check for `.svn`/`.hg`/`CVS` too — a `.gitignore` protects
   nothing under another VCS): refuse `--show-secrets` and write
   `SECRETS.local.md` to `~/.modernize/$1/` instead of the project tree,
   telling the user where it went and why.
2. Write `SECRETS.local.md`: one row per credential — masked preview,
   `file:line`, credential type, what it grants access to,
   production/test guess, rotation recommendation. Only if the user passed
   `--show-secrets`, add the raw value column here — this file only, never
   ASSESSMENT.md.
3. Masking applies to **every section of ASSESSMENT.md**, whichever agent
   produced the finding — the Technical Debt section quotes hardcoded
   config; those quotes follow the same masking rule as Security Findings.
   The Security Findings section adds a one-line pointer:
   "Credential inventory in SECRETS.local.md (gitignored; not for sharing)."

Create `analysis/$1/ASSESSMENT.md` with these sections:
- **Executive Summary** (3-4 sentences: what it is, how big, how risky, headline recommendation)
- **System Inventory** (the scc table + tech fingerprint)
- **Architecture-at-a-Glance** (the domain table; reference the diagram)
- **Production Runtime Profile** (the runtime table from Step 4 with the highest-variance domain called out — or "no telemetry available")
- **Technical Debt** (top 10, ranked)
- **Security Findings** (CWE table)
- **Documentation Gaps** (top 5)
- **Relative Scale** (the COCOMO-II index + KSLOC as a complexity/scale signal for ranking this system against others. **Not a timeline:** state plainly that this is a relative size measure, not an estimate of how long modernization will take or what it will cost — it assumes traditional human-team productivity, which agentic transformation does not follow. Do not print person-months, a schedule, a cost, or a date.)
- **Recommended Modernization Pattern** (one of: Rehost / Replatform / Refactor / Rearchitect / Rebuild / Replace — with one-paragraph rationale, and the command it routes to: **Replatform / Refactor-in-place same-stack version bump → `/modernize-uplift`**; Rearchitect/cross-stack → `/modernize-transform`; Rebuild → `/modernize-reimagine`)

Also create `analysis/$1/ARCHITECTURE.mmd` containing the Mermaid domain
dependency diagram from the legacy-analyst.

## Step 7 — Present

Tell the user the assessment is ready and suggest:
`glow -p analysis/$1/ASSESSMENT.md`
