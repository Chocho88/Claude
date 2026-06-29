"""Retrieval — a real vector-DB query, scoped to the import.

Augments with web search only when scope is IMPORT_WEB (the moment content may
leave the device). Uses no LLM, so its trace records `llm_used=None`.
"""

from __future__ import annotations

from r2a.domain.plan import Scope
from r2a.domain.trace import StageName, TraceRecord
from r2a.pipeline.stage import Deps, Stage, StageContext


class RetrievalStage(Stage):
    name = StageName.RETRIEVAL

    def run(self, ctx: StageContext, deps: Deps) -> TraceRecord:
        plan = ctx.plan
        assert plan is not None, "Retrieval requires a plan"
        query = f"{ctx.answers.raw_request} {plan.strategy} {plan.answer_shape}".strip()

        # Scope to a single import when there's exactly one namespace; otherwise
        # search across all imports attached to the job.
        namespaces = ctx.job.namespaces
        ns = namespaces[0] if len(namespaces) == 1 else None

        qv = deps.embedder.embed_query(query)
        ctx.retrieved = deps.store.search(qv, namespace=ns, top_k=plan.top_k)

        web_n = 0
        if plan.scope == Scope.IMPORT_WEB and deps.web is not None:
            web_n = len(deps.web.search(query, max_results=5))

        rec = TraceRecord(
            stage=self.name,
            intent_understanding=f"retrieve bites relevant to: {plan.intent}",
            inputs_used={
                "query": query,
                "namespace": ns,
                "top_k": plan.top_k,
                "scope": plan.scope.value,
            },
            outputs={
                "n_bites": len(ctx.retrieved),
                "top_scores": [round(s.score, 4) for s in ctx.retrieved[:5]],
                "web_results": web_n,
            },
            confidence=1.0 if ctx.retrieved else 0.2,
            llm_used=None,
            attempt=ctx.attempt,
        )
        deps.tracer.add(rec)
        return rec
