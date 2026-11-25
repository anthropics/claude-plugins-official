# Artifact style — the house look

**Shared across the plugin.** One visual system so every page a skill produces
reads as the same product. Read this before building any HTML artifact; do not
invent a new palette per skill.

**The point is not decoration.** These are operating tools for a plant — a data
quality report, a morning production report, a bad-actor ranking, a cost-basis
sheet. Legible and defensible beats flashy. No hero banners, no marketing
gradients. A shop drawing, not a landing page.

---

## The constraint that shapes everything

**Microsoft 365 is read-only by default.** Write access is an admin opt-in and
Teams has no write path at all. No skill may assume it can post a message or
write a file back into M365.

So every deliverable is produced **in the conversation** and the user places it
themselves. An artifact is a thing they open, read, and save or forward. It is
never something the plugin filed away on their behalf.

**The one exception is the two live dashboards**, Operations and the Quality
Register, which are published to the user's own Claude artifact store and
updated in place, per `live-dashboard.md`. That store is not M365 and not a
system of record. Everything on this page applies to them unchanged.

---

## When to use an artifact, and when not to

Reach for a page when the output is something the user will **refer back to,
print, take into a meeting, or hand to someone else**. A data quality report, a
morning production report, a ranked diagnosis, a scored comparison. Skip it for
a single number or a one-line answer; the chat reply is the deliverable and a
page wrapped around one sentence is noise.

**The artifact is additive, never a replacement.** The user still gets the short
answer in chat. The page is where they go for the full picture.

**Three kinds of output, and only one of them is an artifact:**

| Output | Form | Why |
|---|---|---|
| A report, dashboard, or ranked analysis | HTML artifact, this style | Read at a glance, referred back to |
| A dataset | XLSX workbook, tab per entity | Meant to be filtered, pivoted, and checked |
| A controlled document | The plant's own template | An NCR, an 8D, a quote, a supplier RFQ package and a trade study memo all have a plant-specific or customer-specific shape, captured during `onboarding`. Never restyle a controlled document into the house look. |

That last row matters. A quality manager's 8D goes to a customer against a
contractual format. House styling it would be wrong, not nicer.

---

## Design tokens

Every color and font is a CSS custom property. Components never carry a literal
hex, so one override point recolors the whole page correctly.

```css
:root {
  --ink: #1A1D21;          /* primary text, graphite */
  --paper: #F2F3F5;        /* page background, cool grey */
  --paper-raised: #FFFFFF; /* card surfaces sitting on --paper */
  --line: #D6D9DD;         /* hairline borders and rules */
  --accent: #1F5C8B;       /* primary accent, drawing blue */
  --accent-soft: #E4EDF4;  /* accent tint for pills and highlights */

  /* Semantic, never repurposed as branding */
  --good: #2E7248;
  --good-soft: #E3EFE7;
  --warn: #A8641A;
  --warn-soft: #F7EBDA;
  --critical: #A93226;
  --critical-soft: #F9E9E7;

  --font-display: 'IBM Plex Sans Condensed', 'Arial Narrow', sans-serif;
  --font-body: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'IBM Plex Mono', 'SF Mono', Consolas, monospace;

  --text-xs: 0.75rem;   --text-sm: 0.875rem;  --text-base: 1rem;
  --text-lg: 1.125rem;  --text-xl: 1.375rem;  --text-2xl: 1.75rem;
  --text-3xl: 2.25rem;
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --ink: #E8EAEC;
    --paper: #15181B;
    --paper-raised: #1D2126;
    --line: #2E343A;
    --accent: #6BA8D4;
    --accent-soft: #1B2C39;
    --good: #6FBF88;
    --good-soft: #1B2E22;
    --warn: #D9A15C;
    --warn-soft: #33271A;
    --critical: #DE8378;
    --critical-soft: #35201E;
  }
}

:root[data-theme="dark"] {
  --ink: #E8EAEC;
  --paper: #15181B;
  --paper-raised: #1D2126;
  --line: #2E343A;
  --accent: #6BA8D4;
  --accent-soft: #1B2C39;
  --good: #6FBF88;
  --good-soft: #1B2E22;
  --warn: #D9A15C;
  --warn-soft: #33271A;
  --critical: #DE8378;
  --critical-soft: #35201E;
}
```

