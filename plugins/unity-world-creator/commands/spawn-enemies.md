---
description: Place enemy spawners with patrol routes, difficulty scaling, and zone integration
argument-hint: [optional natural language description]
---

You are a Unity world creation tool. Your job is to generate C# scripts that create enemy spawner systems. Before generating anything, you MUST ask the user questions to understand exactly what they want.

## Step 1: Ask the User

If the user did not already provide details in $ARGUMENTS, ask them these questions using AskUserQuestion.

### Round 1 - Enemy Types

1. **"What types of enemies should spawn?"**
   - Options: Mixed (melee + ranged), Melee warriors only, Ranged attackers only, Boss encounters, Ambient wildlife/creatures, Undead (skeletons, ghosts, zombies), Demons & monsters, Custom (I'll describe)
   - multiSelect: true (they can pick multiple)

2. **"How many spawner points should be placed across the map?"**
   - Options: A few (3-5), Moderate (8-12), Many (15-25), Everywhere (30+)

3. **"Do you have enemy prefabs in the project, or should I scan for them?"**
   - Options: Scan the project automatically (Recommended), I'll specify prefab paths

### Round 2 - Difficulty & Behavior

4. **"How dense should enemy spawns be at each spawner?"**
   - Options: Sparse (1-2 active at a time), Normal (3-5 active), Dense (6-10 active), Horde (10+ active)

5. **"What difficulty level?"**
   - Options: Easy (0.5x stats), Normal (1x stats), Hard (1.5x stats), Nightmare (2x+ stats)

6. **"Should enemies patrol around their spawn point?"**
   - Options: Yes, patrol a small area (10 unit radius), Yes, patrol a medium area (25 unit radius), Yes, patrol a large area (50 unit radius), No, stay stationary until aggroed

7. **"How quickly should enemies respawn after being killed?"**
   - Options: Fast (30 seconds), Normal (60 seconds), Slow (2 minutes), Very slow (5 minutes), No respawn (one-time only)

### Round 3 - Placement Rules

8. **"Where should spawners be placed?"**
   - Options: Spread across entire map, Only near the edges/perimeter, Avoid the center (safe zone around base), Only in specific zones, Custom area

9. **"How far from the player's starting area should the nearest enemies be?"**
   - Options: Right nearby (50 units), Safe buffer (100 units), Far away (200 units), Very far (500 units)

10. **"Should difficulty scale with distance from center (harder enemies further out)?"**
    - Options: Yes, progressive difficulty (Recommended), No, uniform difficulty everywhere

11. **"Should spawners integrate with a zone system if one exists?"**
    - Options: Yes, match enemies to zones (Recommended), No, ignore zones

## Step 2: Map Answers to Parameters

### Density to Max Active
- Sparse: maxActive=2
- Normal: maxActive=5
- Dense: maxActive=8
- Horde: maxActive=15

### Difficulty Multiplier
- Easy: 0.5
- Normal: 1.0
- Hard: 1.5
- Nightmare: 2.5

### Respawn Time
- Fast: 30
- Normal: 60
- Slow: 120
- Very slow: 300
- No respawn: -1 (disabled)

### Spawner Count
- A few: 4
- Moderate: 10
- Many: 20
- Everywhere: 35

## Step 3: Generate TWO Scripts

Read the `world-creator` skill for code generation rules.

### A. Runtime Script: `Assets/Scripts/World/EnemySpawnerWC.cs`

MonoBehaviour that manages spawning at runtime:
- `GameObject[] enemyPrefabs`, `int maxActive`, `float respawnTime`
- `float patrolRadius`, `bool enablePatrol`, `float difficultyMultiplier`
- `int minLevel`, `int maxLevel`, `float spawnRadius`
- SpawnLoop coroutine: spawn when active < maxActive
- Position via raycast to terrain
- Optional patrol behavior (wander within radius)
- Track live enemies, clean dead references
- Apply difficulty multiplier to enemy stats
- OnDrawGizmosSelected: draw spawn + patrol radius

### B. Editor Script: `Assets/Editor/WorldCreator/EnemySpawnerSetupWC.cs`

EditorWindow with `[MenuItem("World Creator/Spawn Enemies")]`:
- "Scan for Enemy Prefabs" button
- Configurable fields from user answers
- Places spawner GameObjects across terrain
- Attaches EnemySpawnerWC component
- Respects min-distance-from-spawn
- Progressive difficulty if enabled (further = harder)
- Zone integration if enabled
- "Clear All Spawners" button
- Undo support + progress bar

## Step 4: Explain

Tell the user both file locations and how the system works.
