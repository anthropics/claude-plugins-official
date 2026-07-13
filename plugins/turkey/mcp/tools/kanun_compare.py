"""Independent MCP tool for comparing two legal texts."""
from __future__ import annotations

import re
from typing import Any

from .base import BaseMcpTool


class KanunCompareTool(BaseMcpTool):
    name = "turkey_kanun_compare"
    description = "İki kanun veya madde metni arasındaki ortak ve farklı ifadeleri çıkarır."
    input_schema = {
        "type": "object",
        "properties": {"left_text": {"type": "string"}, "right_text": {"type": "string"}},
        "required": ["left_text", "right_text"],
        "additionalProperties": False,
    }

    def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        tokens = lambda text: set(re.findall(r"\w+", text.lower(), re.UNICODE))
        left, right = tokens(arguments["left_text"]), tokens(arguments["right_text"])
        return self.result(
            {
                "common_terms": sorted(left & right),
                "only_left": sorted(left - right),
                "only_right": sorted(right - left),
            }
        )

