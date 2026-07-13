"""Independent MCP tool for concise case summaries from supplied text."""
from __future__ import annotations

import re
from typing import Any

from .base import BaseMcpTool


class CaseSummaryTool(BaseMcpTool):
    name = "turkey_case_summary"
    description = "Karar metninin ilk geçiş özetini üretir; hukuki inceleme yerine geçmez."
    input_schema = {
        "type": "object",
        "properties": {"decision_text": {"type": "string"}, "max_sentences": {"type": "integer", "minimum": 1}},
        "required": ["decision_text"],
        "additionalProperties": False,
    }

    def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        sentences = re.split(r"(?<=[.!?])\s+", arguments["decision_text"].strip())
        return self.result({"summary": " ".join(sentences[: arguments.get("max_sentences", 3)]), "review_required": True})
