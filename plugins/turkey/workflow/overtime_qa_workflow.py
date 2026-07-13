"""Top-level orchestration for an overtime ("fazla mesai") question -- the
composition root that wires SearchProvider, CitationProvider, and a
PromptAssembler together.

Depends only on core's contracts (Dependency Inversion Principle): swap
any component for a test double without changing this class. This mirrors
what employment-legal/skills/wage-hour-qa/SKILL.md's Step 2a describes in
prose -- this class is the executable equivalent for Turkey.
"""
from __future__ import annotations

from core.engine.plugin_engine.contracts import (
    CitationProvider,
    PromptAssembler,
    SearchProvider,
    WorkflowResult,
)


class OvertimeQaWorkflow:
    """Satisfies core.engine.plugin_engine.contracts.WorkflowStep."""

    def __init__(
        self,
        search_provider: SearchProvider,
        citation_provider: CitationProvider,
        prompt_assembler: PromptAssembler,
    ):
        self._search_provider = search_provider
        self._citation_provider = citation_provider
        self._prompt_assembler = prompt_assembler

    def execute(self, question: str = "") -> WorkflowResult:
        warnings: list[str] = []

        preflight = self._search_provider.preflight_check()
        if not preflight.available:
            warnings.append(f"search provider not connected: {preflight.reason}")

        body = self._prompt_assembler.assemble("Fazla Mesai", {"question": question})

        citation = "4857 sayılı İş Kanunu m.41"
        risk = self._citation_provider.classify_citation_risk(citation)
        warnings.append(f"citation risk: {risk.tier.value} — {risk.reason}")

        return WorkflowResult(
            topic="overtime-qa",
            body=body,
            citations=[citation],
            warnings=warnings,
        )
