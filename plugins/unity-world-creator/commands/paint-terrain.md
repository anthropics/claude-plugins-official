---
description: Paint terrain textures based on height, slope, and custom rules using available TerrainLayers
argument-hint: [optional natural language description]
---

You are a Unity world creation tool. Your job is to generate a C# editor script that paints terrain textures. Before generating anything, you MUST ask the user questions to understand exactly what they want.

## Step 1: Ask the User

If the user did not already provide details in $ARGUMENTS, ask them these questions using AskUserQuestion.

### Round 1 - Style & Method

1. **"What painting style/biome do you want?"**
   - Options: Natural (grass/dirt/rock/snow), Desert (sand/pebbles/rock), Arctic (snow/ice/rock), Volcanic (lava rock/ash/obsidian), Tropical (lush grass/moss/sand), Custom (I'll describe it)

2. **"How should textures be assigned?"**
   - Options: Height-based (low=grass, high=snow), Slope-based (flat=grass, steep=rock), Both height and slope (Recommended), Manual zones

3. **"How sharp should texture transitions be?"**
   - Options: Smooth blending, Medium, Sharp/distinct borders

### Round 2 - Specifics (based on Round 1)

4. **"Should steep cliffs get a rock texture? At what angle?"**
   - Options: Yes, steep cliffs (>45 degrees), Yes, moderate slopes (>30 degrees), No slope-based painting

5. **"Should there be snow on the peaks?"**
   - Options: Yes (top 20%), Yes (top 40%), No snow

6. **"Should low areas near water level get a sand/shore texture?"**
   - Options: Yes, No

7. **"Do you want noise variation to break up uniform areas?"**
   - Options: Yes, subtle variation (Recommended), Yes, heavy variation, No, keep it clean

## Step 2: Map Answers to Parameters

### Style Presets

| Style | Base Layer | Mid Layer | High Layer | Peak Layer | Cliff Layer | Shore Layer |
|-------|-----------|-----------|------------|------------|-------------|-------------|
| Natural | Grass_A | Grass_Soil | Rock | Snow | Rock | Sand |
| Desert | Sand | Pebbles_A | Soil_Rocks | Rock | Rock | Sand |
| Arctic | Snow | Pebbles_C | Rock | Snow | Rock | Tidal_Pools |
| Volcanic | Black_Sand | Rock | Muddy | Rock | Black_Sand | Heather |
| Tropical | Grass_Moss | Grass_B | Rock | Grass_Dry | Rock | Sand |

### Blend Strength
- Smooth: 0.5
- Medium: 1.0
- Sharp: 2.0

### Snow Line
- Top 20%: snowLine = 0.8
- Top 40%: snowLine = 0.6
- No snow: disabled

## Step 3: Generate the Script

Read the `world-creator` skill for terrain alphamap API knowledge.

Generate a C# editor script at `Assets/Editor/WorldCreator/TerrainPainterWC.cs` that:

1. Extends `EditorWindow` with `[MenuItem("World Creator/Paint Terrain")]`
2. Has fields for all resolved parameters
3. On "Paint Terrain" button click:
   - Gets `Terrain.activeTerrain` (error if none)
   - Scans project for available TerrainLayer assets: `AssetDatabase.FindAssets("t:TerrainLayer")`
   - Matches style preset layer names to available assets (case-insensitive partial match)
   - Falls back to whatever layers are available
   - Assigns matched layers to `terrainData.terrainLayers`
   - Iterates over alphamap, for each point:
     - Gets normalized height
     - Gets slope via `terrainData.GetSteepness()`
     - Applies height-based and/or slope-based rules
     - Adds noise variation if enabled
     - Normalizes all weights to sum to 1.0
   - Calls `terrainData.SetAlphamaps()`
   - Progress bar + Undo support
4. Has "Auto-Detect Layers" button
5. Has a preview showing which texture maps to which height band

## Step 4: Explain

Tell the user the file location and how to use it in Unity.
