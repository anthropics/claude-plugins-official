"""Convention-based discovery: one tool module is one independently added MCP tool."""
from __future__ import annotations

from importlib import import_module
from inspect import getmembers, isclass
from pkgutil import iter_modules

from ..client import McpClient
from .base import BaseMcpTool, McpTool


def discover_mcp_tools(client: McpClient) -> list[McpTool]:
    package = import_module(__package__)
    tools: list[McpTool] = []
    for module_info in sorted(iter_modules(package.__path__), key=lambda item: item.name):
        if module_info.name in {"base", "registry", "source_search"} or module_info.name.startswith("_"):
            continue
        module = import_module(f"{__package__}.{module_info.name}")
        for _, candidate in getmembers(module, isclass):
            if (
                candidate.__module__ == module.__name__
                and candidate is not BaseMcpTool
                and issubclass(candidate, BaseMcpTool)
            ):
                try:
                    tools.append(candidate(client))
                except TypeError:
                    tools.append(candidate())
    return tools
