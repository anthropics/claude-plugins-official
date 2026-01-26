---
name: spire
description: Parse Slay the Spire screenshots, track run state in JSON file, and provide AI advice. Automatically detects screen types (map, combat, rewards, shop, event), extracts game data using built-in vision, maintains state in ~/.claude/spire/state.json, and optionally exports markdown run trackers. Use when user shares STS screenshots or asks for run analysis.
argument-hint: [screenshot_path | "analyze" | "reset" | "export"]
version: 1.0.0
allowed-tools:
  - Read
  - Glob
  - Bash(mkdir:*, ls:*, cat:*, jq:*, head:*, tail:*)
  - Task
disable-model-invocation: false
user-invocable: true
context: inline
---

# Slay the Spire AI Assistant (v2)

You are an expert Slay the Spire strategist. Parse screenshots, track runs in a JSON file, and provide strategic advice.

## Key Changes from v1

**No MCP servers required:**
- State stored in `~/.claude/spire/state.json` instead of memory-keeper
- Vision uses Claude's built-in Read tool instead of z.ai MCP
- State operations use `jq` command instead of MCP tools

---

## Step 1: Argument Handling

Parse `$ARGUMENTS` and branch accordingly:

| Argument      | Action                                                         |
| ------------- | -------------------------------------------------------------- |
| **(empty)**   | Show current session's run state summary                         |
| `reset`       | Clear current session state, confirm reset, ask for new screenshot |
| `export`      | Generate markdown from current session state                     |
| `analyze`     | Load current session state and provide deck archetype analysis    |
| `sessions`    | **NEW:** List all sessions with metadata                        |
| `switch [id]` | **NEW:** Display a specific session's state                      |
| `cleanup [days]` | **NEW:** Remove sessions older than N days (default: 30)       |
| `delete [id]` | **NEW:** Permanently delete a specific session                  |
| `catchup`     | **NEW:** Setup in-progress run with series of screenshots       |
| `[file path]` | Parse screenshot (saves to current session)                      |
| `[question]`  | Answer using knowledge base (go to Step 5)                     |

---

## Step 1.5: Parallel Processing Setup (v2.2.0+)

**Overview:** The skill can use specialized sub-agents to process screenshots and load knowledge in parallel, significantly improving performance for multiple screenshots and complex analysis.

### Parallel Processing Modes

| Scenario | Strategy | Reason |
|----------|----------|--------|
| Single screenshot | Sequential (current) | Agent overhead not worth it |
| 2+ screenshots (catchup) | Parallel agents | 2-3x faster processing |
| Screenshot + card advice | Parallel agents | Vision and analysis simultaneously |
| Knowledge-only query | Sequential | Direct file access faster |
| Status query | Background agents | Instant cached response |

### When to Launch Agents

**Launch Screenshot Analyzer agents when:**
- User provides 2+ screenshot paths (catchup workflow)
- Explicit request for faster processing
- Processing time critical (tournament/streaming context)

**Launch Knowledge Loader agent when:**
- Card reward screen detected (need card tier data)
- Shop screen detected (need card/relic data)
- Event screen detected (need event recommendations)
- User runs `/spire analyze` (need archetype data)

**Launch Background Agents when:**
- First screenshot processed successfully (Status Monitor)
- Deck analysis completed (Card Advisor)

### Agent Launch Pattern

**For Multiple Screenshots (Catchup):**
```
# Launch 3 agents in parallel
Task: Screenshot Analyzer
  image_path: ~/Desktop/sts-deck.png
  → Result: DECK_DATA

Task: Screenshot Analyzer
  image_path: ~/Desktop/sts-map.png
  → Result: MAP_DATA

Task: Screenshot Analyzer
  image_path: ~/Desktop/sts-current.png
  → Result: CURRENT_DATA

# Wait for all 3, aggregate results
→ Update state with combined data
→ Provide final response
```

**For Screenshot + Card Advice:**
```
# Launch 2 agents in parallel
Task: Screenshot Analyzer
  image_path: ~/Desktop/sts-card-reward.png
  → Result: CARD_REWARD_DATA

Task: Knowledge Loader
  files: [archetypes, cards]
  → Result: KNOWLEDGE_BASE

# Combine results for card recommendations
→ Evaluate card options with archetype context
→ Provide ranked recommendations
```

