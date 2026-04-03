---
name: ui-redesign
description: UI redesign with Gemini design generation + visual QA verification loop.
---

# UI Redesign

Vision-guided UI implementation: Design → Build → Verify.

## Usage

```
/ksk:ui-redesign <design task, mockup reference, or visual change request>
```

## Workflow

### Phase 1: Design — Gemini

Generate design specification from reference images or requirements:

```bash
gemini -p "@/path/to/mockup.png Generate a complete design specification:

1. Design Tokens
   - Colors: primary, secondary, neutral, semantic colors with hex values
   - Typography: font families, sizes (px), weights, line heights
   - Spacing scale: base unit, padding/margin scale
   - Border radius tokens

2. Component Patterns
   - Layout structure: grid/flex system
   - Card/button/form/input specifications
   - Navigation pattern
   - Modal/dialog behavior

3. UX Analysis
   - User flow: entry point → goal → exit
   - Readability: font sizes, contrast ratios, text density
   - Information hierarchy: what draws attention first
   - Interaction patterns: hover, active, disabled states

4. Accessibility
   - WCAG 2.1 AA contrast ratios
   - Touch target sizes (>=44x44px)
   - Focus indicators visibility

Output format:
- Summary (design decisions + rationale) — compact for implementation
- Full spec → .ksk/artifact/design-<ts>.md" -y --output-format text 2>/dev/null
```

### Fallback (Gemini unavailable)

```bash
codex exec "Generate design tokens and component specifications for this UI description.

## Requirements
<describe the UI based on available information>

## Output Format (IMPORTANT)
1. Summary (key design decisions) — this is ALL Sonnet reads
2. Details → save to .ksk/artifact/design-<ts>.md" --full-auto 2>/dev/null
```

### Phase 2: Build — Sonnet

Based on design specification:
- Read design artifact for detailed tokens/values
- Implement components following the spec exactly
- Use existing project design system if available
- Ensure responsive behavior

### Phase 3: Verify — Gemini UX/Visual QA (max 3 rounds)

```bash
gemini -p "@/result.png @reference.png
UX and Visual QA:

1. Visual Fidelity (0-100): Does result match design spec?
   - Color accuracy: tokens match spec?
   - Typography: correct fonts, sizes, weights?
   - Spacing: padding/margins match spec?
   - Border radius: matches spec?

2. UX Quality
   - Is the visual hierarchy correct?
   - Any confusing or distracting elements?
   - Does the layout feel balanced?
   - Is text readable and scannable?
   - Are interactive elements discoverable?

3. Accessibility
   - Text contrast >= 4.5:1 (AA)
   - Touch targets >= 44x44px
   - Focus indicators visible

4. Polish
   - Any pixel-level misalignment?
   - Text truncation or overflow?
   - Image distortion or blur?
   - Inconsistent shadows or borders?

Score: N/100 | Verdict: PASS(85+) / NEEDS_WORK / FAIL" -y --output-format text 2>/dev/null
```

- Score >= 85 → Complete
- Score < 85 → Apply specific fixes from QA, repeat Phase 2-3
- After 3 rounds → Report remaining issues to user

## Error Handling
- Gemini returns empty → fallback to Codex for text-based design analysis
- Neither CLI available → Sonnet implements based on best judgment, inform user
- Rate limited → proceed without visual QA, suggest manual review

## Verify Isolation
- Visual QA 프롬프트에 Phase 1의 디자인 결정 이유를 포함하지 마세요
- 결과 이미지와 참조 이미지만 비교하세요
- 편향 없는 객관적 시각 평가여야 합니다

Task: {{ARGUMENTS}}
