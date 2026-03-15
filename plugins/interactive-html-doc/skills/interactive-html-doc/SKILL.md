---
name: interactive-html-doc
description: This skill should be used when the user asks to "convert markdown to interactive HTML", "create an interactive HTML document", "turn a document into an interactive webpage", "make a technical doc interactive", "generate an HTML page from markdown", or wants a polished, self-contained HTML page with diagrams, collapsible sections, and animations from existing text content.
version: 0.1.0
---

# Interactive HTML Document Generator

This skill transforms Markdown technical documents into polished, interactive single-file HTML pages. All CSS, SVG, and JavaScript are inlined — no external dependencies. The output is a self-contained `.html` file that works offline.

## When to Use

Trigger this skill when a user has a Markdown document (or plain text notes) and wants an interactive HTML version with features like collapsible sections, SVG diagrams, animated walkthroughs, or tabbed content.

## Core Design Principles

1. **Single-file, zero-dependency**: Everything inlined — CSS, SVG, JS. No CDN links, no framework imports.
2. **Dark theme by default**: Dark background (`#0f1117`), light text, accent colors for hierarchy. Use CSS variables for theming consistency.
3. **Progressive disclosure**: Not all content visible at once. Use collapsible sections, tabs, and step-through animations to let the reader control depth.
4. **SVG over ASCII art**: Replace every ASCII diagram with an inline SVG. SVGs scale, support color, animation, and interactivity.
5. **Mobile-first responsive**: Sidebar collapses to hamburger menu on narrow screens. Content reflows gracefully.

## Architecture Overview

The HTML document follows a fixed structure:

```
<!DOCTYPE html>
<html lang="...">
<head>
  <style>  /* All CSS here */  </style>
</head>
<body>
  <button class="hamburger">       <!-- Mobile nav toggle -->
  <nav id="toc">                   <!-- Fixed sidebar TOC -->
  <main>                           <!-- Content sections -->
    <h2 id="secN">                 <!-- Section anchors -->
    <div class="section">          <!-- Collapsible blocks -->
    <div class="diagram-box">      <!-- SVG containers -->
    <div class="tabs">             <!-- Tabbed content -->
  </main>
  <script>  /* All JS here */  </script>
</body>
</html>
```

## Step-by-Step Workflow

### Step 1: Analyze the Source Document

Read the source Markdown file completely. Identify:

- **Section hierarchy** (h1/h2/h3/h4) for TOC generation
- **Code blocks** for syntax highlighting
- **Tables** for HTML table conversion
- **ASCII art / diagrams** for SVG replacement candidates
- **Comparison content** for tab-based presentation
- **Sequential/temporal content** for step-through animations
- **Long subsections** for collapsible treatment

### Step 2: Plan the Interactive Elements

Map document features to interaction patterns:

| Source Pattern | Interactive Element |
|---|---|
| ASCII diagram | Inline SVG with color-coded elements |
| Step-by-step process | Animated step-through with buttons |
| A vs B comparison | Tabbed content panels |
| Long subsection | Collapsible accordion section |
| Key insight / warning | Styled callout box |
| Table with many rows | Styled HTML table with hover |

### Step 3: Build the HTML in Stages

For long documents, write the file in multiple passes to avoid exceeding output limits:

1. **Pass 1**: `<!DOCTYPE>` through `</style>`, navigation sidebar, first 1-2 content sections, closing `</html>` with JS placeholder
2. **Pass 2**: Edit to insert middle sections (use Edit tool to replace a placeholder comment)
3. **Pass 3**: Edit to insert remaining sections
4. **Pass 4**: Edit to insert all JavaScript

Place placeholder comments like `<!-- __SECTION_N_PLACEHOLDER__ -->` for staged insertion.

### Step 4: Verify Completeness

After all passes, verify:
- All HTML tags are properly closed (`</main>`, `</body>`, `</html>`)
- All section IDs match TOC `href` anchors
- All SVG `id` attributes referenced by JS exist
- No placeholder comments remain

## CSS Design System

Use CSS variables for consistent theming. Consult `references/design-system.md` for the complete variable set, component classes, and responsive breakpoints.

Key variable categories:
- **Colors**: `--bg`, `--bg-card`, `--bg-code`, `--border`, `--text`, `--text-dim`
- **Accents**: `--accent` (blue), `--accent2` (purple), `--accent3` (green), `--accent4` (amber), `--accent-red`
- **Layout**: `--toc-w` for sidebar width

## SVG Diagram Guidelines

Replace ASCII art with inline SVGs. Consult `references/svg-patterns.md` for reusable SVG patterns including:
- Block diagram with labeled boxes and arrows
- Flow chart with branching paths
- Comparison/timeline visualization
- Heterogeneous width visualization
- Arrowhead marker definitions

Key rules:
- Set explicit `width`, `height`, `viewBox` on every `<svg>`
- Use `font-family: monospace` for technical diagrams
- Match fill/stroke colors to CSS accent variables
- Define reusable arrowhead markers in `<defs>`
- Use `rgba()` fills with low alpha for subtle box backgrounds

## Interactive Component Patterns

### Collapsible Sections

Wrap subsections in a `.section` div with a `.section-toggle` button and a `.section-body` div. Toggle the `.open` class via JS.

### Step-Through Animations

For sequential content (e.g., instruction execution over time):
1. Define a `stepData` array in JS with per-step state (text, colors, styles)
2. Render step-selection buttons (`.step-btn`)
3. On click, update SVG element attributes (`fill`, `textContent`, `stroke-dasharray`, etc.)

### Tabbed Content

Use `.tabs` container with `.tab-btn` buttons and `.tab-content` divs. Toggle `.active` class via JS `switchTab()` function.

### Callout Boxes

Use `.callout` with optional color modifiers: `.green`, `.yellow`, `.red`.

## JavaScript Patterns

All JS goes in a single `<script>` block before `</body>`. Core functions:

- `toggleSection(btn)` — collapse/expand accordion
- `toggleToc()` — mobile sidebar
- `switchTab(e, groupId, tabId)` — tab switching
- `setStep(n)` — step-through animation
- Scroll-based TOC highlighting via `IntersectionObserver` or scroll event

## Writing Long Documents

When the HTML output exceeds ~300 lines, split into multiple write passes:

1. Announce the plan to the user: "I will write this in N passes"
2. Use `Write` for the initial skeleton (head + CSS + first sections + JS placeholder)
3. Use `Edit` for each subsequent content block (replace placeholder comments)
4. Use `Edit` for the final JavaScript insertion
5. Validate structure with `grep` for unclosed tags / remaining placeholders

## Additional Resources

### Reference Files

- **`references/design-system.md`** — Complete CSS variable set, component classes, responsive breakpoints, and typography
- **`references/svg-patterns.md`** — Reusable SVG code snippets for common diagram types (block diagrams, flowcharts, timelines, comparison charts)

### Asset Files

- **`assets/template.html`** — Minimal starter template with full CSS design system, sidebar TOC, one example section, and JS boilerplate. Copy and extend for new documents.
