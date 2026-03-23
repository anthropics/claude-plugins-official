# mcp-server-dev

Skills for designing and building MCP servers that work seamlessly with Claude.

## What's inside

Three skills that compose into a full build path:

| Skill | Purpose |
|---|---|
| **`build-mcp-server`** | Entry point. Interrogates the use case, picks deployment model (remote HTTP / MCPB / local stdio), picks tool-design pattern, routes to a specialized skill. |
| **`build-mcp-app`** | Adds interactive UI widgets (forms, pickers, confirm dialogs) rendered inline in chat. Works on remote servers and MCPB bundles. |
| **`build-mcpb`** | Packages a local stdio server with its runtime so users can install it without Node/Python. For servers that must touch the local machine. |

## How it works

`build-mcp-server` is the front door. It asks what you're connecting to, who'll use it, how big the action surface is, and whether you need in-chat UI. From those answers it recommends one of four paths:

- **Remote streamable-HTTP** (the default recommendation for anything wrapping a cloud API) — scaffolded inline
- **MCP app** — hands off to `build-mcp-app`
- **MCPB** — hands off to `build-mcpb`
- **Local stdio prototype** — scaffolded inline with an MCPB upgrade note

Each skill ships reference files for the parts that don't fit in the main instructions: auth flows (DCR/CIMD), tool-description writing, widget templates, manifest schemas, security hardening.

## Usage

Ask Claude to "help me build an MCP server" and the entry skill will trigger. Or invoke directly:

```
/mcp-server-dev:build-mcp-server
```
