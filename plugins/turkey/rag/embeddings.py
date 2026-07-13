"""Replaceable embedding contract with a dependency-free default."""
from __future__ import annotations

import hashlib
import re
from typing import Protocol, runtime_checkable

_TOKEN_RE = re.compile(r"[\wçğıöşüÇĞİÖŞÜ]+", re.UNICODE)


@runtime_checkable
class EmbeddingProvider(Protocol):
    dimensions: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class HashEmbeddingProvider:
    """Deterministic local embedding suitable for development and tests.

    Production deployments may replace this with a model-backed provider
    without changing document parsing, chunking, or vector-store code.
    """

    def __init__(self, dimensions: int = 256):
        self.dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vector = [0.0] * self.dimensions
            for token in _TOKEN_RE.findall(text.lower()):
                index = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16) % self.dimensions
                vector[index] += 1.0
            vectors.append(vector)
        return vectors
