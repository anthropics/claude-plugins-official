# State Schema v2

## JSON File Structure

The spire skill stores all run state in `~/.claude/spire/state.json` using this schema.

## Complete Schema

```json
{
  "version": "2.0.0",

  "run": {
    "id": "20250125-143000-ironclad-a14",
    "active": true,
    "character": "Ironclad" | "Silent" | "Defect" | "Watcher",
    "ascension": 0-20,
    "floor": 0-60,
    "act": 1 | 2 | 3 | 4,
    "screen": "neow" | "map" | "combat" | "card_reward" | "boss_relic" | "shop" | "event" | "rest" | "treasure" | "deck_view"
  },

  "player": {
    "hp": {
      "current": 0-999,
      "max": 0-999
    },
    "gold": 0-9999,
    "potions": {
      "slots": 2 | 3,
      "slot1": "Potion Name" | null,
      "slot2": "Potion Name" | null,
      "slot3": "Potion Name" | null
    }
  },

  "deck": {
    "cards": ["Card Name 1", "Card Name 2", ...],
    "size": 0-999,
    "attacks": ["Attack Card 1", ...],
    "skills": ["Skill Card 1", ...],
    "powers": ["Power Card 1", ...],
    "status": ["Status Card 1", ...],
    "curses": ["Curse Card 1", ...],
    "seen": ["Card A", "Card B", ...],
    "acquired": {
      "2": "Card Name",
      "5": "Another Card",
      "floor": "card_name"
    }
  },

  "relics": {
    "owned": ["Relic 1", "Relic 2", ...],
    "starter": "Starter Relic Name" | null,
    "boss": "Boss Relic Name" | null,
    "acquired": {
      "3": "Relic Name",
      "10": "Another Relic"
    }
  },

  "map": {
    "path": [0, 1, 2, 3, 4, 5],
    "currentNode": {"x": 5, "y": 2},
    "upcoming": [
      {"type": "elite", "floor": 8},
      {"type": "rest", "floor": 9}
    ],
    "actNodes": {
      "act1": 12,
      "act2": 0,
      "act3": 0,
      "act4": 0
    }
  },

  "combat": {
    "enemies": [
      {
        "name": "Enemy Name",
        "hp": 50,
        "intent": "attack" | "defend" | "buff" | "debuff" | "unknown",
        "value": 6,
        "block": 0
      }
    ],
    "hand": ["Card 1", "Card 2", "Card 3", "Card 4", "Card 5"],
    "energy": 0-9,
    "block": 0-999,
    "turn": 1-99
  },

  "rewards": {
    "cards": [
      {
        "name": "Card Name",
        "cost": 0-3,
        "type": "Attack" | "Skill" | "Power" | "Curse" | "Status",
        "rarity": "Common" | "Uncommon" | "Rare",
        "upgraded": true | false
      }
    ],
    "relics": ["Relic Name"]
  },

  "shop": {
    "cards": [
      {"name": "Card Name", "price": 50}
    ],
    "relics": [
      {"name": "Relic Name", "price": 150}
    ],
    "potions": [
      {"name": "Potion Name", "price": 50}
    ],
    "purgeCost": 50-100
  },

  "event": {
    "name": "Event Name",
    "choices": ["Choice 1", "Choice 2", "Choice 3"],
    "context": {}
  },

  "history": {
    "floors": [
      {
        "floor": 1,
        "type": "unknown" | "monster" | "elite" | "rest" | "shop" | "event" | "treasure",
        "outcome": "Description of what happened"
      }
    ],
    "choices": [
      {"floor": 2, "type": "card", "taken": "Card Name", "skipped": ["Card A", "Card B"]}
    ],
    "events": [
      {"floor": 5, "name": "Event Name", "choice": "Choice taken"}
    ],
    "cardsTaken": {
      "2": "Card Name"
    },
    "relicsTaken": {
      "3": "Relic Name"
    }
  },

  "preferences": {
    "riskTolerance": "high" | "medium" | "low",
    "deckSizePref": "lean" | "medium" | "fat",
    "favoriteArchetypes": ["strength", "block", "poison"],
    "cardTierOverrides": {
      "Card Name": "S" | "A" | "B" | "C" | "D"
    }
  },

  "metadata": {
    "createdAt": "2025-01-25T14:30:00Z",
    "lastUpdate": "2025-01-25T15:45:00Z",
    "screenshots": ["/path/to/screenshot1.png", "/path/to/screenshot2.png"],
    "migratedFrom": "v1" | null
  }
}
```

## Example: New Run Initialization

