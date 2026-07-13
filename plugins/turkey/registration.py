"""Plugin Registration: wires plugins/turkey's concrete implementations
into core.engine.plugin_engine's shared registries.

Implements core.engine.plugin_engine.contracts.PluginRegistrar. The engine
(or a bootstrap script) calls `TurkeyPluginRegistrar().register(engine)`
once, after `engine.load_all()` has already registered countries/tr's
markdown-driven manifest. Nothing in core/ imports this module directly
(Open/Closed Principle): adding Germany later means adding
plugins/germany/registration.py, never editing this file or the engine.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from .config.country_config import TurkeyCountryConfig, load_country_config
from .manifest import PLUGIN_MANIFEST, TurkeyPluginManifest
from .prompts.overtime_prompt_assembler import OvertimePromptAssembler
from .providers.citation_provider import TurkishCitationProvider
from .providers.document_provider import TurkishDocumentProvider
from .providers.legal_sources.registry import discover_legal_source_providers
from .providers.search_provider import TurkishSearchProvider
from .rag.keyword_retriever import KeywordKnowledgeRetriever
from .tools.business_day_calculator_tool import BusinessDayCalculatorTool
from .tools.case_law_search_tool import CaseLawSearchTool
from .tools.citation_formatting_tool import CitationFormattingTool
from .workflow.overtime_qa_workflow import OvertimeQaWorkflow

if TYPE_CHECKING:
    from core.engine.plugin_engine.loader import PluginEngine

_PROVIDER_TYPES = ("citation_provider", "search_provider", "document_provider")


class TurkeyPluginRegistrar:
    """Satisfies core.engine.plugin_engine.contracts.PluginRegistrar.

    Construction wires every layer together once (the composition root);
    `register()` only publishes the already-built objects into the
    engine's registries -- it does not construct anything itself, so a
    caller that only wants the objects (e.g. for a workflow, without an
    engine) can use the public attributes directly.
    """

    country_code = "TR"

    def __init__(self, country_config: TurkeyCountryConfig | None = None):
        self.manifest: TurkeyPluginManifest = PLUGIN_MANIFEST
        self.country_config = country_config or load_country_config()

        self.citation_provider = TurkishCitationProvider()
        self.search_provider = TurkishSearchProvider(adapters=discover_legal_source_providers())
        self.document_provider = TurkishDocumentProvider()

        self.retriever = KeywordKnowledgeRetriever()
        self.prompt_assembler = OvertimePromptAssembler(self.retriever, self.citation_provider)

        self.tools = [
            CaseLawSearchTool(self.search_provider),
            CitationFormattingTool(self.citation_provider),
            BusinessDayCalculatorTool(self.country_config),
        ]

        self.overtime_workflow = OvertimeQaWorkflow(
            search_provider=self.search_provider,
            citation_provider=self.citation_provider,
            prompt_assembler=self.prompt_assembler,
        )

    def _providers(self) -> dict[str, object]:
        return {
            "citation_provider": self.citation_provider,
            "search_provider": self.search_provider,
            "document_provider": self.document_provider,
        }

    def register(self, engine: "PluginEngine") -> None:
        """Attach this plugin's executable Provider objects to the
        bindings the engine already registered from
        countries/tr/country.config.yaml's `default_providers` block.

        Requires `engine.load_all()` to have run first (so a binding
        exists to attach to) -- raises via ProviderRegistry.attach_instance
        otherwise, which is the correct failure: registering executable
        code for a country the engine doesn't know about is a bug, not a
        silently-ignorable edge case.
        """
        for provider_type, instance in self._providers().items():
            engine.providers.attach_instance(provider_type, self.country_code, instance)
