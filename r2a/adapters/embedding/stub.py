"""HashEmbedder — deterministic bag-of-words hashing vectors, no model download.

Shared content words map to shared dimensions, so cosine similarity tracks
lexical overlap. A wide dimension keeps hash collisions rare, and common
stopwords are dropped so they don't manufacture spurious matches. That's enough
for offline retrieval (no semantics across paraphrase); true semantic embeddings
arrive with SentenceTransformerEmbedder (sbert/Gemma) — a drop-in via the
Embedder interface, auto-selected by the factory when installed.
"""

from __future__ import annotations

import hashlib
import math
import re

from r2a.domain.common import Vector

from .base import Embedder

_TOKEN = re.compile(r"\w+")

# Dropped so high-frequency glue words don't create false overlap between
# otherwise-unrelated bites (the cause of cross-topic mis-ranking at low dim).
_STOP = frozenset(
    "a an the this that these those of to in on at for and or but with without "
    "is are was were be been being it its you your they them their he she his "
    "her we our i as by from into out up down so if then than can could should "
    "would may might will have has had do does did not no yes about over under "
    "more most less least very just also which who whom whose what when where "
    "how why all any each both few many much some such own them they're".split()
)


class HashEmbedder(Embedder):
    model_id = "hash-stub"

    def __init__(self, dim: int = 1024) -> None:
        self.dim = dim

    def _vec(self, text: str) -> Vector:
        v = [0.0] * self.dim
        for tok in _TOKEN.findall(text.lower()):
            if len(tok) < 2 or tok in _STOP:
                continue
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            v[h % self.dim] += 1.0
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]

    def embed(self, texts: list[str]) -> list[Vector]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> Vector:
        return self._vec(text)