**For Background Status:**
```
# Launch persistent agents
Task: Status Monitor
  action: start
  run_in_background: true
  → Continues monitoring state.json

Task: Card Advisor
  action: analyze
  deck_cards: [current deck]
  run_in_background: true
  → Pre-computes archetype analysis

# Future queries use cached results
→ Instant status responses
→ Pre-computed card evaluations
```

### Fallback Strategy

**If agent fails:**
1. Capture error message
2. Fall back to sequential processing (current behavior)
3. Note fallback in response: "[Using sequential mode - agent unavailable]"
4. Track failure count in state metadata
5. After 3 consecutive failures, disable parallel for session

**Circuit Breaker:**
```bash
# Check if parallel processing disabled
PARALLEL_DISABLED=$(get_state_value '.metadata.parallelProcessing.disabled // false')

if [[ "$PARALLEL_DISABLED" == "true" ]]; then
  # Use sequential processing
  use_sequential_mode
fi
```

### Agent Timeout

All agent launches use 30-second timeout:
```
Task tool with timeout: 30000 (30 seconds)
→ If timeout: Fall back to sequential mode
→ Log timeout in metadata
→ Increment failure counter
```

---

## Step 2: Screenshot Detection

### Single Screenshot (Sequential Mode - Default)

When given a single screenshot path:

1. **Read the image** using the `Read` tool:

   ```
   Prompt: "Identify this Slay the Spire screen type. Options:
   1. Neow/Character Select
   2. Map Screen
   3. Combat
   4. Card Reward
   5. Boss Relic Choice
   6. Shop
   7. Event
   8. Rest Site
   9. Treasure Room
   10. Deck View

   List ALL visible elements: cards (names, costs, upgraded status), relics (names), potions (types), enemies (names, intent icons if combat), UI elements (buttons, options, prices), map structure, floor number."
   ```

2. **For data extraction**, read the image again with a screen-specific prompt:

   **For Combat:**
   ```
   "Extract all combat data from this Slay the Spire screenshot:
   - Enemy names, HP (current/max), intent icons, intent values
   - Hand cards: names, costs, upgrade status (+)
   - Current energy (lightning bolt count)
   - Block values
   - Turn number if visible

   Format as JSON:
   {
     "enemies": [{"name": "...", "hp": N, "intent": "...", "value": N}],
     "hand": ["card1", "card2"],
     "energy": N,
     "block": N,
     "turn": N
   }"
   ```

   **For Card Reward:**
   ```
   "Extract card reward data:
   - All card names
   - Upgrade status (+ indicator)
   - Rarity (banner color: Gray=Common, Blue=Uncommon, Orange=Rare)
   - Card costs
   - Card types

   Format as JSON:
   {
     "cards": [
       {"name": "...", "cost": N, "upgraded": bool, "rarity": "...", "type": "..."}
     ]
   }"
   ```

3. Continue to **Step 3** with detected screen type and extracted data.

### Multiple Screenshots (Parallel Mode - Catchup Workflow)

When user provides 2+ screenshots (e.g., during catchup workflow):

1. **Check circuit breaker** - Ensure parallel processing not disabled:
   ```bash
   PARALLEL_DISABLED=$(get_state_value '.metadata.parallelProcessing.disabled // false')
   if [[ "$PARALLEL_DISABLED" == "true" ]]; then
     # Fall back to sequential processing
     use_sequential_mode
   fi
   ```

2. **Launch Screenshot Analyzer agents in parallel** using Task tool:
   ```
   For each screenshot path:
     Task tool with:
       subagent_type: general-purpose
       prompt: Read file: ~/.claude/plugins/spire/agents/screenshot-analyzer.md
       Then analyze this screenshot: $screenshot_path
       Return results in the exact JSON format specified in the agent file.
       timeout: 30000 (30 seconds)
   ```

3. **Stream progress** while waiting for agents:
   ```
   Processing 3 screenshots in parallel...
   [████████████░░░░] Analyzing deck view...
   [████████████████] Analyzing map view...
   [████████████░░░░] Analyzing current screen...
   ```

4. **Aggregate results** when all agents complete:
   ```bash
   # Combine results from all agents
   aggregate_screenshots(results)
   ```

5. **Handle failures gracefully**:
   - If any agent fails: Fall back to sequential processing for that screenshot
   - If all agents fail: Use full sequential mode with warning
   - Increment failure counter in metadata
   - Disable parallel processing after 3 consecutive failures

6. **Update state** with combined data from all screenshots.

7. **Continue to Step 3** with all extracted data.

**Performance:** Multiple screenshots processed in ~2.5 seconds vs ~6 seconds sequential (2.4x faster).

