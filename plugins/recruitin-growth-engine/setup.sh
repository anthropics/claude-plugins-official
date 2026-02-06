#!/usr/bin/env bash
# ============================================================
# Recruitin Growth Engine — One-Click Setup
#
# Gebruik: bash setup.sh
#
# Dit script:
#   1. Installeert psql als dat nog niet aanwezig is (macOS)
#   2. Maakt alle database tabellen aan in Supabase
#   3. Vult seed data in (Recruitin client, market intelligence, ICP scores)
#   4. Slaat credentials op in .env
#   5. Verifieert dat alles werkt
# ============================================================

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SQL_FILE="${SCRIPT_DIR}/setup-complete.sql"

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║  Recruitin Growth Engine — Database Setup    ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════╝${NC}"
echo ""

# ---- Check SQL bestand ----
if [ ! -f "$SQL_FILE" ]; then
  echo -e "${RED}FOUT: setup-complete.sql niet gevonden in ${SCRIPT_DIR}${NC}"
  exit 1
fi

# ---- Credentials verzamelen ----
echo -e "${BOLD}Stap 1: Supabase Credentials${NC}"
echo ""

# Check of er al een .env is
if [ -f "${SCRIPT_DIR}/.env" ]; then
  echo -e "${YELLOW}Bestaande .env gevonden. Credentials laden...${NC}"
  source "${SCRIPT_DIR}/.env"
fi

# Project ref
if [ -z "${SUPABASE_PROJECT_REF:-}" ]; then
  echo -e "  Voer je Supabase ${BOLD}Project Reference${NC} in"
  echo -e "  (Vind je op: Settings > General > Reference ID)"
  echo -ne "  > "
  read -r SUPABASE_PROJECT_REF
fi
echo -e "  Project ref: ${GREEN}${SUPABASE_PROJECT_REF}${NC}"

# Database wachtwoord
echo ""
echo -e "  Voer je Supabase ${BOLD}Database Password${NC} in"
echo -e "  (Het wachtwoord dat je koos bij het aanmaken van je project)"
echo -e "  (Vind/reset je op: Settings > Database > Database password)"
echo -ne "  > "
read -rs DB_PASSWORD
echo ""

# Service Role Key
if [ -z "${SUPABASE_SERVICE_ROLE_KEY:-}" ]; then
  echo ""
  echo -e "  Voer je ${BOLD}Service Role Key${NC} in"
  echo -e "  (Settings > Data API > service_role key)"
  echo -ne "  > "
  read -rs SUPABASE_SERVICE_ROLE_KEY
  echo ""
fi

SUPABASE_URL="https://${SUPABASE_PROJECT_REF}.supabase.co"
DB_HOST="db.${SUPABASE_PROJECT_REF}.supabase.co"

# ---- psql installeren indien nodig ----
echo ""
echo -e "${BOLD}Stap 2: PostgreSQL client checken${NC}"
echo ""

if command -v psql &>/dev/null; then
  echo -e "  psql: ${GREEN}gevonden$(psql --version 2>/dev/null | head -1)${NC}"
else
  echo -e "  psql: ${YELLOW}niet gevonden${NC}"

  if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "  ${BLUE}Installeren via Homebrew...${NC}"
    if command -v brew &>/dev/null; then
      brew install libpq 2>/dev/null && brew link --force libpq 2>/dev/null
      if command -v psql &>/dev/null; then
        echo -e "  psql: ${GREEN}geinstalleerd${NC}"
      else
        # Homebrew zet psql soms in een niet-standaard pad
        export PATH="/opt/homebrew/opt/libpq/bin:$PATH"
        if command -v psql &>/dev/null; then
          echo -e "  psql: ${GREEN}geinstalleerd (via /opt/homebrew)${NC}"
        else
          echo -e "  ${RED}Installatie mislukt. Probeer handmatig: brew install libpq${NC}"
          exit 1
        fi
      fi
    else
      echo -e "  ${RED}Homebrew niet gevonden. Installeer eerst Homebrew:${NC}"
      echo -e "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
      exit 1
    fi
  elif [[ "$OSTYPE" == "linux"* ]]; then
    echo -e "  ${BLUE}Installeren via apt...${NC}"
    sudo apt-get update -qq && sudo apt-get install -y -qq postgresql-client
    if command -v psql &>/dev/null; then
      echo -e "  psql: ${GREEN}geinstalleerd${NC}"
    else
      echo -e "  ${RED}Installatie mislukt. Probeer handmatig: sudo apt-get install postgresql-client${NC}"
      exit 1
    fi
  else
    echo -e "  ${RED}Installeer psql handmatig voor jouw OS${NC}"
    exit 1
  fi
fi

# ---- Connectie testen ----
echo ""
echo -e "${BOLD}Stap 3: Connectie testen${NC}"
echo ""

