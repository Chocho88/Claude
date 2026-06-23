"""Edge wiring: pick concrete adapters from config + what's installed.

This is one of the few places allowed to import concretes. Each real adapter is
imported lazily and falls back to its stub double when the optional dependency
(or API key) is missing — so the app always runs, degrading gracefully.
"""

from __future__ import annotations

import os

from r2a.adapters.embedding.base import Embedder
from r2a.adapters.llm.base import LLMProvider
from r2a.adapters.vectorstore.base import VectorStore
from r2a.config import Config
from r2a.pipeline.stage import Deps
from r2a.pipeline.tracer import Tracer
from r2a.retrieval.web import DisabledWebSearch, WebSearchProvider


def default_llm(config: Config) -> LLMProvider:
    routing = config.llm.routing
    want_claude = routing == "force_claude" or (
        routing == "auto" and bool(os.environ.get("ANTHROPIC_API_KEY"))
    )
    if want_claude:
        try:
            from r2a.adapters.llm.claude import ClaudeProvider  # M2

            return ClaudeProvider(model=config.llm.claude_model)
        except Exception:  # not installed / no key — fall back
            pass
    if routing == "force_local":
        from r2a.adapters.llm.stub import LocalProvider  # M5 placeholder

        return LocalProvider()
    from r2a.adapters.llm.stub import StubProvider

    return StubProvider()


def default_embedder(config: Config) -> Embedder:
    try:
        from r2a.adapters.embedding.sbert import SentenceTransformerEmbedder  # M1

        return SentenceTransformerEmbedder(model_id=config.embedding.model_id)
    except Exception:
        from r2a.adapters.embedding.stub import HashEmbedder

        return HashEmbedder()


def default_store(config: Config) -> VectorStore:
    try:
        from r2a.adapters.vectorstore.lancedb_store import LanceDBStore  # M1

        return LanceDBStore(path=config.paths.store())
    except Exception:
        from r2a.adapters.vectorstore.memory import InMemoryStore

        return InMemoryStore()


def build_deps(
    config: Config,
    *,
    llm: LLMProvider | None = None,
    embedder: Embedder | None = None,
    store: VectorStore | None = None,
    tracer: Tracer | None = None,
    web: WebSearchProvider | None = None,
) -> Deps:
    return Deps(
        llm=llm or default_llm(config),
        embedder=embedder or default_embedder(config),
        store=store or default_store(config),
        tracer=tracer or Tracer(),
        config=config,
        web=web or DisabledWebSearch(),
    )
