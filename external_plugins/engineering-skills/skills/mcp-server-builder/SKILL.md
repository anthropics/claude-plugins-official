---
name: mcp-server-builder
description: >
  Build production-ready MCP (Model Context Protocol) servers with tool
  definitions, resource providers, prompt templates, and transport
  configuration. Covers OpenAPI-to-MCP conversion, TypeScript and Python
  implementations, testing strategies, authentication, and deployment. Use when
  exposing APIs to AI agents, building tool servers, or creating MCP
  integrations.
license: MIT + Commons Clause
metadata:
  version: 1.0.0
  author: borghei
  category: engineering
  domain: ai-integration
  tier: POWERFUL
  updated: 2026-03-09
  frameworks: mcp-sdk, typescript, python, openapi
---
# MCP Server Builder

**Tier:** POWERFUL
**Category:** Engineering / AI Integration
**Maintainer:** Claude Skills Team

## Overview

Design and ship production-ready MCP (Model Context Protocol) servers from API contracts. Covers tool definition best practices, resource providers, prompt templates, OpenAPI-to-MCP conversion, TypeScript and Python server implementations, transport selection (stdio, SSE, StreamableHTTP), authentication patterns, testing strategies, and deployment configurations. Treats schema quality and tool discoverability as first-class concerns.

## Keywords

MCP, Model Context Protocol, MCP server, tool definition, resource provider, prompt template, stdio transport, SSE transport, OpenAPI to MCP, AI tool server, Claude tools

## Core Capabilities

### 1. Tool Design and Schema Quality
- Verb-noun naming conventions for maximum LLM selection accuracy
- Description engineering with usage context and return value documentation
- Input schema design with proper types, constraints, and descriptions
- Output formatting for LLM consumption (structured text over raw JSON)

### 2. Server Implementation
- TypeScript server with @modelcontextprotocol/sdk
- Python server with mcp[cli] package
- Tool, resource, and prompt registration patterns
- Error handling with structured error responses
- Middleware for logging, auth, and rate limiting

### 3. Transport and Deployment
- stdio for local/CLI integration (Claude Code, Cursor)
- SSE for web-based integrations
- StreamableHTTP for production HTTP deployments
- Docker containerization for remote MCP servers
- Health checking and graceful shutdown

### 4. Testing and Validation
- Tool schema validation (naming, descriptions, types)
- Integration testing with MCP Inspector
- Contract testing with snapshot comparisons
- Load testing for remote server deployments

## When to Use

- Exposing an internal REST API to Claude, Cursor, or other MCP clients
- Replacing brittle browser automation with typed tool interfaces
- Building a shared MCP server for multiple teams and AI assistants
- Converting an OpenAPI spec into MCP tools automatically
- Creating domain-specific tool servers (database, monitoring, deployment)

## Tool Schema Design

### Naming Conventions

```
Pattern: verb_noun or verb_noun_qualifier

GOOD names:
  search_documents         — clear action + target
  create_github_issue      — includes service for disambiguation
  get_deployment_status    — standard CRUD verb
  run_database_query       — action implies execution
  list_pull_requests       — list for collection retrieval

BAD names:
  search                   — search what?
  documents                — not a verb_noun
  doSearch                 — camelCase, vague
  handle_request           — implementation detail, not intent
  helper                   — meaningless
```

### Description Engineering

The description determines whether an LLM selects your tool. Write it for the LLM, not for humans.

```
Template: "[What it does]. [What it returns]. [When to use it]."

EFFECTIVE:
"Search the codebase for files matching a regex pattern. Returns file paths,
line numbers, and matching content snippets ranked by relevance. Use when
looking for implementations, definitions, or usage of specific code patterns."

INEFFECTIVE:
"Searches files."           — no return value, no usage guidance
"A powerful search tool..." — marketing copy
"Wrapper around ripgrep"    — implementation detail
```

### Input Schema Best Practices

