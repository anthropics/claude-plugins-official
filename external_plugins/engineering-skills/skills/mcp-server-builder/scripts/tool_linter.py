#!/usr/bin/env python3
"""Lint MCP tool definitions for naming conventions, description quality, and schema completeness.

Validates tool definitions against MCP best practices including snake_case naming,
description engineering quality, inputSchema completeness, and property documentation.

Usage:
    python tool_linter.py tools.json
    python tool_linter.py tools.json --strict --json
    python tool_linter.py server_config.json --path tools
"""

import argparse
import json
import re
import sys
from pathlib import Path

SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")
VERB_NOUN_RE = re.compile(r"^[a-z]+_[a-z]")
CAMEL_CASE_RE = re.compile(r"[a-z][A-Z]")

GOOD_VERBS = {
    "get", "list", "search", "create", "update", "delete", "run", "execute",
    "check", "validate", "send", "fetch", "query", "find", "set", "add",
    "remove", "start", "stop", "restart", "deploy", "build", "test",
    "analyze", "generate", "export", "import", "sync", "verify", "configure",
    "publish", "subscribe", "read", "write", "count", "compute", "transform",
}

BAD_NAME_PATTERNS = [
    (re.compile(r"^(handle|process|do|helper|util|misc|manager)"), "Name uses vague/implementation-detail verb"),
    (re.compile(r"^[a-z]+$"), "Single-word name lacks noun — unclear what is acted upon"),
    (re.compile(r"[A-Z]"), "Contains uppercase characters — must be snake_case"),
    (re.compile(r"-"), "Contains hyphens — use underscores for snake_case"),
]

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"
SEVERITY_INFO = "info"


def lint_name(tool: dict) -> list[dict]:
    """Lint the tool name for MCP conventions."""
    issues = []
    name = tool.get("name", "")

    if not name:
        issues.append({"rule": "name-required", "severity": SEVERITY_ERROR,
                        "message": "Tool is missing a 'name' field"})
        return issues

    if not SNAKE_CASE_RE.match(name):
        issues.append({"rule": "name-snake-case", "severity": SEVERITY_ERROR,
                        "message": f"Name '{name}' is not valid snake_case"})

    if CAMEL_CASE_RE.search(name):
        issues.append({"rule": "name-no-camel", "severity": SEVERITY_ERROR,
                        "message": f"Name '{name}' uses camelCase — convert to snake_case"})

    for pattern, msg in BAD_NAME_PATTERNS:
        if pattern.search(name):
            issues.append({"rule": "name-quality", "severity": SEVERITY_WARNING,
                            "message": f"Name '{name}': {msg}"})

    if not VERB_NOUN_RE.match(name):
        issues.append({"rule": "name-verb-noun", "severity": SEVERITY_WARNING,
                        "message": f"Name '{name}' should follow verb_noun pattern (e.g., search_documents)"})

    parts = name.split("_")
    if parts and parts[0] not in GOOD_VERBS:
        issues.append({"rule": "name-known-verb", "severity": SEVERITY_INFO,
                        "message": f"Name '{name}' starts with uncommon verb '{parts[0]}' — "
                                   f"consider standard verbs: get, list, search, create, update, delete, run"})

    if len(name) > 64:
        issues.append({"rule": "name-length", "severity": SEVERITY_WARNING,
                        "message": f"Name '{name}' is {len(name)} chars — keep under 64 for readability"})

    return issues


