"""Trace records and the enums that drive intent-failure localization."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .common import utcnow


class StageName(str, Enum):
    ELICITATION = "elicitation"
    PLANNING = "planning"
    RETRIEVAL = "retrieval"
    SYNTHESIS = "synthesis"
    REFLECTION = "reflection"
    OUTPUT = "output"


class RoutingTarget(str, Enum):
    """Where Reflection sends control next; SHIP ends the loop."""

    SHIP = "SHIP"
    SYNTHESIS = "SYNTHESIS"
    RETRIEVAL = "RETRIEVAL"
    PLANNING = "PLANNING"


class IssueType(str, Enum):
    NONE = "NONE"
    EVIDENCE_GAP = "EVIDENCE_GAP"
    INTENT_OR_STRATEGY = "INTENT_OR_STRATEGY"
    FORMAT = "FORMAT"


class TraceRecord(BaseModel):
    """Emitted by every stage on every attempt.

    `intent_understanding` is the stage's own restatement of what the user
    wants; comparing these across stages (and against Reflection's
    `routing_target`) is what pinpoints where intent diverged.
    """

    stage: StageName
    intent_understanding: str
    inputs_used: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    llm_used: str | None = None  # provider.name, or None when no model was used
    attempt: int = 0  # which loop iteration produced this record
    ts: datetime = Field(default_factory=utcnow)
