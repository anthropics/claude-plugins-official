"""Local retrieval layer over the knowledge/*.md corpus.

Deliberately NOT embedding/vector-based -- consistent with this repo's
retrieval model, where authoritative retrieval happens live via a Search
Provider/MCP connector; this layer only ranks the small, local,
pre-committed knowledge markdown files bundled with the country plugin.
"""
