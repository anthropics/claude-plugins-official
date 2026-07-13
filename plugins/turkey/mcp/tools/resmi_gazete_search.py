"""MCP tool for Resmî Gazete searches."""
from .source_search import SourceSearchTool


class ResmiGazeteSearchTool(SourceSearchTool):
    name = "turkey_resmi_gazete_search"
    description = "Resmî Gazete yayınlarında arama yapar."
    source_tool_name = "resmi_gazete.search"

