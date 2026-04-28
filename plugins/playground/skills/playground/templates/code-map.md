# Code Map Template

Use this template when the playground is about visualizing codebase architecture: component relationships, data flow, layer diagrams, system architecture with interactive commenting for feedback.

## Layout

```
+-------------------+----------------------------------+
|                   |                                  |
|  Controls:        |  SVG Canvas                      |
|  • View presets   |  (nodes + connections)           |
|  • Layer toggles  |  with zoom controls              |
|  • Connection     |                                  |
|    type filters   |  Legend (bottom-left)            |
|                   |                                  |
|  Comments (n):    +----------------------------------+
|  • List of user   |  Prompt output                   |
|    comments with  |  [ Copy Prompt ]                 |
|    delete buttons |                                  |
+-------------------+----------------------------------+
```

Code map playgrounds use an SVG canvas for the architecture diagram. Users click components to add comments, which become part of the generated prompt. Layer and connection filters let users focus on specific parts of the system.

## Control types for code maps

| Decision | Control | Example |
|---|---|---|
| System view | Preset buttons | Full System, Chat Flow, Data Flow, Agent System |
| Visible layers | Checkboxes | Client, Server, SDK, Data, External |
| Connection types | Checkboxes with color indicators | Data Flow (blue), Tool Calls (green), Events (red) |
| Component feedback | Click-to-comment modal | Opens modal with textarea for feedback |
| Zoom level | +/−/reset buttons | Scale SVG for detail |

## Canvas rendering

Use an `<svg>` element with dynamically generated nodes and paths. Key patterns:

- **Nodes:** Rounded rectangles with title and subtitle (file path)
- **Connections:** Curved paths (bezier) with arrow markers, styled by type
- **Layer organization:** Group nodes by Y-position bands (e.g., y: 30-80 = Client, y: 130-180 = Server)
- **Click-to-comment:** Click node → open modal → save comment → node gets visual indicator
- **Filtering:** Toggle visibility of nodes by layer, connections by type

```javascript
const nodes = [
  { id: 'api-client', label: 'API Client', subtitle: 'src/api/client.ts',
    x: 100, y: 50, w: 140, h: 45, layer: 'client', color: '#dbeafe' },
  // ...
];

const connections = [
  { from: 'api-client', to: 'server', type: 'data-flow', label: 'HTTP' },
  { from: 'server', to: 'db', type: 'data-flow' },
  // ...
];

function renderDiagram() {
  const visibleNodes = nodes.filter(n => state.layers[n.layer]);
  // Draw connections first (under nodes), then nodes
  connections.forEach(c => drawConnection(c));
  visibleNodes.forEach(n => drawNode(n));
}
```

## Connection types and styling

Define 3-5 connection types with distinct visual styles:

| Type | Color | Style | Use for |
|---|---|---|---|
| `data-flow` | Blue (#3b82f6) | Solid line | Request/response, data passing |
| `tool-call` | Green (#10b981) | Dashed (6,3) | Function calls, API invocations |
| `event` | Red (#ef4444) | Short dash (4,4) | Async events, pub/sub |
| `skill-invoke` | Orange (#f97316) | Long dash (8,4) | Plugin/skill activation |
| `dependency` | Gray (#6b7280) | Dotted | Import/require relationships |

Use SVG markers for arrowheads:

```html
<marker id="arrowhead-blue" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
  <polygon points="0 0, 8 3, 0 6" fill="#3b82f6"/>
</marker>
```

## Comment system

The key differentiator for code maps is click-to-comment functionality:

1. **Click node** → Open modal with component name, file path, textarea
2. **Save comment** → Add to comments list, mark node with visual indicator (colored border)
3. **View comments** → Sidebar list with component name, comment preview, delete button
4. **Delete comment** → Remove from list, update node visual, regenerate prompt

Comments should include the component context:

```javascript
state.comments.push({
  id: Date.now(),
  target: node.id,
  targetLabel: node.label,
  targetFile: node.subtitle,
  text: userInput
});
```

## Prompt output for code maps

The prompt combines system context with user comments:

```
This is the [PROJECT NAME] architecture, focusing on the [visible layers].

Feedback on specific components:

**API Client** (src/api/client.ts):
I want to add retry logic with exponential backoff here.

**Database Manager** (src/db/manager.ts):
Can we add connection pooling? Current implementation creates new connections per request.

**Auth Middleware** (src/middleware/auth.ts):
This should validate JWT tokens and extract user context.
```

Only include comments the user added. Mention which layers are visible if not showing the full system.

## Pre-populating with real data

For a specific codebase, pre-populate with:

- **Nodes:** 15-25 key components with real file paths
- **Connections:** 20-40 relationships based on actual imports/calls
- **Layers:** Logical groupings (UI, API, Business Logic, Data, External)
- **Presets:** "Full System", "Frontend Only", "Backend Only", "Data Flow"

Organize nodes in horizontal bands by layer, with consistent spacing.

## Layer color palette (light theme)

| Layer | Node fill | Description |
|---|---|---|
| Client/UI | #dbeafe (blue-100) | React components, hooks, pages |
| Server/API | #fef3c7 (amber-100) | Express routes, middleware, handlers |
| SDK/Core | #f3e8ff (purple-100) | Core libraries, SDK wrappers |
| Agent/Logic | #dcfce7 (green-100) | Business logic, agents, processors |
| Data | #fce7f3 (pink-100) | Database, cache, storage |
| External | #fbcfe8 (pink-200) | Third-party services, APIs |

## Example topics

- Codebase architecture explorer (modules, imports, data flow)
- Microservices map (services, queues, databases, API gateways)
- React component tree (components, hooks, context, state)
- API architecture (routes, middleware, controllers, models)
- Agent system (prompts, tools, skills, subagents)
- Data pipeline (sources, transforms, sinks, scheduling)
- Plugin/extension architecture (core, plugins, hooks, events)