**Fonts load from Google Fonts**, the one host the artifact sandbox allows:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Condensed:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
```

---

## Type

- **Display** for page titles and section headers only, weight 600.
- **Body** for everything read as prose.
- **Mono** for every number that sits in a column — counts, quantities, minutes,
  currency, part numbers, work order numbers, dates in a table. Pair with
  `font-variant-numeric: tabular-nums`. Part numbers and work order numbers are
  identifiers, not prose, and they belong in mono so `PN-4471-B` and `PN-4471-8`
  are distinguishable at a glance.

---

## Layout — the panel pattern

Content sits in bordered panels (`--paper-raised` on `--paper`, `1px solid
var(--line)`, `border-radius: 4px`). Panels stack with `gap`, not margin. Wide
tables get their own `overflow-x: auto` wrapper so the page never scrolls
sideways.

```css
.panel {
  background: var(--paper-raised);
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 1.5rem;
}
.page {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}
```

---

## Components

### Header

Every artifact opens the same way: the plant or site name, the page's job in one
line, and when it was generated. No hero, no illustration. Use the plant's own
vocabulary for areas and shifts, per the config profile `onboarding` captures.

```html
<header class="page-header">
  <div>
    <h1>Data Quality Report</h1>
    <p class="meta">Fairview Plant · Generated Sep 8, 2026 06:12</p>
  </div>
</header>
```

**A live dashboard's header carries two clocks**, in place of the single
"Generated" line: when this version was published, and how fresh the data
under it is. They differ, and a reader needs both to know whether a stale
number is the run's fault or the export's.

```html
<p class="meta">Fairview Plant · Updated Sep 1, 2026 04:12 · data as of Sep 1, 2026 03:52</p>
```

"Updated" is printed only on a page that was published in that run. The same
page offered in the conversation instead says *Generated [timestamp] · data as
of [timestamp]*. Per `live-dashboard.md`.

### Freshness banner — required on anything built from an export

**This is the one component that is not optional.** Any page built on
export-sourced data opens with it, before the numbers, per
`absent-is-not-zero.md`. It states each source, when it last refreshed, and the
window it covers. A source that is stale or missing takes a `--critical` or
`--warn` pill and is listed first.

```html
<div class="panel freshness">
  <h2>Sources</h2>
  <div class="table-scroll">
    <table>
      <thead><tr><th>Source</th><th>Last refreshed</th><th>Covers</th><th>Status</th></tr></thead>
      <tbody>
        <tr>
          <td>Inspection export</td>
          <td class="num">Aug 14</td>
          <td class="num">Aug 1–14</td>
          <td><span class="status status--critical">19 days stale</span></td>
        </tr>
        <tr>
          <td>NetSuite</td>
          <td class="num">Sep 8 06:10</td>
          <td class="num">Aug 1 – Sep 8</td>
          <td><span class="status status--good">Live</span></td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
```

Never render this section empty. A source that could not be read is a row with a
status, not an omission.

### Stat tile

The one number that matters, large, with a plain line under it. The context line
is what makes it useful; a number alone is not an answer.

```html
<div class="stat-tile">
  <div class="stat-figure">412 / 447</div>
  <div class="stat-label">Work orders joined</div>
  <p class="stat-context">35 unmatched, all inside a known export window gap.</p>
