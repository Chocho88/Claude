"""Live test for real sentence-transformers embeddings.

Opt-in (`pytest -m live`): needs the 'embeddings' extra and a one-time model
download. Verifies the bge query/document asymmetry actually improves ranking.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.live


def test_bge_embeddings_rank_semantically():
    pytest.importorskip("sentence_transformers")
    from r2a.adapters.embedding.sbert import SentenceTransformerEmbedder
    from r2a.adapters.vectorstore.memory import InMemoryStore
    from r2a.domain.bite import BiteType, KnowledgeBite

    emb = SentenceTransformerEmbedder()
    assert emb.dim > 0

    docs = [
        "Contextual trust is scoped to a person and a situation.",
        "Vanity metrics push users toward performance.",
        "Synchronous co-presence lets people share live experiences.",
    ]
    vecs = emb.embed(docs)
    store = InMemoryStore()
    store.upsert([
        KnowledgeBite(id=f"b{i}", text=t, type=BiteType.CLAIM,
                      source_title="D", namespace="ns", embedding=v)
        for i, (t, v) in enumerate(zip(docs, vecs))
    ])

    qv = emb.embed_query("watching something together at the same time")
    hits = store.search(qv, namespace="ns", top_k=1)
    assert "live experiences" in hits[0].bite.text  # semantic, not lexical, match
