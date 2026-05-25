---
description: Dependency & topology mapping — call graphs, data lineage, batch flows, rendered as navigable diagrams
argument-hint: <system-dir>
---

Build a **dependency and topology map** of `legacy/$1` and render it visually.

The assessment gave us domains. Now go one level deeper: how do the *pieces*
connect? This is the map an engineer needs before touching anything.

## What to produce

Write a one-off analysis script (Python or shell — your choice) that parses
the source under `legacy/$1` and extracts the four datasets below. Three
principles apply across stacks; getting them wrong produces a misleading map:

1. **Edges live in two places** — direct calls in source, *and* dispatcher/
   router calls whose targets are variables (config tables, route maps,
   dependency injection, dynamic dispatch). Resolve variables against config
   before declaring an edge unresolvable.
2. **The code↔storage join is usually external configuration**, not source —
   job/deployment descriptors map logical names to physical stores.
3. **Entry points usually live in deployment config**, not source — without
   parsing it, every top-level module looks unreachable.

Extract:

- **Program/module call graph** — direct calls (`CALL`, method invocations,
  `import`/`require`) *and* dispatcher calls (`EXEC CICS LINK/XCTL`, DI
  container wiring, framework routing, reflection/factory). Resolve variable
  call targets against route tables, copybooks, config, or constant pools.
- **Data dependency graph** — which modules read/write which data stores,
  joined through the relevant config: `SELECT…ASSIGN TO` ↔ JCL `DD` (batch
  COBOL), `EXEC CICS READ/WRITE…FILE()` ↔ CSD `DEFINE FILE` (CICS online),
  `EXEC SQL` table refs (embedded SQL), ORM annotations/mappings (Java/.NET),
  model files (Node/Python/Ruby). Include UI/screen bindings (BMS maps, JSPs,
  templates) — they're dependencies too.
- **Entry points** — whatever the stack's outermost invoker is, read from
  where it's defined: JCL `EXEC PGM=` and CICS CSD `DEFINE TRANSACTION`
  (mainframe), `web.xml`/route annotations/route files (web), `main()`/argv
  parsing (CLI), queue/scheduler subscriptions (event-driven).
- **Dead-end candidates** — modules with no inbound edges. **Only meaningful
  once all the entry-point and call-edge types above are in the graph.**
  Suppress the dead claim for anything that could be the target of an
  unresolved dynamic call. A grep-only graph will mark most dispatcher-driven
  modules (CICS programs, Spring controllers, ORM-bound DAOs) dead when they
  aren't.

If the source is fixed-column (COBOL columns 8–72, RPG, etc.), slice the
code area and strip comment lines before regex matching, or you'll match
sequence numbers and commented-out code.

Save the script as `analysis/$1/extract_topology.py` (or `.sh`) so it can be
re-run and audited. Have it write a machine-readable
`analysis/$1/topology.json` and print a human summary. Run it; show the
summary (cap at ~200 lines for very large estates).

## Render

From the extracted data, generate **three Mermaid diagrams** and write them
to `analysis/$1/TOPOLOGY.html` as a self-contained page that renders in any
browser.

The HTML page must use: dark `#1e1e1e` background, `#d4d4d4` text,
`#cc785c` for `<h2>`/accents, `system-ui` font, all CSS **inline** (no
external stylesheets). Load Mermaid from a CDN in `<head>`:

```html
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
  mermaid.initialize({ startOnLoad: true, theme: 'dark' });
</script>
```

Each diagram goes in a `<pre class="mermaid">...</pre>` block. Do **not**
wrap diagrams in markdown ` ``` ` fences inside the HTML.

1. **`graph TD` — Module call graph.** Cluster by domain (use `subgraph`).
   Highlight entry points in a distinct style. Cap at ~40 nodes — if larger,
   show domain-level with one expanded domain.

2. **`graph LR` — Data lineage.** Programs → data stores.
   Mark read vs write edges.

3. **`flowchart TD` — Critical path.** Trace ONE end-to-end business flow
   (e.g., "monthly billing run" or "process payment") through every program
   and data store it touches, in execution order. If production telemetry is
   available (see `/modernize-assess` Step 4), annotate each step with its
   p50/p99 wall-clock.

Also export the three diagrams as standalone `.mmd` files for re-use:
`analysis/$1/call-graph.mmd`, `analysis/$1/data-lineage.mmd`,
`analysis/$1/critical-path.mmd`.

## Annotate

Below each `<pre class="mermaid">` block in TOPOLOGY.html, add a `<ul>`
with 3-5 **architect observations**: tight coupling clusters, single
points of failure, candidates for service extraction, data stores
touched by too many writers.

## Present

Tell the user to open `analysis/$1/TOPOLOGY.html` in a browser.
