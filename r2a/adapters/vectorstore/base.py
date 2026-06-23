"""VectorStore ABC + namespace contract.

A namespace is a source-document id, stored as a filter column (not a separate
table) so retrieval can be scoped to a single import and so the LanceDB ↔
sqlite-vec swap stays mechanical.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from r2a.domain.bite import KnowledgeBite, ScoredBite
from r2a.domain.common import Vector


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, bites: list[KnowledgeBite]) -> None:
        """Insert/replace bites (each carries its embedding + namespace)."""

    @abstractmethod
    def search(
        self,
        query_vec: Vector,
        *,
        namespace: str | None,
        top_k: int,
        filters: dict | None = None,
    ) -> list[ScoredBite]:
        """Nearest bites. `namespace=None` searches across all imports."""

    @abstractmethod
    def delete_namespace(self, namespace: str) -> None:
        """Drop every bite for one source document."""

    @abstractmethod
    def namespaces(self) -> list[str]:
        """List known source-document ids."""
