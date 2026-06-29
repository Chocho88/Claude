"""Reflection's structured grade of a synthesis draft."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from .trace import IssueType, RoutingTarget


class Criterion(str, Enum):
    TASK_FIT = "TASK_FIT"
    SCOPE_FIT = "SCOPE_FIT"
    EVIDENCE = "EVIDENCE"
    CITATIONS = "CITATIONS"
    CONSTRAINTS = "CONSTRAINTS"
    CLARITY = "CLARITY"
    NOVELTY = "NOVELTY"  # vanilla/obvious output fails this and is re-synthesized


Grade = Literal["PASS", "FAIL"]


class ReflectionResult(BaseModel):
    """PASS/FAIL per criterion plus the routing decision.

    `routing_target` names the stage Reflection blames for any failure, which is
    the second half (with each stage's `intent_understanding`) of intent-failure
    localization.
    """

    grades: dict[Criterion, Grade] = Field(default_factory=dict)
    score: int = 0  # 0..100; best draft across attempts is kept
    routing_target: RoutingTarget = RoutingTarget.SHIP
    issue_type: IssueType = IssueType.NONE
    notes: str = ""

    @property
    def all_pass(self) -> bool:
        return all(g == "PASS" for g in self.grades.values())
