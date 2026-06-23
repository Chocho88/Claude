"""InMemoryStore — a dependency-free VectorStore for tests and the stub pipeline."""

from __future__ import annotations

import math

from r2a.domain.bite import KnowledgeBite, ScoredBite
from r2a.domain.common import Vector

from .base import VectorStore


def _cosine(a: Vector, b: Vector) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class InMemoryStore(VectorStore):
    def __init__(self) -> None:
        self._bites: dict[str, KnowledgeBite] = {}  # id -> bite

    def upsert(self, bites: list[KnowledgeBite]) -> None:
        for b in bites:
            self._bites[b.id] = b

    def search(
        self,
        query_vec: Vector,
        *,
        namespace: str | None,
        top_k: int,
        filters: dict | None = None,
    ) -> list[ScoredBite]:
        scored: list[ScoredBite] = []
        for b in self._bites.values():
            if namespace is not None and b.namespace != namespace:
                continue
            if b.embedding is None:
                continue
            scored.append(ScoredBite(bite=b, score=_cosine(query_vec, b.embedding)))
        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[:top_k]

    def delete_namespace(self, namespace: str) -> None:
        self._bites = {
            i: b for i, b in self._bites.items() if b.namespace != namespace
        }

    def namespaces(self) -> list[str]:
        return sorted({b.namespace for b in self._bites.values()})