```json
{
  "name": "query_database",
  "description": "Execute a read-only SQL query against the application database. Returns up to 100 rows as a formatted table. Use when the user needs to look up data, run reports, or investigate database state. Only SELECT statements are allowed.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "sql": {
        "type": "string",
        "description": "SQL SELECT query to execute. Must be a read-only query. Example: SELECT id, email, created_at FROM users WHERE created_at > '2026-01-01' LIMIT 10"
      },
      "database": {
        "type": "string",
        "enum": ["primary", "analytics", "staging"],
        "default": "primary",
        "description": "Which database to query. Use 'analytics' for reporting queries on large datasets."
      },
      "format": {
        "type": "string",
        "enum": ["table", "json", "csv"],
        "default": "table",
        "description": "Output format. 'table' is best for display, 'json' for programmatic use."
      }
    },
    "required": ["sql"]
  }
}
```

## TypeScript MCP Server

### Complete Server with Tools, Resources, and Prompts

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "project-tools",
  version: "1.0.0",
});

// ──── TOOLS ────

server.tool(
  "search_codebase",
  "Search project files for a regex pattern. Returns file paths, line numbers, and matching lines. Use when looking for code patterns, function definitions, or usage of specific identifiers.",
  {
    pattern: z.string().describe("Regex pattern to search for. Example: 'async function handle'"),
    file_glob: z.string().default("**/*.{ts,tsx,js,jsx}")
      .describe("File glob pattern to filter. Example: '**/*.test.ts' for test files only"),
    max_results: z.number().int().min(1).max(100).default(20)
      .describe("Maximum results to return"),
  },
  async ({ pattern, file_glob, max_results }) => {
    const { execSync } = await import("child_process");
    try {
      const output = execSync(
        `rg --json -e '${pattern.replace(/'/g, "\\'")}' --glob '${file_glob}' --max-count ${max_results}`,
        { cwd: process.env.PROJECT_ROOT || ".", timeout: 10000 }
      ).toString();

      const matches = output
        .split("\n")
        .filter(Boolean)
        .map((line) => JSON.parse(line))
        .filter((entry) => entry.type === "match")
        .map((entry) => ({
          file: entry.data.path.text,
          line: entry.data.line_number,
          content: entry.data.lines.text.trim(),
        }));

      if (matches.length === 0) {
        return { content: [{ type: "text", text: `No matches found for pattern: ${pattern}` }] };
      }

      const formatted = matches
        .map((m) => `${m.file}:${m.line}  ${m.content}`)
        .join("\n");

      return {
        content: [{ type: "text", text: `Found ${matches.length} matches:\n\n${formatted}` }],
      };
    } catch (error) {
      return {
        content: [{ type: "text", text: `Search failed: ${error.message}` }],
        isError: true,
      };
    }
  }
);

server.tool(
  "run_tests",
  "Run the project test suite or specific test files. Returns pass/fail results with failure details. Use when verifying code changes or checking test coverage.",
  {
    file_pattern: z.string().optional()
      .describe("Optional test file pattern. Example: 'auth' to run only auth-related tests"),
    coverage: z.boolean().default(false)
      .describe("Include coverage report in output"),
  },
  async ({ file_pattern, coverage }) => {
    const { execSync } = await import("child_process");
    const args = [file_pattern, coverage ? "--coverage" : ""].filter(Boolean).join(" ");

    try {
      const output = execSync(`pnpm test ${args}`, {
        cwd: process.env.PROJECT_ROOT || ".",
        timeout: 120000,
        env: { ...process.env, CI: "true" },
      }).toString();

      return { content: [{ type: "text", text: output }] };
    } catch (error) {
      return {
        content: [{ type: "text", text: `Tests failed:\n\n${error.stdout?.toString() || error.message}` }],
        isError: true,
      };
    }
  }
);

// ──── RESOURCES ────

server.resource(
  "project://readme",
  "project://readme",
  async (uri) => {
    const fs = await import("fs/promises");
    const content = await fs.readFile("README.md", "utf-8");
    return {
      contents: [{ uri: uri.href, mimeType: "text/markdown", text: content }],
    };
  }
);

