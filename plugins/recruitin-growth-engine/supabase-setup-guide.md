# Supabase Setup Guide — Recruitin Growth Engine

## Stap 1: Project Aanmaken

1. Ga naar https://supabase.com en log in (of maak een account)
2. Klik **New Project**
3. Vul in:
   - **Name:** `recruitin-growth-engine`
   - **Database Password:** kies een sterk wachtwoord (bewaar dit!)
   - **Region:** West EU (Frankfurt) — dichtst bij Nederland
4. Klik **Create new project** en wacht ~2 minuten

## Stap 2: Database Schema Aanmaken

1. Ga naar **SQL Editor** in het linkermenu
2. Klik **New Query**
3. Kopieer en plak het VOLLEDIGE onderstaande script
4. Klik **Run** (of Cmd+Enter)

```sql
-- ============================================
-- RECRUITIN GROWTH ENGINE — DATABASE SETUP
-- Versie: 0.1.0
-- Datum: 2026-02-06
-- ============================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- TABEL 1: CLIENTS (Opdrachtgevers)
-- ============================================
CREATE TABLE clients (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  industry TEXT NOT NULL,
  brand_voice JSONB DEFAULT '{}',
  target_audience JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- TABEL 2: CAMPAIGNS (Campagnes)
-- ============================================
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

-- ============================================
-- TABEL 3: CONTENT LOG (Gegenereerde content)
-- ============================================
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

-- ============================================
-- TABEL 4: WEEKLY METRICS (Wekelijkse cijfers)
-- KPI's worden AUTOMATISCH berekend!
-- ============================================
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
  -- Automatisch berekende KPI's:
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

-- ============================================
-- TABEL 5: CLIENT BRAND VOICES
-- ============================================
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

-- ============================================
-- MATERIALIZED VIEW: WINNING STRATEGIES
-- Dit is het "brein" van de engine
-- ============================================
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

-- ============================================
-- INDEXES (voor snelle queries)
-- ============================================
CREATE INDEX idx_weekly_metrics_campaign ON weekly_metrics(campaign_id);
CREATE INDEX idx_weekly_metrics_week ON weekly_metrics(year, week_number);
CREATE INDEX idx_content_log_campaign ON content_log(campaign_id);
CREATE INDEX idx_campaigns_client ON campaigns(client_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);

-- ============================================
-- FUNCTIE: Refresh winning strategies
-- Voer wekelijks uit na data-import
-- ============================================
CREATE OR REPLACE FUNCTION refresh_winning_strategies()
RETURNS void AS $$
BEGIN
  REFRESH MATERIALIZED VIEW winning_strategies;
END;
$$ LANGUAGE plpgsql;
```

Je zou moeten zien: **"Success. No rows returned"** — dat betekent dat alles is aangemaakt.

## Stap 3: Verifieer de Installatie

Voer deze query uit om te checken of alle tabellen bestaan:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

Je zou moeten zien:
- `campaigns`
- `client_brand_voices`
- `clients`
- `content_log`
- `weekly_metrics`
- `winning_strategies`

## Stap 4: Seed Data — Recruitin als Eerste Client

Voer dit uit om Recruitin zelf als client te registreren (voor authority campagnes):

