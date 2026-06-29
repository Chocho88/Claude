"""Planning — classify intent & scope, set strategy and the answer shape.

If the request is underspecified, Planning sets `needs_input` and returns
follow-up questions; the orchestrator pauses the job rather than guessing.
"""

from __future__ import annotations

from r2a.domain.common import Msg
from r2a.domain.plan import PlanSpec
from r2a.domain.trace import StageName, TraceRecord
from r2a.pipeline.schemas import PlanProposal
from r2a.pipeline.stage import Deps, Stage, StageContext

_SYSTEM = (
    "You are the Planning stage. Classify the user's task and scope and set a "
    "concrete strategy and answer shape. Honour the user's selected task unless "
    "their own words clearly indicate a different one. If the request is too "
    "underspecified to proceed, set needs_input=true and return the follow-up "
    "questions you need answered first."
)


class PlanningStage(Stage):
    name = StageName.PLANNING

    def run(self, ctx: StageContext, deps: Deps) -> TraceRecord:
        a = ctx.answers
        user = (
            f"Request: {a.raw_request!r}\n"
            f"Selected task: {a.task.value}\nSelected scope: {a.scope.value}\n"
            f"Constraints: {a.constraints.model_dump()}"
        )
        prop = deps.llm.complete_json(
            system=_SYSTEM,
            messages=[Msg(role="user", content=user)],
            schema=PlanProposal,
            max_tokens=900,
        )
        ctx.plan = PlanSpec(
            intent=prop.intent_understanding,
            scope=prop.scope,
            task=prop.task,
            strategy=prop.strategy,
            answer_shape=prop.answer_shape,
            top_k=prop.top_k or deps.config.retrieval.top_k,
            needs_input=prop.needs_input,
            followup_questions=prop.followups,
        )
        rec = TraceRecord(
            stage=self.name,
            intent_understanding=prop.intent_understanding,
            inputs_used={"raw_request": a.raw_request, "selected_task": a.task.value},
            outputs={
                "task": ctx.plan.task.value,
                "scope": ctx.plan.scope.value,
                "answer_shape": ctx.plan.answer_shape,
                "needs_input": ctx.plan.needs_input,
                "followups": [q.text for q in ctx.plan.followup_questions],
            },
            confidence=prop.confidence,
            llm_used=deps.llm.name,
            attempt=ctx.attempt,
        )
        deps.tracer.add(rec)
        return rec
