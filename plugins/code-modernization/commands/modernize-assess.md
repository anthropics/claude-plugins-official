---
description: What am I dealing with? Inventory, complexity, debt, security and a recommended modernization pattern
argument-hint: <system> [--show-secrets] | --portfolio <parent-dir>
arguments: system
---

**Mode.** If `$ARGUMENTS` starts with `--portfolio`, run **Portfolio mode** on the
directory that follows. Otherwise run **Single-system mode** on `$system`, the
first token. Flags go after it (`<system> --show-secrets`): a flag in first place
would be read as the system name.

The code is `legacy/$system`, often a symlink to where it really lives: say where it points (`readlink legacy/$system`) in one line before you start. If `legacy/$system` does not exist, stop and say so: nothing can run without the code, so the fix is `/code-modernization:modernize $system --source <path to the code>`. Run every subagent in the foreground and wait for its result: never end your turn while one is still running.

---

# Portfolio mode (`--portfolio <parent-dir>`)

Sweep every immediate subdirectory and produce a heat-map a steering committee
can use to sequence a multi-year program.

If the **Workflow tool** is available (this command is your authorization),
list the subdirectories first (`ls -d <parent-dir>/*/ | xargs -n1 basename`; the
script has no filesystem access), tell the user the count (30 systems means 30
agents), then run one survey agent per system:

Call it by name (the plugin registers it). If the tool does not know the name, pass `scriptPath: "${CLAUDE_PLUGIN_ROOT}/workflows/portfolio-assess.js"` instead:

```
Workflow({
  name: "code-modernization:modernize-portfolio-assess",
  args: { parentDir: "<parent-dir>", systems: ["<sub1>", "<sub2>", ...] }
})
```

Each agent returns a metrics row and the workflow computes the COCOMO index in
code, so every row uses the same formula. If the session dies mid-sweep,
relaunch with `resumeFromRunId` and finished systems return from cache. Without
the Workflow tool, gather the same row per system yourself.

Per system: SLOC and dominant language (`cloc --csv`, else `scc`, else `find` +
`wc -l`), file count, complexity measured one way for every system (`scc`'s per-file
complexity summed, divided by KSLOC, and the most complex single file; without `scc`,
count decision keywords the same way everywhere), dependency freshness (age or pinned-version count of the
manifest), documentation coverage (source files whose opening comment
describes the file, not just a license, and architecture docs present), and the COCOMO index `2.94 × KSLOC^1.10`. **The
index is a relative size measure for ranking systems, never a timeline or a cost**
(it assumes human-team productivity): label the column "index", never print
person-months, a date or a duration.

Write `analysis/portfolio.html` (dark `#1e1e1e` background, `#d4d4d4` text,
`#cc785c` accent, system-ui, CSS inline): one row per system, columns **System ·
Lang · KSLOC · Files · Complexity per KSLOC · Most complex file · Dep Freshness · Doc
Coverage % · Complexity index · Risk**, index and Risk cells graded green to red, and a
2–3 sentence recommendation of which system goes first and why. Tell the user to
open it, then stop.

---

# Single-system mode

Assess `legacy/$system` so a VP of Engineering could take a fact-grounded brief into a
budget meeting.

## Step 1 — Inventory

Run `scc legacy/$system` and `scc --by-file -s complexity legacy/$system | head -25` (the most
complex files). Use scc's COCOMO figure **only as a relative scale index** and
ignore its "Estimated Schedule Effort" and dollar lines: they project a
human-team timeline and budget, which are invalid for agentic modernization.

Without `scc`, use `cloc legacy/$system`, then compute the index yourself
(`2.94 × KSLOC^1.10`); without that, `find` + `wc -l` by extension and rank
complexity by decision keywords (`IF`/`EVALUATE`/`PERFORM` for COBOL,
`if`/`for`/`while`/`case`/`catch` for C-family). Say which tool you used.

## Step 2 — Technology fingerprint

With file evidence: languages, frameworks and runtime versions; build system and
manifest locations; data stores (schemas, copybooks, DDL, ORM configs);
integration points (queues, APIs, batch interfaces, screen maps); test presence
and rough coverage signal.

## Step 3 — Deep analysis (three subagents, in parallel)

