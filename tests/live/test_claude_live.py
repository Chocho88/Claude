"""Live end-to-end vertical slice against the real Claude API.

Opt-in (`pytest -m live`): needs the 'claude' extra and ANTHROPIC_API_KEY.
Ingests a small document with Claude extraction, runs the full pipeline, and
checks the hub note is cited and the trace records the Claude model.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.live

_DOC = (
    "# Designing against engagement traps\n"
    "## Contextual trust\n"
    "Contextual trust is trust scoped to a person and a situation, not a public score.\n\n"
    "## Live experiences\n"
    "Synchronous co-presence lets people share live experiences instead of broadcasting.\n\n"
    "## Vanity metrics\n"
    "Public vanity metrics push users toward performance over genuine connection.\n"
)


@pytest.fixture
def claude():
    pytest.importorskip("anthropic")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
    from r2a.adapters.llm.claude import ClaudeProvider

    return ClaudeProvider()


def test_full_slice_with_claude(tmp_path, claude):
    from r2a.adapters.embedding.stub import HashEmbedder
    from r2a.adapters.vectorstore.memory import InMemoryStore
    from r2a.config import Config
    from r2a.domain.job import Constraints, ElicitationAnswers, Job
    from r2a.domain.plan import Scope, TaskType
    from r2a.ingest import ingest_document
    from r2a.pipeline.orchestrator import run_pipeline
    from r2a.pipeline.stage import Deps, StageContext
    from r2a.pipeline.tracer import Tracer

    doc = tmp_path / "social.md"
    doc.write_text(_DOC, encoding="utf-8")

    embedder, store = HashEmbedder(), InMemoryStore()
    res = ingest_document(doc, embedder=embedder, store=store, llm=claude)
    assert res.n_bites > 0

    answers = ElicitationAnswers(
        raw_request="Give me 3 product ideas for healthier social sharing.",
        task=TaskType.IDEAS,
        scope=Scope.IMPORT,
        constraints=Constraints(count=3, audience="builders"),
    )
    job = Job(id="live1", namespaces=[res.namespace], answers=answers)
    deps = Deps(llm=claude, embedder=embedder, store=store, tracer=Tracer(), config=Config())
    ctx = StageContext(job=job, answers=answers)

    out = run_pipeline(ctx, deps, out_dir=tmp_path / "vault")

    assert out.draft and out.draft.items
    assert out.draft.cited_bite_ids()  # items trace to source bites
    trace = json.loads(Path(out.result.trace_path).read_text())
    stages = {r["stage"] for r in trace}
    assert {"planning", "synthesis", "reflection"} <= stages
    assert any(r["llm_used"] and "claude" in r["llm_used"] for r in trace)