// ──── PROMPTS ────

server.prompt(
  "review_code",
  "Generate a code review prompt for the given file",
  { file_path: z.string().describe("Path to the file to review") },
  async ({ file_path }) => {
    const fs = await import("fs/promises");
    const content = await fs.readFile(file_path, "utf-8");
    return {
      messages: [
        {
          role: "user",
          content: {
            type: "text",
            text: `Review this code for bugs, security issues, and improvement opportunities:\n\n\`\`\`\n${content}\n\`\`\``,
          },
        },
      ],
    };
  }
);

// ──── START SERVER ────
const transport = new StdioServerTransport();
await server.connect(transport);
```

## Python MCP Server

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import subprocess
import json

server = Server("project-tools")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="search_codebase",
            description="Search project files for a regex pattern. Returns file paths, line numbers, and matching content. Use when looking for code patterns or definitions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Regex pattern to search for",
                    },
                    "file_type": {
                        "type": "string",
                        "enum": ["py", "ts", "go", "rs", "all"],
                        "default": "all",
                        "description": "Filter by file type",
                    },
                },
                "required": ["pattern"],
            },
        ),
        Tool(
            name="run_command",
            description="Run a shell command in the project directory. Returns stdout and stderr. Use for running tests, linting, or build commands. Only allows pre-approved commands.",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "enum": ["test", "lint", "build", "typecheck", "format"],
                        "description": "Pre-approved command to run",
                    },
                },
                "required": ["command"],
            },
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "search_codebase":
        return await _search_codebase(arguments)
    elif name == "run_command":
        return await _run_command(arguments)
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

COMMAND_MAP = {
    "test": "python -m pytest -v",
    "lint": "ruff check .",
    "build": "python -m build",
    "typecheck": "mypy src/",
    "format": "ruff format --check .",
}

async def _run_command(args: dict) -> list[TextContent]:
    cmd = COMMAND_MAP.get(args["command"])
    if not cmd:
        return [TextContent(type="text", text=f"Unknown command: {args['command']}")]
    try:
        result = subprocess.run(
            cmd.split(), capture_output=True, text=True, timeout=120
        )
        output = result.stdout + ("\n" + result.stderr if result.stderr else "")
        return [TextContent(type="text", text=output or "Command completed with no output.")]
    except subprocess.TimeoutExpired:
        return [TextContent(type="text", text="Command timed out after 120 seconds.")]

async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## OpenAPI to MCP Conversion

### Conversion Rules

```
OpenAPI Element          → MCP Element
─────────────────────────────────────────────
operationId              → Tool name (snake_case)
summary + description    → Tool description
parameters + requestBody → inputSchema
responses.200            → Tool output format
securitySchemes          → Server auth config
servers[0].url           → Base URL for requests
```

### Conversion Script Pattern

```python
def openapi_operation_to_mcp_tool(operation: dict, path: str, method: str) -> dict:
    """Convert a single OpenAPI operation to an MCP tool definition."""
    # Derive tool name from operationId or path
    name = operation.get("operationId")
    if not name:
        name = f"{method}_{path.replace('/', '_').strip('_')}"
    name = name.replace("-", "_").lower()

    # Build description from summary + description
    summary = operation.get("summary", "")
    description = operation.get("description", "")
    tool_description = f"{summary}. {description}".strip(". ") + "."

    # Build input schema from parameters and request body
    properties = {}
    required = []

    for param in operation.get("parameters", []):
        prop = {
            "type": param["schema"].get("type", "string"),
            "description": param.get("description", ""),
        }
        if "enum" in param["schema"]:
            prop["enum"] = param["schema"]["enum"]
        if "default" in param["schema"]:
            prop["default"] = param["schema"]["default"]
        properties[param["name"]] = prop
        if param.get("required"):
            required.append(param["name"])

    # Request body properties
    body_schema = (
        operation.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
    )
    if body_schema.get("properties"):
        properties.update(body_schema["properties"])
        required.extend(body_schema.get("required", []))

    return {
        "name": name,
        "description": tool_description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }
