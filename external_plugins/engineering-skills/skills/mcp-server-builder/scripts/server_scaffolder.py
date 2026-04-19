#!/usr/bin/env python3
"""Generate MCP server boilerplate (TypeScript or Python) from a tool definition JSON config.

Reads a JSON config file containing server metadata and tool definitions, then
generates a complete, runnable MCP server implementation in the target language.

Usage:
    python server_scaffolder.py config.json --lang typescript --output ./server
    python server_scaffolder.py config.json --lang python --output ./server --json
"""

import argparse
import json
import os
import sys
import textwrap
from pathlib import Path


def load_config(config_path: str) -> dict:
    """Load and validate the tool definition config."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)

    errors = []
    if "name" not in config:
        errors.append("Missing required field: 'name'")
    if "tools" not in config or not isinstance(config.get("tools"), list):
        errors.append("Missing or invalid 'tools' array")
    else:
        for i, tool in enumerate(config["tools"]):
            if "name" not in tool:
                errors.append(f"Tool [{i}] missing 'name'")
            if "description" not in tool:
                errors.append(f"Tool [{i}] missing 'description'")
    if errors:
        raise ValueError("Config validation failed:\n  " + "\n  ".join(errors))
    return config


def generate_typescript(config: dict) -> dict[str, str]:
    """Generate TypeScript MCP server files."""
    server_name = config["name"]
    version = config.get("version", "1.0.0")
    tools = config.get("tools", [])

    # Build tool registrations
    tool_blocks = []
    for tool in tools:
        name = tool["name"]
        desc = tool["description"]
        schema = tool.get("inputSchema", {})
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        # Build zod schema lines
        zod_lines = []
        for prop_name, prop_def in properties.items():
            prop_type = prop_def.get("type", "string")
            prop_desc = prop_def.get("description", "")
            zod_type_map = {
                "string": "z.string()",
                "number": "z.number()",
                "integer": "z.number().int()",
                "boolean": "z.boolean()",
                "array": "z.array(z.any())",
            }
            zod_type = zod_type_map.get(prop_type, "z.string()")
            if "enum" in prop_def:
                enum_vals = ", ".join(f'"{v}"' for v in prop_def["enum"])
                zod_type = f"z.enum([{enum_vals}])"
            if "default" in prop_def:
                default_val = prop_def["default"]
                if isinstance(default_val, str):
                    zod_type += f'.default("{default_val}")'
                elif isinstance(default_val, bool):
                    zod_type += f".default({'true' if default_val else 'false'})"
                else:
                    zod_type += f".default({default_val})"
            if prop_name not in required:
                zod_type += ".optional()"
            if prop_desc:
                zod_type += f'.describe("{prop_desc}")'
            zod_lines.append(f"    {prop_name}: {zod_type},")

        zod_schema = "{\n" + "\n".join(zod_lines) + "\n  }" if zod_lines else "{}"
        params = ", ".join(properties.keys())
        param_destructure = f"{{ {params} }}" if params else "_args"

        block = textwrap.dedent(f"""\
        server.tool(
          "{name}",
          "{desc}",
          {zod_schema},
          async ({param_destructure}) => {{
            // TODO: Implement {name}
            return {{
              content: [{{ type: "text", text: "Tool {name} executed successfully." }}],
            }};
          }}
        );
        """)
        tool_blocks.append(block)

    tools_code = "\n".join(tool_blocks)

    index_ts = textwrap.dedent(f"""\
    import {{ McpServer }} from "@modelcontextprotocol/sdk/server/mcp.js";
    import {{ StdioServerTransport }} from "@modelcontextprotocol/sdk/server/stdio.js";
    import {{ z }} from "zod";

    const server = new McpServer({{
      name: "{server_name}",
      version: "{version}",
    }});

    // ──── TOOLS ────

    {tools_code}
    // ──── START SERVER ────
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error("{server_name} MCP server running on stdio");
    """)

    package_json = json.dumps({
        "name": server_name,
        "version": version,
        "type": "module",
        "scripts": {
            "build": "tsc",
            "start": "node dist/index.js",
            "dev": "tsx src/index.ts"
        },
        "dependencies": {
            "@modelcontextprotocol/sdk": "^1.0.0",
            "zod": "^3.22.0"
        },
        "devDependencies": {
            "typescript": "^5.3.0",
            "tsx": "^4.7.0",
            "@types/node": "^20.0.0"
        }
    }, indent=2) + "\n"

    tsconfig = json.dumps({
        "compilerOptions": {
            "target": "ES2022",
            "module": "ES2022",
            "moduleResolution": "bundler",
            "outDir": "./dist",
            "rootDir": "./src",
            "strict": True,
            "esModuleInterop": True,
            "skipLibCheck": True,
            "declaration": True
        },
        "include": ["src/**/*"]
    }, indent=2) + "\n"

    return {
        "src/index.ts": index_ts,
        "package.json": package_json,
        "tsconfig.json": tsconfig,
    }


def generate_python(config: dict) -> dict[str, str]:
    """Generate Python MCP server files."""
    server_name = config["name"]
    tools = config.get("tools", [])

    # Build tool list entries
    tool_list_entries = []
    handler_blocks = []
    for tool in tools:
        name = tool["name"]
        desc = tool["description"]
        schema = tool.get("inputSchema", {
            "type": "object", "properties": {}, "required": []
        })
        schema_str = json.dumps(schema, indent=12)

        tool_list_entries.append(textwrap.dedent(f"""\
            Tool(
                name="{name}",
                description="{desc}",
                inputSchema={schema_str},
            ),"""))

        handler_blocks.append(textwrap.dedent(f"""\
        if name == "{name}":
            # TODO: Implement {name}
            return [TextContent(type="text", text="Tool {name} executed successfully.")]
        """))

    tools_list_code = "\n        ".join(tool_list_entries)
    handlers_code = "    el".join(handler_blocks) if len(handler_blocks) > 1 else \
        "    " + handler_blocks[0] if handler_blocks else \
        '    return [TextContent(type="text", text=f"Unknown tool: {name}")]'

    # For elif chaining, the first block uses "if", rest use "elif" via the join
    server_py = textwrap.dedent(f"""\
    #!/usr/bin/env python3
    \"\"\"MCP server: {server_name}.\"\"\"

    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent

    server = Server("{server_name}")


    @server.list_tools()
    async def list_tools():
        return [
        {tools_list_code}
        ]


    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
    {handlers_code}
        return [TextContent(type="text", text=f"Unknown tool: {{name}}")]


    async def main():
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())


    if __name__ == "__main__":
        import asyncio
        asyncio.run(main())
    """)

    pyproject = textwrap.dedent(f"""\
    [project]
    name = "{server_name}"
    version = "{config.get('version', '1.0.0')}"
    requires-python = ">=3.10"
    dependencies = ["mcp[cli]>=1.0.0"]

    [build-system]
    requires = ["setuptools>=68.0"]
    build-backend = "setuptools.backends._legacy:_Backend"
    """)

    return {
        "server.py": server_py,
        "pyproject.toml": pyproject,
    }


def write_files(files: dict[str, str], output_dir: str, dry_run: bool = False) -> list[dict]:
    """Write generated files to disk. Returns metadata about written files."""
    results = []
    out = Path(output_dir)
    for rel_path, content in files.items():
        full_path = out / rel_path
        results.append({
            "path": str(full_path),
            "size_bytes": len(content.encode("utf-8")),
            "lines": content.count("\n"),
        })
        if not dry_run:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            if rel_path.endswith(".py"):
                os.chmod(full_path, 0o755)
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Generate MCP server boilerplate from a tool definition JSON config.",
        epilog="Example: %(prog)s config.json --lang typescript --output ./my-server",
    )
    parser.add_argument("config", help="Path to tool definition JSON config file")
    parser.add_argument(
        "--lang", choices=["typescript", "python"], default="typescript",
        help="Target language for server generation (default: typescript)",
    )
    parser.add_argument(
        "--output", "-o", default="./mcp-server",
        help="Output directory for generated files (default: ./mcp-server)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be generated without writing files",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output results as JSON instead of human-readable text",
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        if args.json:
            json.dump({"error": str(e)}, sys.stdout, indent=2)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.lang == "typescript":
        files = generate_typescript(config)
    else:
        files = generate_python(config)

    results = write_files(files, args.output, dry_run=args.dry_run)

    output = {
        "server_name": config["name"],
        "language": args.lang,
        "output_dir": str(Path(args.output).resolve()),
        "tools_count": len(config.get("tools", [])),
        "files": results,
        "dry_run": args.dry_run,
    }

    if args.json:
        json.dump(output, sys.stdout, indent=2)
        print()
    else:
        action = "Would generate" if args.dry_run else "Generated"
        print(f"{action} {args.lang} MCP server: {config['name']}")
        print(f"Output directory: {output['output_dir']}")
        print(f"Tools: {output['tools_count']}")
        print(f"\nFiles:")
        for f in results:
            print(f"  {f['path']} ({f['lines']} lines, {f['size_bytes']} bytes)")
        if not args.dry_run:
            if args.lang == "typescript":
                print(f"\nNext steps:\n  cd {args.output}\n  npm install\n  npm run dev")
            else:
                print(f"\nNext steps:\n  cd {args.output}\n  pip install -e .\n  python server.py")


if __name__ == "__main__":
    main()
