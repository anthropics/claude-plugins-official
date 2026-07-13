"""MCP tool for Yargıtay decision searches."""
from .source_search import SourceSearchTool


class YargitaySearchTool(SourceSearchTool):
    name = "turkey_yargitay_search"
    description = "Yargıtay kararlarında arama yapar."
    source_tool_name = "yargitay.search"

