---
name: product-strategist
description: >
  Strategic product leadership toolkit for Head of Product including OKR cascade
  generation, market analysis, vision setting, and team scaling. Use for
  strategic planning, goal alignment, competitive analysis, and organizational
  design.
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: product
  domain: product-strategy
  updated: 2026-03-31
  tags: [product-strategy, market-analysis, competitive-analysis, positioning]
---
# Product Strategist

Strategic toolkit for Head of Product to drive vision, alignment, and organizational excellence.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Core Capabilities](#core-capabilities)
- [Workflow: Strategic Planning Session](#workflow-strategic-planning-session)
- [OKR Cascade Generator](#okr-cascade-generator)
  - [Usage](#usage)
  - [Configuration Options](#configuration-options)
  - [Input/Output Examples](#inputoutput-examples)
- [Reference Documents](#reference-documents)

---

## Quick Start

### Generate OKRs for Your Team

```bash
# Growth strategy with default teams
python scripts/okr_cascade_generator.py growth

# Retention strategy with custom teams
python scripts/okr_cascade_generator.py retention --teams "Engineering,Design,Data"

# Revenue strategy with 40% product contribution
python scripts/okr_cascade_generator.py revenue --contribution 0.4

# Export as JSON for integration
python scripts/okr_cascade_generator.py growth --json > okrs.json
```

---

## Core Capabilities

| Capability | Description | Tool |
|------------|-------------|------|
| **OKR Cascade** | Generate aligned OKRs from company to team level | `okr_cascade_generator.py` |
| **Alignment Scoring** | Measure vertical and horizontal alignment | Built into generator |
| **Strategy Templates** | 5 pre-built strategy types | Growth, Retention, Revenue, Innovation, Operational |
| **Team Configuration** | Customize for your org structure | `--teams` flag |

---

## Workflow: Strategic Planning Session

A step-by-step guide for running a quarterly strategic planning session.

### Step 1: Define Strategic Focus

Choose the primary strategy type based on company priorities:

| Strategy | When to Use |
|----------|-------------|
| **Growth** | Scaling user base, market expansion |
| **Retention** | Reducing churn, improving LTV |
| **Revenue** | Increasing ARPU, new monetization |
| **Innovation** | Market differentiation, new capabilities |
| **Operational** | Improving efficiency, scaling operations |

See `references/strategy_types.md` for detailed guidance on each strategy.

### Step 2: Gather Input Metrics

Collect current state metrics to inform OKR targets:

```bash
# Example metrics JSON
{
  "current": 100000,      # Current MAU
  "target": 150000,       # Target MAU
  "current_nps": 40,      # Current NPS
  "target_nps": 60        # Target NPS
}
```

### Step 3: Configure Team Structure

Define the teams that will receive cascaded OKRs:

```bash
# Default teams
python scripts/okr_cascade_generator.py growth

# Custom teams for your organization
python scripts/okr_cascade_generator.py growth --teams "Core,Platform,Mobile,AI"
```

### Step 4: Generate OKR Cascade

Run the generator to create aligned OKRs:

```bash
python scripts/okr_cascade_generator.py growth --contribution 0.3
```

### Step 5: Review Alignment Scores

Check the alignment scores in the output:

| Score | Target | Action |
|-------|--------|--------|
| Vertical Alignment | >90% | Ensure all objectives link to parent |
| Horizontal Alignment | >75% | Check for team coordination |
| Coverage | >80% | Validate all company OKRs are addressed |
| Balance | >80% | Redistribute if one team is overloaded |
| **Overall** | **>80%** | Good alignment; <60% needs restructuring |

### Step 6: Refine and Validate

Before finalizing:

- [ ] Review generated objectives with stakeholders
- [ ] Adjust team assignments based on capacity
- [ ] Validate contribution percentages are realistic
- [ ] Ensure no conflicting objectives across teams
- [ ] Set up tracking cadence (bi-weekly check-ins)

### Step 7: Export and Track

Export OKRs for your tracking system:

```bash
# JSON for tools like Lattice, Ally, Workboard
python scripts/okr_cascade_generator.py growth --json > q1_okrs.json
```

---

## PESTEL Analysis Framework

Evaluate macro-environment forces that impact product strategy. PESTEL is a decision lens, not a checklist -- use it to inform roadmap decisions, identify threats before they materialize, and spot opportunities competitors miss.

### When to Use

- Annual/quarterly strategic planning sessions.
- Entering a new market or geography.
- Evaluating regulatory or economic changes that affect your product.
- Pre-investment analysis for new product lines.

### PESTEL Template

```markdown
## PESTEL Analysis

**Product/Company:** [Name]
**Analysis Purpose:** [Decision this analysis informs]
**Time Horizon:** [e.g., 12 months, 3 years]
**Geography/Scope:** [e.g., US, EU, Global]

### 1. Political Factors
| Factor | Impact | Opp/Threat | Product Implication |
|---|---|---|---|
| Government policies | | | |
| Political stability | | | |
| Trade regulations | | | |
| Taxation policy | | | |

### 2. Economic Factors
| Factor | Impact | Opp/Threat | Product Implication |
|---|---|---|---|
| Economic growth | | | |
| Inflation rate | | | |
| Exchange rates | | | |
| Consumer spending | | | |

### 3. Social Factors
| Factor | Impact | Opp/Threat | Product Implication |
|---|---|---|---|
| Demographics | | | |
| Cultural trends | | | |
| Lifestyle changes | | | |
| Consumer attitudes | | | |

### 4. Technological Factors
| Factor | Impact | Opp/Threat | Product Implication |
|---|---|---|---|
| Tech advancements | | | |
| R&D activity | | | |
| Automation | | | |
| Digital transformation | | | |

### 5. Environmental Factors
| Factor | Impact | Opp/Threat | Product Implication |
|---|---|---|---|
| Climate change | | | |
| Sustainability | | | |
| Resource scarcity | | | |
| Environmental regs | | | |

### 6. Legal Factors
| Factor | Impact | Opp/Threat | Product Implication |
|---|---|---|---|
| Compliance requirements | | | |
| IP rights | | | |
| Employment laws | | | |
| Health & safety regs | | | |

### Strategic Synthesis
- **Top 3 Opportunities:** [List]
- **Top 3 Threats:** [List]
- **Strategic Implications for Product:** [List]

### Assumptions to Validate
- [Assumption 1]
- [Assumption 2]
```

### Next Steps After PESTEL

1. Generate a mitigation and monitoring plan (Recommended)
2. Convert into a one-page executive risk brief
3. Generate scenario planning for best/base/worst case
4. Map top threats into roadmap guardrails

---

## TAM-SAM-SOM Market Sizing

Estimate market size for product opportunities using Total Addressable Market, Serviceable Available Market, and Serviceable Obtainable Market analysis.

### When to Use

- Evaluating new product or feature investment.
- Preparing investor or board presentations.
- Comparing market opportunities across product lines.
- Go-to-market planning and resource allocation.

### Market Sizing Framework

#### Step 1: Define the Problem Space

Describe the problem your product solves. Be specific about the job-to-be-done, not the product category.

#### Step 2: Define Geographic Scope

Specify the geographic region (e.g., US, Europe, Global) and relevant data sources:

| Region | Primary Data Sources |
|---|---|
| US | Census Bureau, BLS, industry trade orgs |
| Europe | Eurostat, local statistical agencies |
| Global | World Bank, IMF, global industry reports |

#### Step 3: Identify Industry Segments

What specific industry or market segments does this problem relate to?

#### Step 4: Define Customer Profile

Who are the potential customers? Define by problem characteristics, not demographics.

### TAM-SAM-SOM Template

```markdown
## Market Sizing Analysis

**Problem Space:** [Description]
**Geographic Region:** [Scope]
**Industry Segments:** [Relevant segments]
**Customer Profile:** [Who is affected]

### Total Addressable Market (TAM)
- **Description:** The total market demand for the problem space
- **Population Estimate:** [Number of potential users/organizations]
- **Market Size Estimate:** $[Annual revenue opportunity]
- **Methodology:** [Top-down from industry reports / Bottom-up from customer count]
- **Data Sources:** [List sources]

### Serviceable Available Market (SAM)
- **Segment of TAM:** [The portion you can realistically serve]
- **Filters Applied:** [Geography, segment, capability constraints]
- **Population Estimate:** [Number]
- **Market Size Estimate:** $[Amount]
- **SAM as % of TAM:** [Percentage]

### Serviceable Obtainable Market (SOM)
- **Realistically Capturable:** [What you can win in 1-3 years]
- **Competitive Position:** [Your share vs. alternatives]
- **Population Estimate:** [Number]
- **Market Size Estimate:** $[Amount]
- **SOM as % of SAM:** [Percentage]

### Assumptions & Risks
- [Key assumption about market size]
- [Key assumption about capture rate]
- [Risk that could shrink the market]
```

### Market Sizing Tips

- **Top-down:** Start from industry reports, narrow by filters. Good for ballpark estimates.
- **Bottom-up:** Count potential customers, multiply by expected revenue per customer. More credible for investors.
- **Triangulate:** Use both methods and reconcile. Significant gaps indicate wrong assumptions.
- SOM is typically 1-5% of SAM for startups, 10-20% for established companies in year 1.

---

## OKR Cascade Generator

Automatically cascades company OKRs down to product and team levels with alignment tracking.

### Usage

```bash
python scripts/okr_cascade_generator.py [strategy] [options]
```

**Strategies:**
- `growth` - User acquisition and market expansion
- `retention` - Customer value and churn reduction
- `revenue` - Revenue growth and monetization
- `innovation` - Product differentiation and leadership
- `operational` - Efficiency and organizational excellence

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `--teams`, `-t` | Comma-separated team names | Growth,Platform,Mobile,Data |
| `--contribution`, `-c` | Product contribution to company OKRs (0-1) | 0.3 (30%) |
| `--json`, `-j` | Output as JSON instead of dashboard | False |
| `--metrics`, `-m` | Metrics as JSON string | Sample metrics |

**Examples:**

```bash
# Custom teams
python scripts/okr_cascade_generator.py retention \
  --teams "Engineering,Design,Data,Growth"

# Higher product contribution
python scripts/okr_cascade_generator.py revenue --contribution 0.4

# Full customization
python scripts/okr_cascade_generator.py innovation \
  --teams "Core,Platform,ML" \
  --contribution 0.5 \
  --json
```

### Input/Output Examples

#### Example 1: Growth Strategy (Dashboard Output)

**Command:**
```bash
python scripts/okr_cascade_generator.py growth
```

**Output:**
```
============================================================
OKR CASCADE DASHBOARD
Quarter: Q1 2025
Strategy: GROWTH
Teams: Growth, Platform, Mobile, Data
Product Contribution: 30%
============================================================

🏢 COMPANY OKRS

📌 CO-1: Accelerate user acquisition and market expansion
   └─ CO-1-KR1: Increase MAU from 100000 to 150000
   └─ CO-1-KR2: Achieve 150000% MoM growth rate
   └─ CO-1-KR3: Expand to 150000 new markets

📌 CO-2: Achieve product-market fit in new segments
   └─ CO-2-KR1: Reduce CAC by 150000%
   └─ CO-2-KR2: Improve activation rate to 150000%
   └─ CO-2-KR3: Increase MAU from 100000 to 150000

📌 CO-3: Build sustainable growth engine
   └─ CO-3-KR1: Achieve 150000% MoM growth rate
   └─ CO-3-KR2: Expand to 150000 new markets
   └─ CO-3-KR3: Reduce CAC by 150000%

🚀 PRODUCT OKRS

📌 PO-1: Build viral product features and market expansion
   ↳ Supports: CO-1
   └─ PO-1-KR1: Increase product MAU from 100000 to 45000.0
   └─ PO-1-KR2: Achieve 45000.0% feature adoption rate

📌 PO-2: Validate product hypotheses in new segments
   ↳ Supports: CO-2
   └─ PO-2-KR1: Reduce product onboarding efficiency by 45000.0%
   └─ PO-2-KR2: Improve activation rate to 45000.0%

📌 PO-3: Create product-led growth loops engine
   ↳ Supports: CO-3
   └─ PO-3-KR1: Achieve 45000.0% feature adoption rate
   └─ PO-3-KR2: Expand to 45000.0 new markets

👥 TEAM OKRS

Growth Team:
  📌 GRO-1: Build viral product features through acquisition and activation
     └─ GRO-1-KR1: [Growth] Increase product MAU from 100000 to 11250.0
     └─ GRO-1-KR2: [Growth] Achieve 11250.0% feature adoption rate

Platform Team:
  📌 PLA-1: Build viral product features through infrastructure and reliability
     └─ PLA-1-KR1: [Platform] Increase product MAU from 100000 to 11250.0
     └─ PLA-1-KR2: [Platform] Achieve 11250.0% feature adoption rate


📊 ALIGNMENT MATRIX

Company → Product → Teams
----------------------------------------

CO-1
  ├─ PO-1
    └─ GRO-1 (Growth)
    └─ PLA-1 (Platform)

CO-2
  ├─ PO-2

CO-3
  ├─ PO-3


🎯 ALIGNMENT SCORES
----------------------------------------
✓ Vertical Alignment: 100.0%
! Horizontal Alignment: 75.0%
✓ Coverage: 100.0%
✓ Balance: 97.5%
✓ Overall: 94.0%

✅ Overall alignment is GOOD (≥80%)
```

#### Example 2: JSON Output

**Command:**
```bash
python scripts/okr_cascade_generator.py retention --json
```

**Output (truncated):**
```json
{
  "quarter": "Q1 2025",
  "strategy": "retention",
  "company": {
    "level": "Company",
    "objectives": [
      {
        "id": "CO-1",
        "title": "Create lasting customer value and loyalty",
        "owner": "CEO",
        "key_results": [
          {
            "id": "CO-1-KR1",
            "title": "Improve retention from 100000% to 150000%",
            "current": 100000,
            "target": 150000
          }
        ]
      }
    ]
  },
  "product": {
    "level": "Product",
    "contribution": 0.3,
    "objectives": [...]
  },
  "teams": [...],
  "alignment_scores": {
    "vertical_alignment": 100.0,
    "horizontal_alignment": 75.0,
    "coverage": 100.0,
    "balance": 97.5,
    "overall": 94.0
  },
  "config": {
    "teams": ["Growth", "Platform", "Mobile", "Data"],
    "product_contribution": 0.3
  }
}
```

See `references/examples/sample_growth_okrs.json` for a complete example.

---

## Reference Documents

| Document | Description |
|----------|-------------|
| `references/okr_framework.md` | OKR methodology, writing guidelines, alignment scoring |
| `references/strategy_types.md` | Detailed breakdown of all 5 strategy types with examples |
| `references/examples/sample_growth_okrs.json` | Complete sample output for growth strategy |

---

## Best Practices

### OKR Cascade

- Limit to 3-5 objectives per level
- Each objective should have 3-5 key results
- Key results must be measurable with current and target values
- Validate parent-child relationships before finalizing

### Alignment Scoring

- Target >80% overall alignment
- Investigate any score below 60%
- Balance scores ensure no team is overloaded
- Horizontal alignment prevents conflicting goals

### Team Configuration

- Configure teams to match your actual org structure
- Adjust contribution percentages based on team size
- Platform/Infrastructure teams often support all objectives
- Specialized teams (ML, Data) may only support relevant objectives

---

## Quick Reference

```bash
# Common commands
python scripts/okr_cascade_generator.py growth               # Default growth
python scripts/okr_cascade_generator.py retention            # Retention focus
python scripts/okr_cascade_generator.py revenue -c 0.4       # 40% contribution
python scripts/okr_cascade_generator.py growth --json        # JSON export
python scripts/okr_cascade_generator.py growth -t "A,B,C"    # Custom teams
```

---

## Tool Reference

### okr_cascade_generator.py

Generates aligned OKRs from company strategy down to product and team levels with alignment scoring.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `strategy` | positional | growth | Strategy type: `growth`, `retention`, `revenue`, `innovation`, `operational` |
| `--teams`, `-t` | string | Growth,Platform,Mobile,Data | Comma-separated team names |
| `--contribution`, `-c` | float | 0.3 | Product contribution to company OKRs (0-1) |
| `--json`, `-j` | flag | False | Output as JSON instead of dashboard |
| `--metrics`, `-m` | string | sample metrics | Metrics as JSON string |

**Alignment scores generated:**
- Vertical alignment: How well each level supports the level above (target: >90%)
- Horizontal alignment: How well teams coordinate with each other (target: >75%)
- Coverage: What percentage of company OKRs are addressed by product (target: >80%)
- Balance: Whether work is evenly distributed across teams (target: >80%)
- Overall: Weighted composite score (target: >80%)

```bash
python scripts/okr_cascade_generator.py growth
python scripts/okr_cascade_generator.py retention --teams "Engineering,Design,Data,Growth"
python scripts/okr_cascade_generator.py revenue --contribution 0.4 --json
python scripts/okr_cascade_generator.py innovation --metrics '{"current": 50000, "target": 100000}'
```

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Overall alignment score <60% | Too many orphaned objectives without parent link | Reduce objective count; ensure every product OKR maps to a company OKR |
| Horizontal alignment low | Teams working on isolated goals | Identify shared objectives; add cross-team key results |
| Balance score low | One team overloaded with objectives | Redistribute objectives; adjust team contribution percentages |
| Key results not measurable | Template uses vague language | Replace every KR with specific current/target numbers and timeframe |
| Contribution percentage unrealistic | Product team cannot own 50%+ of company KR | Calibrate with other functions (sales, marketing); 25-35% is typical |
| Teams report OKR fatigue | Too many objectives per team | Limit to 3 objectives and 3-5 key results per team per quarter |
| OKRs disconnected from daily work | Sprint work not mapped to OKRs | Link every epic/story to a team-level key result |

---

## Success Criteria

| Criterion | Target | How to Measure |
|-----------|--------|----------------|
| Overall alignment score | >80% | okr_cascade_generator alignment output |
| OKR completion rate | >70% of KRs hit target | End-of-quarter KR progress review |
| Cascade coverage | 100% of company OKRs have product children | Coverage score in alignment output |
| Planning velocity | <4 hours from strategy to team OKRs | Time from generator run to stakeholder approval |
| Quarterly check-in cadence | Bi-weekly progress reviews | Count of check-in meetings held |
| OKR quality | All KRs have current + target values | Audit key results for measurability |
| Team buy-in | >80% of teams confirm OKR relevance | Survey after OKR rollout |

---

## Scope & Limitations

**In scope:**
- Company-to-team OKR cascade generation
- Five strategy templates (growth, retention, revenue, innovation, operational)
- Alignment scoring across vertical and horizontal dimensions
- Custom team structure configuration
- Contribution percentage modeling
- JSON export for OKR tracking tools

**Out of scope:**
- OKR progress tracking over time (use Lattice, Ally, or Workboard)
- Automated metric collection (connect to analytics platforms)
- Individual contributor OKR generation
- Cross-functional OKRs beyond product (sales, marketing, etc.)
- Historical OKR analysis and trend reporting
- Board-level strategic planning frameworks

---

## Integration Points

| Tool / Platform | Integration Method | Use Case |
|-----------------|-------------------|----------|
| Lattice / Ally / Workboard | `--json` export | Import OKRs into tracking platform |
| Notion / Confluence | Human-readable dashboard output | Document quarterly OKRs for team access |
| Google Sheets | JSON-to-spreadsheet conversion | Executive OKR summary |
| product-manager-toolkit | OKRs inform RICE reach/impact values | Connect objectives to feature prioritization |
| agile-product-owner | Team OKRs guide epic selection | Sprint planning aligned with quarterly goals |
| Slack | Dashboard output summary | Async OKR rollout communication |
