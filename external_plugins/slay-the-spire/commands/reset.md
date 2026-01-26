---
allowed-tools: all
description: Reset current run state
---

# Reset Run

Invoke @spire:spire to reset the current run tracking session.

## Usage

```
/slay-the-spire:reset
```

This will:
- Clear the current session state
- Reset run tracking data
- Confirm before resetting (check with you first)

**Note:** This cannot be undone! Consider using `/slay-the-spire:export` to save your run before resetting.
