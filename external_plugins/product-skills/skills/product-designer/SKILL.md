---
name: product-designer
description: >
  Expert product design covering UI/UX design, design systems, prototyping, user
  research, and design thinking. Use when creating user journey maps, building
  wireframes, defining design tokens and component systems, planning usability
  tests, or establishing design principles for a product.
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: product-design
  domain: product-design
  updated: 2026-03-31
  tags: [design, ux, ui, figma, prototyping, design-systems]
---
# Product Designer

The agent operates as a senior product designer, delivering user-centered design solutions spanning UX research, UI design, design systems, prototyping, and usability testing.

## Workflow

1. **Discover** - Research user needs through interviews, analytics, and competitive analysis. Create user journey maps and identify pain points. Checkpoint: problem statement is validated by at least 3 user data points.
2. **Define** - Synthesize findings into a clear problem statement and design requirements. Build information architecture (card sorting, site maps). Checkpoint: IA has been validated via card sort or tree test.
3. **Develop** - Ideate solutions through sketching and wireframing. Build prototypes at appropriate fidelity. Checkpoint: prototype covers the complete happy path plus one error state.
4. **Test** - Run usability tests with 5-8 participants. Measure task completion rate, time on task, error rate, and SUS score. Checkpoint: all critical usability issues are documented with severity ratings.
5. **Deliver** - Refine designs based on test findings. Prepare dev handoff with design tokens, component specs, and interaction documentation. Checkpoint: engineering has confirmed feasibility of all interactions.

## Design Sprint (5-Day Format)

| Day | Activity | Output |
|-----|----------|--------|
| Monday | Map problem, interview experts | Challenge map, target area |
| Tuesday | Sketch solutions, Crazy 8s | Solution sketches |
| Wednesday | Decide, storyboard | Testable hypothesis |
| Thursday | Build prototype | Realistic clickable prototype |
| Friday | Test with 5 users | Validated/invalidated hypothesis |

## User Journey Map Template

```
PERSONA: Sarah, Product Manager, goal: find analytics insights fast

STAGE:      AWARENESS    CONSIDER     PURCHASE     ONBOARD      RETAIN
Actions:    Searches     Compares     Signs up     Configures   Uses daily
Touchpoint: Google       Website      Checkout     Setup wizard App
Emotion:    Frustrated   Curious      Anxious      Hopeful      Satisfied
Pain point: Too many     Hard to      Complex      Slow setup   Missing
            options      compare      pricing                   features
Opportunity: SEO content  Comparison   Simplify     Quick-start  Feature
                         tool         flow         template     education
```

## Information Architecture

**Card Sorting Methods:**
- Open sort: users create their own categories
- Closed sort: users place items into predefined categories
- Hybrid: combination approach

**Example Site Map:**
```
Home
+-- Products
|   +-- Category A
|   |   +-- Product 1
|   |   +-- Product 2
|   +-- Category B
+-- About
|   +-- Team
|   +-- Careers
+-- Resources
|   +-- Blog
|   +-- Help Center
+-- Account
    +-- Profile
    +-- Settings
```

## UI Design Foundations

### Design Principles

1. **Hierarchy** - Visual weight guides attention via size, color, and contrast
2. **Consistency** - Reuse patterns and components; maintain predictable interactions
3. **Feedback** - Acknowledge every user action; show system status and loading states
4. **Accessibility** - 4.5:1 color contrast minimum, focus indicators, screen reader support

### Design Token System

```css
/* Color tokens */
--color-primary-500: #3b82f6;
--color-primary-600: #2563eb;
--color-gray-50: #f9fafb;
--color-gray-900: #111827;
--color-success: #10b981;
--color-warning: #f59e0b;
--color-error: #ef4444;

/* Typography scale */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */

/* Spacing (4px base unit) */
--space-1: 0.25rem;    /* 4px */
--space-2: 0.5rem;     /* 8px */
--space-4: 1rem;       /* 16px */
--space-6: 1.5rem;     /* 24px */
--space-8: 2rem;       /* 32px */
```

## Component Structure

```
Button/
+-- Variants: Primary, Secondary, Tertiary, Destructive
+-- Sizes: Small (32px), Medium (40px), Large (48px)
+-- States: Default, Hover, Active, Focus, Disabled, Loading
+-- Anatomy: [Leading Icon] Label [Trailing Icon]
```

### Component Design Tokens (JSON)

```json
{
  "color": {
    "primary": {"50": {"value": "#eff6ff"}, "500": {"value": "#3b82f6"}},
    "semantic": {"success": {"value": "{color.green.500}"}, "error": {"value": "{color.red.500}"}}
  },
  "spacing": {"xs": {"value": "4px"}, "sm": {"value": "8px"}, "md": {"value": "16px"}},
  "borderRadius": {"sm": {"value": "4px"}, "md": {"value": "8px"}, "full": {"value": "9999px"}}
}
```

## Example: Usability Test Plan

```markdown
# Usability Test: New Checkout Flow

## Objectives
- Validate that users can complete purchase in < 3 minutes
- Identify friction points in address and payment steps

## Participants
- 6 users (3 new, 3 returning)
- Mix of desktop and mobile

## Tasks
1. "Find a laptop under $1,000 and add it to your cart" (browse + add)
2. "Complete the purchase using a credit card" (checkout flow)
3. "Change the shipping address on your order" (post-purchase edit)

## Success Criteria
| Task | Completion Target | Time Target |
|------|-------------------|-------------|
| Browse + Add | 100% | < 60s |
| Checkout | 90%+ | < 180s |
| Edit address | 80%+ | < 90s |

## Metrics
- Task completion rate
- Time on task
- Error count per task
- System Usability Scale (SUS) score (target: 68+)
```

