"""Domain model sanity + the generic stub default-instance builder."""

from __future__ import annotations

from r2a.adapters.llm.stub import build_default
from r2a.domain.synthesis import SynthesisOutput, SynthItem
from r2a.domain.trace import RoutingTarget, StageName, TraceRecord
from r2a.pipeline.schemas import (
    PlanProposal,
    ReflectionProposal,
    SynthesisProposal,
)


def test_build_default_produces_valid_instances():
    # Every stage schema must be buildable with no inputs (offline pipeline).
    for schema in (PlanProposal, SynthesisProposal, ReflectionProposal):
        inst = build_default(schema)
        assert schema.model_validate(inst.model_dump()) == inst


def test_reflection_default_ships():
    # Unscripted reflection should ship, so the happy path terminates in one pass.
    assert build_default(ReflectionProposal).routing_target == RoutingTarget.SHIP


def test_synthesis_cited_bite_ids():
    draft = SynthesisOutput(
        title="t",
        items=[
            SynthItem(text="a", cites=["b1", "b2"]),
            SynthItem(text="b", cites=["b2"]),
        ],
    )
    assert draft.cited_bite_ids() == {"b1", "b2"}


def test_trace_record_json_roundtrips():
    rec = TraceRecord(
        stage=StageName.PLANNING,
        intent_understanding="x",
        confidence=0.5,
    )
    assert rec.stage == StageName.PLANNING
    assert "planning" in rec.model_dump(mode="json")["stage"]
