"""The orchestrator: linear stages, then the bounded Synthesis↔Reflection loop.

Linearity is real (Elicitation → Planning → Retrieval), but Reflection can rewind
the cursor to Synthesis, Retrieval, or Planning. Every rewind increments a bounded
counter (see decide.py), so the loop provably terminates. The best-scoring draft
is always retained, so every terminal path emits something.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from r2a.domain.common import Question
from r2a.domain.job import JobResult, JobStatus
from r2a.domain.synthesis import SynthesisOutput

from .decide import Decision, decide
from .stage import Deps, StageContext
from .stages import (
    ElicitationStage,
    PlanningStage,
    ReflectionStage,
    RetrievalStage,
    SynthesisStage,
)


@dataclass
class PipelineResult:
    status: JobStatus
    draft: SynthesisOutput | None = None
    ship_with_caveat: bool = False
    result: JobResult | None = None  # set when outputs were written
    followups: list[Question] | None = None  # set when status == NEEDS_INPUT


def _consider_best(ctx: StageContext) -> None:
    """Track the highest-scoring draft across attempts."""
    if ctx.draft is None or ctx.reflection is None:
        return
    ctx.draft.score = ctx.reflection.score
    if ctx.best_draft is None or ctx.draft.score > ctx.best_draft.score:
        ctx.best_draft = ctx.draft


def run_pipeline(
    ctx: StageContext, deps: Deps, *, out_dir: Path | None = None
) -> PipelineResult:
    cfg = deps.config.loop
    elicit, planning = ElicitationStage(), PlanningStage()
    retrieval, synth, reflect = RetrievalStage(), SynthesisStage(), ReflectionStage()

    elicit.run(ctx, deps)

    planning.run(ctx, deps)
    ctx.counters.planning_runs += 1
    assert ctx.plan is not None
    if ctx.plan.needs_input:
        return PipelineResult(
            status=JobStatus.NEEDS_INPUT, followups=ctx.plan.followup_questions
        )

    retrieval.run(ctx, deps)
    ctx.counters.retrieval_runs += 1

    while True:
        ctx.attempt += 1
        synth.run(ctx, deps)
        ctx.counters.synth_attempts += 1
        reflect.run(ctx, deps)
        _consider_best(ctx)

        decision = decide(
            ctx.reflection,
            ctx.counters,
            max_synth_per_phase=cfg.max_synth_per_phase,
            max_escalations=cfg.max_escalations,
        )

        if decision == Decision.SHIP:
            break
        if decision == Decision.RESYNTH:
            continue
        if decision == Decision.ESCALATE_RETRIEVAL:
            ctx.plan.top_k *= 2  # widen the evidence net
            retrieval.run(ctx, deps)
            ctx.counters.retrieval_runs += 1
            ctx.counters.escalations_used += 1
            ctx.counters.synth_attempts = 0  # fresh phase
            continue
        if decision == Decision.ESCALATE_PLANNING:
            planning.run(ctx, deps)
            ctx.counters.planning_runs += 1
            ctx.counters.escalations_used += 1
            ctx.counters.synth_attempts = 0
            continue
        if decision == Decision.SHIP_BEST:
            ctx.ship_with_caveat = True
            ctx.draft = ctx.best_draft  # ship the best we ever produced
            break

    result = None
    if out_dir is not None:
        # Imported here (not at module top) to keep the import surface small;
        # output/ imports domain only, never adapters.
        from r2a.output.vault import write_outputs

        result = write_outputs(ctx, deps.tracer, out_dir)

    return PipelineResult(
        status=JobStatus.DONE,
        draft=ctx.draft,
        ship_with_caveat=ctx.ship_with_caveat,
        result=result,
    )
