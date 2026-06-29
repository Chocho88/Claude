"""Ingest end to end (offline stubs) + a real LanceDB round-trip when installed."""

from __future__ import annotations

import pytest

from r2a.adapters.embedding.stub import HashEmbedder
from r2a.adapters.llm.stub import StubProvider
from r2a.adapters.vectorstore.memory import InMemoryStore
from r2a.domain.bite import BiteType, KnowledgeBite
from r2a.ingest import ingest_document

_DOC = (
    "# Healthier Social Apps\n"
    "An argument for designing against engagement traps.\n\n"
    "## Contextual trust\n"
    "Contextual trust is trust scoped to a person and a situation, "
    "not a public follower score.\n\n"
    "## Live experiences\n"
    "Synchronous co-presence lets people share live experiences together "
    "instead of broadcasting to an audience.\n\n"
    "## Vanity metrics\n"
    "Public vanity metrics push users toward performance over genuine connection.\n"
)


def _write_doc(tmp_path):
    p = tmp_path / "social.md"
    p.write_text(_DOC, encoding="utf-8")
    return p


def test_ingest_creates_namespaced_bites(tmp_path):
    path = _write_doc(tmp_path)
    embedder, store, llm = HashEmbedder(), InMemoryStore(), StubProvider()

    res = ingest_document(path, embedder=embedder, store=store, llm=llm)

    assert res.n_bites == res.n_passages > 0  # stub: one bite per passage
    assert store.namespaces() == [res.namespace]
    assert all(b.namespace == res.namespace for b in store._bites.values())
    assert all(b.embedding is not None for b in store._bites.values())


def test_scoped_search_finds_relevant_passage(tmp_path):
    path = _write_doc(tmp_path)
    embedder, store, llm = HashEmbedder(), InMemoryStore(), StubProvider()
    res = ingest_document(path, embedder=embedder, store=store, llm=llm)

    qv = embedder.embed_query("sharing live experiences synchronously together")
    hits = store.search(qv, namespace=res.namespace, top_k=1)
    assert hits and "live experiences" in hits[0].bite.text


def test_reingest_is_idempotent(tmp_path):
    path = _write_doc(tmp_path)
    embedder, store, llm = HashEmbedder(), InMemoryStore(), StubProvider()
    a = ingest_document(path, embedder=embedder, store=store, llm=llm)
    n_after_first = len(store._bites)
    b = ingest_document(path, embedder=embedder, store=store, llm=llm)
    assert a.namespace == b.namespace
    assert len(store._bites) == n_after_first  # no duplication


def test_lancedb_roundtrip(tmp_path):
    pytest.importorskip("lancedb")
    from r2a.adapters.vectorstore.lancedb_store import LanceDBStore

    embedder = HashEmbedder()
    store = LanceDBStore(tmp_path / "store")
    texts = ["contextual trust is situational", "live experiences synchronously"]
    vecs = embedder.embed(texts)
    bites = [
        KnowledgeBite(
            id=f"ns1:{i}",
            text=t,
            type=BiteType.CLAIM,
            source_title="Doc",
            namespace="ns1",
            embedding=v,
        )
        for i, (t, v) in enumerate(zip(texts, vecs))
    ]
    store.upsert(bites)

    assert store.namespaces() == ["ns1"]
    qv = embedder.embed_query("situational trust")
    hits = store.search(qv, namespace="ns1", top_k=2)
    assert hits and hits[0].bite.namespace == "ns1"
    assert "trust" in hits[0].bite.text

    store.delete_namespace("ns1")
    assert store.namespaces() == []
