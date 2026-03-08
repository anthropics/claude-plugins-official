# Unity World Creator Plugin

A Gaia-like world creation tool for Unity, powered by Claude. Generate terrain, place prefabs, configure lighting, paint textures, create water bodies, spawn enemies, and build entire worlds via slash commands.

## Overview

Unity World Creator turns natural language into Unity C# editor scripts. Instead of manually configuring terrain, placing hundreds of prefabs, or tweaking lighting settings, describe what you want and Claude generates production-ready EditorWindow scripts that integrate with Unity's menu system.

Each command asks you specific questions about what you want before generating code, so the output is always tailored to your exact needs.

## Commands

### `/generate-terrain`

Generate procedural terrain with multi-octave Perlin noise. Supports 10 terrain styles.

**Claude will ask you:**
- What terrain style? (Mountains, Plains, Islands, Canyon, Desert, Volcanic, etc.)
- How big? How tall?
- Should edges drop to sea level? Flat area in center? Erosion?

**Generates:** `TerrainGeneratorWC.cs` - EditorWindow with sliders for all parameters, style presets, and one-click generation.

### `/build-world`

Full world generation pipeline that combines all other commands into one master operation.

**Claude will ask you:**
- What theme/biome? (Forest, Desert, Volcanic, Arctic, Fantasy, Haunted, etc.)
- How big? How dense?
- Which phases to include? (Terrain, painting, vegetation, structures, water, lighting, enemies)

**Generates:** `WorldBuilderWC.cs` - EditorWindow with tabbed phases, progress bar, and individual phase controls.

### `/place-prefabs`

Scatter or place prefabs across terrain with intelligent distribution patterns.

**Claude will ask you:**
- What to place? (Trees, rocks, buildings, props, characters)
- How many? What pattern? (Random scatter, grid, clusters, along path, ring)
- Spacing? Slope limits? Scale variation?

**Generates:** `PrefabPlacerWC.cs` - EditorWindow with project scanner, pattern selector, and terrain-aware placement.

### `/generate-lighting`

Configure scene lighting for any mood or time of day.

**Claude will ask you:**
- What mood? (Bright day, Sunset, Mystical, Dark horror, Moonlit, etc.)
- Fog? Shadow quality? DayNightCycle integration?

**Generates:** `LightingSetupWC.cs` - EditorWindow with mood presets and live preview.

### `/script-world`

Generate custom C# scripts for world behaviors from natural language descriptions.

**Claude will ask you:**
- What type? (Weather, ambient effects, NPC patrols, hazards, interactive objects)
- Describe what it should do
- Singleton? Coroutines? Multiplayer sync?

**Generates:** Custom MonoBehaviour scripts with serialized fields, proper Unity patterns, and optional editor scripts.

### `/paint-terrain`

Paint terrain textures based on height, slope, and biome rules.

**Claude will ask you:**
- What biome style? (Natural, Desert, Arctic, Volcanic, Tropical)
- Height-based? Slope-based? Snow line? Shore painting?

**Generates:** `TerrainPainterWC.cs` - EditorWindow with auto-detected TerrainLayers and splatmap painting.

### `/generate-water`

Create water bodies with terrain carving and wave animation.

**Claude will ask you:**
- What type? (Lake, River, Ocean, Pond, Waterfall, Moat, Stream)
- How large? How deep? Wave intensity? Carve terrain?

**Generates:** `WaterGeneratorWC.cs` - EditorWindow with water type presets and terrain integration.

### `/spawn-enemies`

Place enemy spawner systems with patrol AI and difficulty scaling.

**Claude will ask you:**
- What enemy types? How many spawners? Density?
- Patrol behavior? Respawn time? Difficulty scaling?
- Zone-aware placement?

**Generates:** `EnemySpawnerWC.cs` (runtime spawner) + `EnemySpawnerSetupWC.cs` (editor placement tool).

## How It Works

1. Run a slash command (e.g., `/generate-terrain`)
2. Claude asks you specific questions about what you want
3. Based on your answers, Claude generates a C# editor script
4. Open the script in Unity via the **World Creator** menu
5. Tweak parameters in the EditorWindow and click Generate

All generated scripts:
- Use `[MenuItem("World Creator/...")]` for Unity menu integration
- Include full Undo support
- Show progress bars for long operations
- Auto-scan your project for available assets (prefabs, materials, TerrainLayers)
- Work with Unity 2020.3+

## Requirements

- Unity 2020.3 or later
- A Unity project open in Claude Code

## Installation

Install via the Claude Code plugin marketplace:
```
/install unity-world-creator
```

## Author

ForestGatherz

## Version

1.0.0
