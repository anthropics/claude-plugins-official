---
name: data-memory
description: This skill should be used when the user wants to "import campaign data", "analyze performance metrics", "set up the Supabase database", "track campaign KPIs", "create performance reports", "log campaign results", "build the data schema", "import weekly numbers", or needs guidance on storing campaign performance data, defining KPIs, building reporting dashboards, or training the engine with historical recruitment marketing data.
version: 0.1.0
---

# Data Analysis & Memory Loop for Recruitin Growth Engine

The Data Memory skill manages the persistent intelligence layer of the Growth Engine. It structures, stores, and retrieves campaign performance data from Supabase to enable data-driven decisions across all campaign activities.

## Database Architecture

### Core Tables

The Supabase project requires these tables to power the Growth Engine:

**`clients`** - Client registry

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| name | text | Client company name |
| industry | text | Industry vertical (e.g., "tech", "healthcare", "logistics") |
| brand_voice | jsonb | Tone-of-voice preferences |
| target_audience | jsonb | Default ICP definition |
| created_at | timestamptz | Registration date |

**`campaigns`** - Campaign registry

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| client_id | uuid | FK to clients |
| campaign_type | text | "authority" or "performance" |
| channel | text | "linkedin", "meta", or "multi" |
| status | text | "planning", "active", "paused", "completed" |
| start_date | date | Campaign start |
| end_date | date | Campaign end |
| total_budget | numeric | Total allocated budget in EUR |
| target_role | text | Target job title (for performance campaigns) |
| target_industry | text | Target industry vertical |
| created_at | timestamptz | Creation timestamp |

**`content_log`** - All generated content pieces

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| campaign_id | uuid | FK to campaigns |
| content_type | text | "linkedin_post", "linkedin_article", "meta_ad", "carousel", "video_prompt" |
| tone_of_voice | text | "formal", "informal", "bold", "empathetic" |
| content_body | text | The generated text content |
| visual_prompt | jsonb | Associated visual prompt specification |
| phase | text | Campaign phase when generated |
| published_at | timestamptz | When content went live |
| created_at | timestamptz | Generation timestamp |

**`weekly_metrics`** - Weekly performance snapshots

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| campaign_id | uuid | FK to campaigns |
| week_number | int | ISO week number |
| year | int | Year |
| impressions | int | Total impressions |
| clicks | int | Total clicks |
| applications | int | Total applications received |
| qualified_applications | int | Applications meeting criteria |
| hires | int | Confirmed hires |
| spend | numeric | Budget spent in EUR |
| ctr | numeric | Click-through rate |
| cpc | numeric | Cost per click |
| cpa | numeric | Cost per application |
| cph | numeric | Cost per hire |
| quality_score | numeric | Qualified / Total applications ratio |
| notes | text | Manual observations |
| created_at | timestamptz | Import timestamp |

**`winning_strategies`** - Materialized view of best-performing combinations

| Column | Type | Description |
|--------|------|-------------|
| industry | text | Industry vertical |
| target_role_category | text | Role category (e.g., "tech", "sales", "operations") |
| best_tone | text | Highest-performing tone-of-voice |
| best_content_type | text | Highest-performing content format |
| best_channel | text | Highest-performing channel |
| avg_cph | numeric | Average cost-per-hire for this combination |
| sample_size | int | Number of campaigns in calculation |
| confidence | text | "high" (>10 campaigns), "medium" (5-10), "low" (<5) |
| last_updated | timestamptz | Last recalculation |

**`client_brand_voices`** - Brand voice registry

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| client_id | uuid | FK to clients |
| voice_name | text | Descriptive name |
| formality | text | "formal", "semi-formal", "informal" |
| personality_traits | text[] | Array of traits: "bold", "empathetic", "data-driven" |
| vocabulary_preferences | jsonb | Preferred/avoided terms |
| example_content | text | Reference content in the right voice |
| language | text | "nl", "en", or "nl-en-mixed" |

## Data Import Workflow

### Weekly Import Process

Execute this workflow every Monday morning:

1. **Collect Raw Data** - Gather metrics from Meta Ads Manager and LinkedIn Campaign Manager
2. **Validate Data** - Check for completeness: all active campaigns must have entries
3. **Calculate Derived Metrics** - Compute CTR, CPC, CPA, CPH, quality score
4. **Insert into Supabase** - Use the Supabase MCP tools to insert rows into `weekly_metrics`
5. **Refresh Winning Strategies** - Recalculate the `winning_strategies` view
6. **Generate Anomaly Alerts** - Flag metrics that deviate >20% from the campaign average

