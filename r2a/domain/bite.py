"""Knowledge bites — the atomic units extracted from source content."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from .common import Vector, utcnow


class BiteType(str, Enum):
    """An atomic unit of knowledge — not a fixed-size chunk."""

    CLAIM = "claim"
    DEFINITION = "definition"
    STATISTIC = "statistic"
    EXAMPLE = "example"


class KnowledgeBite(BaseModel):
    """One extracted bite plus its provenance and (optional) embedding.

    `namespace` is the source-document id so retrieval can be scoped to a single
    import. `text` is a verbatim span from the source so `location` stays
    re-locatable and citations are checkable.
    """

    id: str
    text: str
    type: BiteType
    source_title: str
    author: str | None = None
    location: str | None = None  # heading / page if available
    namespace: str
    embedding: Vector | None = None
    confidence: float = 1.0
    created_at: datetime = Field(default_factory=utcnow)


class ScoredBite(BaseModel):
    """A bite returned from a vector search, with its similarity score."""

    bite: KnowledgeBite
    score: float
