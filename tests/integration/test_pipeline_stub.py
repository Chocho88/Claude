"""End-to-end pipeline on stubs: happy path, guaranteed termination, and
intent-failure localization — all offline."""

from __future__ import annotations

import json
from pathlib import Path

from r2a.adapters.llm.stub import StubProvider
from r2a.config import Config
from r2a.domain.job import JobStatus
from r2a.domain.plan import TaskType
from r2a.domain.trace import StageName
from r2a.pipeline.orchestrator import run_pipeline
from r2a.pipeline.stage import Deps
from r2a.pipeline.tracer import Tracer

from tests.conftest import make_answers, make_ctx


def _deps(store, embedder, llm) -> Deps:
    return Deps(llm=llm, embedder=embedder, store=store, tracer=Tracer(), config=Config())


def test_happy_path_produces_cited_hub_note(tmp_path, store, embedder):
    ctx = make_ctx(make_answers(task=TaskType.IDEAS))
    deps = _deps(store, embedder, StubProvider())

    res = run_pipeline(ctx, deps, out_dir=tmp_path)

    assert res.status == JobStatus.DONE
    assert not res.ship_with_caveat
    # The draft grounded one item per retrieved bite (stub fallback).
    assert res.draft is not None and len(res.draft.items) == 5
    assert res.draft.cited_bite_ids()  # every run is citable

    text = Path(res.result.hub_note_path).read_text()
    assert text.startswith("---")  # frontmatter
    assert "research-to-artifact" in text
    assert "Intent timeline" in text
    assert "[[On Healthier Social Apps" in text  # wikilink graph node

    trace = json.loads((tmp_path / "trace.json").read_text())
    stages = [r["stage"] for r in trace]
    assert stages == ["elicitation", "planning", "retrieval", "synthesis", "reflection"]


def test_retrieval_is_scoped_and_relevant(store, embedder):
    ctx = make_ctx(make_answers(raw_request="contextual trust scoped to a situation"))
    deps = _deps(store, embedder, StubProvider())
    run_pipeline(ctx, deps)  # no out_dir: just exercise retrieval

    assert ctx.retrieved
    assert all(sb.bite.namespace == "doc1" for sb in ctx.retrieved)
    # the bite about contextual trust should rank at the top
    assert ctx.retrieved[0].bite.id == "b2"


def test_always_failing_reflection_ships_best_with_caveat(tmp_path, store, embedder):
    # 6 failing reflections: 3 in phase 1, escalate planning, 3 in phase 2 -> SHIP_BEST.
    fail = {
        "routing_target": "PLANNING",
        "issue_type": "INTENT_OR_STRATEGY",
        "score": 40,
        "grades": {"TASK_FIT": "FAIL"},
        "intent_understanding": "still not matching intent",
        "confidence": 0.5,
    }
    llm = StubProvider(scripts={"ReflectionProposal": [dict(fail) for _ in range(6)]})
    ctx = make_ctx(make_answers())
    deps = _deps(store, embedder, llm)

    res = run_pipeline(ctx, deps, out_dir=tmp_path)

    assert res.status == JobStatus.DONE
    assert res.ship_with_caveat
    assert ctx.counters.escalations_used == 1
    assert "Shipped with caveat" in Path(res.result.hub_note_path).read_text()


def test_intent_miss_is_localized_to_planning(store, embedder):
    # User asks for ideas; Planning misclassifies as 'summarize'; Reflection blames PLANNING.
    plan_miss = {
        "task": "summarize",
        "scope": "import",
        "strategy": "condense the document",
        "answer_shape": "a short summary",
        "intent_understanding": "the user wants a summary of the document",
        "confidence": 0.7,
    }
    refl_fail = {
        "routing_target": "PLANNING",
        "issue_type": "INTENT_OR_STRATEGY",
        "score": 45,
        "grades": {"TASK_FIT": "FAIL"},
        "intent_understanding": "draft summarizes, but the user wanted product ideas",
        "confidence": 0.6,
    }
    llm = StubProvider(scripts={
        "PlanProposal": [dict(plan_miss), dict(plan_miss)],
        "ReflectionProposal": [dict(refl_fail) for _ in range(3)],
    })
    ctx = make_ctx(make_answers(task=TaskType.IDEAS,
                                raw_request="Give me product ideas for healthier social sharing."))
    deps = _deps(store, embedder, llm)

    run_pipeline(ctx, deps)

    # The trace pinpoints PLANNING as the divergence, and the loop re-planned.
    assert StageName.PLANNING in deps.tracer.divergence_stages()
    assert ctx.counters.planning_runs == 2
    planning_recs = [r for r in deps.tracer.records if r.stage.value == "planning"]
    assert "summary" in planning_recs[0].intent_understanding.lower()
