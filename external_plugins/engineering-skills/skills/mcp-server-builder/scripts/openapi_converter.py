#!/usr/bin/env python3
"""Convert OpenAPI/Swagger specs into MCP tool definitions.

Reads an OpenAPI 3.x or Swagger 2.0 JSON/YAML-style JSON spec and generates
MCP-compatible tool definitions with proper naming, descriptions, and schemas.

Usage:
    python openapi_converter.py openapi.json --output tools.json
    python openapi_converter.py openapi.json --filter "GET,POST" --json
    python openapi_converter.py swagger.json --prefix api --exclude "/internal/*"
"""

import argparse
import json
import re
import sys
from pathlib import Path
from fnmatch import fnmatch


def load_spec(spec_path: str) -> dict:
    """Load and validate an OpenAPI/Swagger spec."""
    path = Path(spec_path)
    if not path.exists():
        raise FileNotFoundError(f"Spec file not found: {spec_path}")
    with open(path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    if "openapi" not in spec and "swagger" not in spec:
        raise ValueError("File does not appear to be an OpenAPI 3.x or Swagger 2.0 spec "
                         "(missing 'openapi' or 'swagger' key)")
    return spec


def resolve_ref(spec: dict, ref: str) -> dict:
    """Resolve a simple $ref pointer within the spec (single-level)."""
    if not ref.startswith("#/"):
        return {}
    parts = ref[2:].split("/")
    current = spec
    for part in parts:
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return {}
    return current if isinstance(current, dict) else {}


def resolve_schema(spec: dict, schema: dict) -> dict:
    """Resolve a schema object, following $ref if present."""
    if not isinstance(schema, dict):
        return {}
    if "$ref" in schema:
        return resolve_ref(spec, schema["$ref"])
    return schema


def sanitize_name(raw: str) -> str:
    """Convert an operationId or path into a valid snake_case MCP tool name."""
    # Remove common prefixes/suffixes
    name = raw.strip("/").replace("-", "_").replace(".", "_")
    # Convert camelCase to snake_case
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    name = name.lower()
    # Replace path separators with underscores
    name = re.sub(r"[/{}\s]+", "_", name)
    # Remove non-alphanumeric except underscores
    name = re.sub(r"[^a-z0-9_]", "", name)
    # Collapse multiple underscores
    name = re.sub(r"_+", "_", name).strip("_")
    return name


def build_method_prefix(method: str) -> str:
    """Map HTTP method to a verb prefix for tool names."""
    return {
        "get": "get",
        "post": "create",
        "put": "update",
        "patch": "patch",
        "delete": "delete",
        "head": "check",
        "options": "describe",
    }.get(method.lower(), method.lower())


def convert_schema_property(spec: dict, prop_schema: dict) -> dict:
    """Convert an OpenAPI schema property to an MCP-compatible property."""
    prop_schema = resolve_schema(spec, prop_schema)
    result = {}

    prop_type = prop_schema.get("type", "string")
    if prop_type == "integer":
        result["type"] = "number"
    elif prop_type == "array":
        result["type"] = "array"
        items = prop_schema.get("items", {})
        items = resolve_schema(spec, items)
        if items:
            result["items"] = {"type": items.get("type", "string")}
    elif prop_type == "object":
        result["type"] = "object"
    else:
        result["type"] = prop_type

    if "enum" in prop_schema:
        result["enum"] = prop_schema["enum"]
    if "default" in prop_schema:
        result["default"] = prop_schema["default"]
    if "description" in prop_schema:
        result["description"] = prop_schema["description"]
    elif "title" in prop_schema:
        result["description"] = prop_schema["title"]
    if "minimum" in prop_schema:
        result["minimum"] = prop_schema["minimum"]
    if "maximum" in prop_schema:
        result["maximum"] = prop_schema["maximum"]
    if "pattern" in prop_schema:
        result["pattern"] = prop_schema["pattern"]
    if "format" in prop_schema:
        result["description"] = result.get("description", "") + f" (format: {prop_schema['format']})"
        result["description"] = result["description"].strip()

    return result


def convert_operation(spec: dict, path: str, method: str, operation: dict,
                      prefix: str | None = None) -> dict:
    """Convert a single OpenAPI operation to an MCP tool definition."""
    # Derive tool name
    operation_id = operation.get("operationId")
    if operation_id:
        name = sanitize_name(operation_id)
    else:
        verb = build_method_prefix(method)
        path_name = sanitize_name(path)
        name = f"{verb}_{path_name}"

    if prefix:
        name = f"{prefix}_{name}"

    # Build description
    summary = operation.get("summary", "").strip()
    description = operation.get("description", "").strip()
    if summary and description:
        tool_desc = f"{summary}. {description}"
    elif summary:
        tool_desc = summary
    elif description:
        tool_desc = description
    else:
        tool_desc = f"{method.upper()} {path}"

    # Ensure it ends with a period
    tool_desc = tool_desc.rstrip(".")
    tool_desc += "."

    # Build inputSchema properties
    properties = {}
    required = []

    # Path and query parameters
    params = operation.get("parameters", [])
    for param in params:
        param = resolve_schema(spec, param)
        param_name = param.get("name", "")
        if not param_name:
            continue

        param_schema = param.get("schema", {})
        param_schema = resolve_schema(spec, param_schema)

        prop = convert_schema_property(spec, param_schema)
        if "description" not in prop and param.get("description"):
            prop["description"] = param["description"]
        if "description" not in prop:
            prop["description"] = f"{param.get('in', 'query')} parameter: {param_name}"

        properties[param_name] = prop
        if param.get("required", False):
            required.append(param_name)

    # Request body (OpenAPI 3.x)
    request_body = operation.get("requestBody", {})
    if request_body:
        request_body = resolve_schema(spec, request_body)
        content = request_body.get("content", {})
        json_content = content.get("application/json", {})
        body_schema = json_content.get("schema", {})
        body_schema = resolve_schema(spec, body_schema)

        if body_schema.get("properties"):
            for prop_name, prop_def in body_schema["properties"].items():
                properties[prop_name] = convert_schema_property(spec, prop_def)
                if "description" not in properties[prop_name]:
                    properties[prop_name]["description"] = f"Request body field: {prop_name}"
            required.extend(body_schema.get("required", []))

        elif body_schema.get("type") and not body_schema.get("properties"):
            properties["body"] = convert_schema_property(spec, body_schema)
            if "description" not in properties["body"]:
                properties["body"]["description"] = "Request body content"
            if request_body.get("required", False):
                required.append("body")

    # Swagger 2.0 body parameter
    body_params = [p for p in params if p.get("in") == "body"]
    for bp in body_params:
        bp_schema = bp.get("schema", {})
        bp_schema = resolve_schema(spec, bp_schema)
        if bp_schema.get("properties"):
            for prop_name, prop_def in bp_schema["properties"].items():
                properties[prop_name] = convert_schema_property(spec, prop_def)
                if "description" not in properties[prop_name]:
                    properties[prop_name]["description"] = f"Request body field: {prop_name}"
            required.extend(bp_schema.get("required", []))

    # Deduplicate required
    required = list(dict.fromkeys(required))

    tool = {
        "name": name,
        "description": tool_desc,
        "inputSchema": {
            "type": "object",
            "properties": properties,
        },
    }
    if required:
        tool["inputSchema"]["required"] = required

    # Attach source metadata
    tool["_source"] = {
        "path": path,
        "method": method.upper(),
        "operationId": operation.get("operationId"),
    }

    return tool


def convert_spec(spec: dict, prefix: str | None = None,
                 methods_filter: set | None = None,
                 exclude_patterns: list[str] | None = None) -> list[dict]:
    """Convert all operations in an OpenAPI spec to MCP tool definitions."""
    tools = []
    paths = spec.get("paths", {})

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        # Check exclusions
        if exclude_patterns:
            if any(fnmatch(path, pat) for pat in exclude_patterns):
                continue

        for method in ["get", "post", "put", "patch", "delete", "head", "options"]:
            if method not in path_item:
                continue
            if methods_filter and method.upper() not in methods_filter:
                continue

            operation = path_item[method]
            if not isinstance(operation, dict):
                continue

            # Skip deprecated operations
            if operation.get("deprecated", False):
                continue

            tool = convert_operation(spec, path, method, operation, prefix)
            tools.append(tool)

    return tools


def main():
    parser = argparse.ArgumentParser(
        description="Convert OpenAPI/Swagger specs into MCP tool definitions.",
        epilog="Example: %(prog)s openapi.json --output mcp-tools.json",
    )
    parser.add_argument("spec", help="Path to OpenAPI 3.x or Swagger 2.0 JSON spec file")
    parser.add_argument(
        "--output", "-o", default=None,
        help="Output file for MCP tool definitions (default: stdout)",
    )
    parser.add_argument(
        "--prefix", default=None,
        help="Prefix to add to all tool names (e.g., 'github' -> 'github_list_repos')",
    )
    parser.add_argument(
        "--filter", default=None,
        help="Comma-separated HTTP methods to include (e.g., 'GET,POST')",
    )
    parser.add_argument(
        "--exclude", action="append", default=[],
        help="Glob pattern for paths to exclude (e.g., '/internal/*'). Can be repeated.",
    )
    parser.add_argument(
        "--no-source", action="store_true",
        help="Omit _source metadata from output",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output results as JSON with metadata (default for stdout is human-readable)",
    )
    args = parser.parse_args()

    try:
        spec = load_spec(args.spec)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        if args.json:
            json.dump({"error": str(e)}, sys.stdout, indent=2)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    methods_filter = None
    if args.filter:
        methods_filter = {m.strip().upper() for m in args.filter.split(",")}

    tools = convert_spec(spec, prefix=args.prefix, methods_filter=methods_filter,
                         exclude_patterns=args.exclude or None)

    if args.no_source:
        for tool in tools:
            tool.pop("_source", None)

    # Detect spec info
    spec_title = spec.get("info", {}).get("title", "Unknown API")
    spec_version = spec.get("info", {}).get("version", "unknown")
    total_paths = len(spec.get("paths", {}))

    result = {
        "source": {
            "title": spec_title,
            "version": spec_version,
            "total_paths": total_paths,
        },
        "conversion": {
            "tools_generated": len(tools),
            "methods_filter": list(methods_filter) if methods_filter else None,
            "exclude_patterns": args.exclude or None,
            "prefix": args.prefix,
        },
        "tools": tools,
    }

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
            f.write("\n")
        if args.json:
            summary = {k: v for k, v in result.items() if k != "tools"}
            summary["output_file"] = str(out_path.resolve())
            json.dump(summary, sys.stdout, indent=2)
            print()
        else:
            print(f"Converted: {spec_title} v{spec_version}")
            print(f"Paths in spec: {total_paths}")
            print(f"Tools generated: {len(tools)}")
            print(f"Output: {out_path.resolve()}")
            if tools:
                print(f"\nTools:")
                for t in tools:
                    src = t.get("_source", {})
                    method = src.get("method", "?")
                    path = src.get("path", "?")
                    props = len(t.get("inputSchema", {}).get("properties", {}))
                    print(f"  {t['name']:40s} {method:6s} {path:30s} ({props} params)")
    else:
        if args.json:
            json.dump(result, sys.stdout, indent=2)
            print()
        else:
            print(f"# {spec_title} v{spec_version}")
            print(f"# {total_paths} paths -> {len(tools)} MCP tools\n")
            for i, tool in enumerate(tools):
                src = tool.get("_source", {})
                print(f"## Tool {i + 1}: {tool['name']}")
                print(f"   Source: {src.get('method', '?')} {src.get('path', '?')}")
                print(f"   Description: {tool['description']}")
                schema = tool.get("inputSchema", {})
                props = schema.get("properties", {})
                req = schema.get("required", [])
                if props:
                    print(f"   Parameters ({len(props)}):")
                    for pname, pdef in props.items():
                        req_mark = "*" if pname in req else " "
                        ptype = pdef.get("type", "?")
                        pdesc = pdef.get("description", "")[:60]
                        print(f"     {req_mark} {pname}: {ptype} — {pdesc}")
                else:
                    print(f"   Parameters: none")
                print()


if __name__ == "__main__":
    main()
