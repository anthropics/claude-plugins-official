---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, or applications. Generates creative, polished code that avoids generic AI aesthetics.
license: Complete terms in LICENSE.txt
---

This skill guides creation of distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Implement real working code with exceptional attention to aesthetic details and creative choices.

The user provides frontend requirements: a component, page, application, or interface to build. They may include context about the purpose, audience, or technical constraints.

## Scoping: Match Effort to Task Size

Before design thinking, classify the request to avoid over-engineering simple components:

**🔹 Atomic** (single element: button, toggle, badge, spinner, input, icon, divider):
- Skip Design Thinking. Choose one distinctive trait (font, color, or animation) and execute it well.
- Output: ~20-80 lines. Single file preferred.

**🔹🔹 Composite** (multi-element: form, card, modal, navbar, footer, hero section, pricing table):
- Lightweight Design Thinking: pick tone + 1-2 aesthetic dimensions to emphasize.
- Output: ~80-200 lines. May span 1-2 files.

**🔹🔹🔹 Page/App** (full page, dashboard, landing page, SPA, multi-section layout):
- Full Design Thinking process below. Commit to a BOLD aesthetic direction across all dimensions.
- Output: 200+ lines, multi-file architecture as needed.

**Default**: If unclear, start at Composite level and escalate if the user's follow-up reveals larger scope.

## Design Thinking (Page/App level — skip or simplify for smaller scopes)

Before coding for full pages/apps, understand the context and commit to a BOLD aesthetic direction:
- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Pick an extreme: brutally minimal, maximalist chaos, retro-futuristic, organic/natural, luxury/refined, playful/toy-like, editorial/magazine, brutalist/raw, art deco/geometric, soft/pastel, industrial/utilitarian, etc. There are so many flavors to choose from. Use these for inspiration but design one that is true to the aesthetic direction.
- **Constraints**: Technical requirements (framework, performance, accessibility).
- **Differentiation**: What makes this UNFORGETTABLE? What's the one thing someone will remember?

**CRITICAL**: Choose a clear conceptual direction and execute it with precision. Bold maximalism and refined minimalism both work - the key is intentionality, not intensity.

Then implement working code (HTML/CSS/JS, React, Vue, etc.) that is:
- Production-grade and functional
- Visually striking and memorable
- Cohesive with a clear aesthetic point-of-view
- Meticulously refined in every detail

## Frontend Aesthetics Guidelines

Focus on:
- **Typography**: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics; unexpected, characterful font choices. Pair a distinctive display font with a refined body font.
- **Color & Theme**: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes.
- **Motion**: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Use Motion library for React when available. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions. Use scroll-triggering and hover states that surprise. **Always wrap motion in `@media (prefers-reduced-motion: no-preference)`** to respect OS accessibility settings — users with motion sensitivity should get instant transitions instead.
- **Spatial Composition**: Unexpected layouts. Asymmetry. Overlap. Diagonal flow. Grid-breaking elements. Generous negative space OR controlled density.
- **Backgrounds & Visual Details**: Create atmosphere and depth rather than defaulting to solid colors. Add contextual effects and textures that match the overall aesthetic. Apply creative forms like gradient meshes, noise textures, geometric patterns, layered transparencies, dramatic shadows, decorative borders, custom cursors, and grain overlays.

NEVER use generic AI-generated aesthetics like overused font families (Inter, Roboto, Arial, system fonts), cliched color schemes (particularly purple gradients on white backgrounds), predictable layouts and component patterns, and cookie-cutter design that lacks context-specific character.

Interpret creatively and make unexpected choices that feel genuinely designed for the context. No design should be the same. Vary between light and dark themes, different fonts, different aesthetics. NEVER converge on common choices (Space Grotesk, for example) across generations.

**IMPORTANT**: Match implementation complexity to the aesthetic vision. Maximalist designs need elaborate code with extensive animations and effects. Minimalist or refined designs need restraint, precision, and careful attention to spacing, typography, and subtle details. Elegance comes from executing the vision well.

Remember: Claude is capable of extraordinary creative work. Don't hold back, show what can truly be created when thinking outside the box and committing fully to a distinctive vision.

## Production Quality Requirements

These apply at ALL scope levels — they define "production-grade":

### Accessibility (non-negotiable)
- Use semantic HTML elements (`<nav>`, `<main>`, `<article>`, `<button>` — not `<div>` for everything)
- Interactive elements MUST be keyboard-accessible (Tab/Enter/Escape). Use `tabindex` only when necessary.
- Include `aria-label` on icon-only buttons and `aria-hidden="true"` on decorative elements
- Maintain WCAG AA color contrast: 4.5:1 for text, 3:1 for large text. Use CSS `color-mix()` or `oklch()` to derive accessible variants programmatically
- Add `:focus-visible` styles (not just `:focus`) — never leave the default focus ring as the only indicator
- Provide `<label>` for every form input; use `aria-describedby` for error/success messages

### Responsive Design
- Mobile-first: start with narrow viewport (320px), add breakpoints only when the design breaks
- Use relative units (rem, em, %, vw/vh, clamp()) rather than fixed px for layout and typography
- Test mentally at 320px, 768px, 1024px, and 1440px — the layout should work at every width
- Images: `max-width: 100%; height: auto`. Consider `srcset` for art direction.
- Touch targets: minimum 44×44px for interactive elements on mobile

### Motion Accessibility
- All animations, transitions, and scroll-driven effects MUST be wrapped in:
  ```css
  @media (prefers-reduced-motion: no-preference) {
    /* animation styles */
  }
  ```
- Provide instant fallbacks (opacity toggle, static position) for reduced-motion users
- Avoid auto-playing video/audio without a visible pause control

### Theme Variants (Composite and above)
- Support `prefers-color-scheme: dark` via CSS custom properties (`--color-bg`, `--color-text`, etc.)
- Define light and dark palettes in a `:root` / `[data-theme="dark"]` pattern — not inline styles
- Test the dark variant: it should feel intentionally designed, not just inverted

### Performance
- CSS animations: prefer `transform` and `opacity` (GPU-composited, no layout thrashing)
- Lazy-load below-fold images and heavy content (`loading="lazy"`, IntersectionObserver)
- Minimize layout shift: set explicit `width`/`height` on images and embeds