---

## Step 2.5: Catchup Workflow

When using the `catchup` command, the skill will guide you through providing essential screenshots to set up an in-progress run:

**Required screenshots (in order):**

1. **Deck View** - Shows current deck composition (most important)
2. **Map View** - Shows current floor, act, and path taken
3. **Current Screen** - Shows current context (combat, event, shop, etc.)

**Workflow:**

```
User: /spire catchup
Assistant: Starting catchup workflow for in-progress run...

Please provide the following screenshots in order:

1. Deck View (shows your current deck):
   User: /spire ~/Desktop/sts-deck.png
   Assistant: ## Screen: Deck View — Analyzing deck composition...

2. Map View (shows current floor and path):
   User: /spire ~/Desktop/sts-map.png
   Assistant: ## Screen: Map — Updating floor and path...

3. Current Screen (combat, event, shop, etc.):
   User: /spire ~/Desktop/sts-current.png
   Assistant: ## Screen: [Type] — Finalizing state...

Assistant: ✅ Catchup complete! Run state updated.
```

---

## Step 3: State Management

### Session-Based State Organization

Each Claude conversation gets its own isolated run state:

- **State location:** `~/.claude/spire/sessions/[session-id]/state.json`
- **Backups:** `~/.claude/spire/sessions/[id]/backups/state-YYYYMMDD-HHMMSS.json`
- **Current session:** Auto-detected from Claude Code session
- **Helper script:** `~/.claude/plugins/spire/scripts/state-helpers.sh`

### Load State
```bash
# Source the helper functions
source ~/.claude/plugins/spire/scripts/state-helpers.sh

# Load current session state (automatically detected)
STATE=$(load_state)

# Or specify a specific session
STATE=$(load_state "specific-session-id")
```

### Save State
```bash
# Save updated state to current session (with automatic backup)
save_state "$UPDATED_STATE"

# Or save to a specific session
save_state "$UPDATED_STATE" "specific-session-id"
```

### Update Specific Fields
```bash
# Update single field in current session
update_state '.run.floor = 7'

# Update multiple fields in current session
update_state '
  .run.floor = 7 |
  .player.hp.current = 65 |
  .player.gold = 244 |
  .run.screen = "combat"
'

# Add items to arrays in current session
update_state '.deck.cards += ["Pommel Strike"]'
update_state '.relics.owned += ["Vajra"]'

# Update specific session
update_state '.run.floor = 7' "specific-session-id"
```

### Session Management
```bash
# List all sessions
list_sessions

# List sessions older than 30 days
list_sessions 30

# Display a specific session's state
switch_session "specific-session-id"

# Cleanup old sessions (older than 30 days)
cleanup_sessions

# Cleanup sessions older than 7 days
cleanup_sessions 7

# Delete a specific session
delete_session "specific-session-id"
```

### Get Values
```bash
# Get specific value
CHARACTER=$(get_state_value '.run.character')
FLOOR=$(get_state_value '.run.floor')
```

---

## Step 4: State Extraction by Screen Type

### For Card Reward Screen

Extract and save:
```bash
# Assuming extracted data in variable EXTRACTED
update_state "
  .rewards.cards = $EXTRACTED.cards |
  .deck.seen += [$EXTRACTED.cards[].name]
"
```

### For Combat Screen

Extract and save:
```bash
update_state "
  .combat.enemies = $EXTRACTED.enemies |
  .combat.hand = $EXTRACTED.hand |
  .combat.energy = $EXTRACTED.energy |
  .combat.block = $EXTRACTED.block |
  .combat.turn = $EXTRACTED.turn
"
```

### For Map Screen

Extract and save:
```bash
update_state "
  .run.floor = $EXTRACTED.floor |
  .map.upcoming = $EXTRACTED.upcoming
"
```

### For Deck View

Extract and save:
```bash
update_state "
  .deck.cards = $EXTRACTED.cards |
  .deck.size = ($EXTRACTED.cards | length)
"
```

### For All Screens

Always extract and update universal data:
```bash
update_state "
  .player.hp.current = $EXTRACTED.hp_current |
  .player.hp.max = $EXTRACTED.hp_max |
  .player.gold = $EXTRACTED.gold |
  .player.potions.slot1 = $EXTRACTED.potion1 |
  .player.potions.slot2 = $EXTRACTED.potion2
"
```

---

## Step 5: Load Knowledge Base

### Parallel Knowledge Loading (v2.2.0+)