### Import Data Format

Accept data in this structured format:

```json
{
  "campaign_id": "uuid",
  "week_number": 5,
  "year": 2026,
  "impressions": 15000,
  "clicks": 225,
  "applications": 8,
  "qualified_applications": 5,
  "hires": 1,
  "spend": 450.00,
  "notes": "Increased budget mid-week due to high CTR"
}
```

Derived metrics are calculated automatically:
- `ctr = clicks / impressions`
- `cpc = spend / clicks`
- `cpa = spend / applications`
- `cph = spend / hires` (null if hires = 0)
- `quality_score = qualified_applications / applications`

## Analysis Queries

### Query 1: Weekly Performance Summary

```sql
SELECT
  c.name AS client_name,
  cam.target_role,
  wm.week_number,
  wm.impressions,
  wm.clicks,
  wm.ctr,
  wm.applications,
  wm.cph,
  wm.spend
FROM weekly_metrics wm
JOIN campaigns cam ON wm.campaign_id = cam.id
JOIN clients c ON cam.client_id = c.id
WHERE wm.year = EXTRACT(YEAR FROM CURRENT_DATE)
  AND wm.week_number = EXTRACT(WEEK FROM CURRENT_DATE) - 1
ORDER BY wm.cph ASC NULLS LAST;
```

### Query 2: Best Performing Tone-of-Voice by Industry

```sql
SELECT
  cam.target_industry,
  cl.tone_of_voice,
  AVG(wm.cph) AS avg_cost_per_hire,
  COUNT(DISTINCT cam.id) AS campaign_count,
  AVG(wm.ctr) AS avg_ctr,
  AVG(wm.quality_score) AS avg_quality
FROM weekly_metrics wm
JOIN campaigns cam ON wm.campaign_id = cam.id
JOIN content_log cl ON cl.campaign_id = cam.id
WHERE wm.hires > 0
GROUP BY cam.target_industry, cl.tone_of_voice
ORDER BY avg_cost_per_hire ASC;
```

### Query 3: Content Type Performance Ranking

```sql
SELECT
  cl.content_type,
  cam.channel,
  AVG(wm.ctr) AS avg_ctr,
  AVG(wm.cpa) AS avg_cost_per_application,
  AVG(wm.quality_score) AS avg_quality_score,
  COUNT(*) AS data_points
FROM content_log cl
JOIN campaigns cam ON cl.campaign_id = cam.id
JOIN weekly_metrics wm ON wm.campaign_id = cam.id
GROUP BY cl.content_type, cam.channel
HAVING COUNT(*) >= 3
ORDER BY avg_cost_per_application ASC;
```

### Query 4: Campaign Trend Analysis

```sql
SELECT
  wm.week_number,
  AVG(wm.ctr) AS avg_ctr,
  AVG(wm.cpc) AS avg_cpc,
  AVG(wm.cpa) AS avg_cpa,
  SUM(wm.spend) AS total_spend,
  SUM(wm.hires) AS total_hires
FROM weekly_metrics wm
WHERE wm.year = EXTRACT(YEAR FROM CURRENT_DATE)
GROUP BY wm.week_number
ORDER BY wm.week_number;
```

## Anomaly Detection Rules

Flag a metric when it deviates significantly from the campaign's rolling average:

| Metric | Alert Threshold | Action |
|--------|----------------|--------|
| CTR drops > 30% | High priority | Review ad creative fatigue |
| CPC increases > 25% | Medium priority | Check audience saturation |
| Quality Score drops > 20% | High priority | Review targeting criteria |
| Zero applications for 7+ days | Critical | Pause and review campaign |
| Spend > 110% of weekly budget | Medium priority | Check daily budget caps |

## Supabase Setup SQL

Initial database setup script (run once via Supabase SQL editor):