def lint_description(tool: dict) -> list[dict]:
    """Lint the tool description for LLM discoverability."""
    issues = []
    name = tool.get("name", "<unnamed>")
    desc = tool.get("description", "")

    if not desc:
        issues.append({"rule": "desc-required", "severity": SEVERITY_ERROR,
                        "message": f"Tool '{name}' is missing a description"})
        return issues

    if len(desc) < 30:
        issues.append({"rule": "desc-min-length", "severity": SEVERITY_ERROR,
                        "message": f"Tool '{name}' description is {len(desc)} chars — "
                                   f"minimum 30 for reliable LLM tool selection"})

    if len(desc) > 1024:
        issues.append({"rule": "desc-max-length", "severity": SEVERITY_WARNING,
                        "message": f"Tool '{name}' description is {len(desc)} chars — "
                                   f"consider keeping under 1024 to avoid token waste"})

    has_usage = any(phrase in desc.lower() for phrase in [
        "use when", "use for", "use this", "useful for", "use to",
        "helpful when", "call this", "invoke this",
    ])
    if not has_usage:
        issues.append({"rule": "desc-usage-guidance", "severity": SEVERITY_WARNING,
                        "message": f"Tool '{name}' description lacks usage guidance — "
                                   f"add 'Use when...' to help LLMs decide when to select it"})

    has_return = any(phrase in desc.lower() for phrase in [
        "returns", "outputs", "produces", "responds with", "result",
    ])
    if not has_return:
        issues.append({"rule": "desc-return-value", "severity": SEVERITY_INFO,
                        "message": f"Tool '{name}' description does not mention return value — "
                                   f"add 'Returns...' to set LLM expectations"})

    if not desc.rstrip().endswith("."):
        issues.append({"rule": "desc-punctuation", "severity": SEVERITY_INFO,
                        "message": f"Tool '{name}' description should end with a period"})

    vague_starts = ["a tool", "this tool", "tool for", "a powerful", "an advanced", "wrapper"]
    if any(desc.lower().startswith(v) for v in vague_starts):
        issues.append({"rule": "desc-no-fluff", "severity": SEVERITY_WARNING,
                        "message": f"Tool '{name}' description starts with vague phrasing — "
                                   f"lead with what it does, not marketing copy"})

    return issues


def lint_schema(tool: dict) -> list[dict]:
    """Lint the inputSchema for completeness."""
    issues = []
    name = tool.get("name", "<unnamed>")
    schema = tool.get("inputSchema", None)

    if schema is None:
        issues.append({"rule": "schema-required", "severity": SEVERITY_WARNING,
                        "message": f"Tool '{name}' has no inputSchema — "
                                   f"add one even if empty (type: object, properties: {{}})"})
        return issues

    if not isinstance(schema, dict):
        issues.append({"rule": "schema-type-check", "severity": SEVERITY_ERROR,
                        "message": f"Tool '{name}' inputSchema must be an object"})
        return issues

    if schema.get("type") != "object":
        issues.append({"rule": "schema-root-type", "severity": SEVERITY_ERROR,
                        "message": f"Tool '{name}' inputSchema.type must be 'object', "
                                   f"got '{schema.get('type', '<missing>')}'"})

    properties = schema.get("properties", {})
    required = schema.get("required", [])

    for req in required:
        if req not in properties:
            issues.append({"rule": "schema-required-exists", "severity": SEVERITY_ERROR,
                            "message": f"Tool '{name}' lists '{req}' as required "
                                       f"but it is not in properties"})

    for prop_name, prop_def in properties.items():
        if not isinstance(prop_def, dict):
            issues.append({"rule": "schema-prop-object", "severity": SEVERITY_ERROR,
                            "message": f"Tool '{name}' property '{prop_name}' must be an object"})
            continue

        if "description" not in prop_def or not prop_def["description"]:
            issues.append({"rule": "schema-prop-description", "severity": SEVERITY_ERROR,
                            "message": f"Tool '{name}' property '{prop_name}' is missing a description"})

        if "type" not in prop_def and "enum" not in prop_def and "$ref" not in prop_def:
            issues.append({"rule": "schema-prop-type", "severity": SEVERITY_WARNING,
                            "message": f"Tool '{name}' property '{prop_name}' has no type specified"})

        if prop_def.get("type") == "string" and "enum" not in prop_def and \
           "description" in prop_def and len(prop_def["description"]) < 10:
            issues.append({"rule": "schema-prop-desc-quality", "severity": SEVERITY_INFO,
                            "message": f"Tool '{name}' property '{prop_name}' has a very short "
                                       f"description — add examples or constraints"})

    if len(properties) > 15:
        issues.append({"rule": "schema-prop-count", "severity": SEVERITY_WARNING,
                        "message": f"Tool '{name}' has {len(properties)} properties — "
                                   f"consider splitting into multiple tools (one intent per tool)"})

    return issues