</div>
```

`.stat-figure` uses `--font-mono`, `--text-3xl`, `tabular-nums`.

### Status pill

A small rectangular stamp with a slight radius, uppercase, letter-spaced.
Semantic colors only, never the accent.

```html
<span class="status status--good">Matched</span>
<span class="status status--warn">Review</span>
<span class="status status--critical">Blocking</span>
```

```css
.status {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 2px;
  font: 600 var(--text-xs) var(--font-body);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.status--good { background: var(--good-soft); color: var(--good); }
.status--warn { background: var(--warn-soft); color: var(--warn); }
.status--critical { background: var(--critical-soft); color: var(--critical); }
```

### Table

Hairline row dividers, no heavy grid. Numbers and identifiers right-aligned in
`--font-mono`. Wrap in `.table-scroll`.

**Always show example rows, never only counts.** A count tells someone a problem
exists; an example row tells them what it is. Two or three real rows per finding.

### Floor schematic

The plant's floor, redrawn: one inline SVG built in code, numbers baked in,
`viewBox` from the layout's `Aspect`, `width: 100%` inside an `overflow-x:
auto` wrapper. Rules and states are in
`../skills/daily-production-report/reference/floor-schematic.md`.

- **Zones** are `--paper-raised` rectangles (or outline polygons) with a
  `--line` stroke and the zone name in `--text-sm`, `--ink`.
- **Machines** are boxes filled with the state's soft token and stroked with
  its strong one: `--good`, `--warn`, `--critical`; *No data*, *OEE N/A* and
  *mapping not confirmed* use `--paper` with a dashed `--line` stroke.
- **Each box prints its state word** (`OK`, `WATCH`, `POOR`, `DOWN`, `NO
  DATA`, `OEE N/A`, `UNCONFIRMED`) beside its name and figures, in
  `--font-mono`, never below `--text-xs`. Colour is never the only signal.
- **The caption** under it names the density mode, the active OEE cutoffs,
  *"State as of the last export, [timestamp]. Not live."* and *"Positions are
  approximate."*

```html
<figure class="floor">
  <div class="floor-scroll"><svg viewBox="0 0 1600 1000" role="img" aria-label="Fairview floor view">…</svg></div>
  <figcaption>Full view · good at or above 75%, poor below 60% (defaults, not confirmed for this plant) · State as of the last export, Aug 31, 2026 23:00. Not live. Positions are approximate.</figcaption>
</figure>
```

### Proposal block — for anything awaiting a yes

Where a skill proposes a correction it will not apply without approval, the
proposal is visible on the page as well as in chat: what was found, what the fix
would do, how many records it affects, and what it would change them to.

```html
<div class="panel proposal">
  <span class="status status--warn">Awaiting approval</span>
  <h3>Strip revision suffix</h3>
  <p>37 records match if the <code>Rev 2</code> suffix is stripped from the
     quality export's part numbers. Revision data exists on that side only and
     would be preserved in a separate column.</p>
</div>
```

### Footer

Quiet, small, `--text-xs`:

```html
<footer class="page-footer">Generated by <strong>data-consolidate</strong> — Manufacturing</footer>
```

---

## Both themes, always

Follow the token structure exactly: bare `:root` for light, the
`prefers-color-scheme` query guarded by `:not([data-theme="light"])`, and
`:root[data-theme="dark"]` repeating the values so an explicit toggle wins either
direction.

---

## What not to do

- **Do not deliver the page twice.** Publish the artifact; never also hand over
  the same content as a downloadable `.html`. A published dashboard is not
  also pasted into the conversation; the run reports its URL. The only file that ships next to an
  artifact is a genuinely different deliverable the skill already promises, such
  as the XLSX dataset or the pulse's short Operations page.
- **Do not house-style a controlled document.** An NCR, an 8D, a quote or a
  supplier RFQ package uses the plant's or the customer's template.
- **Do not invent a new palette per skill.**
- **Do not add a hero, an illustration, or marketing copy.**
- **Do not skip the freshness banner** on anything built from an export.
- **Do not render a count without an example row.**
- **Do not skip dark mode.**
- **Do not let this rule grow SKILL.md files.** A skill's delivery step is one
  line — "Render the report using the house artifact style," linking to
  `shared/artifact-style.md` relative to the skill's own folder, and naming the
  components it uses. All CSS and component detail stays here.
