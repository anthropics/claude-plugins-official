---
name: campaign-analytics
description: >
  Analyzes campaign performance with multi-touch attribution, funnel conversion,
  and ROI calculation for marketing optimization
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: marketing
  domain: campaign-analytics
  updated: 2026-02-06
  python-tools: attribution_analyzer.py, funnel_analyzer.py, campaign_roi_calculator.py
  tech-stack: marketing-analytics, attribution-modeling
---
# Campaign Analytics

Production-grade campaign performance analysis with multi-touch attribution modeling, funnel conversion analysis, and ROI calculation. Three Python CLI tools provide deterministic, repeatable analytics using standard library only -- no external dependencies, no API calls, no ML models.

---

## Table of Contents

- [Capabilities](#capabilities)
- [Input Requirements](#input-requirements)
- [Output Formats](#output-formats)
- [How to Use](#how-to-use)
- [Scripts](#scripts)
- [Reference Guides](#reference-guides)
- [Best Practices](#best-practices)
- [Limitations](#limitations)

---

## Capabilities

- **Multi-Touch Attribution**: Five attribution models (first-touch, last-touch, linear, time-decay, position-based) with configurable parameters
- **Funnel Conversion Analysis**: Stage-by-stage conversion rates, drop-off identification, bottleneck detection, and segment comparison
- **Campaign ROI Calculation**: ROI, ROAS, CPA, CPL, CAC metrics with industry benchmarking and underperformance flagging
- **A/B Test Support**: Templates for structured A/B test documentation and analysis
- **Channel Comparison**: Cross-channel performance comparison with normalized metrics
- **Executive Reporting**: Ready-to-use templates for campaign performance reports

---

## Input Requirements

All scripts accept a JSON file as positional input argument. See `assets/sample_campaign_data.json` for complete examples.

### Attribution Analyzer

```json
{
  "journeys": [
    {
      "journey_id": "j1",
      "touchpoints": [
        {"channel": "organic_search", "timestamp": "2025-10-01T10:00:00", "interaction": "click"},
        {"channel": "email", "timestamp": "2025-10-05T14:30:00", "interaction": "open"},
        {"channel": "paid_search", "timestamp": "2025-10-08T09:15:00", "interaction": "click"}
      ],
      "converted": true,
      "revenue": 500.00
    }
  ]
}
```

### Funnel Analyzer

```json
{
  "funnel": {
    "stages": ["Awareness", "Interest", "Consideration", "Intent", "Purchase"],
    "counts": [10000, 5200, 2800, 1400, 420]
  }
}
```

### Campaign ROI Calculator

```json
{
  "campaigns": [
    {
      "name": "Spring Email Campaign",
      "channel": "email",
      "spend": 5000.00,
      "revenue": 25000.00,
      "impressions": 50000,
      "clicks": 2500,
      "leads": 300,
      "customers": 45
    }
  ]
}
```

---

## Output Formats

All scripts support two output formats via the `--format` flag:

- `--format text` (default): Human-readable tables and summaries for review
- `--format json`: Machine-readable JSON for integrations and pipelines

---

## How to Use

### Attribution Analysis

```bash
# Run all 5 attribution models
python scripts/attribution_analyzer.py campaign_data.json

# Run a specific model
python scripts/attribution_analyzer.py campaign_data.json --model time-decay

# JSON output for pipeline integration
python scripts/attribution_analyzer.py campaign_data.json --format json

# Custom time-decay half-life (default: 7 days)
python scripts/attribution_analyzer.py campaign_data.json --model time-decay --half-life 14
```

### Funnel Analysis

```bash
# Basic funnel analysis
python scripts/funnel_analyzer.py funnel_data.json

# JSON output
python scripts/funnel_analyzer.py funnel_data.json --format json
```

### Campaign ROI Calculation

```bash
# Calculate ROI metrics for all campaigns
python scripts/campaign_roi_calculator.py campaign_data.json

# JSON output
python scripts/campaign_roi_calculator.py campaign_data.json --format json
```

---

## Scripts

### 1. attribution_analyzer.py

Implements five industry-standard attribution models to allocate conversion credit across marketing channels:

| Model | Description | Best For |
|-------|-------------|----------|
| First-Touch | 100% credit to first interaction | Brand awareness campaigns |
| Last-Touch | 100% credit to last interaction | Direct response campaigns |
| Linear | Equal credit to all touchpoints | Balanced multi-channel evaluation |
| Time-Decay | More credit to recent touchpoints | Short sales cycles |
| Position-Based | 40/20/40 split (first/middle/last) | Full-funnel marketing |

### 2. funnel_analyzer.py

Analyzes conversion funnels to identify bottlenecks and optimization opportunities:

- Stage-to-stage conversion rates and drop-off percentages
- Automatic bottleneck identification (largest absolute and relative drops)
- Overall funnel conversion rate
- Segment comparison when multiple segments are provided

### 3. campaign_roi_calculator.py

Calculates comprehensive ROI metrics with industry benchmarking:

- **ROI**: Return on investment percentage
- **ROAS**: Return on ad spend ratio
- **CPA**: Cost per acquisition
- **CPL**: Cost per lead
- **CAC**: Customer acquisition cost
- **CTR**: Click-through rate
- **CVR**: Conversion rate (leads to customers)
- Flags underperforming campaigns against industry benchmarks

---

## Reference Guides

| Guide | Location | Purpose |
|-------|----------|---------|
| Attribution Models Guide | `references/attribution-models-guide.md` | Deep dive into 5 models with formulas, pros/cons, selection criteria |
| Campaign Metrics Benchmarks | `references/campaign-metrics-benchmarks.md` | Industry benchmarks by channel and vertical for CTR, CPC, CPM, CPA, ROAS |
| Funnel Optimization Framework | `references/funnel-optimization-framework.md` | Stage-by-stage optimization strategies, common bottlenecks, best practices |

---

## Best Practices

1. **Use multiple attribution models** -- No single model tells the full story. Compare at least 3 models to triangulate channel value.
2. **Set appropriate lookback windows** -- Match your time-decay half-life to your average sales cycle length.
3. **Segment your funnels** -- Always compare segments (channel, cohort, geography) to identify what drives best performance.
4. **Benchmark against your own history first** -- Industry benchmarks provide context, but your own historical data is the most relevant comparison.
5. **Run ROI analysis at regular intervals** -- Weekly for active campaigns, monthly for strategic review.
6. **Include all costs** -- Factor in creative, tooling, and labor costs alongside media spend for accurate ROI.
7. **Document A/B tests rigorously** -- Use the provided template to ensure statistical validity and clear decision criteria.

---

## Limitations

- **No statistical significance testing** -- A/B test analysis requires external tools for p-value calculations. Scripts provide descriptive metrics only.
- **Standard library only** -- No advanced statistical or data processing libraries. Suitable for most campaign sizes but not optimized for datasets exceeding 100K journeys.
- **Offline analysis** -- Scripts analyze static JSON snapshots. No real-time data connections or API integrations.
- **Single-currency** -- All monetary values assumed to be in the same currency. No currency conversion support.
- **Simplified time-decay** -- Uses exponential decay based on configurable half-life. Does not account for weekday/weekend or seasonal patterns.
- **No cross-device tracking** -- Attribution operates on provided journey data as-is. Cross-device identity resolution must be handled upstream.

---

## Typical Analysis Workflow

For a complete campaign review, run the three scripts in sequence:

```bash
# Step 1 -- Attribution: understand which channels drive conversions
python scripts/attribution_analyzer.py campaign_data.json --model time-decay

# Step 2 -- Funnel: identify where prospects drop off on the path to conversion
python scripts/funnel_analyzer.py funnel_data.json

# Step 3 -- ROI: calculate profitability and benchmark against industry standards
python scripts/campaign_roi_calculator.py campaign_data.json
```

Use attribution results to identify top-performing channels, then focus funnel analysis on those channels' segments, and finally validate ROI metrics to prioritize budget reallocation.

---

## Input Validation

Before running scripts, verify your JSON is valid and matches the expected schema. Common errors:

- **Missing required keys** (e.g., `journeys`, `funnel.stages`, `campaigns`) -- script exits with a descriptive `KeyError`
- **Mismatched array lengths** in funnel data (`stages` and `counts` must be the same length) -- raises `ValueError`
- **Non-numeric monetary values** in ROI data -- raises `TypeError`

Use `python -m json.tool your_file.json` to validate JSON syntax before passing it to any script.

## Related Skills

- **marketing-demand-acquisition**: For planning campaigns that analytics measures.
- **social-media-analyzer**: For social-specific analytics complementing cross-channel analysis.
- **marketing-strategy-pmm**: For strategic context behind campaign performance.
- **content-creator**: For optimizing content based on analytics findings.

---

## Troubleshooting

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| Attribution model shows all credit on one channel | Using first-touch or last-touch on a multi-channel funnel | Switch to linear, time-decay, or position-based attribution. Compare at least 3 models to triangulate true channel value. GA4's data-driven attribution (DDA) is the recommended default for 2026 |
| Funnel conversion rate is unrealistically high or low | Mismatched stage definitions or counts array length error | Verify that `stages` and `counts` arrays are the same length and ordered top-to-bottom (largest count first). Ensure counts represent unique users at each stage, not cumulative events |
| ROI calculator flags all campaigns as underperforming | Channel name in JSON does not match built-in benchmark keys | Use exact channel names: `email`, `paid_search`, `paid_social`, `display`, `organic_search`, `organic_social`, `referral`, `direct`. Unrecognized channels fall back to `default` benchmarks |
| Time-decay model produces unexpected credit distribution | Half-life parameter does not match your sales cycle | Set `--half-life` to approximately half your average sales cycle length. For B2B SaaS (60-90 day cycles), use `--half-life 30`. For e-commerce (1-7 day cycles), use `--half-life 3` |
| JSON parsing errors on script execution | Malformed JSON, trailing commas, or encoding issues | Validate JSON with `python -m json.tool your_file.json` before passing to any script. Ensure UTF-8 encoding and no BOM characters |
| GA4 attribution data does not match script output | Different lookback windows and model defaults | GA4 uses a 30-day lookback for acquisition and 90-day for engagement by default. DDA falls back to last-click when a key event has fewer than 400 conversions. Align your script's `--half-life` and data window to match GA4 settings |
| Campaign spend data shows zero ROI despite conversions | Revenue field missing or set to zero in input JSON | Ensure every campaign object includes a `revenue` field with actual attributed revenue. If revenue attribution is not available, use estimated values based on average deal size multiplied by customer count |

---

## Success Criteria

- **Attribution Model Coverage**: Run at least 3 attribution models per analysis cycle to triangulate channel value. Position-based (40/20/40) or GA4 data-driven attribution is recommended as primary model for hybrid PLG/sales-led motions
- **Funnel Conversion Rate**: Target overall funnel conversion (top-to-bottom) of 2-5% for B2B SaaS and 5-15% for B2C. Identify and address any single stage with >60% drop-off rate as a critical bottleneck
- **Campaign ROAS**: Achieve minimum 4:1 ROAS for paid search, 3:1 for paid social, and 30:1+ for email channels (2026 industry targets). Flag any campaign below 2:1 ROAS for immediate optimization or budget reallocation
- **Cost Per Acquisition**: Maintain blended CPA below $45 across channels (2026 B2B SaaS median). Channel-specific targets: email <$15, paid search <$50, paid social <$40, display <$75
- **UTM Compliance**: Achieve 100% UTM parameter coverage on all paid and owned media links. Use lowercase, standardized naming (GA4 is case-sensitive). Teams with standardized UTM conventions see 29% improvement in attribution accuracy
- **Analysis Cadence**: Run campaign ROI analysis weekly for active campaigns and monthly for strategic review. Update attribution models quarterly as channel mix evolves
- **Benchmark Accuracy**: All campaigns should be assessed against channel-specific benchmarks, not generic averages. The built-in benchmark tables cover CTR, ROAS, and CPA by channel with low/target/high ranges

---

## Scope & Limitations

**In Scope:**
- Multi-touch attribution modeling with 5 industry-standard models (first-touch, last-touch, linear, time-decay, position-based)
- Funnel conversion analysis with stage-by-stage metrics, bottleneck detection, and segment comparison
- Campaign ROI calculation with 10+ metrics (ROI, ROAS, CPA, CPL, CAC, CTR, CVR, CPC, CPM, lead conversion rate)
- Industry benchmarking by channel with underperformance flagging
- Portfolio-level summary with channel breakdown

**Out of Scope:**
- Real-time data connections or API integrations (scripts analyze static JSON snapshots)
- Statistical significance testing for A/B tests (descriptive metrics only; use dedicated A/B testing tools for p-value calculations)
- Cross-device identity resolution (must be handled upstream by your CDP or analytics platform)
- Currency conversion (all monetary values assumed same currency)
- Predictive modeling or forecasting (current analysis is retrospective)
- GA4 or HubSpot direct integration (export data from those platforms into JSON format for analysis)
- Datasets exceeding 100K journeys (standard library implementation, not optimized for very large datasets)

---

## Integration Points

| Integration | Purpose | How to Connect |
|-------------|---------|----------------|
| **Google Analytics 4 (GA4)** | Source of journey and conversion data | Export GA4 Exploration reports or use BigQuery export to generate journey JSON. GA4's DDA model (default in 2026) complements this skill's 5 models. Align lookback windows: GA4 defaults to 30-day acquisition / 90-day engagement |
| **HubSpot** | CRM attribution, lead scoring, deal data | Export HubSpot contact journey data with UTM parameters as JSON input. Use W-shaped (40-20-40) attribution for hybrid PLG/sales motions. Map HubSpot lifecycle stages to funnel analyzer stages |
| **UTM Parameter Standards** | Consistent campaign tagging | Enforce lowercase UTM values: `utm_source={channel}`, `utm_medium={type}`, `utm_campaign={campaign-id}`, `utm_content={variant}`, `utm_term={keyword}`. GA4 treats `Email` and `email` as separate entries |
| **social-media-analyzer skill** | Social channel performance data | Feed social media campaign metrics from `calculate_metrics.py` into `campaign_roi_calculator.py` for cross-channel ROI comparison |
| **marketing-demand-acquisition skill** | Demand gen campaign planning | Use attribution results to identify top-performing channels, then feed insights into demand gen budget allocation decisions |
| **Business intelligence tools (Looker, Tableau, Power BI)** | Dashboard visualization | Use `--format json` output from all three scripts for direct ingestion into BI tools. JSON output is structured for easy transformation |
| **Spreadsheet tools (Excel, Google Sheets)** | Manual analysis and reporting | Use `--format text` output for human-readable reports. Copy JSON output into spreadsheets for custom pivot analysis |

---

## Tool Reference

### attribution_analyzer.py

**Type:** CLI script with argparse

**Usage:**
```bash
python attribution_analyzer.py <input_file> [--model MODEL] [--half-life DAYS] [--format FORMAT]
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `input_file` | Yes | -- | Path to JSON file containing journey/touchpoint data. Must have a top-level `journeys` array |
| `--model` | No | all 5 models | Run a specific model: `first-touch`, `last-touch`, `linear`, `time-decay`, `position-based` |
| `--half-life` | No | `7.0` | Half-life in days for time-decay model. Set to ~half your average sales cycle |
| `--format` | No | `text` | Output format: `text` (human-readable tables) or `json` (machine-readable) |

**Input Schema:** `{"journeys": [{"journey_id": "str", "touchpoints": [{"channel": "str", "timestamp": "ISO-8601", "interaction": "str"}], "converted": bool, "revenue": float}]}`

**Output:** Summary statistics (total journeys, conversion rate, total revenue, channels observed) plus per-model channel credit allocation with revenue and share percentages. Cross-model comparison table when running all models.

### funnel_analyzer.py

**Type:** CLI script with argparse

**Usage:**
```bash
python funnel_analyzer.py <input_file> [--format FORMAT]
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `input_file` | Yes | -- | Path to JSON file containing funnel data. Must have `funnel` (single) or `segments` (multi-segment) key |
| `--format` | No | `text` | Output format: `text` or `json` |

**Single Funnel Input:** `{"funnel": {"stages": ["Stage1", "Stage2", ...], "counts": [10000, 5200, ...]}}`

**Multi-Segment Input:** `{"stages": ["Stage1", "Stage2", ...], "segments": {"segment_a": {"counts": [...]}, "segment_b": {"counts": [...]}}}`

**Output:** Stage-by-stage conversion rates, drop-off counts and percentages, cumulative conversion, bottleneck identification (both absolute and relative), and segment rankings when comparing multiple segments.

### campaign_roi_calculator.py

**Type:** CLI script with argparse

**Usage:**
```bash
python campaign_roi_calculator.py <input_file> [--format FORMAT]
```

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `input_file` | Yes | -- | Path to JSON file containing campaign data. Must have a top-level `campaigns` array |
| `--format` | No | `text` | Output format: `text` or `json` |

**Input Schema:** `{"campaigns": [{"name": "str", "channel": "str", "spend": float, "revenue": float, "impressions": int, "clicks": int, "leads": int, "customers": int}]}`

**Recognized Channels for Benchmarking:** `email`, `paid_search`, `paid_social`, `display`, `organic_search`, `organic_social`, `referral`, `direct`. Unrecognized channels use `default` benchmarks.

**Calculated Metrics:** ROI %, ROAS, CPA, CPL, CAC, CTR %, CVR % (lead-to-customer), CPC, CPM, click-to-lead rate %, profit. Each campaign assessed against channel-specific benchmarks (low/target/high) with performance flags and recommendations.

**Output:** Portfolio summary (totals, blended metrics, top performer, flagged campaigns, channel breakdown) plus per-campaign detail with benchmark assessments, warning flags, and actionable recommendations.
