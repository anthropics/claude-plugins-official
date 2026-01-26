---
allowed-tools: all
description: Start a new Slay the Spire run tracking session
---

# Start New Run

Invoke @spire:spire to initialize a new run tracking session.

## Usage

```
/slay-the-spire:start
```

This will:
- Create a new session state file
- Prompt for character selection (Ironclad, Silent, Defect, Watcher)
- Prompt for ascension level
- Initialize run tracking from scratch

**Optional:** Provide a screenshot to start from an existing run:
```
/slay-the-spire:start /path/to/screenshot.png
```