## Prototype Fidelity Guide

| Fidelity | Purpose | Tools | Timeline |
|----------|---------|-------|----------|
| Paper | Quick exploration | Paper, pen | Minutes |
| Low-fi | Flow validation | Figma, Sketch | Hours |
| Mid-fi | Usability testing | Figma | Days |
| High-fi | Dev handoff, final testing | Figma | Days-Weeks |

## Scripts

```bash
# Design token generator
python scripts/token_generator.py --source tokens.json --output css/

# Accessibility checker
python scripts/a11y_checker.py --url https://example.com

# Asset exporter
python scripts/asset_export.py --figma-file FILE_ID --format svg,png

# Design QA report
python scripts/design_qa.py --spec spec.figma --impl https://staging.example.com
```

## Reference Materials

- `references/design_principles.md` - Core design principles
- `references/component_library.md` - Component guidelines
- `references/accessibility.md` - Accessibility checklist
- `references/research_methods.md` - Research techniques

---

## Tool Reference

### design_critique.py

Evaluates a UI design against Nielsen's 10 Usability Heuristics and accessibility standards. Generates a structured critique report with severity ratings, compliance scores, and prioritized improvement recommendations.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--checklist` | flag | - | Generate empty checklist for evaluation |
| `--answers` | string | - | Path to completed checklist JSON file |
| `--json` | flag | False | Output as JSON |

```bash
python scripts/design_critique.py --checklist
python scripts/design_critique.py --checklist --json > checklist.json
python scripts/design_critique.py --answers completed_checklist.json
python scripts/design_critique.py --answers completed_checklist.json --json
```

### journey_mapper.py

Creates structured user journey maps with emotion curves, pain point identification, and opportunity analysis. Includes pre-built templates for SaaS, e-commerce, and mobile app journeys.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--template`, `-t` | choice | - | Pre-built template: `saas`, `ecommerce`, `mobile_app` |
| `--stages`, `-s` | string | - | Path to custom stages JSON file |
| `--json` | flag | False | Output as JSON |

```bash
python scripts/journey_mapper.py --template saas
python scripts/journey_mapper.py --template ecommerce --json
python scripts/journey_mapper.py --stages custom_journey.json
```

### usability_scorer.py

Calculates System Usability Scale (SUS) scores and task performance metrics from usability test data. Provides individual and aggregate analysis with grade interpretation and benchmarking.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `action` | positional | - | "sample" to create sample CSV files |
| `--sus-responses` | string | - | CSV with SUS responses (participant, q1-q10) |
| `--task-data` | string | - | CSV with task data (participant, task, completed, time_seconds, errors) |
| `--json` | flag | False | Output as JSON |

```bash
python scripts/usability_scorer.py sample
python scripts/usability_scorer.py --sus-responses responses.csv
python scripts/usability_scorer.py --task-data tasks.csv
python scripts/usability_scorer.py --sus-responses responses.csv --task-data tasks.csv --json
```

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| SUS score below 68 (benchmark) | Significant usability issues | Focus on critical severity findings from design_critique first |
| Low task completion rate (<80%) | Task flow too complex or unclear | Simplify flow; add progressive disclosure; reduce steps |
| Users cannot find features | Poor information architecture | Conduct card sorting; redesign navigation; add search |
| High error rate on forms | Insufficient validation and guidance | Add inline validation, smart defaults, and contextual help |
| Inconsistent design across screens | Missing or ignored design system | Audit with design_critique; enforce token usage |
| Usability test participants are unrepresentative | Poor recruitment criteria | Screen for target persona match; mix new and returning users |
| Journey map emotions are flat | Insufficient research data | Conduct deeper interviews; observe real usage sessions |

---

## Success Criteria

| Criterion | Target | How to Measure |
|-----------|--------|----------------|
| SUS score | >68 (industry average), target >80 | usability_scorer aggregate score |
| Task completion rate | >85% for core flows | usability_scorer task metrics |
| Time on task | <2x expected duration | usability_scorer avg_time_seconds |
| Design critique compliance | >80% checklist pass rate | design_critique compliance_score |
| Accessibility compliance | WCAG AA on all screens | design_critique accessibility section |
| Journey map coverage | All key personas mapped | Count of completed journey maps |
| Usability test cadence | Test every sprint or release | Count of tests per quarter |

---

## Scope & Limitations

**In scope:**
- Heuristic evaluation and design critique
- User journey mapping with emotion curves
- Usability test scoring (SUS and task metrics)
- Design sprint facilitation structure
- Information architecture planning
- Prototype fidelity guidance
- Accessibility checkpoint evaluation

**Out of scope:**
- Automated visual regression testing (use Chromatic/Percy)
- Real-time analytics dashboards (use Amplitude/Mixpanel)
- Figma file manipulation or asset export (use Figma API)
- Eye tracking or biometric analysis
- A/B test implementation (see ab-test-setup skill)
- Design token generation (see ui-design-system or design-system-lead skills)

---

## Integration Points

| Tool / Platform | Integration Method | Use Case |
|-----------------|-------------------|----------|
| Figma | Journey map and critique findings as design specs | Translate research into design changes |
| Maze / UserTesting | Export task data CSV for usability_scorer | Score test results from remote testing platforms |
| Dovetail / Condens | Export interview themes for journey_mapper | Build journey maps from research repositories |
| Jira / Linear | design_critique JSON priorities as tickets | Track usability improvements in sprint backlog |
| Notion / Confluence | Human-readable output from all tools | Document research findings and design decisions |
| Miro / FigJam | journey_mapper JSON output | Collaborative journey map workshops |
