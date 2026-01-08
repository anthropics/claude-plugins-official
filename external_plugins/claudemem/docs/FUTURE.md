# Future: Obsidian Integration

ClaudeMem stores everything as markdown. This makes it compatible with Obsidian as a visual layer.

**Status**: Planned, not yet implemented

---

## The Vision

```
Claude Code          Obsidian
    │                    │
    └────── ~/Vault ─────┘
           (same files)
```

- **Claude** reads/writes the files
- **Obsidian** provides visual interface
- No sync needed - same folder

---

## What Obsidian Would Add

### Kanban Boards

Using the [Kanban plugin](https://github.com/mgmeyers/obsidian-kanban):

```
┌─────────────┬─────────────┬─────────────┐
│   Pending   │ In Progress │    Done     │
├─────────────┼─────────────┼─────────────┤
│ Task 1      │ Task 3      │ Task 5      │
│ Task 2      │             │ Task 6      │
│ Task 4      │             │             │
└─────────────┴─────────────┴─────────────┘
```

Drag tasks between columns → markdown updates → Claude sees changes.

### Graph View

Visualize connections between:
- Projects
- Epics
- Decisions
- Sessions

### Quick Manual Edits

Sometimes faster to edit directly in Obsidian than asking Claude.

### Mobile Access

Obsidian mobile app for checking status on the go.

---

## Potential Implementation

### 1. Auto-Generated Kanban

When creating a project, also create:

```markdown
<!-- Projects/{id}/Kanban.md -->
---
kanban-plugin: basic
---

## Pending
- [ ] Task from epic

## In Progress

## Done
```

### 2. Obsidian Plugin for ClaudeMem

A custom plugin that:
- Syncs task status between epic files and kanban
- Generates views from project data
- Provides quick actions (mark done, add task)

### 3. Templater Integration

Use Obsidian's Templater plugin for:
- Quick project creation
- Session note templates
- Decision log entries

---

## Why Not Build This Now?

1. **Core system must work first** - ClaudeMem needs to be solid before adding visual layer
2. **Optional complexity** - Many users won't need/want Obsidian
3. **Obsidian is just a viewer** - The value is in the Claude integration, not the UI

---

## How to Try It Today

Even without official integration:

1. Install Obsidian
2. "Open folder as vault" → select `~/Vault`
3. Install Kanban plugin
4. View your projects visually

Claude writes files, Obsidian displays them. No integration needed for basic use.

---

## Contributing

If you want to build Obsidian integration:

1. Open an issue to discuss approach
2. Keep it optional (core ClaudeMem should work without Obsidian)
3. Don't modify core file schemas
