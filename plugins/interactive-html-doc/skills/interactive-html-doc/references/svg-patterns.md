# SVG Diagram Patterns Reference

Reusable SVG code snippets for common diagram types. All SVGs use `font-family: monospace` and colors matching the CSS design system.

## Common Setup

### Arrowhead Marker Definitions

Place inside `<defs>` within the SVG:

```xml
<defs>
  <!-- Blue arrowhead -->
  <marker id="arrow-blue" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
    <path d="M0,0 L8,3 L0,6" fill="#6c9eff"/>
  </marker>
  <!-- Purple arrowhead -->
  <marker id="arrow-purple" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
    <path d="M0,0 L8,3 L0,6" fill="#a78bfa"/>
  </marker>
  <!-- Green arrowhead -->
  <marker id="arrow-green" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
    <path d="M0,0 L8,3 L0,6" fill="#34d399"/>
  </marker>
  <!-- Dim / neutral arrowhead -->
  <marker id="arrow-dim" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
    <path d="M0,0 L8,3 L0,6" fill="#546e7a"/>
  </marker>
  <!-- Red arrowhead -->
  <marker id="arrow-red" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
    <path d="M0,0 L8,3 L0,6" fill="#f87171"/>
  </marker>
  <!-- Amber arrowhead -->
  <marker id="arrow-amber" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
    <path d="M0,0 L8,3 L0,6" fill="#f59e0b"/>
  </marker>
</defs>
```

### SVG Boilerplate

```xml
<svg width="W" height="H" viewBox="0 0 W H"
     xmlns="http://www.w3.org/2000/svg"
     style="font-family:monospace;font-size:12px">
  <!-- content -->
</svg>
```

Always set explicit `width`, `height`, and matching `viewBox`. Wrap in a `.diagram-box` div.

## Pattern 1: Block Diagram with Labeled Boxes and Arrows

Vertical flow: Component A → Component B → Component C.

```xml
<svg width="400" height="260" viewBox="0 0 400 260"
     xmlns="http://www.w3.org/2000/svg" style="font-family:monospace;font-size:12px">
  <!-- Box A -->
  <rect x="100" y="10" width="200" height="50" rx="8"
        fill="rgba(108,158,255,.08)" stroke="#6c9eff" stroke-width="1.5"/>
  <text x="155" y="40" fill="#6c9eff" font-size="14" font-weight="bold">Component A</text>

  <!-- Arrow A → B -->
  <line x1="200" y1="60" x2="200" y2="95" stroke="#546e7a" stroke-width="1.5"
        marker-end="url(#arrow-dim)"/>
  <text x="210" y="82" fill="#546e7a" font-size="10">label</text>

  <!-- Box B -->
  <rect x="100" y="100" width="200" height="50" rx="8"
        fill="rgba(167,139,250,.08)" stroke="#a78bfa" stroke-width="1.5"/>
  <text x="155" y="130" fill="#a78bfa" font-size="14" font-weight="bold">Component B</text>

  <!-- Arrow B → C -->
  <line x1="200" y1="150" x2="200" y2="185" stroke="#546e7a" stroke-width="1.5"
        marker-end="url(#arrow-dim)"/>

  <!-- Box C -->
  <rect x="100" y="190" width="200" height="50" rx="8"
        fill="rgba(245,158,11,.08)" stroke="#f59e0b" stroke-width="1.5"/>
  <text x="155" y="220" fill="#f59e0b" font-size="14" font-weight="bold">Component C</text>

  <defs>
    <marker id="arrow-dim" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6" fill="#546e7a"/>
    </marker>
  </defs>
</svg>
```

## Pattern 2: Side-by-Side Comparison

Two states shown next to each other (e.g., before/after, time T0/T1):

```xml
<svg width="600" height="150" viewBox="0 0 600 150"
     xmlns="http://www.w3.org/2000/svg" style="font-family:monospace;font-size:12px">
  <!-- Left: State A -->
  <text x="80" y="20" fill="#6c9eff" font-weight="bold" font-size="13">State A</text>
  <rect x="30" y="30" width="220" height="100" rx="6"
        fill="rgba(108,158,255,.06)" stroke="#2a2d3a"/>
  <!-- ... inner elements ... -->

  <!-- Right: State B -->
  <text x="420" y="20" fill="#34d399" font-weight="bold" font-size="13">State B</text>
  <rect x="350" y="30" width="220" height="100" rx="6"
        fill="rgba(52,211,153,.06)" stroke="#2a2d3a"/>
  <!-- ... inner elements ... -->
</svg>
```

