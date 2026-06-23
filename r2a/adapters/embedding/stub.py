"""HashEmbedder — deterministic bag-of-words hashing vectors, no model download.

Shared words map to shared dimensions, so cosine similarity tracks lexical
overlap. That's enough for offline retrieval tests; real semantics arrive with
SentenceTransformerEmbedder in M1.
"""

from __future__ import annotations

import hashlib
import math
import re

from r2a.domain.common import Vector

from .base import Embedder

_TOKEN = re.compile(r"\w+")


class HashEmbedder(Embedder):
    model_id = "hash-stub"

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim

    def _vec(self, text: str) -> Vector:
        v = [0.0] * self.dim
        for tok in _TOKEN.findall(text.lower()):
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            v[h % self.dim] += 1.0
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]

    def embed(self, texts: list[str]) -> list[Vector]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> Vector:
        return self._vec(text)
