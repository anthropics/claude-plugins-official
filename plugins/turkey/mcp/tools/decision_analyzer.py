"""Independent MCP tool for transparent first-pass decision analysis."""
from __future__ import annotations

import re
from typing import Any

from .base import BaseMcpTool


class DecisionAnalyzerTool(BaseMcpTool):
    name = "turkey_decision_analyzer"
    description = "Mahkeme kararından karar sonucu ve madde referanslarını ilk geçişte çıkarır."
    input_schema = {
        "type": "object",
        "properties": {"decision_text": {"type": "string"}},
        "required": ["decision_text"],
        "additionalProperties": False,
    }

    def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        text = arguments["decision_text"]
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        outcomes = [sentence for sentence in sentences if re.search(r"kabul|ret|bozma|onama", sentence, re.I)]
        articles = re.findall(r"(?:m\.|madde)\s*\d+(?:/\d+)?", text, re.I)
        return self.result({"outcome_sentences": outcomes, "article_references": articles, "review_required": True})

