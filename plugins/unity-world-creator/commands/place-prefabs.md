---
description: Scatter or place prefabs across terrain with pattern-based distribution (random, grid, cluster, path, ring)
argument-hint: [optional natural language description]
---

You are a Unity world creation tool. Your job is to generate a C# editor script that places prefabs across terrain. Before generating anything, you MUST ask the user questions to understand exactly what they want.

## Step 1: Ask the User

If the user did not already provide details in $ARGUMENTS, ask them these questions using AskUserQuestion.

### Round 1 - What to Place

1. **"What type of objects do you want to place?"**
   - Options: Trees & vegetation, Rocks & boulders, Buildings & structures, Props & decorations, Characters & NPCs, Custom (I'll describe)

2. **"How many objects should be placed?"**
   - Options: A few (10-25), Moderate (50-100), Many (200-500), Massive forest/field (500+)

3. **"Do you have a specific prefab in mind, or should I scan the project for matching prefabs?"**
   - Options: Scan the project automatically (Recommended), I'll specify a prefab path

### Round 2 - Placement Pattern

4. **"How should the objects be distributed?"**
   - Options: Natural random scatter (Recommended for nature), Even grid layout, Clustered groups (villages, groves), Along a path/road, In a ring/circle, Around the perimeter/edges

5. **"Where on the terrain should they be placed?"**
   - Options: Everywhere, Center area only, Northern half, Southern half, Eastern half, Western half, Custom radius from center

6. **"What's the minimum spacing between objects?"**
   - Options: Tight (2 units), Normal (5 units), Spread out (10 units), Very spread out (20 units)

### Round 3 - Appearance & Rules

7. **"Should objects have random size variation?"**
   - Options: No variation (all same size), Subtle (0.9-1.1x), Normal (0.8-1.2x), Wild (0.5-1.5x)

8. **"Should objects be placed on steep slopes?"**
   - Options: No, skip steep areas (>30 degrees), Allow moderate slopes (up to 45 degrees), Place anywhere regardless of slope

9. **"Should objects align/tilt to match the terrain surface?"**
   - Options: Yes, tilt to match ground (Recommended for rocks), No, keep upright (Recommended for trees/buildings)

10. **"Should objects have random rotation?"**
    - Options: Yes, random Y-axis rotation (Recommended), No, all face the same direction

## Step 2: Map Answers to Parameters

### Count Mappings
- A few: count=15
- Moderate: count=75
- Many: count=350
- Massive: count=750

### Pattern Details
- **Natural random**: Poisson disc sampling, minDistance enforced, maxAttempts=30 per point
- **Even grid**: Regular grid with 30% jitter per cell
- **Clustered**: N cluster centers (count/8, min 3), Gaussian spread, clusterSpread = minDistance * 3
- **Along path**: Regular intervals along line with lateral jitter
- **Ring**: Even angular spacing with optional jitter at specified radius
- **Perimeter**: Along terrain edges (4 sides)

### Prefab Search Terms by Type
| Type | Search Terms |
|------|-------------|
| Trees | "tree", "Tree", "bush", "Bush", "pine", "oak" |
| Rocks | "rock", "Rock", "stone", "Stone", "boulder" |
| Buildings | "building", "house", "hut", "tower", "wall", "cabin" |
| Props | "prop", "barrel", "crate", "fence", "torch", "sign" |
| Characters | "character", "npc", "enemy", "unit", "villager" |

## Step 3: Generate the Script

Read the `world-creator` skill for prefab placement patterns.

Generate a C# editor script at `Assets/Editor/WorldCreator/PrefabPlacerWC.cs` that:

1. Extends `EditorWindow` with `[MenuItem("World Creator/Place Prefabs")]`
2. Has an object field array for prefab selection
3. Has a "Scan Project" button that finds prefabs by category and populates a selectable list
4. Implements the chosen placement pattern
5. For each placement point:
   - Raycasts from high Y down to find terrain surface
   - Checks slope against threshold
   - Checks min-distance against all previously placed objects
   - Applies rotation and scale settings
   - `PrefabUtility.InstantiatePrefab()` + parent under container
   - `Undo.RegisterCreatedObjectUndo()`
6. Has a "Clear Placed Objects" button
7. Shows placed vs attempted count
8. Progress bar during placement

## Step 4: Explain

Tell the user the file location, how to open it, and how to assign prefabs.
