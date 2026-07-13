"""Shared, country-agnostic Provider/Tool/Adapter/Retriever/Workflow
contracts every country plugin implements.

These are the Python-code counterparts of the markdown interface
specifications in core/engine/providers/*.interface.md. This module adds
no new concept -- it gives those concepts a `typing.Protocol` so a
concrete country plugin (e.g. plugins/turkey/) has something real to
implement against, and so callers depend on the abstraction (Dependency
Inversion Principle) instead of a concrete country's classes.

Zero country-specific content lives here -- see core/README.md's design
rule: if a file under core/ names a country, a statute, or a court, that
is a design error. This module only names *shapes*.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from .loader import PluginEngine


# --- Citation Provider -------------------------------------------------------

class RiskTier(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class ProvenanceTag:
    tag: str
    source_description: str
    requires_live_tool_result: bool


@dataclass(frozen=True)
class PinpointPattern:
    pattern_name: str
    description: str
    example: str


@dataclass(frozen=True)
class RiskAssessment:
    tier: RiskTier
    reason: str


@runtime_checkable
class CitationProvider(Protocol):
    """Python counterpart of core/engine/providers/citation-provider.interface.md."""

    def format_statute_citation(
        self, instrument: str, section: str, subsection: str | None = None
    ) -> str: ...

    def format_case_citation(self, **fields: Any) -> str: ...

    def get_provenance_tag_vocabulary(self) -> list[ProvenanceTag]: ...

    def get_high_risk_pinpoint_patterns(self) -> list[PinpointPattern]: ...

    def classify_citation_risk(self, citation_text: str) -> RiskAssessment: ...


# --- Search Provider ----------------------------------------------------------

@dataclass(frozen=True)
class SearchRequest:
    query: str
    jurisdiction_scope: str | None = None
    source_type: str | None = None


@dataclass(frozen=True)
class SearchResult:
    title: str
    citation_raw: str
    source_id: str
    retrieved_at: str
    url: str | None = None
    snippet: str | None = None


@dataclass(frozen=True)
class PreflightResult:
    available: bool
    source_id: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class SourceDescriptor:
    source_id: str
    tier: str  # "free" | "paid"
    coverage: str


@runtime_checkable
class SearchProvider(Protocol):
    """Python counterpart of core/engine/providers/search-provider.interface.md."""

    def search(self, request: SearchRequest) -> list[SearchResult]: ...

    def preflight_check(self) -> PreflightResult: ...

    def get_source_catalog(self) -> list[SourceDescriptor]: ...


# --- Document Provider ----------------------------------------------------------

class DocumentStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in-review"
    FINAL = "final"
    ARCHIVED = "archived"


class SignatureStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PARTIALLY_SIGNED = "partially_signed"
    EXECUTED = "executed"
    VOIDED = "voided"


class FilingStatus(str, Enum):
    NOT_FILED = "not_filed"
    FILED = "filed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass(frozen=True)
class IrreversibilityFlags:
    irreversible: bool
    gate_required: bool
    reason: str | None = None


@runtime_checkable
class DocumentProvider(Protocol):
    """Python counterpart of core/engine/providers/document-provider.interface.md."""

    def get_document_status(self, document_id: str) -> DocumentStatus: ...

    def get_signature_status(self, envelope_id: str) -> SignatureStatus: ...

    def get_filing_status(self, docket_id: str) -> FilingStatus: ...

    def get_irreversibility_flags(self, action_type: str) -> IrreversibilityFlags: ...


# --- Generic cross-cutting contracts (Tool / Adapter / Retriever / Prompt / Workflow) ---

@runtime_checkable
class Tool(Protocol):
    """A named, callable unit a workflow can invoke -- the code
    counterpart of a Tool Registry capability_id binding."""

    name: str

    def run(self, **kwargs: Any) -> Any: ...


@runtime_checkable
class Adapter(Protocol):
    """A boundary object wrapping exactly one external system.
    `is_available()` must never assume connectivity -- see the
    'degrades gracefully' rule in CONNECTORS.md."""

    def is_available(self) -> bool: ...


@dataclass(frozen=True)
class RetrievedChunk:
    source_path: str
    heading: str
    text: str
    score: float


@runtime_checkable
class Retriever(Protocol):
    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedChunk]: ...


@runtime_checkable
class PromptAssembler(Protocol):
    def assemble(self, topic: str, context: dict[str, Any]) -> str: ...


@dataclass
class WorkflowResult:
    topic: str
    body: str
    citations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@runtime_checkable
class WorkflowStep(Protocol):
    def execute(self, **kwargs: Any) -> WorkflowResult: ...


@runtime_checkable
class PluginRegistrar(Protocol):
    """Implemented by each country/vertical plugin's own registration
    module; called once to register that plugin's concrete providers,
    tools, and prompts into the engine's shared registries."""

    def register(self, engine: "PluginEngine") -> None: ...
