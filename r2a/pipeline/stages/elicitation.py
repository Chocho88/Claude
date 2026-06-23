"""Elicitation — confirm the core answers and propose adaptive follow-ups."""

from __future__ import annotations

from r2a.domain.common import Msg
from r2a.domain.trace import StageName, TraceRecord
from r2a.pipeline.schemas import ElicitationProposal
from r2a.pipeline.stage import Deps, Stage, StageContext

_SYSTEM = (
    "You are the Elicitation stage. Restate, in one sentence, what the user "
    "wants. Then propose tappable adaptive follow-up questions that would each "
    "change the work (e.g. which concepts to anchor on, audience, deck style). "
    "Only ask questions that matter."
)


class ElicitationStage(Stage):
    name = StageName.ELICITATION

    def run(self, ctx: StageContext, deps: Deps) -> TraceRecord:
        a = ctx.answers
        user = (
            f"Request: {a.raw_request!r}\n"
            f"Task: {a.task.value}\nScope: {a.scope.value}\n"
            f"Constraints: {a.constraints.model_dump()}"
        )
        prop = deps.llm.complete_json(
            system=_SYSTEM,
            messages=[Msg(role="user", content=user)],
            schema=ElicitationProposal,
            max_tokens=800,
        )
        rec = TraceRecord(
            stage=self.name,
            intent_understanding=prop.intent_understanding,
            inputs_used={
                "raw_request": a.raw_request,
                "task": a.task.value,
                "scope": a.scope.value,
            },
            outputs={"followups": [q.text for q in prop.followups]},
            confidence=prop.confidence,
            llm_used=deps.llm.name,
            attempt=ctx.attempt,
        )
        deps.tracer.add(rec)
        return rec
