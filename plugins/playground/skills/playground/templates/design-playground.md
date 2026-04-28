# Design Playground Template

Use this template when the playground is about visual design decisions: components, layouts, spacing, color, typography, animation, responsive behavior.

## Layout

```
+-------------------+----------------------+
|                   |                      |
|  Controls         |  Live component/     |
|  grouped by:      |  layout preview      |
|  • Spacing        |  (renders in a       |
|  • Color          |   mock page or       |
|  • Typography     |   isolated card)     |
|  • Shadow/Border  |                      |
|  • Interaction    |                      |
|                   +----------------------+
|                   |  Prompt output       |
|                   |  [ Copy Prompt ]     |
+-------------------+----------------------+
```

## Control types by decision

| Decision | Control | Example |
|---|---|---|
| Sizes, spacing, radius | Slider | border-radius 0–24px |
| On/off features | Toggle | show border, hover effect |
| Choosing from a set | Dropdown | font-family, easing curve |
| Colors | Hue + saturation + lightness sliders | shadow color, accent |
| Layout structure | Clickable cards | sidebar-left / top-nav / no-nav |
| Responsive behavior | Viewport-width slider | watch grid reflow at breakpoints |

## Preview rendering

Apply state values directly to a preview element's inline styles:

```javascript
function renderPreview() {
  const el = document.getElementById('preview');
  el.style.borderRadius = state.radius + 'px';
  el.style.padding = state.padding + 'px';
  el.style.boxShadow = state.shadow
    ? `0 ${state.shadowY}px ${state.shadowBlur}px rgba(0,0,0,${state.shadowOpacity})`
    : 'none';
}
```

Show the preview on both light and dark backgrounds if relevant. Include a context toggle.

## Prompt output for design

Frame it as a direction to a developer, not a spec sheet:

> "Update the card to feel soft and elevated: 12px border-radius, 24px horizontal padding, a medium box-shadow (0 4px 12px rgba(0,0,0,0.1)). On hover, lift it with translateY(-1px) and deepen the shadow slightly."

If the user is working in Tailwind, suggest Tailwind classes. If raw CSS, use CSS properties.

## Example topics

- Button style explorer (radius, padding, weight, hover/active states)
- Card component (shadow depth, radius, content layout, image)
- Layout builder (sidebar width, content max-width, header height, grid)
- Typography scale (base size, ratio, line heights across h1-body-caption)
- Color palette generator (primary hue, derive secondary/accent/surface)
- Dashboard density (airy → compact slider that scales everything proportionally)
- Modal/dialog (width, overlay opacity, entry animation, corner radius)