1. **legacy-analyst** — "Build a structural map of legacy/$system: the 5–12 major
   functional domains (group optional subsystems under one umbrella), which
   files belong to each, and how they depend on each other (control flow and
   shared data). Return a markdown table and a Mermaid `graph TD` of the
   domains, clustered with `subgraph`, at most ~40 edges. Cite repo-relative
   paths. Flag dangling references."
2. **legacy-analyst** — "Identify technical debt in legacy/$system: dead code,
   deprecated APIs, duplication, god objects, missing error handling, hardcoded
   config. Return the top 10 by remediation value, each with file:line. Mask any
   credential value per your secret-handling rules."
3. **security-auditor** — "Scan legacy/$system for vulnerabilities: injection, auth
   weaknesses, hardcoded secrets, vulnerable dependencies, missing input
   validation. Return a CWE-tagged table with file:line and severity. Mask every
   credential (file:line plus a 2–4 character preview, never the value)."

Wait for all three and synthesize.

## Step 4 — Production runtime overlay (optional)

If telemetry exists (an APM MCP server, batch logs, runtime exports the user can
supply), gather p50/p95/p99 for the key jobs or routes, tag each domain with its
wall-clock cost and p99/p50 variance, and call out the highest-variance domain as
the operational risk. Include a small Runtime Profile table. If none exists, say
so in the assessment and move on.

## Step 5 — Documentation gaps

Compare what the code *does* with what README, docs and comments *say*: list the
top 5 behaviors or subsystems a new engineer would need explained.

## Step 6 — Write the assessment

**Secrets first.** The assessment gets shared and committed, so discovered
credential values never appear in it. If credentials were found:

1. Ensure `analysis/.gitignore` contains `SECRETS.local.md` and `*.local.patch`
   (create or append). In a git repo, verify with
   `git check-ignore -q analysis/$system/SECRETS.local.md` before writing any
   finding. With no git repo (check for `.svn`, `.hg`, `CVS` too: a `.gitignore`
   protects nothing under another VCS), refuse `--show-secrets` and write
   `SECRETS.local.md` to `~/.modernize/$system/`, telling the user where and why.
2. Write `SECRETS.local.md`: per credential a masked preview, `file:line`, type,
   what it grants, production or test guess, rotation advice. Only with
   `--show-secrets`, add a raw-value column, in this file alone.
3. Masking applies to every section of `ASSESSMENT.md`, whichever agent produced
   the finding (Technical Debt quotes hardcoded config too). Security Findings
   points to "Credential inventory in SECRETS.local.md (gitignored; not for sharing)".

Write `analysis/$system/ASSESSMENT.md` with: **Executive Summary** (3–4 sentences:
what it is, how big, how risky, the headline recommendation) · **System
Inventory** · **Architecture at a Glance** (domain table, refer to the diagram) ·
**Production Runtime Profile** (or "no telemetry available") · **Technical Debt**
(top 10) · **Security Findings** (CWE table) · **Documentation Gaps** (top 5) ·
**Relative Scale** (the index and KSLOC for ranking against other systems; state
plainly that it is not a timeline or a cost, and print no person-months, schedule,
cost or date) · **Recommended Modernization Pattern**: one of Rehost, Replatform,
Refactor, Rearchitect, Rebuild, Replace, with a one-paragraph rationale and the
command it routes to: a move to a newer version of the same technology (or its
supporting platform) → `uplift`; a rewrite in another technology, piece by piece →
`transform`; a rebuild on a new architecture → `reimagine`. Rehost (move as is) and
Replace (buy or adopt a product) change no code, so no build command applies: say so,
and say what the analysis is still good for. For Rehost, `map`, `harden` and the `preflight`
build check show what the move must carry along; for Replace, `extract-rules` turns
what the system does into the acceptance criteria a replacement is judged against.

Also write `analysis/$system/ARCHITECTURE.mmd`, the domain diagram from the
legacy-analyst.

## Step 7 — Finish

Refresh the report: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/build_report.py" $system`
(a convenience: if it fails or `python3` is missing, say so in one line and carry on). Tell the user the assessment is ready
(`analysis/$system/ASSESSMENT.md`, and the report at `analysis/$system/REPORT.html`) and
that the next step is `/code-modernization:modernize-map $system`.