```sql
-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Clients table
CREATE TABLE clients (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  industry TEXT NOT NULL,
  brand_voice JSONB DEFAULT '{}',
  target_audience JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Campaigns table
CREATE TABLE campaigns (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  client_id UUID REFERENCES clients(id),
  campaign_type TEXT CHECK (campaign_type IN ('authority', 'performance')),
  channel TEXT CHECK (channel IN ('linkedin', 'meta', 'multi')),
  status TEXT DEFAULT 'planning' CHECK (status IN ('planning', 'active', 'paused', 'completed')),
  start_date DATE,
  end_date DATE,
  total_budget NUMERIC(10,2),
  target_role TEXT,
  target_industry TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Content log
CREATE TABLE content_log (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  campaign_id UUID REFERENCES campaigns(id),
  content_type TEXT NOT NULL,
  tone_of_voice TEXT,
  content_body TEXT,
  visual_prompt JSONB,
  phase TEXT,
  published_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Weekly metrics
CREATE TABLE weekly_metrics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  campaign_id UUID REFERENCES campaigns(id),
  week_number INT NOT NULL,
  year INT NOT NULL,
  impressions INT DEFAULT 0,
  clicks INT DEFAULT 0,
  applications INT DEFAULT 0,
  qualified_applications INT DEFAULT 0,
  hires INT DEFAULT 0,
  spend NUMERIC(10,2) DEFAULT 0,
  ctr NUMERIC(8,6) GENERATED ALWAYS AS (
    CASE WHEN impressions > 0 THEN clicks::NUMERIC / impressions ELSE 0 END
  ) STORED,
  cpc NUMERIC(10,2) GENERATED ALWAYS AS (
    CASE WHEN clicks > 0 THEN spend / clicks ELSE NULL END
  ) STORED,
  cpa NUMERIC(10,2) GENERATED ALWAYS AS (
    CASE WHEN applications > 0 THEN spend / applications ELSE NULL END
  ) STORED,
  cph NUMERIC(10,2) GENERATED ALWAYS AS (
    CASE WHEN hires > 0 THEN spend / hires ELSE NULL END
  ) STORED,
  quality_score NUMERIC(5,4) GENERATED ALWAYS AS (
    CASE WHEN applications > 0 THEN qualified_applications::NUMERIC / applications ELSE NULL END
  ) STORED,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(campaign_id, week_number, year)
);

-- Client brand voices
CREATE TABLE client_brand_voices (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  client_id UUID REFERENCES clients(id),
  voice_name TEXT NOT NULL,
  formality TEXT CHECK (formality IN ('formal', 'semi-formal', 'informal')),
  personality_traits TEXT[],
  vocabulary_preferences JSONB DEFAULT '{}',
  example_content TEXT,
  language TEXT DEFAULT 'nl' CHECK (language IN ('nl', 'en', 'nl-en-mixed')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Winning strategies materialized view
CREATE MATERIALIZED VIEW winning_strategies AS
SELECT
  cam.target_industry AS industry,
  COALESCE(cam.target_role, 'general') AS target_role_category,
  MODE() WITHIN GROUP (ORDER BY cl.tone_of_voice) AS best_tone,
  MODE() WITHIN GROUP (ORDER BY cl.content_type) AS best_content_type,
  MODE() WITHIN GROUP (ORDER BY cam.channel) AS best_channel,
  AVG(wm.cph) FILTER (WHERE wm.cph IS NOT NULL) AS avg_cph,
  COUNT(DISTINCT cam.id) AS sample_size,
  CASE
    WHEN COUNT(DISTINCT cam.id) > 10 THEN 'high'
    WHEN COUNT(DISTINCT cam.id) > 5 THEN 'medium'
    ELSE 'low'
  END AS confidence,
  NOW() AS last_updated
FROM campaigns cam
JOIN content_log cl ON cl.campaign_id = cam.id
JOIN weekly_metrics wm ON wm.campaign_id = cam.id
WHERE cam.status IN ('active', 'completed')
  AND wm.hires > 0
GROUP BY cam.target_industry, COALESCE(cam.target_role, 'general');

-- Index for fast lookups
CREATE INDEX idx_weekly_metrics_campaign ON weekly_metrics(campaign_id);
CREATE INDEX idx_weekly_metrics_week ON weekly_metrics(year, week_number);
CREATE INDEX idx_content_log_campaign ON content_log(campaign_id);
CREATE INDEX idx_campaigns_client ON campaigns(client_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);

-- Refresh function for winning strategies
CREATE OR REPLACE FUNCTION refresh_winning_strategies()
RETURNS void AS $$
BEGIN
  REFRESH MATERIALIZED VIEW winning_strategies;
END;
$$ LANGUAGE plpgsql;
```
