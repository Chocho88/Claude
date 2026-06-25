"""Reflection — grade the draft and decide where control goes next.

Emits PASS/FAIL per criterion plus SCORE / ROUTING_TARGET / ISSUE_TYPE. The
routing target names the stage Reflection blames, which (with each stage's
intent_understanding) is what localizes an intent miss.
"""

from __future__ import annotations

from r2a.domain.common import Msg
from r2a.domain.reflection import ReflectionResult
from r2a.domain.trace import StageName, TraceRecord
from r2a.pipeline.schemas import ReflectionProposal
from r2a.pipeline.stage import Deps, Stage, StageContext

_SYSTEM = (
    "You are the Reflection stage — a HOSTILE critic, not a rubber stamp. Grade "
    "the draft PASS/FAIL on TASK_FIT, SCOPE_FIT, EVIDENCE, CITATIONS, CONSTRAINTS, "
    "CLARITY, NOVELTY. Then emit a 0-100 SCORE and route: SHIP only if it truly "
    "clears the bar; else name the stage to blame (SYNTHESIS / RETRIEVAL / "
    "PLANNING) and the ISSUE_TYPE (EVIDENCE_GAP / INTENT_OR_STRATEGY / FORMAT).\n"
    "- FAIL NOVELTY if any idea is obvious, safe, generic, derivative, or could be "
    "built without THIS corpus or without modern AI. Vanilla output FAILS and "
    "routes to SYNTHESIS to force a sharper re-synthesis.\n"
    "- FAIL TASK_FIT and route PLANNING (INTENT_OR_STRATEGY) if it misreads intent.\n"
    "Score by the tiebreak axes — AI-native, asymmetric edge, provocative POV, "
    "artistic resonance. A merely competent, unsurprising draft scores below 70 "
    "and does NOT ship."
)


class ReflectionStage(Stage):
    name = StageName.REFLECTION

    def run(self, ctx: StageContext, deps: Deps) -> TraceRecord:
        draft = ctx.draft
        assert draft is not None, "Reflection requires a draft"
        user = (
            f"User request: {ctx.answers.raw_request!r}\n"
            f"Planned task: {ctx.plan.task.value if ctx.plan else '?'}\n"
            f"Draft title: {draft.title}\nSummary: {draft.summary}\n"
            f"Items: {len(draft.items)}; cited bites: {len(draft.cited_bite_ids())}"
        )
        prop = deps.llm.complete_json(
            system=_SYSTEM,
            messages=[Msg(role="user", content=user)],
            schema=ReflectionProposal,
            max_tokens=900,
        )
        ctx.reflection = ReflectionResult(
            grades=prop.grades,
            score=prop.score,
            routing_target=prop.routing_target,
            issue_type=prop.issue_type,
            notes=prop.notes,
        )
        rec = TraceRecord(
            stage=self.name,
            intent_understanding=prop.intent_understanding,
            inputs_used={"draft_title": draft.title, "n_items": len(draft.items)},
            outputs={
                "routing_target": ctx.reflection.routing_target.value,
                "issue_type": ctx.reflection.issue_type.value,
                "score": ctx.reflection.score,
                "grades": {k.value: v for k, v in ctx.reflection.grades.items()},
                "notes": ctx.reflection.notes,
            },
            confidence=prop.confidence,
            llm_used=deps.llm.name,
            attempt=ctx.attempt,
        )
        deps.tracer.add(rec)
        return rec