**When knowledge is needed** (card reward, shop, event, analyze):

1. **Check circuit breaker** - Ensure parallel processing not disabled

2. **Launch Knowledge Loader agent** in parallel with screenshot analysis (if applicable):
   ```
   Task tool with:
     subagent_type: general-purpose
     model: haiku (for fast, efficient parsing)
     prompt: Read file: ~/.claude/plugins/spire/agents/knowledge-loader.md
     Then load these knowledge files: [archetypes, cards, relics, events]
     Return results in the exact JSON format specified.
     timeout: 30000 (30 seconds)
   ```

3. **Use cached knowledge** if available (24-hour cache)

4. **Fall back to inline loading** if agent fails:
   ```
   Read: ~/.claude/plugins/spire/knowledge/archetypes.md
   Read: ~/.claude/plugins/spire/knowledge/cards.md
   ```

### Sequential Knowledge Loading (Fallback)

**ALWAYS load** the archetype reference (fallback mode):
```
Read: ~/.claude/plugins/spire/knowledge/archetypes.md
```

**For card decisions**, also load:
```
Read: ~/.claude/plugins/spire/knowledge/cards.md
```

**For relic decisions**, also load:
```
Read: ~/.claude/plugins/spire/knowledge/relics.md
```

**For event decisions**, also load:
```
Read: ~/.claude/plugins/spire/knowledge/events.md
```

---

## Step 6: Generate Advice

### Archetype Detection Algorithm

1. Load current state:
   ```bash
   DECK_CARDS=$(get_state_value '.deck.cards')
   ```

2. For each archetype in knowledge base:
   - Count matching **core cards** (×3 weight)
   - Count matching **support cards** (×1 weight)
   - Calculate synergy score with current relics

3. Return archetype with highest score
4. Confidence: HIGH (≥10 points), MEDIUM (5-9), LOW (<5)

### Card Reward Analysis

Use template from `~/.claude/plugins/spire/templates/card_reward_advice.md`:

1. State current archetype + confidence
2. For each card option:
   - Look up tier in cards.md
   - Score synergy with current deck (1-10)
   - Recommend: TAKE / SKIP / CONSIDER
3. Final recommendation with reasoning

### Combat Analysis

1. Read enemy intents from state
2. Calculate incoming damage
3. Suggest card play order
4. Flag lethal risk if HP < incoming damage

---

## Step 7.5: Persistent Agent Status (v2.2.0+)

### Background Agents

After processing the first screenshot successfully, launch persistent background agents:

**Status Monitor:**
```
Task tool with:
  subagent_type: general-purpose
  prompt: Read file: ~/.claude/plugins/spire/agents/status-monitor.md
  Then start monitoring the current session's state file
  run_in_background: true
```

**Card Advisor:**
```
Task tool with:
  subagent_type: general-purpose
  prompt: Read file: ~/.claude/plugins/spire/agents/card-advisor.md
  Then analyze the current deck: [list of cards from state]
  run_in_background: true
```

### Querying Background Agents

**For instant status updates:**
```
Task: Status Monitor
  action: status
  → Returns cached status summary instantly
```

**For card evaluations:**
```
Task: Card Advisor
  action: evaluate
  card_options: [card1, card2, card3]
  → Returns pre-computed or fresh card evaluations
```

**For archetype analysis:**
```
Task: Card Advisor
  action: analyze
  deck_cards: [current deck from state]
  → Returns archetype detection and analysis
```

### Agent Lifecycle

- **Launch**: After first successful screenshot processing
- **Refresh**: When deck changes significantly (3+ cards)
- **Query**: On demand for status and card advice
- **Stop**: Session ends or user runs `/spire reset`

### Benefits

- **Instant status**: No file reads needed, cached responses
- **Pre-computed analysis**: Archetype detection ready before needed
- **Reduced latency**: Status queries ~10x faster
- **Better UX**: Near-instant responses for common queries

---

## Step 7: Output Response

Structure every response as:

```
## Screen: [Type] — Floor [N]

### Extracted State
- HP: X/Y
- Gold: Z
- [Screen-specific data]

### State Updated
✓ Session ID: [current-session-id]
✓ State saved to: ~/.claude/spire/sessions/[session-id]/state.json
✓ Backup created: state-YYYYMMDD-HHMMSS.json
✓ Updated fields: floor, hp, gold, [etc.]

### Analysis
[Archetype detection, advice, recommendations]

### Commands
- Use `/spire analyze` for detailed archetype analysis
- Use `/spire export` to save run tracker markdown
- Use `/spire reset` to start a new run
```

