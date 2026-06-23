"""Synthesis — produce the deliverable, grounded in the retrieved bites.

Fidelity: each item cites the source bite(s) it derives from; content beyond the
source is flagged derived / [model knowledge]. If the model returns no items
(e.g. the offline stub), we fall back to grounding one item per retrieved bite so
a run always yields a citable draft.
"""

from __future__ import annotations

from r2a.domain.common import Msg
from r2a.domain.synthesis import SynthesisOutput, SynthItem
from r2a.domain.trace import StageName, TraceRecord
from r2a.pipeline.schemas import SynthesisProposal
from r2a.pipeline.stage import Deps, Stage, StageContext

_SYSTEM = (
    "You are the Synthesis stage. Produce the deliverable in the planned answer "
    "shape, honouring the constraints. Cite the source bite id for every item. "
    "Flag content that goes beyond the source as derived; label model knowledge "
    "[model knowledge]; cite any web sources. When the task is 'ideas', apply the "
    "ideation design lens: prefer AI-native ideas built on contextual trust that "
    "empower sharing live experiences, favour collaboration over performance, and "
    "are anti-exploitation (no vanity metrics; the user winning aligns with the "
    "business)."
)


def _bite_digest(ctx: StageContext, limit: int = 20) -> str:
    lines = []
    for sb in ctx.retrieved[:limit]:
        b = sb.bite
        lines.append(f"- [{b.id}] ({b.type.value}) {b.text}")
    return "\n".join(lines) or "(no bites retrieved)"


class SynthesisStage(Stage):
    name = StageName.SYNTHESIS

    def run(self, ctx: StageContext, deps: Deps) -> TraceRecord:
        plan = ctx.plan
        assert plan is not None, "Synthesis requires a plan"
        user = (
            f"Task: {plan.task.value}\nAnswer shape: {plan.answer_shape}\n"
            f"Constraints: {ctx.answers.constraints.model_dump()}\n"
            f"Retrieved bites:\n{_bite_digest(ctx)}"
        )
        prop = deps.llm.complete_json(
            system=_SYSTEM,
            messages=[Msg(role="user", content=user)],
            schema=SynthesisProposal,
            max_tokens=2000,
        )

        items = list(prop.items)
        if not items:
            # Offline/stub fallback: ground one item per retrieved bite.
            items = [
                SynthItem(text=sb.bite.text, cites=[sb.bite.id])
                for sb in ctx.retrieved
            ]

        ctx.draft = SynthesisOutput(
            title=prop.title or f"{plan.task.value.title()} from import",
            summary=prop.summary,
            items=items,
            mermaid=prop.mermaid,
        )

        rec = TraceRecord(
            stage=self.name,
            intent_understanding=prop.intent_understanding,
            inputs_used={
                "task": plan.task.value,
                "answer_shape": plan.answer_shape,
                "n_bites": len(ctx.retrieved),
            },
            outputs={
                "title": ctx.draft.title,
                "n_items": len(items),
                "n_cited_bites": len(ctx.draft.cited_bite_ids()),
                "has_mermaid": ctx.draft.mermaid is not None,
            },
            confidence=prop.confidence,
            llm_used=deps.llm.name,
            attempt=ctx.attempt,
        )
        deps.tracer.add(rec)
        return rec
