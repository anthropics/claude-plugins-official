# Unity Terrain API Reference

## TerrainData Core Methods

### Heightmap
| Method | Signature | Notes |
|--------|-----------|-------|
| GetHeights | `float[,] GetHeights(int xBase, int yBase, int width, int height)` | Returns normalized 0-1. Index order: [y, x] |
| SetHeights | `void SetHeights(int xBase, int yBase, float[,] heights)` | Normalized 0-1. Call terrain.Flush() after |
| heightmapResolution | `int` (read/write) | Must be power of 2 + 1 (33, 65, 129, 257, 513, 1025) |
| GetSteepness | `float GetSteepness(float x, float y)` | Returns slope in degrees (0-90). Inputs normalized 0-1 |
| GetInterpolatedNormal | `Vector3 GetInterpolatedNormal(float x, float y)` | Surface normal. Inputs normalized 0-1 |
| GetInterpolatedHeight | `float GetInterpolatedHeight(float x, float y)` | World-space height. Inputs normalized 0-1 |

### Alphamap (Texture Splatmap)
| Method | Signature | Notes |
|--------|-----------|-------|
| GetAlphamaps | `float[,,] GetAlphamaps(int x, int y, int width, int height)` | Third dim = layer index. Weights sum to 1.0 |
| SetAlphamaps | `void SetAlphamaps(int x, int y, float[,,] map)` | All layer weights at each point must sum to 1.0 |
| alphamapWidth | `int` (read-only) | Usually 512 or 1024 |
| alphamapHeight | `int` (read-only) | Usually 512 or 1024 |
| alphamapLayers | `int` (read-only) | Number of terrain layers |
| terrainLayers | `TerrainLayer[]` (read/write) | Modern API (replaces deprecated splatPrototypes) |

### Trees
| Method | Signature | Notes |
|--------|-----------|-------|
| treePrototypes | `TreePrototype[]` (read/write) | Array of tree prefab references |
| treeInstances | `TreeInstance[]` (read/write) | All placed trees. Position is normalized 0-1 |
| SetTreeInstance | `void SetTreeInstance(int index, TreeInstance instance)` | Modify single tree |
| treeInstanceCount | `int` (read-only) | Total tree count |

### Detail (Grass/Small Objects)
| Method | Signature | Notes |
|--------|-----------|-------|
| detailPrototypes | `DetailPrototype[]` (read/write) | Grass/detail definitions |
| GetDetailLayer | `int[,] GetDetailLayer(int xBase, int yBase, int width, int height, int layer)` | Density values |
| SetDetailLayer | `void SetDetailLayer(int xBase, int yBase, int layer, int[,] details)` | Set density per point |
| detailWidth | `int` (read-only) | Detail map width |
| detailHeight | `int` (read-only) | Detail map height |
| detailResolution | `int` (read/write via SetDetailResolution) | Resolution of detail maps |

### Size & Bounds
| Property | Type | Notes |
|----------|------|-------|
| size | `Vector3` (read/write) | (width, height, length) in world units |
| bounds | `Bounds` (read-only) | World-space bounding box |

## Terrain Component Methods
| Method | Notes |
|--------|-------|
| `Terrain.activeTerrain` | Static - returns first active terrain |
| `terrain.Flush()` | Must call after height changes to update rendering |
| `terrain.SampleHeight(Vector3 worldPos)` | World-space height at XZ position |
| `terrain.GetPosition()` | World position of terrain origin corner |

## TerrainLayer Properties
```csharp
TerrainLayer layer = new TerrainLayer();
layer.diffuseTexture = albedoTex;       // Main color texture
layer.normalMapTexture = normalTex;      // Normal map
layer.maskMapTexture = maskTex;          // Mask map (metallic, AO, height, smoothness)
layer.tileSize = new Vector2(15, 15);    // UV tiling size
layer.tileOffset = Vector2.zero;         // UV offset
layer.specular = Color.gray;             // Specular color
layer.metallic = 0f;                     // Metallic value 0-1
layer.smoothness = 0.5f;                 // Smoothness value 0-1
```

## TreeInstance Properties
```csharp
TreeInstance tree = new TreeInstance();
tree.position = new Vector3(normX, 0, normZ);  // Normalized 0-1 (y is ignored, auto-placed on surface)
tree.widthScale = Random.Range(0.8f, 1.2f);    // Width scale variation
tree.heightScale = Random.Range(0.8f, 1.2f);   // Height scale variation
tree.rotation = Random.Range(0, 2f * Mathf.PI); // Radians
tree.color = Color.white;                        // Instance color tint
tree.lightmapColor = Color.white;                // Lightmap color
tree.prototypeIndex = 0;                         // Index into treePrototypes array
```

## Perlin Noise Cheatsheet

### Standard Multi-Octave
```
Total iterations = octaves
Each octave: amplitude *= persistence, frequency *= lacunarity
Higher octaves = more detail, persistence < 1 = detail fades
Typical: octaves=4-8, persistence=0.3-0.6, lacunarity=1.8-2.5
```

### Ridged Noise (Canyons/Ridges)
```
value = 1.0 - abs(perlin * 2.0 - 1.0)
Creates sharp ridges where standard Perlin crosses zero
```

### Domain Warping (Organic Shapes)
```
float warpX = Perlin(x * 0.1, y * 0.1) * warpStrength;
float warpY = Perlin(x * 0.1 + 5.2, y * 0.1 + 1.3) * warpStrength;
float height = Perlin((x + warpX) * scale, (y + warpY) * scale);
```

### Radial Falloff (Islands)
```
float dx = (x / width) - 0.5f;
float dy = (y / height) - 0.5f;
float dist = Mathf.Sqrt(dx*dx + dy*dy) * 2f; // 0 at center, 1 at corners
float falloff = Mathf.Clamp01(1f - dist * falloffStrength);
height *= falloff;
```

## Editor Integration Patterns

### EditorWindow Template
```csharp
public class MyToolWC : EditorWindow
{
    [MenuItem("World Creator/My Tool")]
    static void ShowWindow() => GetWindow<MyToolWC>("My Tool");

    void OnGUI()
    {
        // Parameters
        value = EditorGUILayout.FloatField("Value", value);
        value = EditorGUILayout.Slider("Value", value, min, max);
        option = (MyEnum)EditorGUILayout.EnumPopup("Option", option);
        prefab = (GameObject)EditorGUILayout.ObjectField("Prefab", prefab, typeof(GameObject), false);

        EditorGUILayout.Space(10);
        if (GUILayout.Button("Generate", GUILayout.Height(30)))
        {
            Generate();
        }
    }
}
```

### Progress Bar for Long Operations
```csharp
try
{
    for (int i = 0; i < total; i++)
    {
        EditorUtility.DisplayProgressBar("World Creator", $"Processing {i}/{total}", (float)i / total);
        // ... work ...
    }
}
finally
{
    EditorUtility.ClearProgressBar();
}
```

### Asset Discovery
```csharp
// Find all prefabs containing "tree" in name
string[] guids = AssetDatabase.FindAssets("tree t:Prefab");
foreach (string guid in guids)
{
    string path = AssetDatabase.GUIDToAssetPath(guid);
    GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
}

// Find all TerrainLayer assets
string[] layerGuids = AssetDatabase.FindAssets("t:TerrainLayer");
```
