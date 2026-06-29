"""Small shared types used across the domain and adapter ABCs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

# An embedding vector. Kept as a plain list so domain stays dependency-free
# (no numpy in the model layer).
Vector = list[float]


def utcnow() -> datetime:
    """Timezone-aware UTC now. One place so trace timestamps are consistent."""
    return datetime.now(timezone.utc)


class Msg(BaseModel):
    """A chat message handed to an LLMProvider."""

    role: Literal["user", "assistant"]
    content: str


class LLMResponse(BaseModel):
    """Plain-text completion plus accounting, returned by LLMProvider.complete."""

    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    stop_reason: str | None = None


class Question(BaseModel):
    """A tappable elicitation question (core or adaptive follow-up)."""

    id: str
    text: str
    kind: Literal["single", "multi", "text"] = "single"
    options: list[str] = Field(default_factory=list)
    # Why this question matters — shown in the UI and the trace. Each question
    # must change the work; this records how.
    rationale: str | None = None