```

## Client Configuration

### Claude Code (claude_desktop_config.json)

```json
{
  "mcpServers": {
    "project-tools": {
      "command": "node",
      "args": ["dist/index.js"],
      "cwd": "/path/to/mcp-server",
      "env": {
        "PROJECT_ROOT": "/path/to/project",
        "DATABASE_URL": "postgresql://..."
      }
    },
    "remote-api-tools": {
      "url": "https://mcp.mycompany.com/sse",
      "headers": {
        "Authorization": "Bearer ${MCP_API_TOKEN}"
      }
    }
  }
}
```

## Testing MCP Servers

### Schema Validation

```typescript
function validateToolSchema(tool: { name: string; description: string; inputSchema: any }): string[] {
  const issues: string[] = [];

  // Name validation
  if (!/^[a-z][a-z0-9_]*$/.test(tool.name)) {
    issues.push(`Name '${tool.name}' must be snake_case`);
  }

  // Description validation
  if (tool.description.length < 30) {
    issues.push("Description too short for reliable LLM tool selection");
  }
  if (!tool.description.includes("Use when") && !tool.description.includes("Use for")) {
    issues.push("Description should include usage guidance ('Use when...')");
  }

  // Schema validation
  const schema = tool.inputSchema;
  if (schema.type !== "object") {
    issues.push("inputSchema.type must be 'object'");
  }
  for (const [prop, def] of Object.entries(schema.properties || {})) {
    if (!(def as any).description) {
      issues.push(`Property '${prop}' missing description`);
    }
  }

  return issues;
}
```

### Integration Testing with MCP Inspector

```bash
# Install MCP Inspector
npx @modelcontextprotocol/inspector

# Test stdio server
npx @modelcontextprotocol/inspector node dist/index.js

# Test SSE server
npx @modelcontextprotocol/inspector --url http://localhost:3001/sse
```

## Versioning Strategy

- **Additive changes** (new tools, new optional parameters): non-breaking, bump minor version
- **Tool removal or rename**: breaking, requires deprecation period + major version bump
- **Required parameter addition**: breaking, consider making it optional with a default instead
- **Response format changes**: potentially breaking, document in changelog

## Common Pitfalls

- **Vague tool descriptions** causing the LLM to select the wrong tool or skip yours entirely
- **Missing property descriptions** leaving the LLM to guess what a parameter means
- **No timeout on tool execution** allowing runaway processes to hang the server
- **Exposing destructive operations without confirmation** — add a `confirm: true` required parameter
- **Returning raw JSON instead of formatted text** — LLMs work better with readable text output
- **No error handling** causing the server to crash on unexpected input
- **Breaking changes without versioning** breaking all connected clients simultaneously

## Best Practices

1. **Description-first design** — write the tool description before implementing the handler
2. **One intent per tool** — a tool that does three things confuses LLM selection
3. **Validate inputs in the handler** — never trust that the LLM sent correct types
4. **Return human-readable text** — format output as tables or structured text, not raw JSON
5. **Set timeouts on all operations** — prevent runaway commands from blocking the server
6. **Test tool selection** — present your tools to an LLM and verify it picks the right one for various prompts
7. **Log every tool call** — capture name, inputs, outputs, duration, and errors for debugging
8. **Version your tools** — maintain backward compatibility for at least one release cycle

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| LLM never selects my tool | Tool description is too vague or missing usage guidance | Rewrite the description using the template: "[What it does]. [What it returns]. [When to use it]." Ensure at least 30 characters and include "Use when..." phrasing |
| Tool call returns empty or `null` | Handler returns raw `undefined` instead of a content array | Always return `{ content: [{ type: "text", text: "..." }] }` even for empty results — never return bare `null` or `undefined` |
| `ECONNREFUSED` when connecting to remote server | SSE/HTTP server not running or wrong port in client config | Verify the server process is listening (`curl http://localhost:<port>/sse`), check `url` in `claude_desktop_config.json`, and confirm no firewall rules block the port |
| `spawn ENOENT` on stdio server startup | The `command` path in client config points to a missing binary | Use absolute paths for `command` (e.g., `/usr/local/bin/node`) or ensure the binary is on the shell PATH that the MCP host process inherits |
| Client connects but lists zero tools | `list_tools` handler not registered or returns an empty array | Confirm `@server.list_tools()` (Python) or `server.tool()` (TypeScript) is called before `server.connect()`. Test with MCP Inspector to verify the handshake |
| Tool execution times out | No timeout set on subprocess or HTTP calls inside the handler | Add explicit `timeout` to every `subprocess.run()`, `execSync()`, and `fetch()` call. 10-30 seconds for queries, 120 seconds max for builds |
| Schema validation errors from the client | `inputSchema.type` is not `"object"` or required fields are misspelled | Validate your tool definitions with the `validateToolSchema` function from the Testing section. Every `inputSchema` must have `type: "object"` at the top level |

