"""LLM I/O contracts for each stage.

These are the schemas passed to `LLMProvider.complete_json`. They are deliberately
separate from the domain models: a stage takes the proposal, merges it with
deterministic inputs (the user's answers, the retrieved bites), and produces the
domain object. Defaults are chosen so an unscripted StubProvider yields a sane,
ship-able run with no network.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from r2a.domain.common import Question
from r2a.domain.plan import Scope, TaskType
from r2a.domain.reflection import Criterion, Grade
from r2a.domain.synthesis import SynthItem
from r2a.domain.trace import IssueType, RoutingTarget


class ElicitationProposal(BaseModel):
    followups: list[Question] = Field(default_factory=list)
    intent_understanding: str = "(stub) understood the request as stated"
    confidence: float = 0.8


class PlanProposal(BaseModel):
    task: TaskType = TaskType.IDEAS
    scope: Scope = Scope.IMPORT
    strategy: str = "retrieve scoped bites, then synthesize in the answer shape"
    answer_shape: str = "a list of grounded items"
    top_k: int = 8
    needs_input: bool = False
    followups: list[Question] = Field(default_factory=list)
    intent_understanding: str = "(stub) plan honours the user's selected task"
    confidence: float = 0.8


class SynthesisProposal(BaseModel):
    title: str = "Synthesis"
    summary: str = ""
    items: list[SynthItem] = Field(default_factory=list)
    mermaid: str | None = None
    intent_understanding: str = "(stub) deliver the planned shape from the bites"
    confidence: float = 0.8


class ReflectionProposal(BaseModel):
    grades: dict[Criterion, Grade] = Field(default_factory=dict)
    score: int = 75
    routing_target: RoutingTarget = RoutingTarget.SHIP
    issue_type: IssueType = IssueType.NONE
    notes: str = ""
    intent_understanding: str = "(stub) draft fits the request"
    confidence: float = 0.8
