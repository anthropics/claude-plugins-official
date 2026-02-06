#!/usr/bin/env bash
# ============================================================
# Recruitin Growth Engine — Supabase Setup Script
# Run: bash setup-supabase.sh
# ============================================================

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  Recruitin Growth Engine — Supabase Setup${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# ---- Stap 1: Credentials ophalen ----
if [ -z "${SUPABASE_URL:-}" ]; then
  echo -e "${YELLOW}Voer je Supabase Project URL in (bijv. https://xxxxx.supabase.co):${NC}"
  read -r SUPABASE_URL
fi

if [ -z "${SUPABASE_SERVICE_ROLE_KEY:-}" ]; then
  echo -e "${YELLOW}Voer je Supabase Service Role Key in:${NC}"
  read -rs SUPABASE_SERVICE_ROLE_KEY
  echo ""
fi

# Strip trailing slash
SUPABASE_URL="${SUPABASE_URL%/}"

# ---- Helper: SQL uitvoeren via Supabase REST API ----
run_sql() {
  local description="$1"
  local sql="$2"

  echo -ne "  ${description}... "

  local response
  local http_code

  response=$(curl -s -w "\n%{http_code}" \
    "${SUPABASE_URL}/rest/v1/rpc/exec_sql" \
    -H "apikey: ${SUPABASE_SERVICE_ROLE_KEY}" \
    -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE_KEY}" \
    -H "Content-Type: application/json" \
    -d "{\"query\": $(echo "$sql" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')}" \
    2>/dev/null) || true

  http_code=$(echo "$response" | tail -1)
  local body
  body=$(echo "$response" | head -n -1)

  # Als rpc/exec_sql niet bestaat, probeer de postgres REST endpoint
  if [[ "$http_code" == "404" ]] || echo "$body" | grep -q "Could not find"; then
    return 1
  fi

  if [[ "$http_code" =~ ^2 ]]; then
    echo -e "${GREEN}OK${NC}"
    return 0
  else
    echo -e "${RED}FOUT${NC}"
    echo "    $body" | head -5
    return 1
  fi
}

# ---- Helper: SQL via psql-achtige endpoint (Supabase pg_net/sql) ----
run_sql_direct() {
  local description="$1"
  local sql="$2"

  echo -ne "  ${description}... "

  # Extract project ref from URL
  local project_ref
  project_ref=$(echo "$SUPABASE_URL" | sed -E 's|https://([^.]+)\.supabase\.co.*|\1|')

  local response
  response=$(curl -s -w "\n%{http_code}" \
    "https://${project_ref}.supabase.co/pg/query" \
    -H "apikey: ${SUPABASE_SERVICE_ROLE_KEY}" \
    -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE_KEY}" \
    -H "Content-Type: application/json" \
    -d "{\"query\": $(echo "$sql" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')}" \
    2>/dev/null) || true

  local http_code
  http_code=$(echo "$response" | tail -1)
  local body
  body=$(echo "$response" | head -n -1)

  if [[ "$http_code" =~ ^2 ]]; then
    echo -e "${GREEN}OK${NC}"
    return 0
  else
    echo -e "${RED}FOUT (HTTP $http_code)${NC}"
    return 1
  fi
}

# ---- Stap 2: Connectie testen ----
echo -e "\n${BLUE}[1/6] Connectie testen...${NC}"

test_response=$(curl -s -o /dev/null -w "%{http_code}" \
  "${SUPABASE_URL}/rest/v1/" \
  -H "apikey: ${SUPABASE_SERVICE_ROLE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE_KEY}" \
  2>/dev/null) || true

if [[ "$test_response" =~ ^2 ]]; then
  echo -e "  Connectie: ${GREEN}OK${NC}"
else
  echo -e "  Connectie: ${RED}MISLUKT (HTTP $test_response)${NC}"
  echo -e "  ${YELLOW}Check je URL en Service Role Key.${NC}"
  exit 1
fi

# ---- Stap 3: SQL-bestanden samenvoegen en uitvoeren ----
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "\n${BLUE}[2/6] Database schema aanmaken...${NC}"

# We schrijven alles naar een enkel SQL-bestand voor psql of Supabase SQL Editor
SQL_FILE=$(mktemp /tmp/recruitin-setup-XXXXXX.sql)

cat > "$SQL_FILE" << 'SQLEOF'
-- ============================================================
-- RECRUITIN GROWTH ENGINE — VOLLEDIGE DATABASE SETUP
-- ============================================================

-- Enable UUID generation
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

-- TABEL 4: WEEKLY METRICS
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
SQLEOF

echo -e "  SQL geschreven naar: ${SQL_FILE}"

# ---- Stap 4: Seed data SQL ----
echo -e "\n${BLUE}[3/6] Seed data voorbereiden...${NC}"

SEED_FILE=$(mktemp /tmp/recruitin-seed-XXXXXX.sql)

cat > "$SEED_FILE" << 'SEEDEOF'
-- ============================================================
-- SEED DATA: Recruitin als eerste client
-- ============================================================

INSERT INTO clients (name, industry, brand_voice, target_audience) VALUES (
  'Recruitin',
  'recruitment-marketing',
  '{"formality": "semi-formal", "personality": ["data-driven", "bold", "approachable"], "language": "nl-en-mixed", "avoid_phrases": ["dynamisch team", "marktconform salaris", "passie voor", "unieke kans", "no-nonsense", "hands-on mentaliteit", "in de huidige markt", "platte organisatie"], "preferred_phrases": ["cost-per-hire", "talent pipeline", "employer brand", "data-gedreven", "candidate experience"]}',
  '{"primary": {"title": "HR Directors & Talent Acquisition Managers", "company_size": "50-500 medewerkers", "location": "Nederland", "pain_points": ["Te hoge cost-per-hire", "Te weinig gekwalificeerde sollicitanten", "Geen inzicht in welke kanalen werken", "Employer brand is niet onderscheidend"]}, "secondary": {"title": "Marketing Directors bij staffing agencies", "focus": "Modernisering van recruitment aanpak"}, "tertiary": {"title": "Founders/CEOs van scale-ups", "focus": "Snelle groei, veel vacatures tegelijk"}}'
) ON CONFLICT DO NOTHING;

INSERT INTO client_brand_voices (
  client_id, voice_name, formality, personality_traits, vocabulary_preferences, example_content, language
) VALUES (
  (SELECT id FROM clients WHERE name = 'Recruitin'),
  'Recruitin Authority Voice',
  'semi-formal',
  ARRAY['data-driven', 'bold', 'approachable', 'contrarian'],
  '{"use": ["cost-per-hire", "talent pipeline", "employer brand", "candidate experience", "hiring funnel"], "avoid": ["dynamisch team", "passie voor", "unieke kans", "marktconform", "no-nonsense"], "style_notes": "Korte zinnen. Concrete cijfers. Geen corporate jargon. Nederlands met Engelse vakterm waar standaard."}',
  'Vorig kwartaal analyseerden we 47 recruitment campagnes. Het resultaat? Bedrijven die hun employer brand consistent communiceren op LinkedIn betalen gemiddeld 34% minder per hire dan bedrijven die alleen vacatures posten. Geen rocket science. Gewoon data.',
  'nl-en-mixed'
);

INSERT INTO campaigns (
  client_id, campaign_type, channel, status, start_date, end_date, total_budget, target_role, target_industry
) VALUES (
  (SELECT id FROM clients WHERE name = 'Recruitin'),
  'authority', 'linkedin', 'active',
  CURRENT_DATE, CURRENT_DATE + INTERVAL '12 weeks',
  0.00, 'HR Decision Makers', 'recruitment-marketing'
);

-- Market intelligence seed data
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

INSERT INTO icp_scores (company_name, bedrijfsgrootte_fte, sector, regio, recruitment_type, budget_range, decision_maker_role, urgentie, icp_score, icp_match, score_percentage, classification) VALUES
  ('ASML', 42000, 'manufacturing', 'gelderland', 'RPO', '€100k+', 'HR Director', 'urgent', 26.5, true, 93.0, 'A'),
  ('VDL Groep', 15000, 'automotive', 'noord-brabant', 'w&s', '€50k-€100k', 'HR Manager', 'normaal', 21.0, true, 73.7, 'B'),
  ('Alfen', 800, 'renewable energy', 'gelderland', 'w&s', '€25k-€50k', 'HR Manager', 'urgent', 19.5, true, 68.4, 'B'),
  ('Stork', 3000, 'industrial services', 'gelderland', 'interim', '€50k-€100k', 'Head of HR', 'normaal', 20.0, true, 70.2, 'B'),
  ('BAM', 20000, 'construction', 'gelderland, overijssel', 'RPO', '€100k+', 'Directeur HR', 'langzaam', 22.5, true, 78.9, 'A');
SEEDEOF

echo -e "  Seed data geschreven naar: ${SEED_FILE}"

# ---- Stap 5: Probeer uit te voeren via Supabase Management API ----
echo -e "\n${BLUE}[4/6] Database setup uitvoeren...${NC}"

PROJECT_REF=$(echo "$SUPABASE_URL" | sed -E 's|https://([^.]+)\.supabase\.co.*|\1|')

# Methode 1: Via Supabase Management API (sql endpoint)
echo -e "  Probeer via Supabase SQL API..."

SCHEMA_RESULT=$(curl -s -w "\n%{http_code}" \
  "https://${PROJECT_REF}.supabase.co/rest/v1/rpc/" \
  -X POST \
  -H "apikey: ${SUPABASE_SERVICE_ROLE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE_KEY}" \
  -H "Content-Type: application/json" \
  -H "Prefer: return=minimal" \
  2>/dev/null) || true

SCHEMA_HTTP=$(echo "$SCHEMA_RESULT" | tail -1)

# Methode 2: Probeer via psql als dat beschikbaar is
if command -v psql &>/dev/null; then
  echo -e "  ${GREEN}psql gevonden${NC} — directe database connectie"

  DB_HOST="db.${PROJECT_REF}.supabase.co"
  DB_PORT="5432"
  DB_NAME="postgres"
  DB_USER="postgres"

  echo -e "${YELLOW}  Voer je database wachtwoord in (van project aanmaak):${NC}"
  read -rs DB_PASS
  echo ""

  echo -e "  Schema aanmaken..."
  PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$SQL_FILE" 2>&1 | while read -r line; do
    echo "    $line"
  done

  echo -e "  Seed data laden..."
  PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$SEED_FILE" 2>&1 | while read -r line; do
    echo "    $line"
  done

  echo -e "\n${BLUE}[5/6] Verificatie...${NC}"
  PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public' ORDER BY table_name;
  " 2>&1 | while read -r line; do
    echo "    $line"
  done

  PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
    SELECT c.name AS client, cbv.voice_name, cam.campaign_type, cam.status,
           (SELECT COUNT(*) FROM market_intelligence) AS intel_rows,
           (SELECT COUNT(*) FROM icp_scores) AS icp_rows
    FROM clients c
    LEFT JOIN client_brand_voices cbv ON cbv.client_id = c.id
    LEFT JOIN campaigns cam ON cam.client_id = c.id
    WHERE c.name = 'Recruitin';
  " 2>&1 | while read -r line; do
    echo "    $line"
  done

else
  # Geen psql — geef instructies voor SQL Editor
  echo -e "\n  ${YELLOW}psql niet gevonden. Gebruik de Supabase SQL Editor:${NC}"
  echo ""
  echo -e "  ${GREEN}OPTIE A: Kopieer en plak handmatig${NC}"
  echo -e "  1. Open: ${BLUE}https://supabase.com/dashboard/project/${PROJECT_REF}/sql/new${NC}"
  echo -e "  2. Plak inhoud van: ${SQL_FILE}"
  echo -e "     Klik Run"
  echo -e "  3. Plak inhoud van: ${SEED_FILE}"
  echo -e "     Klik Run"
  echo ""
  echo -e "  ${GREEN}OPTIE B: Installeer psql en draai dit script opnieuw${NC}"
  echo -e "  macOS:  brew install libpq && brew link --force libpq"
  echo -e "  Ubuntu: sudo apt-get install postgresql-client"
  echo ""
  echo -e "  ${GREEN}OPTIE C: Gebruik npx supabase CLI${NC}"
  echo -e "  npx supabase db execute --project-ref ${PROJECT_REF} < ${SQL_FILE}"
  echo -e "  npx supabase db execute --project-ref ${PROJECT_REF} < ${SEED_FILE}"
fi

# ---- Stap 6: .env bestand aanmaken ----
echo -e "\n${BLUE}[6/6] Environment configuratie opslaan...${NC}"

ENV_FILE="${SCRIPT_DIR}/.env"

cat > "$ENV_FILE" << ENVEOF
# Recruitin Growth Engine — Supabase Configuratie
# Gegenereerd: $(date -Iseconds)
SUPABASE_URL=${SUPABASE_URL}
SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
SUPABASE_PROJECT_REF=${PROJECT_REF}
ENVEOF

echo -e "  .env opgeslagen: ${ENV_FILE}"
echo -e "  ${RED}LET OP: Voeg .env toe aan .gitignore!${NC}"

# Voeg .env toe aan .gitignore als het er nog niet in staat
if [ -f "${SCRIPT_DIR}/.gitignore" ]; then
  if ! grep -q "^\.env$" "${SCRIPT_DIR}/.gitignore" 2>/dev/null; then
    echo ".env" >> "${SCRIPT_DIR}/.gitignore"
    echo -e "  .env toegevoegd aan .gitignore"
  fi
else
  echo ".env" > "${SCRIPT_DIR}/.gitignore"
  echo -e "  .gitignore aangemaakt met .env"
fi

# ---- Klaar ----
echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  Setup voltooid!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "  SQL bestanden bewaard op:"
echo -e "    Schema: ${SQL_FILE}"
echo -e "    Seeds:  ${SEED_FILE}"
echo ""
echo -e "  Volgende stappen:"
echo -e "    1. Verifieer tabellen in Supabase Dashboard > Table Editor"
echo -e "    2. Kopieer cowork-project-instructions.md naar je Claude Project"
echo -e "    3. Start je eerste campagne: ${BLUE}/recruitin-campaign authority${NC}"
echo ""
