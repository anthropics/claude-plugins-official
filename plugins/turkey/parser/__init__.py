"""Parser layer: turns a file on disk into an in-memory Python value.

Interface Segregation: a parser only parses. It never fetches (that's
adapters/), validates against a schema (that's core/engine's validation.py),
or interprets domain meaning (that's sources/, config/, citations/).
"""
