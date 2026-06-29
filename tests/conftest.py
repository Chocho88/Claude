"""Shared fixtures: stub providers + a preloaded in-memory store, all offline."""

from __future__ import annotations

import pytest

from r2a.adapters.embedding.stub import HashEmbedder
from r2a.adapters.vectorstore.memory import InMemoryStore
from r2a.config import Config
from r2a.domain.bite import BiteType, KnowledgeBite
from r2a.domain.job import Constraints, ElicitationAnswers, Job
from r2a.domain.plan import Scope, TaskType
from r2a.pipeline.stage import Deps, StageContext
from r2a.pipeline.tracer import Tracer

# A handful of bites for one source document.
_SAMPLE = [
    ("b1", BiteType.CLAIM, "Public vanity metrics push users toward performance over genuine connection."),
    ("b2", BiteType.DEFINITION, "Contextual trust is trust scoped to a person and a situation, not a public score."),
    ("b3", BiteType.CLAIM, "Synchronous co-presence lets people share live experiences instead of broadcasting."),
    ("b4", BiteType.STATISTIC, "Most engagement-maximizing feeds correlate with lower reported wellbeing."),
    ("b5", BiteType.EXAMPLE, "A small group watching a sunset together over video is collaboration, not performance."),
]


@pytest.fixture
def cfg() -> Config:
    return Config()


@pytest.fixture
def embedder() -> HashEmbedder:
    return HashEmbedder()


@pytest.fixture
def store(embedder: HashEmbedder) -> InMemoryStore:
    s = InMemoryStore()
    texts = [t for _, _, t in _SAMPLE]
    vecs = embedder.embed(texts)
    bites = [
        KnowledgeBite(
            id=bid,
            text=text,
            type=btype,
            source_title="On Healthier Social Apps",
            author="A. Researcher",
            location="Intro",
            namespace="doc1",
            embedding=vec,
        )
        for (bid, btype, text), vec in zip(_SAMPLE, vecs)
    ]
    s.upsert(bites)
    return s


def make_answers(
    task: TaskType = TaskType.IDEAS,
    scope: Scope = Scope.IMPORT,
    raw_request: str = "Give me product ideas for healthier social sharing.",
) -> ElicitationAnswers:
    return ElicitationAnswers(
        raw_request=raw_request,
        task=task,
        scope=scope,
        constraints=Constraints(count=3, audience="builders"),
    )


def make_ctx(answers: ElicitationAnswers, namespaces=("doc1",)) -> StageContext:
    job = Job(id="job1", source_paths=[], namespaces=list(namespaces), answers=answers)
    return StageContext(job=job, answers=answers)


def make_deps(store, embedder, llm, tracer: Tracer | None = None) -> Deps:
    return Deps(
        llm=llm,
        embedder=embedder,
        store=store,
        tracer=tracer or Tracer(),
        config=Config(),
    )


# Expose helpers without importing from conftest explicitly.
@pytest.fixture
def helpers():
    class H:
        make_answers = staticmethod(make_answers)
        make_ctx = staticmethod(make_ctx)
        make_deps = staticmethod(make_deps)

    return H
