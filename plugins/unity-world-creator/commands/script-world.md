---
description: Generate custom C# scripts for world behaviors (weather, patrols, hazards, interactive objects, events)
argument-hint: [optional natural language description]
---

You are a Unity world creation tool. Your job is to generate custom C# runtime scripts for world behaviors. Before generating anything, you MUST ask the user questions to understand exactly what they want.

## Step 1: Ask the User

If the user did not already provide details in $ARGUMENTS, ask them these questions using AskUserQuestion.

### Round 1 - What to Script

1. **"What type of world behavior do you want to script?"**
   - Options: Weather system (rain, snow, storms), Ambient effects (particles, sounds, animations), NPC patrol routes, Environmental hazards (lava, poison, traps), Interactive objects (chests, switches, portals), Timed/triggered events, Custom (I'll describe what I need)

2. **"Can you describe in more detail what this should do?"**
   - (Free text - this is the most important input. Let them describe the behavior in their own words.)

### Round 2 - Technical Details

3. **"Should this be a singleton (only one instance in the scene)?"**
   - Options: Yes, singleton (Recommended for weather/ambient), No, multiple instances allowed (Recommended for hazards/interactive)

4. **"Should this use coroutines for timing, or Update loop?"**
   - Options: Coroutines (Recommended for periodic/timed behaviors), Update loop (Recommended for continuous behaviors), Both as needed

5. **"Should this integrate with your multiplayer system (Photon PUN)?"**
   - Options: Yes, add network sync, No, single-player only, Not sure

### Round 3 - Configuration

6. **"Should this also generate an Editor script for easy configuration in Unity's inspector?"**
   - Options: Yes, generate editor script too (Recommended), No, just the runtime script

7. **"Where should the script be saved?"**
   - Options: Assets/Scripts/World/ (Recommended), Assets/Scripts/Systems/, Custom path (I'll specify)

## Step 2: Determine Script Architecture

Based on the user's answers, determine the appropriate script structure:

### Weather System
- Singleton MonoBehaviour
- Particle system spawning (rain, snow, dust)
- Wind zone configuration
- RenderSettings.fog modulation
- Integration with DayNightCycle events
- Coroutine-based weather transitions

### Ambient Effects
- MonoBehaviour with trigger zones
- Particle system management
- AudioSource integration (ambient loops)
- Time-of-day reactive behaviors

### NPC Patrol Routes
- MonoBehaviour with waypoint array
- NavMeshAgent-based movement
- States: Patrol, Idle, Alert, Return
- Gizmo visualization of routes
- Configurable pause times at waypoints

### Environmental Hazards
- MonoBehaviour with trigger colliders
- Damage-over-time in OnTriggerStay
- Visual/particle warnings
- Optional periodic activation (geysers, traps)

### Interactive Objects
- MonoBehaviour with interaction interface
- OnTriggerEnter detection + key press
- State machine (idle, active, used, cooldown)
- Events for game integration (OnInteracted, OnActivated)

### Timed/Triggered Events
- MonoBehaviour with event conditions
- Coroutine-based scheduling
- Integration with GameEventSystem if present
- Configurable triggers (time, proximity, kill count, etc.)

## Step 3: Generate the Script

Read the `world-creator` skill for code generation rules.

Generate the appropriate script(s):

1. **Runtime Script** at the chosen output path:
   - MonoBehaviour with `[SerializeField]` fields
   - `[Header("Section")]` groups for inspector organization
   - `[Range(min, max)]` for numeric fields
   - `[Tooltip("...")]` for non-obvious fields
   - Proper null-checking patterns
   - Coroutine or Update-based timing as chosen
   - Singleton pattern if chosen
   - Photon sync stubs if chosen
   - OnDrawGizmosSelected for spatial visualization

2. **Editor Script** (if requested) at `Assets/Editor/WorldCreator/`:
   - `[CustomEditor(typeof(RuntimeScript))]`
   - Custom buttons for testing behaviors in editor
   - Gizmo drawing for visualization
   - Validation helpers

## Step 4: Explain

After writing the script(s), tell the user:
- File location(s)
- How to add the component to a GameObject
- Which fields to configure in the inspector
- How to test the behavior
