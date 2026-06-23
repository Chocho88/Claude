"""LLMProvider ABC — the linchpin of provider-swappability.

Every stage that needs structured output goes through `complete_json`, which
returns a validated pydantic instance. The Claude implementation realises this
with forced tool-use; the stub realises it deterministically. Stages never know
which provider answered (only the trace records `llm_used`).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

from r2a.domain.common import LLMResponse, Msg

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    #: Short identifier recorded in every TraceRecord.llm_used (e.g.
    #: "claude-sonnet-4-6", "gemma-...", "stub").
    name: str = "abstract"

    @abstractmethod
    def complete(
        self,
        *,
        system: str,
        messages: list[Msg],
        max_tokens: int,
        temperature: float = 0.0,
        stop: list[str] | None = None,
    ) -> LLMResponse:
        """Plain-text completion."""

    @abstractmethod
    def complete_json(
        self,
        *,
        system: str,
        messages: list[Msg],
        schema: type[T],
        max_tokens: int,
        temperature: float = 0.0,
    ) -> T:
        """Return a validated instance of `schema`.

        Implementations must validate against the schema and, on failure, retry
        once with the validation error fed back before raising.
        """
