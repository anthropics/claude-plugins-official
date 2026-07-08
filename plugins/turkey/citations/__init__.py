"""Citation logic layer: formatting + risk classification.

Deliberately split into four narrow classes (statute formatting, case
formatting, risk classification, provenance vocabulary) rather than one
class -- Single Responsibility + Interface Segregation. providers/
citation_provider.py composes them (composition over inheritance) into
the single object that satisfies core's CitationProvider protocol.
"""