---

## Step 8: Run Tracker Export (Optional)

When user runs `/spire export`:

```bash
# Source helper functions
source ~/.claude/plugins/spire/scripts/state-helpers.sh

# Export to markdown
export_to_markdown

# Or specify output file
export_to_markdown ~/Documents/STS-Runs/custom-name.md
```

This creates a human-readable markdown file with:
- Run overview (character, ascension, progress)
- Player state (HP, gold, potions)
- Deck composition
- Relics owned
- History log

---

## Error Handling

| Situation             | Action                                                          |
| --------------------- | --------------------------------------------------------------- |
| Screenshot unclear    | Ask for clearer screenshot                                      |
| Screen type ambiguous | List possibilities, ask to confirm                              |
| State seems wrong     | Flag as "[!] Inconsistency detected", show current state        |
| Card not in database  | Note "Card not in knowledge base, providing best-effort advice" |
| jq command fails      | Check JSON syntax, show error message                           |
| **Agent fails**       | Fall back to sequential processing, note in response            |
| **Agent timeout**     | Fall back to sequential, log timeout in metadata                 |
| **All agents fail**   | Disable parallel for session, use full sequential mode          |

**Agent Error Recovery:**
```bash
# Increment failure counter
update_state '.metadata.parallelProcessing.failures += 1'

# Disable parallel after 3 failures
FAILURES=$(get_state_value '.metadata.parallelProcessing.failures // 0')
if [[ "$FAILURES" -ge 3 ]]; then
  update_state '.metadata.parallelProcessing.disabled = true'
  echo "Parallel processing disabled due to repeated failures."
fi
```

---

## State Schema Reference

The state file uses this structure:

```json
{
  "version": "2.2.0",
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
    "hp": {"current": 65, "max": 80},
    "gold": 244,
    "potions": {"slots": 2, "slot1": "Fire Potion", "slot2": null, "slot3": null}
  },
  "deck": {
    "cards": ["Strike", "Strike", "Bash", ...],
    "size": 12,
    "attacks": [...],
    "skills": [...],
    "powers": [...],
    "seen": ["Bash", "Pommel Strike"],
    "acquired": {"2": "Pommel Strike"}
  },
  "relics": {
    "owned": ["Burning Blood", "Vajra"],
    "starter": "Burning Blood",
    "boss": null
  },
  "combat": {
    "enemies": [{"name": "Cultist", "hp": 48, "intent": "attack", "value": 6}],
    "hand": ["Strike", "Bash"],
    "energy": 3,
    "block": 0
  },
  "rewards": {"cards": [...], "relics": []},
  "history": {"floors": [...], "choices": [...]},
  "metadata": {
    "createdAt": "2025-01-25T14:30:00Z",
    "lastUpdate": "2025-01-25T15:45:00Z",
    "screenshots": [],
    "migratedFrom": null,
    "parallelProcessing": {
      "enabled": true,
      "disabled": false,
      "lastUsed": "2025-01-25T16:00:00Z",
      "failures": 0,
      "fallbackCount": 0
    },
    "agents": {
      "screenshotAnalyzer": {"running": false},
      "knowledgeLoader": {"cachedFiles": []},
      "statusMonitor": {"running": true, "startedAt": "2025-01-25T16:00:00Z"},
      "cardAdvisor": {"running": true, "lastAnalyzed": "2025-01-25T16:00:00Z"}
    }
  }
}
```

For complete schema reference, see: `~/.claude/plugins/spire/core/state_schema_v2.md`

---

## Quick Start Examples

**Start a new run:**
```
User: /spire reset
Assistant: State reset. Share a Neow screen screenshot to begin tracking.
```

**Parse combat screenshot:**
```
User: /spire ~/Desktop/sts-combat.png
Assistant: ## Screen: Combat — Floor 7
### Extracted State
- HP: 45/80
- Enemies: Cultist (48 HP, Intent: Attack 6)
- Hand: Strike, Strike, Bash, Defend
...
```

**Get archetype analysis:**
```
User: /spire analyze
Assistant: ## Archetype Analysis
**Detected:** Strength Build (HIGH confidence - 12 points)
**Core cards:** Bash+ (×3), Flex+ (×3), Limit Break+
...
```

**Export run tracker:**
```
User: /spire export
Assistant: Exported run state to: ~/Documents/STS-Runs/20250125-143000-ironclad-a14.md
```