```json
{
  "version": "2.0.0",
  "run": {
    "id": "20250125-143000-ironclad-a14",
    "active": true,
    "character": "Ironclad",
    "ascension": 14,
    "floor": 0,
    "act": 1,
    "screen": "neow"
  },
  "player": {
    "hp": {"current": 80, "max": 80},
    "gold": 100,
    "potions": {"slots": 2, "slot1": null, "slot2": null, "slot3": null}
  },
  "deck": {
    "cards": ["Strike", "Strike", "Strike", "Strike", "Strike", "Defend", "Defend", "Defend", "Defend", "Bash"],
    "size": 10,
    "attacks": ["Strike", "Strike", "Strike", "Strike", "Strike", "Bash"],
    "skills": ["Defend", "Defend", "Defend", "Defend"],
    "powers": [],
    "status": [],
    "curses": [],
    "seen": ["Bash"],
    "acquired": {}
  },
  "relics": {
    "owned": ["Burning Blood"],
    "starter": "Burning Blood",
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
    "createdAt": "2025-01-25T14:30:00Z",
    "lastUpdate": "2025-01-25T14:30:00Z",
    "screenshots": [],
    "migratedFrom": null
  }
}
```

## Example: Mid-Run State

```json
{
  "version": "2.0.0",
  "run": {
    "id": "20250125-143000-ironclad-a14",
    "active": true,
    "character": "Ironclad",
    "ascension": 14,
    "floor": 7,
    "act": 1,
    "screen": "combat"
  },
  "player": {
    "hp": {"current": 45, "max": 84},
    "gold": 187,
    "potions": {"slots": 2, "slot1": "Fire Potion", "slot2": null, "slot3": null}
  },
  "deck": {
    "cards": ["Strike", "Strike", "Strike", "Strike", "Defend", "Defend", "Defend", "Defend", "Bash", "Pommel Strike", "Flex", "Inflame"],
    "size": 12,
    "attacks": ["Strike", "Strike", "Strike", "Strike", "Bash", "Pommel Strike"],
    "skills": ["Defend", "Defend", "Defend", "Defend", "Flex"],
    "powers": ["Inflame"],
    "status": [],
    "curses": [],
    "seen": ["Bash", "Pommel Strike", "Flex", "Inflame", "Cleave"],
    "acquired": {"2": "Pommel Strike", "3": "Flex", "4": "Inflame"}
  },
  "relics": {
    "owned": ["Burning Blood", "Vajra"],
    "starter": "Burning Blood",
    "boss": null,
    "acquired": {"3": "Vajra"}
  },
  "map": {
    "path": [0, 1, 2, 3, 4, 5, 6],
    "currentNode": {"x": 3, "y": 2},
    "upcoming": [{"type": "elite", "floor": 8}],
    "actNodes": {"act1": 12, "act2": 0, "act3": 0, "act4": 0}
  },
  "combat": {
    "enemies": [{"name": "Cultist", "hp": 24, "intent": "attack", "value": 6, "block": 0}],
    "hand": ["Strike", "Bash", "Defend", "Defend"],
    "energy": 3,
    "block": 0,
    "turn": 2
  },
  "rewards": {"cards": [], "relics": []},
  "shop": {"cards": [], "relics": [], "potions": [], "purgeCost": null},
  "event": {},
  "history": {
    "floors": [
      {"floor": 1, "type": "unknown", "outcome": "gained 3 max HP"},
      {"floor": 2, "type": "monster", "outcome": "victory, took Pommel Strike"},
      {"floor": 3, "type": "elite", "outcome": "victory, took Vajra"},
      {"floor": 4, "type": "rest", "outcome": "smithed Pommel Strike"},
      {"floor": 5, "type": "monster", "outcome": "victory, took Flex"},
      {"floor": 6, "type": "monster", "outcome": "victory, took Inflame"},
      {"floor": 7, "type": "monster", "outcome": "in progress"}
    ],
    "choices": [
      {"floor": 2, "type": "card", "taken": "Pommel Strike", "skipped": ["Iron Wave", "Flex"]},
      {"floor": 5, "type": "card", "taken": "Flex", "skipped": ["Clothesline", "Iron Wave"]},
      {"floor": 6, "type": "card", "taken": "Inflame", "skipped": ["Armaments", "Body Slam"]}
    ],
    "events": [],
    "cardsTaken": {"2": "Pommel Strike", "5": "Flex", "6": "Inflame"},
    "relicsTaken": {"3": "Vajra"}
  },
  "preferences": {
    "riskTolerance": "medium",
    "deckSizePref": "medium",
    "favoriteArchetypes": ["strength"],
    "cardTierOverrides": {}
  },
  "metadata": {
    "createdAt": "2025-01-25T14:30:00Z",
    "lastUpdate": "2025-01-25T15:45:00Z",
    "screenshots": ["/path/to/screenshot.png"],
    "migratedFrom": null
  }
}
```

