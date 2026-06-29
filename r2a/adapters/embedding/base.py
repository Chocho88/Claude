"""Embedder ABC.

`embed` (documents) and `embed_query` (queries) are kept distinct because
asymmetric models like bge expect a query prefix; collapsing them silently
degrades retrieval.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from r2a.domain.common import Vector


class Embedder(ABC):
    #: Vector dimensionality.
    dim: int = 0
    #: Identifier of the underlying model (recorded for reproducibility).
    model_id: str = "abstract"

    @abstractmethod
    def embed(self, texts: list[str]) -> list[Vector]:
        """Embed documents/bites (batched)."""

    @abstractmethod
    def embed_query(self, text: str) -> Vector:
        """Embed a single query (may apply a query-side prefix)."""
