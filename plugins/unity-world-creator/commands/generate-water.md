---
description: Create water bodies (lakes, rivers, oceans, ponds) with terrain carving and wave animation
argument-hint: [optional natural language description]
---

You are a Unity world creation tool. Your job is to generate a C# editor script that creates water bodies. Before generating anything, you MUST ask the user questions to understand exactly what they want.

## Step 1: Ask the User

If the user did not already provide details in $ARGUMENTS, ask them these questions using AskUserQuestion.

### Round 1 - Water Type

1. **"What type of water body do you want?"**
   - Options: Lake, River, Ocean/Sea, Pond, Waterfall, Moat (ring around a point), Stream

2. **"How large should the water body be?"**
   - Options: Small (50 units), Medium (100 units), Large (250 units), Massive (500+ units)

3. **"Where should the water be placed?"**
   - Options: At the lowest point on the terrain (Recommended for lakes), Center of the terrain, Terrain edge (Recommended for ocean), I'll specify coordinates

### Round 2 - Terrain Interaction

4. **"Should the terrain be carved/dug out to create the water bed?"**
   - Options: Yes, carve a natural depression (Recommended), Yes, carve a deep basin, No, just place water at existing terrain level

5. **"How deep should the water be?"**
   - Options: Shallow (2 units), Medium (5 units), Deep (10 units), Very deep (20 units)

6. **"Should the shore/banks have blended terrain textures (sand/mud)?"**
   - Options: Yes (Recommended), No

### Round 3 - Appearance (ask based on type)

7. **"What wave intensity do you want?"**
   - Options: Calm/still water, Gentle ripples (Recommended for lakes), Moderate waves, Rough/stormy waves

8. **"What water color/tint?"**
   - Options: Ocean blue (#1A5276), Tropical turquoise (#1ABC9C), Dark/murky (#2C3E50), Crystal clear (light blue), Swamp green (#556B2F), Custom color

If type is **river/stream**, also ask:

9. **"How wide should the river be?"**
   - Options: Narrow stream (5 units), Normal river (15 units), Wide river (30 units), Massive river (50+ units)

10. **"How should the river path flow?"**
    - Options: Winding/natural curves (Recommended), Mostly straight, S-curves, I'll describe the path

## Step 2: Map Answers to Parameters

### Wave Presets
| Intensity | Height | Speed |
|-----------|--------|-------|
| Calm | 0.02 | 0.2 |
| Gentle | 0.15 | 0.5 |
| Moderate | 0.4 | 1.0 |
| Rough | 0.8 | 2.0 |

### Carve Depth (added to user depth choice)
- Natural depression: smooth falloff using `1 - (dist/radius)^2`
- Deep basin: steeper falloff, flat bottom
- No carve: just place water plane

### Type-Specific Defaults
| Type | Default Waves | Default Size | Carve Shape |
|------|--------------|-------------|-------------|
| Lake | Gentle | 100 | Circular depression |
| River | Moderate | length=500 | Channel along path |
| Ocean | Moderate | 2000+ | Flatten coastline |
| Pond | Calm | 30 | Shallow circular dip |
| Waterfall | Rough | 20 wide | Cliff edge + pool |
| Moat | Calm | ring | Ring channel |
| Stream | Gentle | narrow | Narrow winding channel |

## Step 3: Generate the Script

Read the `world-creator` skill for terrain heightmap API and water specifications.

Generate a C# editor script at `Assets/Editor/WorldCreator/WaterGeneratorWC.cs` that:

1. Extends `EditorWindow` with `[MenuItem("World Creator/Generate Water")]`
2. Has fields for all resolved parameters
3. On "Generate Water":
   - Gets `Terrain.activeTerrain`
   - Searches project for water material: `AssetDatabase.FindAssets("water t:Material")`
   - Creates "[WC] Water" parent GameObject
   - Implements type-specific generation:
     - **Lake/Pond**: carve circular depression, place scaled plane
     - **River/Stream**: generate winding path, carve channel, place plane segments
     - **Ocean**: large plane at edge, flatten coastline
     - **Moat**: ring-shaped carve + water planes
     - **Waterfall**: cliff carve + vertical effect + pool
   - Adds wave animation component (LowPolyWater if found, or generates WaterWaveAnimator.cs)
   - Optionally paints shore textures
   - Undo support + progress bar

## Step 4: Explain

Tell the user the file location and how to use it.
