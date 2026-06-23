"""Ingest: a document path becomes namespaced knowledge bites in the vector store.

    load_document -> chunk_text -> extract_bites -> embed -> store.upsert

Each step is small and independently testable. Heavy parsers are imported lazily
so the package imports cleanly without the optional `ingest` extra.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from r2a.adapters.embedding.base import Embedder
from r2a.adapters.llm.base import LLMProvider
from r2a.adapters.vectorstore.base import VectorStore

from .chunker import chunk_text
from .extractor import extract_bites
from .loaders import load_document


class IngestResult(BaseModel):
    namespace: str
    source_title: str
    n_passages: int
    n_bites: int


def namespace_for(path: str | Path, title: str) -> str:
    """Stable per-document namespace id (slug + short path hash)."""
    import hashlib
    import re

    slug = re.sub(r"[^\w]+", "-", title.lower()).strip("-")[:40] or "doc"
    h = hashlib.sha1(str(Path(path).resolve()).encode()).hexdigest()[:8]
    return f"{slug}-{h}"


def ingest_document(
    path: str | Path,
    *,
    embedder: Embedder,
    store: VectorStore,
    llm: LLMProvider,
    namespace: str | None = None,
) -> IngestResult:
    """Ingest one file end to end and return what was stored."""
    text, meta = load_document(path)
    ns = namespace or namespace_for(path, meta.title)

    passages = chunk_text(text, meta.ext)
    bites = extract_bites(passages, meta, llm, namespace=ns)

    if bites:
        vectors = embedder.embed([b.text for b in bites])
        for bite, vec in zip(bites, vectors):
            bite.embedding = vec
        store.delete_namespace(ns)  # idempotent re-ingest
        store.upsert(bites)

    return IngestResult(
        namespace=ns,
        source_title=meta.title,
        n_passages=len(passages),
        n_bites=len(bites),
    )
