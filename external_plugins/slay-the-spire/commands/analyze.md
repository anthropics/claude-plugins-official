---
allowed-tools: all
description: Analyze a Slay the Spire screenshot
---

# Analyze Screenshot

Invoke @spire:spire to analyze a Slay the Spire screenshot and extract game data.

## Usage

**With a screenshot:**
```
/slay-the-spire:analyze /path/to/screenshot.png
```

**Run current state analysis:**
```
/slay-the-spire:analyze
```

This will:
- Detect the screen type (combat, map, rewards, shop, event, etc.)
- Extract all visible game data (cards, relics, HP, gold, etc.)
- Update your run state in `~/.claude/spire/sessions/[session-id]/state.json`
- Provide strategic advice based on the current situation
