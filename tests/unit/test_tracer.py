"""Tracer renders machine JSON and localizes intent divergence."""

from __future__ import annotations

import json

from r2a.domain.trace import StageName, TraceRecord
from r2a.pipeline.tracer import Tracer


def _rec(stage: StageName, intent: str, **outputs) -> TraceRecord:
    return TraceRecord(stage=stage, intent_understanding=intent, outputs=outputs)


def test_divergence_stage_from_reflection_routing():
    t = Tracer()
    t.add(_rec(StageName.PLANNING, "summarize the document"))  # the miss
    t.add(_rec(StageName.SYNTHESIS, "write a summary"))
    t.add(_rec(StageName.REFLECTION, "user wanted ideas, not a summary",
               routing_target="PLANNING", issue_type="INTENT_OR_STRATEGY"))
    assert t.divergence_stages() == [StageName.PLANNING]


def test_ship_routing_is_not_a_divergence():
    t = Tracer()
    t.add(_rec(StageName.REFLECTION, "looks good", routing_target="SHIP"))
    assert t.divergence_stages() == []


def test_timeline_marks_blamed_stage_and_json_roundtrips():
    t = Tracer()
    t.add(_rec(StageName.PLANNING, "summarize the document"))
    t.add(_rec(StageName.REFLECTION, "wrong task",
               routing_target="PLANNING", issue_type="INTENT_OR_STRATEGY"))
    callout = t.intent_timeline_callout()
    assert callout.startswith("> [!info]- Intent timeline")
    assert "⚠ **planning**" in callout  # the divergence is flagged
    # machine trace is valid JSON
    assert len(json.loads(t.to_json())) == 2
