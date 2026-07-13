"""Implements core.engine.plugin_engine.contracts.DocumentProvider for
Turkey.

No live e-imza/UYAP MCP wiring exists yet (see
countries/tr/providers/document-provider.tr.md and countries/tr/
capabilities.yaml, which honestly marks getDocumentStatus not_supported
and getSignatureStatus/getFilingStatus partial). This implementation is
equally honest in code: it raises NotImplementedError for those three
methods rather than fabricating a status, and fully implements
get_irreversibility_flags (capabilities.yaml: full) using the documented,
static flags for known TR employment-legal actions."""
from __future__ import annotations

from core.engine.plugin_engine.contracts import (
    DocumentStatus,
    FilingStatus,
    IrreversibilityFlags,
    SignatureStatus,
)

_KNOWN_ACTIONS: dict[str, IrreversibilityFlags] = {
    "send-termination-letter": IrreversibilityFlags(
        irreversible=True,
        gate_required=True,
        reason="Fesih bildirimi tebliğ edildiğinde feshin geçerlilik süreci başlar (İş Kanunu m.19).",
    ),
    "send-offer-letter": IrreversibilityFlags(irreversible=False, gate_required=False),
    "sign-ibraname": IrreversibilityFlags(
        irreversible=True,
        gate_required=True,
        reason="İmzalandığında işçinin alacaklarından feragati yürürlüğe girer (TBK m.420).",
    ),
}

_DEFAULT_FLAGS = IrreversibilityFlags(
    irreversible=True,
    gate_required=True,
    reason="tanımsız eylem türü — güvenli varsayılan (bkz. document-provider.interface.md)",
)


class TurkishDocumentProvider:
    """Satisfies core.engine.plugin_engine.contracts.DocumentProvider."""

    def get_document_status(self, document_id: str) -> DocumentStatus:
        raise NotImplementedError(
            "no DMS/CLM binding wired for TR yet -- see countries/tr/capabilities.yaml"
        )

    def get_signature_status(self, envelope_id: str) -> SignatureStatus:
        raise NotImplementedError(
            "no e-imza MCP binding wired for TR yet -- see countries/tr/capabilities.yaml"
        )

    def get_filing_status(self, docket_id: str) -> FilingStatus:
        raise NotImplementedError(
            "no UYAP e-Dosya binding wired for TR yet -- see countries/tr/capabilities.yaml"
        )

    def get_irreversibility_flags(self, action_type: str) -> IrreversibilityFlags:
        return _KNOWN_ACTIONS.get(action_type, _DEFAULT_FLAGS)
