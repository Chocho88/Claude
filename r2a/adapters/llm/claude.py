"""ClaudeProvider — the Claude API path (M2).

Structured output uses **forced tool-use**: a single tool whose `input_schema`
is the stage's pydantic schema, with `tool_choice` pinning it. We validate the
returned input against the schema and retry once (feeding the error back) before
raising — this is the reliable JSON path per the claude-api guidance.

Notes locked in from the claude-api skill:
  * Default model is `claude-opus-4-8`.
  * `temperature` is rejected on Opus 4.8 — we never send it.
  * The client is injectable so the logic is unit-testable offline without the
    `anthropic` package or a network call.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError

from r2a.domain.common import LLMResponse, Msg

from .base import LLMProvider, T

_TOOL_NAME = "emit_result"


def _schema_for(schema: type[BaseModel]) -> dict:
    """JSON schema for the tool input, from the pydantic model."""
    return schema.model_json_schema()


def _first_tool_input(response: Any) -> dict:
    for block in response.content:
        if getattr(block, "type", None) == "tool_use":
            return block.input
    raise ValueError("Claude response contained no tool_use block")


class ClaudeProvider(LLMProvider):
    def __init__(self, model: str = "claude-opus-4-8", client: Any | None = None) -> None:
        self.model = model
        self.name = model
        if client is None:
            import anthropic  # imported lazily so the package import stays light

            client = anthropic.Anthropic()
        self._client = client

    def _messages(self, messages: list[Msg]) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in messages]

    def complete(
        self,
        *,
        system: str,
        messages: list[Msg],
        max_tokens: int,
        temperature: float = 0.0,
        stop: list[str] | None = None,
    ) -> LLMResponse:
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=self._messages(messages),
            stop_sequences=stop or None,
        )
        text = "".join(
            b.text for b in resp.content if getattr(b, "type", None) == "text"
        )
        usage = getattr(resp, "usage", None)
        return LLMResponse(
            text=text,
            model=getattr(resp, "model", self.model),
            input_tokens=getattr(usage, "input_tokens", 0) or 0,
            output_tokens=getattr(usage, "output_tokens", 0) or 0,
            stop_reason=getattr(resp, "stop_reason", None),
        )

    def complete_json(
        self,
        *,
        system: str,
        messages: list[Msg],
        schema: type[T],
        max_tokens: int,
        temperature: float = 0.0,
    ) -> T:
        tool = {
            "name": _TOOL_NAME,
            "description": "Return the structured result for this stage.",
            "input_schema": _schema_for(schema),
        }
        base = self._messages(messages)
        msgs = base
        last_error: ValidationError | None = None

        for attempt in range(2):
            resp = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                tools=[tool],
                tool_choice={"type": "tool", "name": _TOOL_NAME},
                messages=msgs,
            )
            data = _first_tool_input(resp)
            try:
                return schema.model_validate(data)
            except ValidationError as e:
                last_error = e
                # Retry once: append the error as a fresh user turn (no assistant
                # turn, so the message sequence stays valid).
                msgs = base + [
                    {
                        "role": "user",
                        "content": (
                            "Your previous tool input failed validation:\n"
                            f"{e}\nRe-emit valid input that satisfies the schema."
                        ),
                    }
                ]
        assert last_error is not None
        raise last_error