## Success Criteria

- **Tool selection accuracy ≥ 90%** — when presented with 10 natural-language prompts, the LLM picks the correct tool at least 9 times
- **Schema validation passes at 100%** — every tool clears the `validateToolSchema` checks with zero issues (snake_case name, ≥30-char description, usage guidance, property descriptions)
- **Median tool response time < 2 seconds** — measured end-to-end from tool call to content response for typical queries
- **Zero unhandled exceptions** — every tool handler catches errors and returns a structured `isError: true` response instead of crashing the server
- **MCP Inspector green path** — the server connects, lists tools, executes each tool, and returns valid content through MCP Inspector without manual fixes
- **Client configuration works first try** — a new developer can copy the provided `claude_desktop_config.json` snippet, start the server, and invoke a tool within 5 minutes
- **OpenAPI conversion coverage ≥ 80%** — for a standard OpenAPI 3.x spec, at least 80% of operations convert to usable MCP tools without manual edits

## Scope & Limitations

**This skill covers:**
- Designing tool schemas, resource providers, and prompt templates for MCP servers
- Implementing servers in TypeScript (`@modelcontextprotocol/sdk`) and Python (`mcp[cli]`)
- Transport selection and client configuration (stdio, SSE, StreamableHTTP)
- OpenAPI-to-MCP conversion patterns and testing strategies

**This skill does NOT cover:**
- Building MCP clients or custom LLM orchestration layers — see `engineering/agent-workflow-designer`
- Designing multi-agent systems that consume MCP tools — see `engineering/agent-designer`
- API design itself (REST conventions, endpoint naming, versioning) — see `engineering/api-design-reviewer`
- Infrastructure provisioning, container orchestration, or CI/CD pipelines for deploying MCP servers — see `engineering/ci-cd-pipeline-builder`

## Integration Points

| Skill | Integration | Data Flow |
|-------|-------------|-----------|
| `engineering/api-design-reviewer` | Review the underlying REST API before converting it to MCP tools | OpenAPI spec → API review findings → refined spec → MCP conversion |
| `engineering/api-test-suite-builder` | Generate integration tests for the HTTP endpoints that MCP tools wrap | MCP tool definitions → endpoint mapping → test suite generation |
| `engineering/agent-designer` | Design agents that consume the MCP tools this skill produces | MCP tool schemas → agent tool inventory → agent behavior design |
| `engineering/observability-designer` | Add structured logging, tracing, and metrics to MCP server handlers | MCP server code → instrumentation plan → logging/tracing middleware |
| `engineering/ci-cd-pipeline-builder` | Automate build, test, and deploy pipelines for MCP server releases | MCP server repo → pipeline config → automated deploy to staging/prod |
| `engineering/env-secrets-manager` | Manage API keys, database credentials, and tokens used in MCP server configs | MCP server env vars → secrets audit → secure injection patterns |
