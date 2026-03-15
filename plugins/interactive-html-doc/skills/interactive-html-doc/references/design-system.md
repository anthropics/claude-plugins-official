# CSS Design System Reference

## CSS Variables

```css
:root {
  /* Backgrounds */
  --bg: #0f1117;           /* Page background */
  --bg-card: #1a1d27;      /* Card / sidebar background */
  --bg-code: #12141c;      /* Code block background */

  /* Borders & Lines */
  --border: #2a2d3a;       /* Borders, dividers */

  /* Text */
  --text: #e0e0e8;         /* Primary text */
  --text-dim: #8b8fa3;     /* Secondary / muted text */

  /* Accent Colors */
  --accent: #6c9eff;       /* Primary accent (blue) — links, highlights, Lane A */
  --accent2: #a78bfa;      /* Secondary accent (purple) — h3 headings, Lane B */
  --accent3: #34d399;      /* Tertiary accent (green) — success, reuse, Lane C */
  --accent4: #f59e0b;      /* Quaternary accent (amber) — warnings, execution units */
  --accent-red: #f87171;   /* Error / danger accent */

  /* Layout */
  --toc-w: 260px;          /* Sidebar width */
}
```

### Color Usage Guidelines

- **Blue (`--accent`)**: Primary interactive elements, links, first-level items, Lane A
- **Purple (`--accent2`)**: Secondary hierarchy, h3 headings, Lane B
- **Green (`--accent3`)**: Success states, positive indicators, reuse hits, Lane C
- **Amber (`--accent4`)**: Warnings, execution units, important callouts
- **Red (`--accent-red`)**: Errors, missing items, danger states, absence indicators

## Typography

```css
body {
  font-family: -apple-system, "Segoe UI", Roboto, "Noto Sans SC", sans-serif;
  font-size: 15px;
  line-height: 1.75;
}
code {
  font-family: "JetBrains Mono", "Fira Code", "Cascadia Code", monospace;
}
```

### Heading Sizes

| Level | Size | Color | Notes |
|-------|------|-------|-------|
| h1 | 28px | Gradient (accent → accent2) | Use `-webkit-background-clip: text` |
| h2 | 20px | `--accent` | Section headers, with bottom border |
| h3 | 16px | `--accent2` | Subsection headers |
| h4 | 15px | `--accent3` | Term definitions, minor headers |

## Component Classes

### Sidebar TOC (`nav#toc`)

```css
nav#toc {
  position: fixed; top: 0; left: 0;
  width: var(--toc-w); height: 100vh;
  background: var(--bg-card);
  border-right: 1px solid var(--border);
  overflow-y: auto; z-index: 100;
  padding: 20px 0;
}
nav#toc a {
  display: block; padding: 6px 20px;
  color: var(--text-dim); text-decoration: none;
  font-size: 13px; border-left: 3px solid transparent;
}
nav#toc a:hover, nav#toc a.active {
  color: var(--accent);
  background: rgba(108,158,255,.07);
  border-left-color: var(--accent);
}
nav#toc a.sub { padding-left: 36px; font-size: 12px; }
```

### Collapsible Section

```css
.section { margin-bottom: 12px; }
.section-toggle {
  width: 100%; text-align: left;
  background: var(--bg-card);
  border: 1px solid var(--border); border-radius: 8px;
  padding: 14px 20px; color: var(--text);
  font-size: 16px; cursor: pointer;
  display: flex; align-items: center; gap: 10px;
  font-weight: 600;
}
.section-toggle:hover { border-color: var(--accent); }
.section-toggle .arrow {
  display: inline-block;
  transition: transform .3s;
  font-size: 12px; color: var(--accent);
}
.section-toggle.open .arrow { transform: rotate(90deg); }
.section-body {
  max-height: 0; overflow: hidden;
  transition: max-height .4s ease;
}
.section-body.open { max-height: 8000px; padding: 16px 8px; }
```

### Code Blocks

