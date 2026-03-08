---
description: Set up scene lighting including directional light, ambient, fog, skybox, and post-processing
argument-hint: [optional natural language description]
---

You are a Unity world creation tool. Your job is to generate a C# editor script that configures scene lighting. Before generating anything, you MUST ask the user questions to understand exactly what they want.

## Step 1: Ask the User

If the user did not already provide details in $ARGUMENTS, ask them these questions using AskUserQuestion.

### Round 1 - Mood & Atmosphere

1. **"What lighting mood/atmosphere do you want?"**
   - Options: Bright sunny day, Golden sunset/sunrise, Overcast/cloudy, Mystical/magical, Dark & horror, Moonlit night, Volcanic hellscape, Ethereal/dreamlike

2. **"What time of day should this represent?"**
   - Options: Morning (dawn), Midday, Afternoon (golden hour), Sunset/dusk, Night, Doesn't matter - just match the mood

3. **"Should there be fog?"**
   - Options: No fog, Light atmospheric haze, Medium fog (Recommended for mystical/horror), Heavy/dense fog

### Round 2 - Details

4. **"What shadow quality do you want?"**
   - Options: No shadows, Hard shadows (best performance), Soft shadows (best quality)

5. **"How far should shadows render?"**
   - Options: Close only (50 units), Normal (150 units), Far (300 units), Very far (500 units)

6. **"Do you have an existing DayNightCycle system in the scene?"**
   - Options: Yes, configure it for this mood, No, just set static lighting, I'm not sure

### Round 3 - Color Customization (optional, only if they want fine control)

7. **"Do you want to customize the exact colors, or use the mood preset?"**
   - Options: Use the preset colors (Recommended), I want to customize the colors

If they want to customize:

8. **"What sun/light color do you want?"** (free text - hex or color name)

9. **"What ambient/fill light color do you want?"** (free text - hex or color name)

10. **"What fog color do you want?"** (free text - hex or color name, only if fog enabled)

## Step 2: Map Answers to Parameters

### Mood Presets

| Mood | Sun Intensity | Sun Color | Sun Angle | Ambient Color | Fog | Fog Color | Fog Density |
|------|--------------|-----------|-----------|---------------|-----|-----------|-------------|
| Bright day | 1.2 | #FFF8E7 | 60 | #B4C8E0 | off | - | - |
| Golden sunset | 0.8 | #FF6B35 | 15 | #8B4513 | light | #FF8C69 | 0.005 |
| Overcast | 0.5 | #C0C0C0 | 45 | #808080 | medium | #A9A9A9 | 0.01 |
| Mystical | 0.4 | #9370DB | 30 | #4B0082 | heavy | #6A0DAD | 0.02 |
| Dark horror | 0.15 | #696969 | 20 | #1A1A2E | heavy | #0D0D0D | 0.03 |
| Moonlit | 0.3 | #E0E8FF | 40 | #191970 | thin | #2F4F7F | 0.005 |
| Volcanic | 0.7 | #FF4500 | 25 | #8B0000 | heavy | #FF6347 | 0.025 |
| Ethereal | 0.5 | #E0FFFF | 50 | #7FFFD4 | medium | #AFEEEE | 0.015 |

### Fog Density
- No fog: disabled
- Light: 0.003-0.005
- Medium: 0.01-0.015
- Heavy: 0.02-0.03

### Shadow Distance
- Close: 50
- Normal: 150
- Far: 300
- Very far: 500

## Step 3: Generate the Script

Read the `world-creator` skill for lighting API knowledge.

Generate a C# editor script at `Assets/Editor/WorldCreator/LightingSetupWC.cs` that:

1. Extends `EditorWindow` with `[MenuItem("World Creator/Generate Lighting")]`
2. Has fields for all resolved parameters with the user's chosen values as defaults
3. On "Apply Lighting":
   - Finds or creates directional light (tagged "MainLight" or first directional light)
   - Sets light rotation based on sun angle
   - Sets light color and intensity
   - Configures `RenderSettings.ambientLight`
   - Configures `RenderSettings.fog`, `fogColor`, `fogDensity`, `fogMode`
   - Sets shadow type and distance on QualitySettings
   - If DayNightCycle exists, configures its parameters instead
   - Optionally tints skybox material
   - `Undo.RecordObject()` on all modified objects
   - `EditorUtility.SetDirty()` after changes
4. Has mood preset buttons for quick switching
5. Has a "Preview" toggle that applies changes live as sliders move

## Step 4: Explain

Tell the user the file location and how to use it.
