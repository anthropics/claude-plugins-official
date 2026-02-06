-- ============================================================
-- RECRUITIN GROWTH ENGINE — VOLLEDIGE DATABASE SETUP
-- Plak dit in Supabase SQL Editor en klik Run
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- TABEL 1: CLIENTS
CREATE TABLE IF NOT EXISTS clients (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  industry TEXT NOT NULL,
  brand_voice JSONB DEFAULT '{}',
  target_audience JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- TABEL 2: CAMPAIGNS
CREATE TABLE IF NOT EXISTS campaigns (
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

-- TABEL 3: CONTENT LOG
CREATE TABLE IF NOT EXISTS content_log (
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

-- TABEL 4: WEEKLY METRICS (KPI's worden automatisch berekend)
CREATE TABLE IF NOT EXISTS weekly_metrics (
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

-- TABEL 5: CLIENT BRAND VOICES
CREATE TABLE IF NOT EXISTS client_brand_voices (
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

-- TABEL 6: MARKET INTELLIGENCE
CREATE TABLE IF NOT EXISTS market_intelligence (
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

-- TABEL 7: ICP SCORES
CREATE TABLE IF NOT EXISTS icp_scores (
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

-- MATERIALIZED VIEW: WINNING STRATEGIES
CREATE MATERIALIZED VIEW IF NOT EXISTS winning_strategies AS
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

-- INDEXES
CREATE INDEX IF NOT EXISTS idx_weekly_metrics_campaign ON weekly_metrics(campaign_id);
CREATE INDEX IF NOT EXISTS idx_weekly_metrics_week ON weekly_metrics(year, week_number);
CREATE INDEX IF NOT EXISTS idx_content_log_campaign ON content_log(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_client ON campaigns(client_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_market_intelligence_type ON market_intelligence(data_type);
CREATE INDEX IF NOT EXISTS idx_market_intelligence_week ON market_intelligence(year, week_number);
CREATE INDEX IF NOT EXISTS idx_market_intelligence_keyword ON market_intelligence(keyword);
CREATE INDEX IF NOT EXISTS idx_icp_scores_classification ON icp_scores(classification);
CREATE INDEX IF NOT EXISTS idx_icp_scores_sector ON icp_scores(sector);

-- REFRESH FUNCTIE
CREATE OR REPLACE FUNCTION refresh_winning_strategies()
RETURNS void AS $$
BEGIN
  REFRESH MATERIALIZED VIEW winning_strategies;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- SEED DATA
-- ============================================================

-- Recruitin als client
INSERT INTO clients (name, industry, brand_voice, target_audience) VALUES (
  'Recruitin',
  'recruitment-marketing',
  '{"formality": "semi-formal", "personality": ["data-driven", "bold", "approachable"], "language": "nl-en-mixed", "avoid_phrases": ["dynamisch team", "marktconform salaris", "passie voor", "unieke kans", "no-nonsense", "hands-on mentaliteit", "in de huidige markt", "platte organisatie"], "preferred_phrases": ["cost-per-hire", "talent pipeline", "employer brand", "data-gedreven", "candidate experience"]}',
  '{"primary": {"title": "HR Directors & Talent Acquisition Managers", "company_size": "50-500 medewerkers", "location": "Nederland"}, "secondary": {"title": "Marketing Directors bij staffing agencies"}, "tertiary": {"title": "Founders/CEOs van scale-ups"}}'
);

-- Brand voice
INSERT INTO client_brand_voices (client_id, voice_name, formality, personality_traits, vocabulary_preferences, example_content, language) VALUES (
  (SELECT id FROM clients WHERE name = 'Recruitin'),
  'Recruitin Authority Voice',
  'semi-formal',
  ARRAY['data-driven', 'bold', 'approachable', 'contrarian'],
  '{"use": ["cost-per-hire", "talent pipeline", "employer brand", "candidate experience", "hiring funnel"], "avoid": ["dynamisch team", "passie voor", "unieke kans", "marktconform", "no-nonsense"], "style_notes": "Korte zinnen. Concrete cijfers. Geen corporate jargon. Nederlands met Engelse vakterm waar standaard."}',
  'Vorig kwartaal analyseerden we 47 recruitment campagnes. Het resultaat? Bedrijven die hun employer brand consistent communiceren op LinkedIn betalen gemiddeld 34% minder per hire dan bedrijven die alleen vacatures posten. Geen rocket science. Gewoon data.',
  'nl-en-mixed'
);

-- Eerste authority campagne
INSERT INTO campaigns (client_id, campaign_type, channel, status, start_date, end_date, total_budget, target_role, target_industry) VALUES (
  (SELECT id FROM clients WHERE name = 'Recruitin'),
  'authority', 'linkedin', 'active', CURRENT_DATE, CURRENT_DATE + INTERVAL '12 weeks', 0.00, 'HR Decision Makers', 'recruitment-marketing'
);

-- Market intelligence sample data
INSERT INTO market_intelligence (data_type, keyword, region, source, metric_value, metric_label, risk_level, week_number, year) VALUES
  ('market_trend', 'PLC programmeur', 'Gelderland', 'Indeed', 127, 'vacancy_count', 'HIGH', 5, 2026),
  ('market_trend', 'PLC programmeur', 'Overijssel', 'Indeed', 43, 'vacancy_count', 'MEDIUM', 5, 2026),
  ('market_trend', 'PLC programmeur', 'Noord-Brabant', 'Indeed', 89, 'vacancy_count', 'HIGH', 5, 2026),
  ('market_trend', 'field service engineer', 'Gelderland', 'Indeed', 156, 'vacancy_count', 'HIGH', 5, 2026),
  ('market_trend', 'maintenance engineer', 'Overijssel', 'Indeed', 67, 'vacancy_count', 'MEDIUM', 5, 2026),
  ('market_trend', 'automation engineer', 'Gelderland', 'Indeed', 98, 'vacancy_count', 'MEDIUM', 5, 2026),
  ('market_trend', 'commissioning engineer', 'Noord-Brabant', 'Indeed', 34, 'vacancy_count', 'LOW', 5, 2026),
  ('market_trend', 'technisch commercieel', 'Gelderland', 'Indeed', 112, 'vacancy_count', 'HIGH', 5, 2026);

INSERT INTO market_intelligence (data_type, keyword, region, source, metric_value, metric_label, relevance_score, week_number, year) VALUES
  ('icp_signal', 'ASML', 'Gelderland', 'career_page', 8, 'open_positions', 85, 5, 2026),
  ('icp_signal', 'VDL Groep', 'Noord-Brabant', 'career_page', 12, 'open_positions', 78, 5, 2026),
  ('icp_signal', 'Philips', 'Noord-Brabant', 'career_page', 5, 'open_positions', 62, 5, 2026),
  ('icp_signal', 'Siemens', 'Gelderland', 'career_page', 6, 'open_positions', 70, 5, 2026),
  ('icp_signal', 'Alfen', 'Gelderland', 'career_page', 4, 'open_positions', 55, 5, 2026);

INSERT INTO market_intelligence (data_type, keyword, source, metric_value, metric_label, risk_level, relevance_score, week_number, year) VALUES
  ('competitor_activity', 'Yacht', 'blog', 3, 'posts_this_week', 'GEMIDDELD', 45, 5, 2026),
  ('competitor_activity', 'Brunel', 'blog', 5, 'posts_this_week', 'HOOG', 72, 5, 2026),
  ('competitor_activity', 'Randstad', 'linkedin', 8, 'posts_this_week', 'HOOG', 38, 5, 2026),
  ('competitor_activity', 'Olympia', 'blog', 1, 'posts_this_week', 'LAAG', 22, 5, 2026),
  ('competitor_activity', 'Tempo-Team', 'blog', 2, 'posts_this_week', 'LAAG', 30, 5, 2026);

-- ICP scores
INSERT INTO icp_scores (company_name, bedrijfsgrootte_fte, sector, regio, recruitment_type, budget_range, decision_maker_role, urgentie, icp_score, icp_match, score_percentage, classification) VALUES
  ('ASML', 42000, 'manufacturing', 'gelderland', 'RPO', '€100k+', 'HR Director', 'urgent', 26.5, true, 93.0, 'A'),
  ('VDL Groep', 15000, 'automotive', 'noord-brabant', 'w&s', '€50k-€100k', 'HR Manager', 'normaal', 21.0, true, 73.7, 'B'),
  ('Alfen', 800, 'renewable energy', 'gelderland', 'w&s', '€25k-€50k', 'HR Manager', 'urgent', 19.5, true, 68.4, 'B'),
  ('Stork', 3000, 'industrial services', 'gelderland', 'interim', '€50k-€100k', 'Head of HR', 'normaal', 20.0, true, 70.2, 'B'),
  ('BAM', 20000, 'construction', 'gelderland, overijssel', 'RPO', '€100k+', 'Directeur HR', 'langzaam', 22.5, true, 78.9, 'A');