## Migration from v1

v1 used flat keys with `sts:` prefix in memory-keeper. v2 uses nested JSON structure.

| v1 Key | v2 Path |
|--------|---------|
| `sts:run:id` | `.run.id` |
| `sts:character` | `.run.character` |
| `sts:hp:current` | `.player.hp.current` |
| `sts:deck:current` | `.deck.cards` |
| `sts:relics:current` | `.relics.owned` |
| `sts:combat:enemies` | `.combat.enemies` |
| `sts:rewards:cards` | `.rewards.cards` |

See `scripts/migrate-v1-to-v2.sh` for automated migration.

---

## Session-Based State Organization (v2.1.0)

### Directory Structure

Starting with v2.1.0, state is organized per Claude session:

```
~/.claude/spire/
└── sessions/
    └── [session-uuid]/
        ├── state.json
        └── backups/
            ├── state-YYYYMMDD-HHMMSS.json
            └── ...
```

### Session ID Resolution

The current session is determined by:
1. Finding the most recently modified `~/.claude/session-env/[uuid]/` directory
2. This corresponds to the active Claude Code conversation
3. Each session gets isolated run state

### Benefits

- **Isolation**: Multiple conversations can track different runs simultaneously
- **Context Preservation**: Switching conversations doesn't lose run state
- **Cleanup**: Old completed runs can be archived or deleted
- **Migration**: Legacy state preserved in 'default' session

### Migration from v2.0.x

v2.0.x used a single state file at `~/.claude/spire/state.json`.
v2.1.0 automatically migrates this to `sessions/default/state.json`.

No manual action required - migration happens on first use.

### New Metadata Fields

```json
{
  "metadata": {
    "createdAt": "2025-01-25T14:30:00Z",
    "lastUpdate": "2025-01-25T15:45:00Z",
    "screenshots": [],
    "migratedFrom": "legacy",  // Added in v2.1.0
    "migratedAt": "2025-01-25T15:45:00Z",  // Added in v2.1.0
    "parallelProcessing": {  // Added in v2.2.0
      "enabled": true,
      "disabled": false,
      "lastUsed": "2025-01-25T16:00:00Z",
      "failures": 0,
      "fallbackCount": 0,
      "lastFailure": null,
      "lastFallback": null
    },
    "agents": {  // Added in v2.2.0
      "screenshotAnalyzer": {
        "running": false,
        "lastUsed": null
      },
      "knowledgeLoader": {
        "cachedFiles": [],
        "lastCacheHit": null
      },
      "statusMonitor": {
        "running": false,
        "startedAt": null,
        "lastUpdate": null
      },
      "cardAdvisor": {
        "running": false,
        "lastAnalyzed": null,
        "lastUpdate": null
      }
    }
  }
}
```

## Parallel Processing Metadata (v2.2.0)

### parallelProcessing Object

Tracks parallel sub-agent usage and circuit breaker state:

```json
{
  "parallelProcessing": {
    "enabled": true,           // Global enable flag
    "disabled": false,         // Circuit breaker - disables after 3 failures
    "lastUsed": "2025-01-25T16:00:00Z",  // ISO timestamp of last successful parallel use
    "failures": 0,             // Consecutive failure count
    "fallbackCount": 5,        // Total fallbacks to sequential mode
    "lastFailure": null,       // Last failure reason (string or null)
    "lastFallback": null       // Last fallback reason (string or null)
  }
}
```

**Circuit Breaker Logic:**
- `disabled` set to `true` after 3 consecutive `failures`
- When `disabled: true`, all processing uses sequential mode
- Reset via `reset_parallel_circuit_breaker()` function

### agents Object

Tracks background agent status:

```json
{
  "agents": {
    "screenshotAnalyzer": {
      "running": false,
      "lastUsed": null
    },
    "knowledgeLoader": {
      "cachedFiles": ["archetypes", "cards"],
      "lastCacheHit": "2025-01-25T16:00:00Z"
    },
    "statusMonitor": {
      "running": true,
      "startedAt": "2025-01-25T15:30:00Z",
      "lastUpdate": "2025-01-25T16:00:00Z"
    },
    "cardAdvisor": {
      "running": true,
      "lastAnalyzed": "2025-01-25T16:00:00Z",
      "lastUpdate": "2025-01-25T16:00:00Z"
    }
  }
}
```

**Agent Status:**
- `running`: Boolean indicating if agent is active
- Timestamps in ISO 8601 format (UTC)
- `cachedFiles`: Array of currently cached knowledge files
