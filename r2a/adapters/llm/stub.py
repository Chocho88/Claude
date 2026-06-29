"""Deterministic LLM doubles for offline tests and the no-network pipeline.

`StubProvider` answers `complete_json` from a script (responses keyed by schema
name, consumed in order) and falls back to a generic minimal-but-valid instance
of the requested schema. This lets the whole pipeline run with zero network and
lets tests pin exact routing behaviour.

`LocalProvider` is the placeholder for Gemma-via-Ollama/MLX (M5); it shares this
interface so wiring it later touches nothing in domain/ or pipeline/.
"""

from __future__ import annotations

import types
import typing
from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from r2a.domain.common import LLMResponse, Msg, utcnow

from .base import LLMProvider, T


def _default_for(annotation: typing.Any) -> typing.Any:
    """Synthesize a minimal valid value for a type annotation."""
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)

    # Optional[X] / Unions (incl. X | Y) — prefer None, else build the first arm.
    if origin in (typing.Union, types.UnionType):
        if type(None) in args:
            return None
        return _default_for(args[0])

    # Literal[...] — first allowed value.
    if origin is typing.Literal:
        return args[0]

    if origin in (list, set, tuple):
        return [] if origin is not tuple else ()
    if origin is dict:
        return {}

    if isinstance(annotation, type):
        if issubclass(annotation, BaseModel):
            return build_default(annotation)
        if issubclass(annotation, Enum):
            return next(iter(annotation))  # first member
        if issubclass(annotation, bool):
            return False
        if issubclass(annotation, int):
            return 0
        if issubclass(annotation, float):
            return 0.0
        if issubclass(annotation, str):
            return ""
        if issubclass(annotation, datetime):
            return utcnow()
    return None


def build_default(model: type[T]) -> T:
    """Build a minimal valid instance: defaults where declared, else synthesized."""
    values: dict[str, typing.Any] = {}
    for name, field in model.model_fields.items():
        if not field.is_required():
            continue  # let the declared default / default_factory apply
        values[name] = _default_for(field.annotation)
    return model(**values)


class StubProvider(LLMProvider):
    name = "stub"

    def __init__(self, scripts: dict[str, list[dict]] | None = None) -> None:
        # schema name -> queued response payloads (consumed FIFO)
        self.scripts = {k: list(v) for k, v in (scripts or {}).items()}
        self.calls: list[str] = []  # schema names seen, for assertions

    def complete(
        self,
        *,
        system: str,
        messages: list[Msg],
        max_tokens: int,
        temperature: float = 0.0,
        stop: list[str] | None = None,
    ) -> LLMResponse:
        text = messages[-1].content if messages else ""
        return LLMResponse(text=f"[stub] {text[:80]}", model=self.name)

    def complete_json(
        self,
        *,
        system: str,
        messages: list[Msg],
        schema: type[T],
        max_tokens: int,
        temperature: float = 0.0,
    ) -> T:
        key = schema.__name__
        self.calls.append(key)
        queue = self.scripts.get(key)
        if queue:
            payload = queue.pop(0)
            return schema.model_validate(payload)
        return build_default(schema)


class LocalProvider(StubProvider):
    """Placeholder for local Gemma (Ollama/MLX), wired on the Mac in M5."""

    name = "local-gemma"