export PGPASSWORD="$DB_PASSWORD"

if psql -h "$DB_HOST" -p 5432 -U postgres -d postgres -c "SELECT 1;" &>/dev/null; then
  echo -e "  Database connectie: ${GREEN}OK${NC}"
else
  echo -e "  Database connectie: ${RED}MISLUKT${NC}"
  echo ""
  echo -e "  Mogelijke oorzaken:"
  echo -e "  - Verkeerd database wachtwoord"
  echo -e "  - Project is gepauzeerd in Supabase"
  echo -e "  - Netwerk blokkering"
  echo ""
  echo -e "  ${YELLOW}Reset je wachtwoord op:${NC}"
  echo -e "  https://supabase.com/dashboard/project/${SUPABASE_PROJECT_REF}/settings/database"
  exit 1
fi

# ---- SQL uitvoeren ----
echo ""
echo -e "${BOLD}Stap 4: Database schema + seed data aanmaken${NC}"
echo ""

echo -e "  SQL uitvoeren vanuit: ${SQL_FILE}"
echo ""

RESULT=$(psql -h "$DB_HOST" -p 5432 -U postgres -d postgres -f "$SQL_FILE" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo -e "  ${GREEN}SQL succesvol uitgevoerd!${NC}"
else
  echo -e "  ${RED}SQL fouten gevonden:${NC}"
  echo "$RESULT" | grep -i "error" | head -10
  echo ""
  echo -e "  ${YELLOW}Niet alle stappen zijn gelukt. Check de output hierboven.${NC}"
fi

# ---- Verificatie ----
echo ""
echo -e "${BOLD}Stap 5: Verificatie${NC}"
echo ""

echo -e "  ${BLUE}Tabellen:${NC}"
psql -h "$DB_HOST" -p 5432 -U postgres -d postgres -t -c "
  SELECT '    ✓ ' || table_name
  FROM information_schema.tables
  WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
  ORDER BY table_name;
" 2>/dev/null

echo ""
echo -e "  ${BLUE}Materialized Views:${NC}"
psql -h "$DB_HOST" -p 5432 -U postgres -d postgres -t -c "
  SELECT '    ✓ ' || matviewname
  FROM pg_matviews
  WHERE schemaname = 'public';
" 2>/dev/null

echo ""
echo -e "  ${BLUE}Seed Data:${NC}"
psql -h "$DB_HOST" -p 5432 -U postgres -d postgres -t -c "
  SELECT '    Clients: ' || COUNT(*) FROM clients;
" 2>/dev/null
psql -h "$DB_HOST" -p 5432 -U postgres -d postgres -t -c "
  SELECT '    Brand Voices: ' || COUNT(*) FROM client_brand_voices;
" 2>/dev/null
psql -h "$DB_HOST" -p 5432 -U postgres -d postgres -t -c "
  SELECT '    Campaigns: ' || COUNT(*) FROM campaigns;
" 2>/dev/null
psql -h "$DB_HOST" -p 5432 -U postgres -d postgres -t -c "
  SELECT '    Market Intelligence: ' || COUNT(*) FROM market_intelligence;
" 2>/dev/null
psql -h "$DB_HOST" -p 5432 -U postgres -d postgres -t -c "
  SELECT '    ICP Scores: ' || COUNT(*) FROM icp_scores;
" 2>/dev/null

# ---- .env opslaan ----
echo ""
echo -e "${BOLD}Stap 6: Configuratie opslaan${NC}"
echo ""

cat > "${SCRIPT_DIR}/.env" << ENVEOF
# Recruitin Growth Engine — Supabase Configuratie
# Gegenereerd: $(date '+%Y-%m-%d %H:%M')
SUPABASE_URL=${SUPABASE_URL}
SUPABASE_PROJECT_REF=${SUPABASE_PROJECT_REF}
SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
ENVEOF

echo -e "  .env opgeslagen in: ${SCRIPT_DIR}/.env"

# Zorg dat .env in .gitignore staat
if [ -f "${SCRIPT_DIR}/.gitignore" ]; then
  if ! grep -q "^\.env$" "${SCRIPT_DIR}/.gitignore" 2>/dev/null; then
    echo ".env" >> "${SCRIPT_DIR}/.gitignore"
  fi
fi

unset PGPASSWORD

# ---- Klaar ----
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Setup voltooid!                             ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BOLD}Volgende stappen:${NC}"
echo ""
echo -e "  1. Kopieer ${BLUE}cowork-project-instructions.md${NC}"
echo -e "     naar je Claude Project Instructions op claude.ai"
echo ""
echo -e "  2. Koppel Supabase MCP in je Cowork project"
echo -e "     URL: ${SUPABASE_URL}"
echo ""
echo -e "  3. Start je eerste campagne:"
echo -e "     ${BLUE}/recruitin-campaign authority${NC}"
echo ""
