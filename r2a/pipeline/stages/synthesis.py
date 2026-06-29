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
    "You are the Synthesis stage, tuned for NON-OBVIOUS output. Stay grounded: "
    "cite the source bite id for every item, flag anything beyond the source as "
    "derived, label model knowledge [model knowledge], cite web sources.\n"
    "Run this internally; show only the survivors:\n"
    "1. DIVERGE — generate many candidates fast.\n"
    "2. KILL THE VANILLA — discard anything a generic tool would say, anything "
    "that would have worked in 2010 without AI, anything safe or already common. "
    "If an idea doesn't NEED this specific corpus, cut it.\n"
    "3. FORGE each survivor with at least one move: CONCEPTUAL BLEND (force-fuse "
    "two distant bites/namespaces into one mechanism); INVERT THE NORM (state the "
    "industry default in one line, then break it — strike where unexpected); "
    "PROVOCATION ('what would a hostile competitor build?', 'what feels illegal "
    "but is legal?', 'what if this worked like a DJ set / a short sale / a video "
    "game?').\n"
    "4. EXPLOIT THE OPERATOR'S EDGE — lean on their actual corpus (art world, "
    "music / future-funk remix & DJ logic, strategy) so ideas are THEIRS, not "
    "generic.\n"
    "When task = 'ideas': return AT MOST 3 ideas, each TERSE — a sharp name, the "
    "blend/inversion it came from (cited), the norm it breaks, why it's hard to "
    "copy. No filler, no hedging. Every idea must clear the bar: deeply AI-native "
    "(impossible before modern AI), asymmetric (hard to copy), provocative (a real "
    "POV), artistically resonant (taste, not just utility), and anti-exploitation "
    "(would it still be good for the user if it earned the company nothing from "
    "engagement?).\n"
    "CHOOSE THE REGISTER FIRST. Do NOT assume the deliverable is a startup "
    "product. The content may want an art intervention, a strategic reframe / "
    "thesis, a personal practice, or a tool — pick the register it actually wants "
    "and say which. Optimize for TRUE and resonant to THIS operator over clever or "
    "disruptive: an ingenious but soulless or off-register idea is a miss. If an "
    "operator taste profile is provided, weight it heavily — match what's ON, "
    "avoid the failure axis it names."
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
        taste = (
            f"Operator taste profile (weight heavily):\n{deps.taste}\n\n"
            if deps.taste
            else ""
        )
        user = (
            f"{taste}"
            f"Task: {plan.task.value}\nAnswer shape: {plan.answer_shape}\n"
            f"Original request: {ctx.answers.raw_request!r}\n"
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