```css
pre {
  background: var(--bg-code);
  border: 1px solid var(--border);
  border-radius: 6px; padding: 16px;
  overflow-x: auto; font-size: 13px; line-height: 1.6;
}
/* Syntax highlight classes */
.kw { color: #c792ea; }  /* keyword */
.tp { color: #82aaff; }  /* type */
.cm { color: #546e7a; }  /* comment */
.st { color: #c3e88d; }  /* string/number */
.fn { color: #82aaff; }  /* function */
```

### Tables

```css
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th {
  background: rgba(108,158,255,.1); color: var(--accent);
  padding: 10px 12px; text-align: left; font-weight: 600;
  border-bottom: 2px solid var(--border);
}
td { padding: 8px 12px; border-bottom: 1px solid var(--border); }
tr:hover td { background: rgba(108,158,255,.04); }
```

### Callout Boxes

```css
.callout {
  border-left: 3px solid var(--accent);
  background: rgba(108,158,255,.06);
  padding: 12px 16px;
  border-radius: 0 6px 6px 0;
}
.callout.green  { border-left-color: var(--accent3); background: rgba(52,211,153,.06); }
.callout.yellow { border-left-color: var(--accent4); background: rgba(245,158,11,.06); }
.callout.red    { border-left-color: var(--accent-red); background: rgba(248,113,113,.06); }
```

### Tabs

```css
.tabs { display: flex; gap: 0; }
.tab-btn {
  padding: 8px 20px;
  border: 1px solid var(--border);
  background: var(--bg); color: var(--text-dim);
  cursor: pointer; font-size: 13px; border-bottom: none;
}
.tab-btn:first-child { border-radius: 6px 0 0 0; }
.tab-btn:last-child  { border-radius: 0 6px 0 0; }
.tab-btn.active {
  background: var(--bg-card); color: var(--accent);
}
.tab-content {
  display: none;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 0 6px 6px 6px;
  padding: 16px;
}
.tab-content.active { display: block; }
```

### Step Controls

```css
.step-controls {
  display: flex; gap: 8px; align-items: center; flex-wrap: wrap;
}
.step-btn {
  padding: 6px 16px; border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg-card); color: var(--text);
  cursor: pointer; font-size: 13px;
}
.step-btn:hover { border-color: var(--accent); color: var(--accent); }
.step-btn.active {
  background: var(--accent); color: #000;
  border-color: var(--accent); font-weight: 600;
}
```

### Utility Classes

```css
/* Diagram container */
.diagram-box {
  background: var(--bg-code);
  border: 1px solid var(--border);
  border-radius: 8px; padding: 20px;
  overflow-x: auto;
}

/* Chip / badge row */
.chips { display: flex; gap: 8px; flex-wrap: wrap; }
.chip {
  font-size: 12px; padding: 4px 12px;
  border-radius: 20px; border: 1px solid var(--border);
  color: var(--text-dim);
}
.chip.blue   { border-color: var(--accent);  color: var(--accent); }
.chip.purple { border-color: var(--accent2); color: var(--accent2); }
.chip.green  { border-color: var(--accent3); color: var(--accent3); }

/* Inline highlights */
.hl-reuse   { color: var(--accent3);   font-weight: 600; }
.hl-noreuse { color: var(--accent-red); font-weight: 600; }
.hl-new     { color: var(--accent4);    font-weight: 600; }

/* Section badge */
.section-toggle .badge {
  font-size: 11px; padding: 2px 8px;
  border-radius: 10px;
  background: rgba(108,158,255,.15);
  color: var(--accent); margin-left: auto;
  font-weight: 400;
}
```

## Responsive Breakpoints

```css
@media (max-width: 840px) {
  nav#toc { transform: translateX(-100%); }
  nav#toc.open { transform: translateX(0); }
  .overlay.open { display: block; }
  .hamburger { display: block; }
  main { margin-left: 0; padding: 60px 20px 60px; }
}
```

Mobile elements:

```css
.hamburger {
  display: none; position: fixed; top: 12px; left: 12px; z-index: 200;
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: 6px; padding: 8px 10px; cursor: pointer;
  color: var(--text); font-size: 18px;
}
.overlay {
  display: none; position: fixed; inset: 0;
  background: rgba(0,0,0,.5); z-index: 99;
}
```
