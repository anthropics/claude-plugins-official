---
name: world-creator
description: >
  Unity world creation knowledge base. Use when the user asks to generate terrain,
  place prefabs, configure lighting, create water, paint terrain textures, spawn enemies,
  script world behaviors, or build an entire world in Unity. Triggers on keywords like
  "terrain", "world", "biome", "prefab placement", "lighting setup", "water body",
  "enemy spawner", "procedural generation", "heightmap", "splatmap", "vegetation scatter".
version: 1.0.0
---

# Unity World Creator - Knowledge Base

## Overview

This skill provides Claude with comprehensive knowledge for generating Unity C# editor scripts and runtime scripts that create, modify, and populate game worlds. All commands produce compilable C# code that integrates with Unity's editor workflow.

## Code Generation Rules

### Editor Scripts
- Output path: `Assets/Editor/WorldCreator/`
- Must include `using UnityEditor;`
- Use `[MenuItem("World Creator/COMMAND_NAME")]` for menu entries
- Use `EditorWindow` subclass for tools with UI (sliders, buttons, previews)
- Always call `Undo.RecordObject(target, "description")` before modifications
- Always call `EditorUtility.SetDirty(target)` after modifications
- Call `terrain.Flush()` after heightmap changes
- Call `AssetDatabase.Refresh()` after creating new files
- Check `!EditorApplication.isPlaying` before executing
- Use `EditorUtility.DisplayProgressBar()` for long operations
- Group undo operations with `Undo.SetCurrentGroupName()`

### Runtime Scripts
- Output path: `Assets/Scripts/World/`
- Must be `MonoBehaviour` subclasses
- Use `[SerializeField]` for inspector-configurable fields
- Use `[Header("Section")]` to organize inspector groups
- Use `[Range(min, max)]` for numeric fields where applicable
- Use `[Tooltip("...")]` for non-obvious fields
- Follow singleton pattern when `--singleton` is specified: `public static T Instance { get; private set; }`
- Use coroutines for timed/repeating behaviors
- Always null-check external references

### Naming Conventions
- Editor scripts: `{Feature}WC.cs` (e.g., `TerrainGeneratorWC.cs`)
- Runtime scripts: descriptive name (e.g., `WeatherSystem.cs`, `PatrolRoute.cs`)
- MenuItem path: `"World Creator/{Feature Name}"`
- Parent GameObjects: `"[WC] {Category}"` (e.g., `"[WC] Trees"`, `"[WC] Water"`)

## Unity Terrain API Quick Reference

### Heightmap Operations
```csharp
// Get terrain reference
Terrain terrain = Terrain.activeTerrain; // or FindObjectsByType<Terrain>(FindObjectsSortMode.None)[0]
TerrainData td = terrain.terrainData;

// Read/write heights (normalized 0-1)
int res = td.heightmapResolution; // power of 2 + 1 (e.g., 513, 1025)
float[,] heights = td.GetHeights(0, 0, res, res);
heights[y, x] = normalizedValue; // NOTE: y first, then x
td.SetHeights(0, 0, heights);
terrain.Flush();

// Terrain size
td.size = new Vector3(width, maxHeight, length);
```

### Texture Painting (Alphamaps/Splatmaps)
```csharp
// Terrain layers (modern API - use instead of deprecated splatPrototypes)
TerrainLayer[] layers = td.terrainLayers;
int alphaW = td.alphamapWidth;
int alphaH = td.alphamapHeight;
int layerCount = td.alphamapLayers;

// Read/write splatmap
float[,,] alphamap = td.GetAlphamaps(0, 0, alphaW, alphaH);
// alphamap[y, x, layerIndex] = weight; // all layers at a point must sum to 1.0
td.SetAlphamaps(0, 0, alphamap);

// Add new terrain layer
TerrainLayer newLayer = new TerrainLayer();
newLayer.diffuseTexture = texture;
newLayer.tileSize = new Vector2(15, 15);
var layerList = td.terrainLayers.ToList();
layerList.Add(newLayer);
td.terrainLayers = layerList.ToArray();
```

### Tree Placement
```csharp
// Tree prototypes
TreePrototype proto = new TreePrototype();
proto.prefab = treePrefab;
td.treePrototypes = new TreePrototype[] { proto };

// Place trees
TreeInstance tree = new TreeInstance();
tree.position = new Vector3(normX, 0, normZ); // normalized 0-1
tree.widthScale = 1f;
tree.heightScale = 1f;
tree.prototypeIndex = 0;
tree.color = Color.white;
tree.lightmapColor = Color.white;
td.treeInstances = treeArray;
```

### Detail/Grass
```csharp
// Detail layer (grass, flowers)
DetailPrototype detail = new DetailPrototype();
detail.prototypeTexture = grassTexture; // or detail.prototype = grassPrefab;
detail.renderMode = DetailRenderMode.GrassBillboard;
td.detailPrototypes = new DetailPrototype[] { detail };

int[,] detailLayer = td.GetDetailLayer(0, 0, td.detailWidth, td.detailHeight, 0);
detailLayer[y, x] = density; // integer density value
td.SetDetailLayer(0, 0, 0, detailLayer);
```

### Terrain Slope & Normal
```csharp
float steepness = td.GetSteepness(normX, normZ); // returns degrees 0-90
Vector3 normal = td.GetInterpolatedNormal(normX, normZ);
```

## Noise Generation Patterns

