# ICP Scoring Model

Reference implementation from Recruitin's existing Pipedrive/Zapier ICP scoring calculator. This model is used to qualify prospects and should inform campaign targeting decisions.

## 7-Criteria Scoring Model

### Criteria Overview

| # | Criterion | Weight | Max Raw | Max Weighted |
|---|-----------|--------|---------|-------------|
| 1 | Bedrijfsgrootte (FTE) | 2.0x | 3 | 6.0 |
| 2 | Sector | 1.5x | 3 | 4.5 |
| 3 | Regio | 1.0x | 3 | 3.0 |
| 4 | Recruitment Type | 1.5x | 3 | 4.5 |
| 5 | Budget Range | 2.0x | 3 | 6.0 |
| 6 | Decision Maker | 1.0x | 3 | 3.0 |
| 7 | Urgentie | 0.5x | 3 | 1.5 |
| | **TOTAAL** | | | **28.5** |

**ICP Match Threshold:** ≥ 14.25 (50% of max score)

### Criterion 1: Bedrijfsgrootte (Weight: 2x)

| FTE | Score | Rationale |
|-----|-------|-----------|
| < 50 | 0 | Te klein, geen recruitmentbudget |
| 50-199 | 1 | Potentieel, maar beperkt volume |
| 200-800 | 2 | Sweet spot: genoeg volume, beslissingsvermogen |
| > 800 | 3 | Enterprise: groot volume, RPO-potentieel |

### Criterion 2: Sector (Weight: 1.5x)

| Sector Category | Score | Examples |
|----------------|-------|---------|
| Perfect fit | 3 | Oil & Gas, Renewable Energy, Wind Energy |
| Target sector | 2 | Productie, Constructie, Automation, Engineering |
| Adjacent sector | 1 | IT, Engineering Services, Technical Services |
| Other | 0 | Retail, Hospitality, etc. |

### Criterion 3: Regio (Weight: 1x)

| Location | Score | Description |
|----------|-------|-------------|
| Multi-locatie in target | 3 | 2+ vestigingen in Gelderland/Overijssel/Brabant |
| Target regio | 2 | 1 vestiging in Gelderland/Overijssel/Brabant |
| Andere NL provincie | 1 | Utrecht, Zuid-Holland, Noord-Holland, etc. |
| Buiten Nederland | 0 | International only |

### Criterion 4: Recruitment Type (Weight: 1.5x)

| Type | Score | Revenue Potential |
|------|-------|------------------|
| RPO (Recruitment Process Outsourcing) | 3 | Hoogste: recurring revenue |
| Werving & Selectie / Interim | 2 | Standaard: per placement |
| Recruitment Marketing only | 1 | Laagste: campaign-based |
| Other | 0 | Not aligned |

### Criterion 5: Budget Range (Weight: 2x)

| Budget | Score | Typical Engagement |
|--------|-------|--------------------|
| ≥ €100k | 3 | RPO / Multi-vacancy contract |
| €50k-€100k | 2 | Meerdere W&S plaatsingen |
| €25k-€50k | 1 | Enkele plaatsing + marketing |
| < €25k | 0 | Te laag voor profitable service |

### Criterion 6: Decision Maker (Weight: 1x)

| Role Level | Score | Examples |
|-----------|-------|---------|
| C-level / Director | 3 | CEO, CFO, COO, HR Director, Directeur |
| Manager / Head of | 2 | HR Manager, Head of Recruitment |
| Coordinator / Specialist | 1 | HR Coordinator, Recruitment Specialist |
| Other / Unknown | 0 | No clear decision authority |

### Criterion 7: Urgentie (Weight: 0.5x)

| Timeline | Score | Meaning |
|----------|-------|---------|
| Urgent (< 1 maand) | 3 | Acute vacature, snelle beslissing |
| Normaal (1-3 maanden) | 2 | Gepland, budget beschikbaar |
| Langzaam (> 3 maanden) | 1 | Orientatie, nog geen concreet plan |
| Onbekend | 0 | Geen timeline gecommuniceerd |

## Score Interpretation

| Score Range | Percentage | Classification | Action |
|------------|-----------|----------------|--------|
| 22-28.5 | 77-100% | A-prospect | IMMEDIATE outreach, priority campaigns |
| 14.25-21.99 | 50-77% | B-prospect (ICP Match) | Active nurturing, standard campaigns |
| 7-14.24 | 25-50% | C-prospect | Low-priority monitoring |
| 0-6.99 | 0-25% | No match | Do not pursue |

## Integration with Campaign Strategy

### A-Prospects (Score ≥ 22)
- Personalized campaign approach
- Dedicated landing page consideration
- Multi-channel strategy (LinkedIn + Meta + Direct outreach)
- Higher budget allocation per prospect
- Custom brand voice matching

### B-Prospects (Score 14.25-22)
- Standard campaign inclusion
- Grouped by sector/region for efficiency
- Standard Meta + LinkedIn campaigns
- Monthly nurture content

### C-Prospects (Score 7-14.24)
- Authority content only (no performance spend)
- Include in newsletter distribution
- Monitor for score increases (new hiring signals, budget changes)

## Using ICP Data in the Growth Engine

When the optimization engine queries for the best campaign strategy, incorporate ICP scores:

1. **High ICP score prospects** → Justify higher cost-per-hire budget, use premium channels
2. **Industry clusters** → Group similar-scoring companies for sector-specific campaigns
3. **Geographic patterns** → Allocate regional budgets based on ICP density
4. **Urgency signals** → Prioritize campaigns for urgent prospects, adjust messaging tone

### Supabase Integration

```sql
-- ICP scores table (synced from Pipedrive via Zapier)
CREATE TABLE icp_scores (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_name TEXT NOT NULL,
  pipedrive_deal_id TEXT,
  bedrijfsgrootte_fte INT,
  sector TEXT,
  regio TEXT,
  recruitment_type TEXT,
  budget_range TEXT,
  decision_maker_role TEXT,
  urgentie TEXT,
  icp_score NUMERIC(5,2),
  icp_match BOOLEAN,
  score_percentage NUMERIC(5,1),
  classification TEXT CHECK (classification IN ('A', 'B', 'C', 'no_match')),
  last_updated TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_icp_scores_classification ON icp_scores(classification);
CREATE INDEX idx_icp_scores_sector ON icp_scores(sector);
```