## Pattern 3: Flow Chart with Branching

Decision point that splits into two paths:

```xml
<svg width="500" height="200" viewBox="0 0 500 200"
     xmlns="http://www.w3.org/2000/svg" style="font-family:monospace;font-size:12px">
  <!-- Start -->
  <rect x="150" y="10" width="200" height="30" rx="4"
        fill="rgba(108,158,255,.08)" stroke="#6c9eff"/>
  <text x="200" y="30" fill="#6c9eff" font-size="11">Start Step</text>

  <!-- Vertical line down to branch point -->
  <line x1="250" y1="40" x2="250" y2="60" stroke="#546e7a" stroke-width="1"/>
  <!-- Horizontal split -->
  <line x1="250" y1="60" x2="100" y2="60" stroke="#546e7a" stroke-width="1"/>
  <line x1="250" y1="60" x2="400" y2="60" stroke="#546e7a" stroke-width="1"/>

  <!-- Left branch (yes/true) -->
  <line x1="100" y1="60" x2="100" y2="80" stroke="#34d399" stroke-width="1"/>
  <rect x="20" y="85" width="160" height="30" rx="4"
        fill="rgba(52,211,153,.1)" stroke="#34d399"/>
  <text x="45" y="105" fill="#34d399" font-size="11">Yes → Action A</text>

  <!-- Right branch (no/false) -->
  <line x1="400" y1="60" x2="400" y2="80" stroke="#f87171" stroke-width="1"/>
  <rect x="320" y="85" width="160" height="30" rx="4"
        fill="rgba(248,113,113,.1)" stroke="#f87171"/>
  <text x="345" y="105" fill="#f87171" font-size="11">No → Action B</text>
</svg>
```

## Pattern 4: Timeline / Evolution

Horizontal timeline with labeled milestones:

```xml
<svg width="500" height="120" viewBox="0 0 500 120"
     xmlns="http://www.w3.org/2000/svg" style="font-family:monospace;font-size:12px">
  <!-- Timeline axis -->
  <line x1="40" y1="50" x2="460" y2="50" stroke="#546e7a" stroke-width="2"/>

  <!-- Milestone 1 -->
  <circle cx="120" cy="50" r="8" fill="#a78bfa"/>
  <text x="90" y="30" fill="#a78bfa" font-weight="bold" font-size="14">Gen 1</text>
  <text x="60" y="75" fill="#546e7a" font-size="11">Description line 1</text>
  <text x="60" y="90" fill="#546e7a" font-size="11">Description line 2</text>

  <!-- Arrow between milestones -->
  <line x1="130" y1="50" x2="340" y2="50" stroke="#f59e0b" stroke-width="2"
        marker-end="url(#arrow-amber)"/>

  <!-- Milestone 2 -->
  <circle cx="350" cy="50" r="8" fill="#6c9eff"/>
  <text x="320" y="30" fill="#6c9eff" font-weight="bold" font-size="14">Gen 2</text>
  <text x="290" y="75" fill="#6c9eff" font-size="11">Description line 1</text>
  <text x="290" y="90" fill="#6c9eff" font-size="11">Description line 2</text>

  <defs>
    <marker id="arrow-amber" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6" fill="#f59e0b"/>
    </marker>
  </defs>
</svg>
```

## Pattern 5: Heterogeneous Width Visualization

Boxes of different widths to show proportional sizes:

```xml
<svg width="580" height="130" viewBox="0 0 580 130"
     xmlns="http://www.w3.org/2000/svg" style="font-family:monospace;font-size:12px">
  <!-- Wide (128b) -->
  <rect x="20" y="30" width="140" height="50" rx="6"
        fill="rgba(108,158,255,.12)" stroke="#6c9eff" stroke-width="2"/>
  <text x="50" y="15" fill="#6c9eff" font-weight="bold">Item A</text>
  <text x="50" y="60" fill="#6c9eff" font-weight="bold">128b</text>

  <!-- Medium (64b) -->
  <rect x="180" y="35" width="100" height="40" rx="6"
        fill="rgba(167,139,250,.12)" stroke="#a78bfa" stroke-width="2"/>
  <text x="200" y="15" fill="#a78bfa" font-weight="bold">Item B</text>
  <text x="205" y="60" fill="#a78bfa" font-weight="bold">64b</text>

  <!-- None (0) -->
  <rect x="300" y="40" width="80" height="30" rx="6"
        fill="rgba(248,113,113,.06)" stroke="#f87171" stroke-dasharray="5,3"/>
  <text x="310" y="15" fill="#f87171" font-weight="bold">Item C</text>
  <text x="315" y="60" fill="#f87171">none</text>

  <!-- Small (32b) -->
  <rect x="400" y="40" width="60" height="30" rx="6"
        fill="rgba(245,158,11,.12)" stroke="#f59e0b" stroke-width="2"/>
  <text x="405" y="15" fill="#f59e0b" font-weight="bold">Item D</text>
  <text x="412" y="60" fill="#f59e0b" font-weight="bold">32b</text>

  <!-- Scale bar -->
  <text x="20" y="110" fill="#546e7a" font-size="10">
    ▲ Width proportional to data size
  </text>
</svg>
```

## Pattern 6: Mapping / Routing Diagram

Show how items map from source to destination (with crossed paths):

```xml
<svg width="520" height="140" viewBox="0 0 520 140"
     xmlns="http://www.w3.org/2000/svg" style="font-family:monospace;font-size:12px">
  <!-- Source items (left) -->
  <text x="20" y="30" fill="#c792ea" font-size="12">Source A</text>
  <text x="20" y="80" fill="#c792ea" font-size="12">Source B</text>

  <!-- Solid arrows to physical destination -->
  <line x1="120" y1="25" x2="250" y2="25" stroke="#f87171" stroke-width="1.5"
        marker-end="url(#arrow-red)"/>
  <text x="260" y="30" fill="#f87171" font-size="11">Physical Dest 1</text>

  <line x1="120" y1="75" x2="250" y2="75" stroke="#f87171" stroke-width="1.5"
        marker-end="url(#arrow-red)"/>
  <text x="260" y="80" fill="#f87171" font-size="11">Physical Dest 2</text>

  <!-- Dashed arrows to logical destination (converging) -->
  <line x1="120" y1="35" x2="300" y2="110" stroke="#34d399" stroke-width="1.5"
        stroke-dasharray="4,3" marker-end="url(#arrow-green)"/>
  <line x1="120" y1="85" x2="300" y2="110" stroke="#34d399" stroke-width="1.5"
        stroke-dasharray="4,3" marker-end="url(#arrow-green)"/>

  <rect x="310" y="95" width="180" height="35" rx="6"
        fill="rgba(52,211,153,.1)" stroke="#34d399" stroke-width="1.5"/>
  <text x="330" y="117" fill="#34d399" font-weight="bold">Shared Logical Unit</text>
</svg>
```

## Pattern 7: Interactive / Animated Elements

For SVGs that change state via JS, give elements unique `id` attributes:

```xml
<!-- Rect whose fill/stroke change on step -->
<rect id="cell-a0" x="60" y="30" width="120" height="40" rx="5"
      fill="rgba(108,158,255,.15)" stroke="#6c9eff" stroke-width="2"/>

<!-- Text whose content changes on step -->
<text id="cell-a0-val" x="72" y="62" fill="#6c9eff" font-size="12">initial value</text>
<text id="cell-a0-st"  x="130" y="46" fill="#6c9eff" font-size="10">[status]</text>
```

JavaScript update pattern:

```javascript
function applyCell(prefix, data) {
  var rect = document.getElementById(prefix);
  var val  = document.getElementById(prefix + '-val');
  var st   = document.getElementById(prefix + '-st');
  rect.setAttribute('fill', data.fill);
  rect.setAttribute('stroke-width', data.sw);
  rect.setAttribute('stroke-dasharray', data.dash);
  val.textContent = data.val;
  val.setAttribute('fill', data.valC);
  st.textContent = data.st;
  st.setAttribute('fill', data.stC);
}
```

## Tips

- Keep SVG `width` under 620px for comfortable reading in the main content area
- Use `font-size: 12px` for labels, `13-14px` for titles within SVGs
- Use `rx="4"` to `rx="8"` for rounded corners depending on box size
- For inactive/empty elements, use `stroke-dasharray="4,3"` or `"5,3"`
- Use `rgba()` fills with alpha `.05`–`.15` for subtle backgrounds
- Place `<defs>` with markers at the end of the SVG to keep content readable
- For lines with arrows, use `marker-end="url(#arrow-color)"`
