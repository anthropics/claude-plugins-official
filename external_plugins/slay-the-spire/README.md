# Slay the Spire AI Assistant

A Claude Code plugin that parses Slay the Spire screenshots, tracks run state, detects deck archetypes, and provides AI-powered strategic advice.

**Version 1.0.0** - Zero MCP dependencies required!

## Features

- **Screenshot Analysis** - Automatically detects 10 screen types (map, combat, rewards, shop, event, etc.)
- **State Tracking** - Persistent JSON-based state storage (no session memory drift)
- **Archetype Detection** - Identifies your deck archetype with confidence scoring
- **Strategic Advice** - Card/relic recommendations based on your current build
- **Combat Analysis** - Enemy intent reading and turn-by-turn suggestions
- **Run Export** - Optional markdown run trackers for sharing and review

## Requirements

- Claude Code installed
- `jq` installed (`brew install jq` on macOS)
- Slay the Spire (obviously)

## Installation

### From GitHub Marketplace

```bash
# Add marketplace
claude plugin marketplace add slay-the-spire https://github.com/ben-w-smith/spire

# Install plugin
claude plugin install slay-the-spire@slay-the-spire
```

### From Official Claude Code Marketplace (Coming Soon)

If approved, installation will be:
```bash
claude plugin install slay-the-spire@claude-plugin-directory
```

## Quick Start

### 1. Start a New Run

```
User: /slay-the-spire:start
Assistant: Starting new run tracking session...
Please share a Neow screen screenshot to begin tracking.
```

### 2. Analyze a Screenshot

```
User: /slay-the-spire:analyze ~/Desktop/sts-combat.png
Assistant: ## Screen: Combat — Floor 7

### Extracted State
- HP: 45/80
- Gold: 187
- Enemies: Cultist (24 HP, Intent: Attack 6)
- Hand: Strike, Bash, Defend, Defend

### Analysis
[Archetype detection, advice, recommendations]
```

### 3. Export Run Tracker

```
User: /slay-the-spire:export
Assistant: Exported run state to: ~/Documents/STS-Runs/20250125-143000-ironclad-a14.md
```

### 4. Reset Run

```
User: /slay-the-spire:reset
Assistant: Run state reset. Ready for a new run!
```

## Commands

| Command | Description |
|---------|-------------|
| `/slay-the-spire:start [path]` | Start new run tracking session |
| `/slay-the-spire:analyze [path]` | Analyze screenshot and update run state |
| `/slay-the-spire:export [path]` | Export run tracker as markdown |
| `/slay-the-spire:reset` | Reset current run state |

## State Management

Run state is stored in `~/.claude/spire/state.json` with automatic backups created before each update.

### Manual State Operations

```bash
# View current state
cat ~/.claude/spire/state.json | jq .

# Reset state (same as /slay-the-spire:reset)
rm ~/.claude/spire/state.json
```

## Supported Screen Types

1. **Neow/Character Select** - Character, ascension, bonus selection
2. **Map Screen** - Floor, path, node types, upcoming routes
3. **Combat** - Enemies, intents, hand cards, energy, block
4. **Card Reward** - Three cards with rarities and costs
5. **Boss Relic** - Current vs offered boss relic
6. **Shop** - Cards, relics, potions with prices
7. **Event** - Event name, description, choices
8. **Rest Site** - Rest, Smith, Recall, Dig options
9. **Treasure Room** - Relic acquisition
10. **Deck View** - Full card list with counts

## Knowledge Base

The plugin includes curated Slay the Spire knowledge for:
- Deck archetypes and card synergies
- Card tier lists and recommendations
- Relic effects and rankings
- Event choice guidance
- Watcher stance mechanics

## Troubleshooting

### "jq: command not found"

Install jq:
```bash
brew install jq  # macOS
```

### "State file has invalid JSON"

Check the state file:
```bash
cat ~/.claude/spire/state.json | jq .
```

If corrupted, restore from backup:
```bash
source ~/.claude/plugins/spire/scripts/state-helpers.sh
restore_backup state-YYYYMMDD-HHMMSS.json
```

### Screenshot not detected

Ensure:
- Screenshot is in PNG/JPG format
- Image is clear and readable
- Slay the Spire is in English
- All game UI elements are visible

## License

MIT License - see [LICENSE](LICENSE) file.

## Acknowledgments

- Built for Claude Code
- Knowledge base compiled from community guides
- Inspired by the Slay the Spire community

## Links

- **GitHub:** https://github.com/ben-w-smith/spire
- **Issues:** https://github.com/ben-w-smith/spire/issues
- **Claude Code Docs:** https://code.claude.com

---

**Version:** 1.0.0
**Last Updated:** 2025-01-25
**Author:** Ben Smith
