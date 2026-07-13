"""Provenance tag vocabulary: which [Tag] markers Turkey's Citation
Provider is allowed to use, sourced from the Legal Source Registry
(Dependency Inversion -- depends on the registry's public interface, not
its file format)."""
from __future__ import annotations

from core.engine.plugin_engine.contracts import ProvenanceTag

from ..sources.legal_source_registry import TurkishLegalSourceRegistry

_SOURCE_ID_TO_TAG = {
    "yargitay": "[Yargıtay]",
    "resmi-gazete": "[Resmi Gazete]",
    "mevzuat-bilgi-sistemi": "[mevzuat.gov.tr]",
}


class TurkishProvenanceTagVocabulary:
    def __init__(self, registry: TurkishLegalSourceRegistry | None = None):
        self._registry = registry or TurkishLegalSourceRegistry()

    def get(self) -> list[ProvenanceTag]:
        tags: list[ProvenanceTag] = []
        for source in self._registry.all():
            tag = _SOURCE_ID_TO_TAG.get(source.source_id)
            if tag:
                tags.append(
                    ProvenanceTag(
                        tag=tag, source_description=source.name, requires_live_tool_result=True
                    )
                )
        return tags