def lint_tool(tool: dict) -> list[dict]:
    """Run all lint rules against a single tool definition."""
    issues = []
    issues.extend(lint_name(tool))
    issues.extend(lint_description(tool))
    issues.extend(lint_schema(tool))
    return issues


def load_tools(file_path: str, json_path: str | None) -> list[dict]:
    """Load tool definitions from a JSON file, optionally at a nested path."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if json_path:
        for key in json_path.split("."):
            if isinstance(data, dict) and key in data:
                data = data[key]
            elif isinstance(data, list):
                try:
                    data = data[int(key)]
                except (ValueError, IndexError):
                    raise ValueError(f"Cannot traverse path '{json_path}' — "
                                     f"key '{key}' not found in array")
            else:
                raise ValueError(f"Cannot traverse path '{json_path}' — "
                                 f"key '{key}' not found")

    if isinstance(data, dict) and "name" in data:
        return [data]
    if isinstance(data, list):
        return data
    raise ValueError(f"Expected a tool object or array of tools, got {type(data).__name__}")


def main():
    parser = argparse.ArgumentParser(
        description="Lint MCP tool definitions for naming, description quality, and schema completeness.",
        epilog="Example: %(prog)s tools.json --strict",
    )
    parser.add_argument("file", help="JSON file containing MCP tool definitions")
    parser.add_argument(
        "--path", default=None,
        help="Dot-separated path to tools array within the JSON (e.g., 'tools' or 'server.tools')",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Treat warnings as errors (exit code 1 if any warnings found)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output results as JSON instead of human-readable text",
    )
    args = parser.parse_args()

    try:
        tools = load_tools(args.file, args.path)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        if args.json:
            json.dump({"error": str(e)}, sys.stdout, indent=2)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    all_results = []
    total_errors = 0
    total_warnings = 0
    total_info = 0

    for tool in tools:
        issues = lint_tool(tool)
        tool_name = tool.get("name", "<unnamed>")
        errors = [i for i in issues if i["severity"] == SEVERITY_ERROR]
        warnings = [i for i in issues if i["severity"] == SEVERITY_WARNING]
        infos = [i for i in issues if i["severity"] == SEVERITY_INFO]
        total_errors += len(errors)
        total_warnings += len(warnings)
        total_info += len(infos)

        all_results.append({
            "tool": tool_name,
            "issues": issues,
            "counts": {"errors": len(errors), "warnings": len(warnings), "info": len(infos)},
            "passed": len(errors) == 0 and (not args.strict or len(warnings) == 0),
        })

    output = {
        "tools_checked": len(tools),
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "total_info": total_info,
        "all_passed": total_errors == 0 and (not args.strict or total_warnings == 0),
        "results": all_results,
    }

    if args.json:
        json.dump(output, sys.stdout, indent=2)
        print()
    else:
        for result in all_results:
            status = "PASS" if result["passed"] else "FAIL"
            print(f"\n[{status}] {result['tool']}")
            if not result["issues"]:
                print("  No issues found.")
            for issue in result["issues"]:
                sev = issue["severity"].upper()
                prefix = {"ERROR": "E", "WARNING": "W", "INFO": "I"}.get(sev, "?")
                print(f"  {prefix} [{issue['rule']}] {issue['message']}")

        print(f"\n{'=' * 60}")
        print(f"Tools checked: {len(tools)}")
        print(f"Errors: {total_errors}  Warnings: {total_warnings}  Info: {total_info}")
        if output["all_passed"]:
            print("Result: ALL PASSED")
        else:
            print("Result: ISSUES FOUND")

    sys.exit(0 if output["all_passed"] else 1)


if __name__ == "__main__":
    main()
