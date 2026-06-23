"""Stage ABC, the shared run state (StageContext), and the dependency bundle."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from r2a.adapters.embedding.base import Embedder
from r2a.adapters.llm.base import LLMProvider
from r2a.adapters.vectorstore.base import VectorStore
from r2a.config import Config
from r2a.domain.bite import ScoredBite
from r2a.domain.job import ElicitationAnswers, Job
from r2a.domain.plan import PlanSpec
from r2a.domain.reflection import ReflectionResult
from r2a.domain.synthesis import SynthesisOutput
from r2a.domain.trace import StageName, TraceRecord
from r2a.retrieval.web import WebSearchProvider

if TYPE_CHECKING:
    from r2a.pipeline.tracer import Tracer


@dataclass
class RunCounters:
    """Bounds that make the reflection loop provably terminate."""

    synth_attempts: int = 0  # within the current phase; reset on escalation
    escalations_used: int = 0
    planning_runs: int = 0
    retrieval_runs: int = 0


@dataclass
class StageContext:
    """Mutable state threaded through one run. Stages mutate it in place."""

    job: Job
    answers: ElicitationAnswers
    plan: PlanSpec | None = None
    retrieved: list[ScoredBite] = field(default_factory=list)
    draft: SynthesisOutput | None = None
    best_draft: SynthesisOutput | None = None  # highest score seen
    reflection: ReflectionResult | None = None
    counters: RunCounters = field(default_factory=RunCounters)
    ship_with_caveat: bool = False
    attempt: int = 0  # current synthesis attempt index, stamped onto traces


@dataclass
class Deps:
    """Everything a stage needs, all swappable behind ABCs."""

    llm: LLMProvider
    embedder: Embedder
    store: VectorStore
    tracer: "Tracer"
    config: Config
    web: WebSearchProvider | None = None


class Stage(ABC):
    name: StageName

    @abstractmethod
    def run(self, ctx: StageContext, deps: Deps) -> TraceRecord:
        """Advance `ctx` and return the TraceRecord this stage emitted.

        Implementations MUST set `intent_understanding` and `confidence` on the
        record — that is what makes intent-failure localization possible.
        """
