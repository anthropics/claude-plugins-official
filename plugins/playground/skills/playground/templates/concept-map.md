# Concept Map Template

Use this template when the playground is about learning, exploration, or mapping relationships: concept maps, knowledge gap identification, scope mapping, task decomposition with dependencies.

## Layout

```
+--------------------------------------+
|  Canvas (draggable nodes, edges)     |
|  with tooltip on hover               |
+-------------------------+------------+
|                         |            |
|  Sidebar:               | Prompt     |
|  • Knowledge levels     | output     |
|  • Connection types     |            |
|  • Node list            | [Copy]     |
|  • Actions              |            |
+-------------------------+------------+
```

Canvas-based playgrounds differ from the two-panel split. The interactive visual IS the control — users drag nodes and draw connections rather than adjusting sliders. The sidebar supplements with toggles and list controls.

## Control types for concept maps

| Decision | Control | Example |
|---|---|---|
| Knowledge level per node | Click-to-cycle button in sidebar list | Know → Fuzzy → Unknown |
| Connection type | Selector before drawing | calls, depends on, contains, reads from |
| Node arrangement | Drag on canvas | spatial layout reflects mental model |
| Which nodes to include | Toggle or checkbox per node | hide/show concepts |
| Actions | Buttons | Auto-layout (force-directed), clear edges, reset |

## Canvas rendering

Use a `<canvas>` element with manual draw calls. Key patterns:

- **Hit testing:** Check mouse position against node bounding circles on mousedown/mousemove
- **Drag:** On mousedown on a node, track offset and update position on mousemove
- **Edge drawing:** Click node A, then click node B. Draw arrow between them with the selected relationship type
- **Tooltips:** On hover, position a div absolutely over the canvas with description text
- **Force-directed auto-layout:** Simple spring simulation — repulsion between all pairs, attraction along edges, iterate 100-200 times with damping

```javascript
function draw() {
  ctx.clearRect(0, 0, W, H);
  edges.forEach(e => drawEdge(e));  // edges first, under nodes
  nodes.forEach(n => drawNode(n));  // nodes on top
}
```

## Prompt output for concept maps

The prompt should be a targeted learning request shaped by the user's knowledge markings:

> "I'm learning [CODEBASE/DOMAIN]. I already understand: [know nodes]. I'm fuzzy on: [fuzzy nodes]. I have no idea about: [unknown nodes]. Here are the relationships I want to understand: [edge list in natural language]. Please explain the fuzzy and unknown concepts, focusing on these relationships. Build on what I already know. Use concrete code references."

Only include edges the user drew. Only mention concepts they marked as fuzzy or unknown in the explanation request.

## Pre-populating with real data

For codebases or domains, pre-populate with:
- **Nodes:** 15-20 key concepts with real file paths and short descriptions
- **Edges:** 20-30 pre-drawn relationships based on actual architecture
- **Knowledge:** Default all to "Fuzzy" so the user adjusts from there
- **Presets:** "Zoom out" (hide internal nodes, show only top-level), "Focus on [layer]" (highlight nodes in one area)

## Example topics

- Codebase architecture map (modules, data flow, state management)
- Framework learning (how React hooks connect, Next.js data fetching layers)
- System design (services, databases, queues, caches and how they relate)
- Task decomposition (goals → sub-tasks with dependency arrows, knowledge tags)
- API surface map (endpoints grouped by resource, shared middleware, auth layers)
