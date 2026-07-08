"""Legal Source Registry: answers "what Turkish legal authorities exist
and how are they cited" -- never "how do I search them" (adapters/,
providers/) or "is this citation risky" (citations/). Single Responsibility.
"""
from __future__ import annotations

from pathlib import Path

from ..parser.yaml_parser import YamlFileParser
from ..paths import LEGAL_SOURCE_REGISTRY_PATH
from .models import CitationFormat, LegalSource


class TurkishLegalSourceRegistry:
    def __init__(
        self,
        path: Path = LEGAL_SOURCE_REGISTRY_PATH,
        parser: YamlFileParser | None = None,
    ):
        self._parser = parser or YamlFileParser()
        self._path = path
        self._sources: dict[str, LegalSource] | None = None

    def _load(self) -> dict[str, LegalSource]:
        if self._sources is None:
            raw = self._parser.parse(self._path)
            sources: dict[str, LegalSource] = {}
            for entry in raw.get("sources", []):
                cf_raw = entry.get("citation_format", {}) or {}
                source = LegalSource(
                    source_id=entry["source_id"],
                    name=entry.get("name", ""),
                    source_type=entry.get("source_type", ""),
                    citation_format=CitationFormat(
                        pattern_description=cf_raw.get("pattern_description", ""),
                        example=cf_raw.get("example", ""),
                    ),
                    primary_url_pattern=entry.get("primary_url_pattern", ""),
                    tier=entry.get("tier", "free"),
                    notes=entry.get("notes", ""),
                    hierarchy_level=entry.get("hierarchy_level", ""),
                )
                sources[source.source_id] = source
            self._sources = sources
        return self._sources

    def get(self, source_id: str) -> LegalSource | None:
        return self._load().get(source_id)

    def all(self) -> list[LegalSource]:
        return sorted(self._load().values(), key=lambda s: s.source_id)

    def by_type(self, source_type: str) -> list[LegalSource]:
        return [s for s in self.all() if s.source_type == source_type]
