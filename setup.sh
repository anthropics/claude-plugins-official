#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════
#  COE Pricing Intelligence — Setup Script
#  Al-Futtaim Automotive | UC Pricing COE
#  Run from: claude-plugins-official/ root
# ══════════════════════════════════════════════════════════════════

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
  echo ""
  echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
  echo -e "${BLUE}  COE Pricing Intelligence — Setup${NC}"
  echo -e "${BLUE}  Al-Futtaim Automotive | UC Pricing COE${NC}"
  echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
  echo ""
}

check_ok()   { echo -e "  ${GREEN}✓${NC}  $1"; }
check_warn() { echo -e "  ${YELLOW}⚠${NC}  $1"; }
check_fail() { echo -e "  ${RED}✗${NC}  $1"; }

print_header

# ── 1. Prerequisites ──────────────────────────────────────────────
echo "Checking prerequisites..."

node_ver=$(node --version 2>/dev/null || echo "NOT FOUND")
if [[ "$node_ver" == "NOT FOUND" ]]; then
  check_fail "Node.js not found. Install from https://nodejs.org"
  exit 1
else
  check_ok "Node.js $node_ver"
fi

if command -v claude &> /dev/null; then
  claude_ver=$(claude --version 2>/dev/null || echo "installed")
  check_ok "Claude Code CLI: $claude_ver"
else
  check_warn "Claude Code CLI not found — install with: npm install -g @anthropic-ai/claude-code"
fi

echo ""

# ── 2. Install plugin dependencies ───────────────────────────────
echo "Installing plugin dependencies..."
npm install --silent
check_ok "Plugin dependencies installed"
echo ""

# ── 3. Validate manifest ──────────────────────────────────────────
echo "Validating plugin manifest..."
node -e "
  const m = require('./.claude-plugin/manifest.json');
  const count = m.commands.length;
  console.log('  Commands registered: ' + count);
  if (count !== 9) process.exit(1);
" || { check_fail "Manifest validation failed"; exit 1; }
check_ok "Manifest valid — 9 commands registered"
echo ""

# ── 4. Test plugin dispatcher ─────────────────────────────────────
echo "Testing plugin dispatcher..."
node -e "
  const { dispatch } = require('./plugins/coe-pricing/index');
  dispatch('vin-scan', { vin: 'JTMAU7BJ5R4049000' })
    .then(r => { console.log('  Dispatcher OK — command: ' + r.command); })
    .catch(e => { console.error(e.message); process.exit(1); });
"
check_ok "Dispatcher test passed"
echo ""

# ── 5. Check linked services ──────────────────────────────────────
echo "Checking linked services..."

check_service() {
  local name=$1
  local url=$2
  if curl -s --max-time 2 "$url" > /dev/null 2>&1; then
    check_ok "$name is ONLINE ($url)"
  else
    check_warn "$name is OFFLINE ($url) — start it to enable live pricing"
  fi
}

check_service "af-pricing-agent     " "http://localhost:3001/api/health"
check_service "vehicle-pricing-widget" "http://localhost:5173"
check_service "Dubizzle scraper     " "http://localhost:3002/api/health"
echo ""

# ── 6. Run CLI health check ───────────────────────────────────────
echo "Running CLI health check..."
node cli.js health
echo ""

# ── 7. VS Code extension hint ─────────────────────────────────────
echo -e "${YELLOW}VS Code Extension Setup:${NC}"
echo "  1. Open this folder in VS Code"
echo "  2. Press F5 to launch Extension Development Host"
echo "  3. OR: install vsce and package:  npx vsce package"
echo ""

# ── 8. Done ───────────────────────────────────────────────────────
echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Setup complete!${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════════════${NC}"
echo ""
echo "  Quick test commands:"
echo "    node cli.js vin-scan --vin JTMAU7BJ5R4049000"
echo "    node cli.js master-scan --vin JTMAU7BJ5R4049000 --make Toyota --model \"Land Cruiser\" --year 2024"
echo ""
echo "  In VS Code (Ctrl+Shift+P):"
echo "    > COE: ★ Master Full Scan (All 7 Modules)"
echo "    > COE: VIN Intelligence Scan"
echo "    > COE: Generate Copilot Handoff Block"
echo ""
echo "  Keyboard shortcuts:"
echo "    Ctrl+Shift+M  →  Master Full Scan"
echo "    Ctrl+Shift+H  →  Copilot Handoff"
echo ""
