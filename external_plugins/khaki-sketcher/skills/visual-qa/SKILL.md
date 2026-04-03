---
name: visual-qa
description: Screenshot comparison and visual quality assessment via Gemini. Use for before/after checks and pixel-level QA.
---

# Visual QA

Single-pass visual comparison: Verify (Gemini comparison) → Report.

## Usage

```
/ksk:visual-qa <description of what to compare, with image paths>
```

## Step 1: Identify Images

Get the before/after image paths (absolute or relative to project root).

## Step 2: Verify — Gemini Visual Comparison

```bash
gemini -p "@/path/to/before.png @/path/to/after.png
Compare these screenshots thoroughly:

1. Visual Fidelity
   - List ALL visual differences, classify: intentional / regression / side-effect
   - Color accuracy: do hex values match?
   - Typography: font sizes, weights, line heights
   - Spacing: padding, margins, grid alignment (8px grid)
   - Border radius consistency

2. UX Quality
   - Is visual hierarchy correct?
   - Any confusing or distracting elements?
   - Does the layout feel balanced?
   - Is text readable and scannable?
   - Are interactive elements discoverable?

3. Accessibility
   - Text contrast >= 4.5:1 (WCAG 2.1 AA)
   - Touch targets >= 44x44px
   - Focus indicators visible

4. Polish
   - Pixel-level misalignment?
   - Text truncation or overflow?
   - Image distortion or blur?

## Output Format (IMPORTANT)
1. Summary (score + verdict) — this is ALL Sonnet reads
2. Detailed Comparison → save to .ksk/artifact/visual-qa-<ts>.md

Score: N/100 | Verdict: PASS(85+) / NEEDS_WORK(60-84) / FAIL(<60)

Differences:
1. [location] - [description] - [intentional/regression]

Suggestions:
1. [specific actionable fix]" -y --output-format text 2>/dev/null
```

Save result to `.ksk/artifact/visual-qa-<ts>.md`. Sonnet reads ONLY the summary.

### Fallback (Gemini unavailable)

```bash
codex exec "Compare these two UI descriptions and identify all differences.

## Before
<describe or paste relevant code for before state>

## After
<describe or paste relevant code for after state>

## Output Format (IMPORTANT)
1. Summary (score + verdict)
2. Details → save to .ksk/artifact/visual-qa-<ts>.md" --full-auto 2>/dev/null
```

## Step 3: Report

Return the structured verdict to the user. This skill does NOT modify code.

```
## Visual QA Report
**Score**: N/100
**Verdict**: [PASS|NEEDS_WORK|FAIL]
**Differences**: N found (M intentional, K regression)
**Artifact**: .ksk/artifact/visual-qa-<ts>.md
```

## Error Handling
- Gemini returns empty → fallback to Codex for text-based comparison
- Neither CLI available → Sonnet compares code diff directly, note lack of visual verification
- Rate limited → proceed without external QA, suggest manual visual review

Task: {{ARGUMENTS}}
