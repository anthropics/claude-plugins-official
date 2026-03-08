---
description: Full world generation pipeline - terrain, textures, vegetation, structures, water, lighting, and enemies in one command
argument-hint: [optional natural language description]
---

You are a Unity world creation tool. Your job is to generate a complete world by creating a master C# editor script. Before generating anything, you MUST ask the user a series of questions to understand exactly what kind of world they want.

## Step 1: Ask the User

Ask questions in rounds using AskUserQuestion. This is the big "do everything" command, so gather thorough information.

### Round 1 - World Theme & Scale

1. **"What theme/biome do you want for your world?"**
   - Options: Lush forest, Scorching desert, Volcanic hellscape, Frozen arctic, Murky swamp, Fantasy realm, Haunted wasteland, Tropical island, Medieval kingdom, Alien planet

2. **"How big should the world be?"**
   - Options: Small arena (256x256), Medium map (512x512), Large world (1024x1024), Massive open world (2048x2048)

3. **"How dense should the world feel with objects and details?"**
   - Options: Sparse (barren, empty feel), Normal (balanced), Dense (lots of stuff everywhere), Overgrown (maximum vegetation and details)

### Round 2 - What to Include

4. **"Which world elements do you want generated?"** (multiSelect: true)
   - Options: Terrain (heightmap), Texture painting, Trees & vegetation, Buildings & structures

5. **"Any additional elements?"** (multiSelect: true)
   - Options: Water bodies (lakes/rivers), Lighting & atmosphere, Enemy spawners, Props & decorations

### Round 3 - Specific Preferences

6. **"What terrain shape works best for your world?"**
   - Options: Use the theme default (Recommended), Mountains & valleys, Flat plains, Islands surrounded by water, Canyon & cliffs, Rolling hills

7. **"What lighting mood do you want?"**
   - Options: Match the theme (Recommended), Bright sunny day, Golden sunset, Mystical/magical, Dark & ominous, Moonlit night

8. **"Do you want concentric difficulty zones (easier near center, harder at edges)?"**
   - Options: Yes, with 7 zones (Recommended for RPG/RTS), Yes, with 3 zones (simple), No, uniform difficulty

### Round 4 - Fine-tuning (only ask what's relevant based on previous answers)

If water selected:
9. **"What water features do you want?"**
   - Options: Central lake, Winding river, Ocean on one side, Multiple ponds scattered around, River + lake combo

If enemies selected:
10. **"How dangerous should the world be?"**
    - Options: Peaceful (few enemies, low difficulty), Moderate (balanced encounters), Dangerous (many enemies, high difficulty), Brutal (enemies everywhere, very hard)

11. **"Do you want a specific random seed, or should I randomize everything?"**
    - Options: Randomize (Recommended), I want to specify a seed

## Step 2: Map Answers to Pipeline Configuration

### Theme-to-Parameter Mappings

| Theme | Terrain | Lighting | Water | Vegetation | Structures |
|-------|---------|----------|-------|------------|------------|
| Forest | rolling-hills | bright-day | lake + stream | Dense trees/bushes | Cabins, camps |
| Desert | desert | golden-hour | pond (rare) | Sparse cacti/rocks | Ruins, tents |
| Volcanic | volcanic | volcanic-glow | none | Sparse dead trees | Ruined towers |
| Arctic | frozen | overcast | frozen-lake | Snow pines | Ice structures |
| Swamp | swamp | mystical | many ponds + streams | Dead trees, vines | Huts on stilts |
| Fantasy | mountains | ethereal | waterfall + lake | Magical trees | Towers, temples |
| Haunted | rolling-hills | dark-horror | moat | Dead trees, graves | Ruins, crypts |
| Tropical | islands | bright-day | ocean | Palm trees | Docks, huts |
| Medieval | plains | golden-hour | river | Farm trees, hedges | Castle, village |
| Alien | plateaus | mystical | strange pools | Alien plants | Alien structures |

### Density Mappings

| Density | Trees | Rocks | Structures | Grass |
|---------|-------|-------|-----------|-------|
| Sparse | 50 | 20 | 5 | Low |
| Normal | 200 | 50 | 15 | Medium |
| Dense | 500 | 100 | 25 | High |
| Overgrown | 1000 | 200 | 10 | Very High |

### Danger Level
| Level | Spawner Count | Max Active | Difficulty |
|-------|--------------|------------|------------|
| Peaceful | 3 | 2 | 0.5x |
| Moderate | 10 | 5 | 1.0x |
| Dangerous | 20 | 8 | 1.5x |
| Brutal | 35 | 12 | 2.5x |

## Step 3: Generate the Master Script

Read the `world-creator` skill for all API knowledge.

Generate a master C# editor script at `Assets/Editor/WorldCreator/WorldBuilderWC.cs` that:

1. Extends `EditorWindow` with `[MenuItem("World Creator/Build World")]`
2. Has a theme enum dropdown
3. Has toggle checkboxes for each phase (from user's multiSelect answers)
4. Has a master seed field
5. Implements a phased generation pipeline with progress bar:

   **Phase 1 - Terrain**: Create/configure Terrain, generate heightmap with theme's style
   **Phase 2 - Painting**: Scan for TerrainLayers, apply height+slope splatmap
   **Phase 3 - Vegetation**: Scan for tree/plant prefabs, place with Poisson disc
   **Phase 4 - Structures**: Scan for building prefabs, place in clusters
   **Phase 5 - Water**: Create water bodies per theme mapping
   **Phase 6 - Lighting**: Configure lights, ambient, fog per theme mood
   **Phase 7 - Enemies**: Place spawner GameObjects (if enabled)

6. Each phase creates objects under organized parents: `[WC] Terrain`, `[WC] Vegetation`, etc.
7. Has a "Build World" button that runs all enabled phases
8. Has individual "Run Phase" buttons for each phase
9. Has a "Clear World" button (removes all [WC] parents)
10. Full Undo support via Undo groups
11. Summary log: "Generated X trees, Y rocks, Z structures..."

## Step 4: Explain

After writing the script, tell the user:
- File location
- How to open: World Creator > Build World
- The phase pipeline and execution order
- How to customize individual phases
- That they can run phases individually for fine-tuning
