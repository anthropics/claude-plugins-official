"""MCP tool for Mevzuat Bilgi Sistemi searches."""
from .source_search import SourceSearchTool


class MevzuatSearchTool(SourceSearchTool):
    name = "turkey_mevzuat_search"
    description = "Mevzuat Bilgi Sistemi içinde kanun, yönetmelik ve tebliğ arar."
    source_tool_name = "mevzuat.search"

