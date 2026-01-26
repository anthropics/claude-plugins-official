# Slay the Spire Run - {CHARACTER} A{ASCENSION}

## Run Overview

| Field | Value |
|-------|-------|
| **Character** | {CHARACTER} |
| **Ascension** | A{ASCENSION} |
| **Started** | {TIMESTAMP} |
| **Current Floor** | {FLOOR} |
| **Current Act** | {ACT} |
| **Status** | {STATUS} |

---

## Current State

### Resources
- **HP**: {CURRENT_HP}/{MAX_HP} ({PERCENT}%)
- **Gold**: {GOLD}
- **Potions**: [{POTION1}] [{POTION2}] [{POTION3}]

### Deck
- **Size**: {DECK_SIZE} cards
- **Attacks**: {ATTACK_COUNT}
- **Skills**: {SKILL_COUNT}
- **Powers**: {POWER_COUNT}
- **Status/Curses**: {CURSE_COUNT}

### Relics ({RELIC_COUNT})
{RELIC_LIST}

### Detected Archetype
**{ARCHETYPE_NAME}** (Confidence: {CONFIDENCE})
- **Core cards identified**: {CORE_CARDS}
- **Missing**: {MISSING_CARDS}
- **Strengths**: {STRENGTHS}
- **Weaknesses**: {WEAKNESSES}

---

## Floor Log

### Floor {FLOOR} - {NODE_TYPE}
- **Encounter**: {ENEMY_NAME|EVENT_NAME|SHOP|REST_SITE}
- **Outcome**: {OUTCOME}
- **Rewards**: {REWARDS}
- **State Changes**: {HP_CHANGE}, {GOLD_CHANGE}, {NEW_CARDS}, {NEW_RELICS}

---

## Path Taken

### Act 1 (Exordia)
{FLOOR_1}({NODE_TYPE}) → {FLOOR_2}({NODE_TYPE}) → {FLOOR_3}({NODE_TYPE}) → ... → {BOSS_FLOOR}(B)

**Summary**:
- Monsters: {MONSTER_COUNT}
- Elites: {ELITE_COUNT}
- Shops: {SHOP_COUNT}
- Rest Sites: {REST_COUNT}
- Unknowns: {UNKNOWN_COUNT}
- Events: {EVENT_LIST}

### Act 2 (City)
[... same structure ...]

### Act 3 (The Beyond)
[... same structure ...]

### Act 4 (The Spire)
[... same structure ...]

---

## Deck Composition

### Attacks ({ATTACK_COUNT})
| Card | Count | Upgraded |
|------|-------|----------|
| {CARD_NAME} | x{COUNT} | {YES/NO} |
[... list all attacks ...]

### Skills ({SKILL_COUNT})
| Card | Count | Upgraded |
|------|-------|----------|
| {CARD_NAME} | x{COUNT} | {YES/NO} |
[... list all skills ...]

### Powers ({POWER_COUNT})
| Card | Count | Upgraded |
|------|-------|----------|
| {CARD_NAME} | x{COUNT} | {YES/NO} |
[... list all powers ...]

### Status/Curses ({CURSE_COUNT})
| Card | Count | Upgraded |
|------|-------|----------|
| {CARD_NAME} | x{COUNT} | {YES/NO} |
[... list all status/curses ...]

---

## Upgrade Progress
- **Upgraded**: {UPGRADED_COUNT}/{TOTAL_CARDS} ({PERCENT}%)
- **Priority Upgrades Needed**: {PRIORITY_UPGRADES}

---

## Relic Effects Analysis
{RELIC_SYNERGIES}

---

## Key Synergies Detected
{SYNERGY_LIST}

---

## Weaknesses
{WEAKNESS_LIST}

---

## Notes
{USER_NOTES}
