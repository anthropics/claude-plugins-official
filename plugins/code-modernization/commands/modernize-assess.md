---
description: Full discovery & portfolio analysis of a legacy system — inventory, complexity, debt, effort estimation
argument-hint: <system-dir> | --portfolio <parent-dir>
---

**Mode select.** If `$ARGUMENTS` starts with `--portfolio`, run **Portfolio
mode** against the directory that follows. Otherwise run **Single-system
mode** against `legacy/$1`.

---

# Portfolio mode (`--portfolio <parent-dir>`)

Sweep every immediate subdirectory of the parent dir and produce a
heat-map a steering committee can use to sequence a multi-year program.

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

## Step P2 — COCOMO-II effort

Compute person-months per system using COCOMO-II basic:
`PM = 2.94 × (KSLOC)^1.10` (nominal scale factors). Show the formula and
inputs so the figure is defensible, not a guess.

## Step P3 — Documentation coverage

For each system, count source files with vs without a header comment
block, and list architecture docs present (`README`, `docs/`, ADRs).
Report coverage % and the top undocumented subsystems.

## Step P4 — Render the heat-map

Write `analysis/portfolio.html` (dark `#1e1e1e` bg, `#d4d4d4` text,
`#cc785c` accent, system-ui font, all CSS inline). One row per system;
columns: **System · Lang · KSLOC · Files · Mean CCN · Max CCN · Dep
Freshness · Doc Coverage % · COCOMO PM · Risk**. Color-grade the PM and
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
highest-complexity files. Capture the COCOMO effort/cost estimate scc provides.

If `scc` is not installed, fall back in order:
1. `cloc legacy/$1` for the LOC table, then compute COCOMO-II effort
   yourself: `PM = 2.94 × (KSLOC)^1.10` (nominal scale factors). Show the
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
   remediation value, each with file:line evidence."

3. **security-auditor** — "Scan legacy/$1 for security vulnerabilities:
   injection, auth weaknesses, hardcoded secrets, vulnerable dependencies,
   missing input validation. Return findings in CWE-tagged table form with
   file:line evidence and severity."

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

Create `analysis/$1/ASSESSMENT.md` with these sections:
- **Executive Summary** (3-4 sentences: what it is, how big, how risky, headline recommendation)
- **System Inventory** (the scc table + tech fingerprint)
- **Architecture-at-a-Glance** (the domain table; reference the diagram)
- **Production Runtime Profile** (the runtime table from Step 4 with the highest-variance domain called out — or "no telemetry available")
- **Technical Debt** (top 10, ranked)
- **Security Findings** (CWE table)
- **Documentation Gaps** (top 5)
- **Effort Estimation** (COCOMO-derived person-months, ±range, key cost drivers)
- **Recommended Modernization Pattern** (one of: Rehost / Replatform / Refactor / Rearchitect / Rebuild / Replace — with one-paragraph rationale)

Also create `analysis/$1/ARCHITECTURE.mmd` containing the Mermaid domain
dependency diagram from the legacy-analyst.

## Step 7 — Present

Tell the user the assessment is ready and suggest:
`glow -p analysis/$1/ASSESSMENT.md`