```sql
-- Recruitin als client registreren
INSERT INTO clients (name, industry, brand_voice, target_audience) VALUES (
  'Recruitin',
  'recruitment-marketing',
  '{
    "formality": "semi-formal",
    "personality": ["data-driven", "bold", "approachable"],
    "language": "nl-en-mixed",
    "avoid_phrases": [
      "dynamisch team",
      "marktconform salaris",
      "passie voor",
      "unieke kans",
      "no-nonsense",
      "hands-on mentaliteit",
      "in de huidige markt",
      "platte organisatie"
    ],
    "preferred_phrases": [
      "cost-per-hire",
      "talent pipeline",
      "employer brand",
      "data-gedreven",
      "candidate experience"
    ]
  }',
  '{
    "primary": {
      "title": "HR Directors & Talent Acquisition Managers",
      "company_size": "50-500 medewerkers",
      "location": "Nederland",
      "pain_points": [
        "Te hoge cost-per-hire",
        "Te weinig gekwalificeerde sollicitanten",
        "Geen inzicht in welke kanalen werken",
        "Employer brand is niet onderscheidend"
      ]
    },
    "secondary": {
      "title": "Marketing Directors bij staffing agencies",
      "focus": "Modernisering van recruitment aanpak"
    },
    "tertiary": {
      "title": "Founders/CEOs van scale-ups",
      "focus": "Snelle groei, veel vacatures tegelijk"
    }
  }'
);

-- Recruitin brand voice registreren
INSERT INTO client_brand_voices (
  client_id,
  voice_name,
  formality,
  personality_traits,
  vocabulary_preferences,
  example_content,
  language
) VALUES (
  (SELECT id FROM clients WHERE name = 'Recruitin'),
  'Recruitin Authority Voice',
  'semi-formal',
  ARRAY['data-driven', 'bold', 'approachable', 'contrarian'],
  '{
    "use": ["cost-per-hire", "talent pipeline", "employer brand", "candidate experience", "hiring funnel"],
    "avoid": ["dynamisch team", "passie voor", "unieke kans", "marktconform", "no-nonsense"],
    "style_notes": "Korte zinnen. Concrete cijfers. Geen corporate jargon. Nederlands met Engelse vakterm waar standaard."
  }',
  'Vorig kwartaal analyseerden we 47 recruitment campagnes. Het resultaat? Bedrijven die hun employer brand consistent communiceren op LinkedIn betalen gemiddeld 34% minder per hire dan bedrijven die alleen vacatures posten. Geen rocket science. Gewoon data.',
  'nl-en-mixed'
);

-- Eerste authority campagne aanmaken (12-weken cyclus)
INSERT INTO campaigns (
  client_id,
  campaign_type,
  channel,
  status,
  start_date,
  end_date,
  total_budget,
  target_role,
  target_industry
) VALUES (
  (SELECT id FROM clients WHERE name = 'Recruitin'),
  'authority',
  'linkedin',
  'active',
  CURRENT_DATE,
  CURRENT_DATE + INTERVAL '12 weeks',
  0.00,  -- Authority campagne = organisch, geen ad spend
  'HR Decision Makers',
  'recruitment-marketing'
);
```

## Stap 5: API Keys Noteren

Ga naar **Settings > API** in je Supabase dashboard en noteer:

| Waarde | Waar te vinden | Waarvoor |
|--------|---------------|----------|
| **Project URL** | `https://xxxxx.supabase.co` | MCP verbinding |
| **anon key** | `eyJhbGci...` | Client-side (niet nodig) |
| **service_role key** | `eyJhbGci...` | Claude Code MCP verbinding |

**Bewaar de service_role key veilig** — deze geeft volledige database-toegang.

## Stap 6: Verbind met Claude Code

Bij het eerste gebruik van de Supabase MCP in Claude Code wordt je gevraagd om in te loggen. Volg de OAuth flow of voer je project credentials in.

## Stap 7: Test de Setup

Voer in Supabase SQL Editor uit:

```sql
-- Check of Recruitin correct is aangemaakt
SELECT
  c.name,
  c.industry,
  cbv.voice_name,
  cbv.formality,
  cbv.personality_traits,
  cam.campaign_type,
  cam.status,
  cam.start_date,
  cam.end_date
FROM clients c
LEFT JOIN client_brand_voices cbv ON cbv.client_id = c.id
LEFT JOIN campaigns cam ON cam.client_id = c.id
WHERE c.name = 'Recruitin';
```

Je zou 1 rij moeten zien met alle Recruitin-gegevens.

## Klaar!

Je database is nu opgezet met:
- 6 tabellen + 1 materialized view
- Automatisch berekende KPI's (CTR, CPC, CPA, CPH, Quality Score)
- Recruitin als eerste client met brand voice
- Een actieve 12-weken authority campagne
- Indexes voor snelle queries

**Volgende stap:** Kopieer de `cowork-project-instructions.md` naar je Cowork Project Instructions en begin met je eerste `/recruitin-campaign authority`.
