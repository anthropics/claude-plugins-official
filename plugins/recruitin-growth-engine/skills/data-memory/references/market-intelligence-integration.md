# Market Intelligence Integration

Reference data from Recruitin's existing intelligence-hub and content-intelligence-system repositories. This data feeds the Growth Engine's optimization loop with real market context.

## Existing Intelligence Systems

### 1. Market Trends Scraper

**Source:** `intelligence-hub/scrapers/market-trends-scraper.js`
**Schedule:** Weekly (Monday 08:00 UTC)
**Sources:** Indeed.nl + Monsterboard.nl

**Tracked Keywords (10):**
- automation engineer
- field service engineer
- maintenance engineer
- process engineer
- electrical engineer
- mechanical engineer
- project engineer
- commissioning engineer
- PLC programmeur
- technisch commercieel

**Tracked Regions (3):**
- Gelderland
- Overijssel
- Noord-Brabant

**Output Metrics:**
- Vacancy count per keyword/location/source
- Salary ranges (Indeed only)
- Week-over-week trend percentage
- Ghosting risk per keyword (HIGH/MEDIUM/LOW based on competitor vacancy activity)

**Total Coverage:** 60 scrapes per run (10 keywords x 3 regions x 2 sources)

### 2. ICP Monitor

**Source:** `intelligence-hub/scrapers/icp-monitor.js`
**Schedule:** Weekly (Monday 08:30 UTC)

**Tracked Companies (17+ target, expanding to 500):**

| Company | Sector | Region |
|---------|--------|--------|
| ASML | Manufacturing | Gelderland |
| VDL Groep | Automotive | Noord-Brabant |
| Philips | Healthcare | Noord-Brabant |
| Siemens | Automation | Multi |
| Stork | Industrial Services | Gelderland |
| BAM | Construction | Multi |
| Alfen | Renewable Energy | Gelderland |
| + 10 more | Various | Gelderland/Overijssel/Brabant |

**Scoring System:**
- Activity Score: 0-100
- Status: HOT (70-100) | WARM (40-69) | COLD (0-39)
- Action Priority: IMMEDIATE | THIS WEEK | MONITOR

**Signal Sources:**
- Career page vacancy detection (6 URL patterns)
- Google News company mentions
- LinkedIn company activity
- Hiring signal keywords: "vacature", "werken bij", "career"
- News keywords: "order", "contract", "expansion"

### 3. Concurrent Tracker

**Source:** `intelligence-hub/scrapers/concurrent-tracker.js`
**Schedule:** Weekly (Monday 09:00 UTC)

**Tracked Competitors (8):**

| Competitor | Focus Areas |
|-----------|------------|
| Yacht | techniek, IT, engineering |
| Brunel | engineering, oil & gas, renewable energy |
| Olympia | techniek, productie, logistiek |
| Tempo-Team | techniek, bouw, industrie |
| Randstad | engineering, techniek, industrie |
| Unique | techniek, productie |
| Manpower | techniek, engineering, productie |
| Cottus | bouw, infra, techniek |

**Monitored Channels:**
- Company blogs (content volume + relevance)
- LinkedIn posts (via Google search proxy)
- Google News mentions

**Scoring:**
- Relevance Score: 0-100 per channel
- Activity Level: ZEER ACTIEF | ACTIEF | MATIG ACTIEF | INACTIEF
- Threat Level: HOOG | GEMIDDELD | LAAG | MINIMAAL

**Content Keywords Tracked:**
- Techniek: automation, field service, maintenance, technisch, engineer, PLC, SCADA
- Trending: AI, digitalisering, sustainability, renewable energy, net zero, energietransitie
- Recruitment: krapte, arbeidstekort, talent, personeelstekort, werving, selectie
- Regional: gelderland, overijssel, noord-brabant, arnhem, nijmegen, zwolle, eindhoven

## Google Sheets Intelligence Dashboard

**URL:** https://docs.google.com/spreadsheets/d/14pX6dV6-5KLHYPuU1YsZSzu5SLHVbUxU78YQvIIRV_c/edit

**8 Sheets:**

| Sheet | Content | Update Frequency |
|-------|---------|-----------------|
| Market Trends | Vacancy volumes per functiegroep/region | Weekly Monday 06:00 |
| ICP Activity | Company monitoring + match scores | Weekly Monday 06:30 |
| Ghosting Patterns | Pipeline stall analysis | Weekly Monday 08:00 |
| Sector News | Industry updates + relevance scores | Daily 06:00 |
| Concurrent Activity | Competitor content tracking | Weekly Monday |
| Newsletter Monthly | Monthly aggregation for email | Monthly end-of-month |
| Dashboard | Real-time KPIs | Auto-updated |
| README | Documentation | Static |

**Dashboard KPIs:**
- Total vacatures this week (sum from Market Trends)
- Change vs last week (%)
- HIGH priority posts count
- Hottest functiegroep (by volume)
- Newsletter status
- Content opportunities count

## Integration with Growth Engine

### How Market Intelligence Feeds Campaign Creation

When generating campaigns, the engine should incorporate these intelligence signals:

**For Authority Campaigns (Recruitin LinkedIn):**
1. Use Market Trends data to identify trending topics (vacancy explosions, salary shifts)
2. Use Sector News (relevance ≥7) as content inspiration
3. Reference specific numbers from intelligence data in posts for authority
4. Use Concurrent Tracker to identify content gaps (topics competitors aren't covering)
5. Time posts to respond to market shifts detected by scrapers

**For Performance Campaigns (Client Vacancies):**
1. Check Market Trends for vacancy volume in the target keyword/region
2. Use ghosting risk data to adjust messaging (high competition = differentiate harder)
3. Check ICP Activity for hiring signals at the target company
4. Use competitor activity data to avoid crowded channels/timings
5. Reference salary data in ad copy when available

### Data Flow: Intelligence → Supabase

Import intelligence data into Supabase for the optimization loop:

```sql
-- New table for market intelligence
CREATE TABLE market_intelligence (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  data_type TEXT CHECK (data_type IN ('market_trend', 'icp_signal', 'competitor_activity', 'sector_news')),
  keyword TEXT,
  region TEXT,
  source TEXT,
  metric_value NUMERIC,
  metric_label TEXT,
  risk_level TEXT,
  relevance_score INT,
  raw_data JSONB,
  scraped_at TIMESTAMPTZ DEFAULT NOW(),
  week_number INT,
  year INT
);

CREATE INDEX idx_market_intelligence_type ON market_intelligence(data_type);
CREATE INDEX idx_market_intelligence_week ON market_intelligence(year, week_number);
CREATE INDEX idx_market_intelligence_keyword ON market_intelligence(keyword);
```

### Weekly Import Query Example

```sql
-- Import market trend signal
INSERT INTO market_intelligence (data_type, keyword, region, source, metric_value, metric_label, risk_level, week_number, year)
VALUES ('market_trend', 'PLC programmeur', 'Gelderland', 'Indeed', 127, 'vacancy_count', 'MEDIUM', 6, 2026);

-- Import ICP hiring signal
INSERT INTO market_intelligence (data_type, keyword, region, source, metric_value, metric_label, relevance_score, week_number, year)
VALUES ('icp_signal', 'ASML', 'Gelderland', 'career_page', 8, 'open_positions', 85, 6, 2026);

-- Import competitor activity
INSERT INTO market_intelligence (data_type, keyword, source, metric_value, metric_label, risk_level, relevance_score, week_number, year)
VALUES ('competitor_activity', 'Brunel', 'blog', 5, 'posts_this_week', 'HOOG', 72, 6, 2026);
```
