---
description: Generate Unity terrain with procedural heightmaps (mountains, plains, islands, canyon, etc.)
argument-hint: [optional natural language description]
---

You are a Unity world creation tool. Your job is to generate a C# editor script that creates procedural terrain. Before generating anything, you MUST ask the user questions to understand exactly what they want.

## Step 1: Ask the User

If the user did not already provide details in $ARGUMENTS, ask them the following questions using AskUserQuestion. Group related questions together (max 4 per call). Ask in rounds - start with the most important questions first.

### Round 1 - Core Shape

1. **"What terrain style do you want?"**
   - Options: Mountains, Plains, Islands, Canyon, Desert, Volcanic, Frozen Tundra, Swamp, Plateaus, Rolling Hills
   - (Or let them describe something custom)

2. **"How big should the terrain be?"**
   - Options: Small (256x256), Medium (512x512), Large (1024x1024), Huge (2048x2048)

3. **"How tall should the terrain's highest peaks be?"**
   - Options: Flat (10 units), Low (30 units), Medium (60 units), Tall (100 units), Extreme (200 units)

### Round 2 - Detail & Features (ask based on Round 1 answers)

4. **"How much terrain detail/roughness do you want?"**
   - Options: Smooth (few octaves), Normal, Detailed (many octaves), Ultra-detailed

5. **"Should the terrain have an island falloff (edges drop to sea level)?"**
   - Options: Yes, No
   - (Auto-yes if they chose Islands style)

6. **"Do you want a flat area in the center for building a base?"**
   - Options: Yes (small), Yes (large), No

7. **"Do you want erosion applied for a more natural look?"**
   - Options: Yes, No

### Round 3 - Optional (only ask if relevant)

8. **"Do you want a specific random seed for reproducibility, or should I randomize it?"**
   - Options: Randomize, Let me specify a seed

9. **"Should the terrain integrate with a zone system (concentric difficulty rings)?"**
   - Options: Yes, No, What's that?

## Step 2: Map Answers to Parameters

After gathering answers, map them to these generation parameters:

### Style Presets

| Style | Scale | Octaves | Persistence | Lacunarity | Height | Special |
|-------|-------|---------|-------------|------------|--------|---------|
| Mountains | 15 | 6 | 0.45 | 2.5 | 150 | Exponential height curve |
| Plains | 40 | 3 | 0.3 | 1.8 | 20 | Gentle undulation |
| Islands | 20 | 5 | 0.5 | 2.2 | 80 | Radial falloff from center |
| Canyon | 12 | 5 | 0.5 | 2.3 | 120 | Ridged noise: 1 - abs(perlin*2-1) |
| Desert | 30 | 3 | 0.35 | 2.0 | 40 | Directional dune ridges |
| Volcanic | 10 | 4 | 0.5 | 2.0 | 130 | Central peak + caldera crater |
| Frozen | 25 | 4 | 0.4 | 2.0 | 30 | Gentle rolling + ice sheet flats |
| Swamp | 35 | 3 | 0.25 | 1.5 | 10 | Very flat + sparse mounds |
| Plateaus | 18 | 5 | 0.5 | 2.2 | 100 | Stepped/quantized heights |
| Rolling Hills | 25 | 4 | 0.45 | 2.0 | 50 | Smooth sine-like undulation |

### Size Mappings
- Small: width=256, length=256, resolution=257
- Medium: width=512, length=512, resolution=513
- Large: width=1024, length=1024, resolution=513
- Huge: width=2048, length=2048, resolution=1025

### Detail Mappings
- Smooth: octaves preset -2
- Normal: use style preset
- Detailed: octaves preset +2
- Ultra-detailed: octaves preset +4, persistence +0.1

## Step 3: Generate the Script

Read the `world-creator` skill for Unity Terrain API knowledge and code generation rules.

Generate a C# editor script at `Assets/Editor/WorldCreator/TerrainGeneratorWC.cs` that:

1. Extends `EditorWindow` with `[MenuItem("World Creator/Generate Terrain")]`
2. Has all parameters as serialized fields with the values determined from the user's answers
3. Includes a style dropdown (`enum TerrainStyle`) that auto-fills parameters when changed
4. Has a "Generate" button that:
   - Creates a new Terrain GameObject if none exists, or uses `Terrain.activeTerrain`
   - Sets `terrainData.heightmapResolution` and `terrainData.size`
   - Generates heightmap using multi-octave Perlin noise with the style's parameters
   - Applies style-specific modifications (ridged noise for canyon, radial falloff for islands, etc.)
   - If falloff enabled, applies radial edge falloff
   - If erosion enabled, applies thermal erosion pass
   - If flatten-center enabled, smoothly flattens circular area at center
   - Uses `Undo.RecordObject()` before changes
   - Calls `terrain.Flush()` and `EditorUtility.SetDirty()` after
   - Shows a progress bar during generation
5. Has a "Randomize Seed" button
6. Has a "Reset to Style Defaults" button
7. Checks for ZoneTerrainModifier and calls `ApplyZoneModifications()` if found

## Step 4: Explain

After writing the script, tell the user:
- The file location
- How to open it: Unity menu > World Creator > Generate Terrain
- How to tweak parameters in the EditorWindow
- That they can regenerate with different settings anytime

The generated code must compile in Unity 2020.3+.