### Multi-Octave Perlin Noise
```csharp
float GenerateHeight(int x, int y, int seed, float scale, int octaves, float persistence, float lacunarity)
{
    float amplitude = 1f, frequency = 1f, height = 0f;
    System.Random prng = new System.Random(seed);
    Vector2 offset = new Vector2(prng.Next(-10000, 10000), prng.Next(-10000, 10000));

    for (int o = 0; o < octaves; o++)
    {
        float sampleX = (x + offset.x) / scale * frequency;
        float sampleY = (y + offset.y) / scale * frequency;
        float perlinValue = Mathf.PerlinNoise(sampleX, sampleY) * 2f - 1f;
        height += perlinValue * amplitude;
        amplitude *= persistence;
        frequency *= lacunarity;
    }
    return height;
}
```

### Style-Specific Noise Modifications
- **Mountains**: High octaves (6), low persistence (0.45), exponential height curve
- **Plains**: Low octaves (3), high scale (40), low max height (20)
- **Islands**: Radial falloff: `height *= 1f - Vector2.Distance(center, point).normalized`
- **Canyon**: Ridged noise: `1f - Mathf.Abs(perlinValue * 2f - 1f)`
- **Desert**: Directional dune ridges via rotated coordinates
- **Volcanic**: Central peak (Gaussian) + caldera crater (inverted Gaussian at smaller radius)
- **Frozen**: Gentle rolling + flat ice sheets (clamped low areas)
- **Swamp**: Very flat (low height) + scattered mounds (sparse high-frequency noise)

## Prefab Placement Patterns

### Poisson Disc Sampling (Natural Random Distribution)
Best for trees, rocks, vegetation - ensures minimum spacing without grid artifacts.

### Grid with Jitter
Regular grid + random offset per cell. Good for buildings, crops.

### Cluster Placement
Multiple cluster centers (random or specified), Gaussian spread around each center. Good for villages, forests.

### Path Placement
Along a spline/bezier curve. Good for fences, roads, torches, river objects.

### Ring Placement
Circular arrangement at specified radius. Good for walls, arena seating, ritual circles.

### Terrain-Aware Placement Rules
```csharp
// Raycast to find terrain surface
Ray ray = new Ray(new Vector3(worldX, 1000f, worldZ), Vector3.down);
if (Physics.Raycast(ray, out RaycastHit hit, 2000f))
{
    Vector3 pos = hit.point;
    float slope = Vector3.Angle(hit.normal, Vector3.up);
    if (slope <= maxSlope) // Place object
    {
        GameObject obj = PrefabUtility.InstantiatePrefab(prefab) as GameObject;
        obj.transform.position = pos;
        if (alignToTerrain) obj.transform.up = hit.normal;
        obj.transform.rotation *= Quaternion.Euler(0, Random.Range(0, 360), 0);
        float scale = Random.Range(scaleMin, scaleMax);
        obj.transform.localScale = Vector3.one * scale;
        obj.transform.SetParent(parentContainer);
        Undo.RegisterCreatedObjectUndo(obj, "Place Prefab");
    }
}
```

## Lighting Mood Presets

| Mood | Sun Intensity | Sun Color | Ambient Color | Fog | Fog Color | Fog Density |
|------|--------------|-----------|---------------|-----|-----------|-------------|
| bright-day | 1.2 | #FFF8E7 | #B4C8E0 | off | - | - |
| sunset | 0.8 | #FF6B35 | #8B4513 | light | #FF8C69 | 0.005 |
| golden-hour | 0.9 | #FFD700 | #DEB887 | light | #F0E68C | 0.003 |
| overcast | 0.5 | #C0C0C0 | #808080 | medium | #A9A9A9 | 0.01 |
| mystical | 0.4 | #9370DB | #4B0082 | heavy | #6A0DAD | 0.02 |
| dark-horror | 0.15 | #696969 | #1A1A2E | heavy | #0D0D0D | 0.03 |
| moonlit | 0.3 | #E0E8FF | #191970 | thin | #2F4F7F | 0.005 |
| dawn | 0.6 | #FF7F50 | #FFE4E1 | light | #FFDAB9 | 0.004 |
| volcanic-glow | 0.7 | #FF4500 | #8B0000 | heavy | #FF6347 | 0.025 |
| ethereal | 0.5 | #E0FFFF | #7FFFD4 | medium | #AFEEEE | 0.015 |

## Water Body Types

| Type | Wave Height | Wave Speed | Carve Depth | Notes |
|------|------------|------------|-------------|-------|
| lake | 0.2 | 0.5 | 5 | Circular depression at low point |
| river | 0.3 | 1.5 | 3 | Carved channel along bezier path |
| ocean | 0.8 | 1.0 | 0 | Large plane at terrain edge, flatten coast |
| pond | 0.05 | 0.3 | 2 | Small circular, minimal waves |
| waterfall | 0.5 | 2.0 | 8 | Steep terrain drop + particles |
| moat | 0.1 | 0.2 | 4 | Ring around specified center point |
| stream | 0.1 | 1.0 | 1.5 | Narrow winding path |

## Integration Patterns

### Scanning Project for Assets
```csharp
// Find all prefabs in project
string[] guids = AssetDatabase.FindAssets("t:Prefab", new[] { "Assets" });
foreach (string guid in guids)
{
    string path = AssetDatabase.GUIDToAssetPath(guid);
    GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
}

// Find terrain layers
string[] layerGuids = AssetDatabase.FindAssets("t:TerrainLayer", new[] { "Assets" });

// Find materials
string[] matGuids = AssetDatabase.FindAssets("t:Material", new[] { "Assets" });
```

### Zone Integration (Optional)
If a `ZoneManager` component exists in the scene, world generation commands should respect zone boundaries for enemy spawning, vegetation density, and terrain modifications. Check for zone system:
```csharp
var zoneManager = FindObjectsByType<MonoBehaviour>(FindObjectsSortMode.None)
    .FirstOrDefault(m => m.GetType().Name == "ZoneManager");
```
