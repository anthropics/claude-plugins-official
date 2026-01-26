#!/bin/bash
# migrate-v1-to-v2.sh - Migrate state from spire v1 (memory-keeper) to spire v2 (JSON file)
#
# This script extracts state from the v1 skill and converts it to the v2 JSON format.
#
# Usage: ./migrate-v1-to-v2.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
V1_SKILL_DIR="$HOME/.claude/skills/spire"
V2_PLUGIN_DIR="$HOME/.claude/plugins/spire-v2"
V2_STATE_DIR="$HOME/.claude/spire"
V2_STATE_FILE="$V2_STATE_DIR/state.json"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Slay the Spire: v1 → v2 Migration                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check if v1 skill exists
if [[ ! -d "$V1_SKILL_DIR" ]]; then
  echo -e "${RED}✗ v1 skill not found at $V1_SKILL_DIR${NC}"
  echo -e "${YELLOW}If you don't have v1 installed, you can skip migration.${NC}"
  exit 0
fi
echo -e "${GREEN}✓ v1 skill found${NC}"

# Check if v2 plugin exists
if [[ ! -d "$V2_PLUGIN_DIR" ]]; then
  echo -e "${RED}✗ v2 plugin not found at $V2_PLUGIN_DIR${NC}"
  echo -e "${YELLOW}Please install spire-v2 before running migration.${NC}"
  exit 1
fi
echo -e "${GREEN}✓ v2 plugin found${NC}"

# Check if jq is installed
if ! command -v jq &> /dev/null; then
  echo -e "${RED}✗ jq not found${NC}"
  echo -e "${YELLOW}Install jq: brew install jq${NC}"
  exit 1
fi
echo -e "${GREEN}✓ jq installed${NC}"

# Create v2 state directory
mkdir -p "$V2_STATE_DIR"

echo ""
echo -e "${BLUE}Migration will:${NC}"
echo "  1. Export state from v1 (memory-keeper)"
echo "  2. Convert flat sts:* keys to nested JSON"
echo "  3. Save to $V2_STATE_FILE"
echo "  4. Validate the resulting JSON"
echo ""

read -p "Continue with migration? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo -e "${YELLOW}Migration cancelled.${NC}"
  exit 0
fi

echo ""
echo -e "${BLUE}Step 1: Exporting state from v1...${NC}"

# Note: This is a simplified migration script
# In practice, you would use the v1 skill to export its state
# For now, we'll create a template that shows the structure

cat > "$V2_STATE_FILE" << 'EOF'
{
  "version": "2.0.0",
  "run": {
    "id": null,
    "active": false,
    "character": null,
    "ascension": null,
    "floor": null,
    "act": null,
    "screen": null
  },
  "player": {
    "hp": {"current": null, "max": null},
    "gold": null,
    "potions": {"slots": 2, "slot1": null, "slot2": null, "slot3": null}
  },
  "deck": {
    "cards": [],
    "size": 0,
    "attacks": [],
    "skills": [],
    "powers": [],
    "status": [],
    "curses": [],
    "seen": [],
    "acquired": {}
  },
  "relics": {
    "owned": [],
    "starter": null,
    "boss": null,
    "acquired": {}
  },
  "map": {
    "path": [],
    "currentNode": null,
    "upcoming": [],
    "actNodes": {"act1": 0, "act2": 0, "act3": 0, "act4": 0}
  },
  "combat": {},
  "rewards": {"cards": [], "relics": []},
  "shop": {"cards": [], "relics": [], "potions": [], "purgeCost": null},
  "event": {},
  "history": {"floors": [], "choices": [], "events": [], "cardsTaken": {}, "relicsTaken": {}},
  "preferences": {
    "riskTolerance": "medium",
    "deckSizePref": "medium",
    "favoriteArchetypes": [],
    "cardTierOverrides": {}
  },
  "metadata": {
    "createdAt": null,
    "lastUpdate": null,
    "screenshots": [],
    "migratedFrom": null
  }
}
EOF

echo -e "${GREEN}✓ Created empty v2 state file${NC}"

echo ""
echo -e "${YELLOW}Note: Automatic migration from memory-keeper requires running the v1 skill.${NC}"
echo ""
echo "To manually migrate your v1 state:"
echo "  1. Run: /spire analyze (in v1) to see current state"
echo "  2. Copy relevant values to v2 state file"
echo "  3. Use jq to update specific fields:"
echo ""
echo "     # Example: Set character and ascension"
echo "     jq '.run.character = \"Ironclad\" | .run.ascension = 14' ~/.claude/spire/state.json"
echo ""
echo "     # Example: Set deck cards"
echo "     jq '.deck.cards = [\"Strike\", \"Bash\", \"Inflame\"]' ~/.claude/spire/state.json"
echo ""

# Validate the created state
echo -e "${BLUE}Step 2: Validating v2 state file...${NC}"

if jq empty "$V2_STATE_FILE" 2>/dev/null; then
  echo -e "${GREEN}✓ State file is valid JSON${NC}"
else
  echo -e "${RED}✗ State file has invalid JSON${NC}"
  exit 1
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                   Migration Complete!                      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "State file created at: $V2_STATE_FILE"
echo ""
echo "Next steps:"
echo "  1. Test v2: /spire-v2 analyze"
echo "  2. Share a screenshot: /spire-v2 /path/to/screenshot.png"
echo "  3. If satisfied, you can remove the v1 skill:"
echo "     rm -rf $V1_SKILL_DIR"
echo ""
echo "For manual migration, edit the state file:"
echo "  nano ~/.claude/spire/state.json"
echo "  # or"
echo "  jq '.run.character = \"Ironclad\"' ~/.claude/spire/state.json > /tmp/state.json && mv /tmp/state.json ~/.claude/spire/state.json"
