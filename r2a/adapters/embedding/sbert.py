"""SentenceTransformerEmbedder — local, offline, cross-platform embeddings (M1).

Default bge-small-en-v1.5 is small and strong on a Mac. bge is asymmetric: the
query side gets an instruction prefix, which is why `embed_query` differs from
`embed`. The model + torch arrive via the 'embeddings' extra.
"""

from __future__ import annotations

from r2a.domain.common import Vector

from .base import Embedder

# Recommended retrieval instruction for bge-*-en-v1.5 query embeddings.
_BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class SentenceTransformerEmbedder(Embedder):
    def __init__(self, model_id: str = "BAAI/bge-small-en-v1.5") -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:  # pragma: no cover
            raise ImportError(
                "Embeddings need the 'embeddings' extra: pip install -e '.[embeddings]'"
            ) from e
        self.model_id = model_id
        self._model = SentenceTransformer(model_id)
        self.dim = int(self._model.get_sentence_embedding_dimension())
        # Apply the query prefix only for known asymmetric (bge) models.
        self._use_prefix = "bge" in model_id.lower()

    def embed(self, texts: list[str]) -> list[Vector]:
        vecs = self._model.encode(texts, normalize_embeddings=True)
        return [v.tolist() for v in vecs]

    def embed_query(self, text: str) -> Vector:
        q = (_BGE_QUERY_PREFIX + text) if self._use_prefix else text
        return self._model.encode([q], normalize_embeddings=True)[0].tolist()
