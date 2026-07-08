"""Composes the citations/ layer's focused classes into the single
TurkishCitationProvider that satisfies
core.engine.plugin_engine.contracts.CitationProvider.

Composition over inheritance: each of the four responsibilities (statute
formatting, case formatting, risk classification, provenance vocabulary)
is its own small class, injected here rather than re-implemented (Single
Responsibility + Dependency Inversion). See
countries/tr/providers/citation-provider.tr.md for the design this
class codifies in code.
"""
from __future__ import annotations

from core.engine.plugin_engine.contracts import PinpointPattern, ProvenanceTag, RiskAssessment

from ..citations.case_formatter import TurkishCaseCitationFormatter
from ..citations.provenance import TurkishProvenanceTagVocabulary
from ..citations.risk_classifier import TurkishCitationRiskClassifier
from ..citations.statute_formatter import TurkishStatuteCitationFormatter


class TurkishCitationProvider:
    """Satisfies core.engine.plugin_engine.contracts.CitationProvider."""

    def __init__(
        self,
        statute_formatter: TurkishStatuteCitationFormatter | None = None,
        case_formatter: TurkishCaseCitationFormatter | None = None,
        risk_classifier: TurkishCitationRiskClassifier | None = None,
        provenance: TurkishProvenanceTagVocabulary | None = None,
    ):
        self._statute_formatter = statute_formatter or TurkishStatuteCitationFormatter()
        self._case_formatter = case_formatter or TurkishCaseCitationFormatter()
        self._risk_classifier = risk_classifier or TurkishCitationRiskClassifier()
        self._provenance = provenance or TurkishProvenanceTagVocabulary()

    def format_statute_citation(
        self, instrument: str, section: str, subsection: str | None = None
    ) -> str:
        return self._statute_formatter.format(instrument, section, subsection)

    def format_case_citation(self, **fields: object) -> str:
        return self._case_formatter.format(**fields)

    def get_provenance_tag_vocabulary(self) -> list[ProvenanceTag]:
        return self._provenance.get()

    def get_high_risk_pinpoint_patterns(self) -> list[PinpointPattern]:
        return self._risk_classifier.get_high_risk_pinpoint_patterns()

    def classify_citation_risk(self, citation_text: str) -> RiskAssessment:
        return self._risk_classifier.classify(citation_text)
