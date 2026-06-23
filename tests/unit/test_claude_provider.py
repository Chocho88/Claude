"""ClaudeProvider logic, exercised offline with a fake Anthropic client."""

from __future__ import annotations

import pytest

from r2a.adapters.llm.claude import _TOOL_NAME, ClaudeProvider
from r2a.domain.common import Msg
from r2a.pipeline.schemas import PlanProposal


class _Block:
    def __init__(self, type, **kw):
        self.type = type
        for k, v in kw.items():
            setattr(self, k, v)


class _Usage:
    input_tokens = 11
    output_tokens = 7


class _Resp:
    def __init__(self, content):
        self.content = content
        self.usage = _Usage()
        self.model = "claude-opus-4-8"
        self.stop_reason = "tool_use"


class _Messages:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


class _Client:
    def __init__(self, responses):
        self.messages = _Messages(responses)


def _tool_resp(data: dict) -> _Resp:
    return _Resp([_Block("tool_use", name=_TOOL_NAME, input=data)])


def test_complete_json_forces_the_tool_and_validates():
    client = _Client([_tool_resp({"task": "ideas", "scope": "import"})])
    provider = ClaudeProvider(client=client)

    out = provider.complete_json(
        system="sys",
        messages=[Msg(role="user", content="plan this")],
        schema=PlanProposal,
        max_tokens=500,
    )
    assert isinstance(out, PlanProposal)
    call = client.messages.calls[0]
    assert call["tool_choice"] == {"type": "tool", "name": _TOOL_NAME}
    assert call["tools"][0]["input_schema"]["type"] == "object"
    assert "temperature" not in call  # removed on Opus 4.8


def test_complete_json_retries_once_on_invalid_then_succeeds():
    client = _Client([
        _tool_resp({"task": "not-a-real-task"}),   # fails enum validation
        _tool_resp({"task": "summarize", "scope": "import"}),
    ])
    provider = ClaudeProvider(client=client)

    out = provider.complete_json(
        system="sys",
        messages=[Msg(role="user", content="plan this")],
        schema=PlanProposal,
        max_tokens=500,
    )
    assert out.task.value == "summarize"
    assert len(client.messages.calls) == 2
    # the retry fed the validation error back as a user turn
    assert "failed validation" in client.messages.calls[1]["messages"][-1]["content"]


def test_complete_json_raises_after_two_failures():
    client = _Client([_tool_resp({"task": "bad"}), _tool_resp({"task": "worse"})])
    provider = ClaudeProvider(client=client)
    with pytest.raises(Exception):
        provider.complete_json(
            system="s",
            messages=[Msg(role="user", content="x")],
            schema=PlanProposal,
            max_tokens=200,
        )


def test_complete_returns_text_and_usage():
    client = _Client([_Resp([_Block("text", text="hello world")])])
    provider = ClaudeProvider(client=client)
    resp = provider.complete(system="s", messages=[Msg(role="user", content="hi")], max_tokens=50)
    assert resp.text == "hello world"
    assert resp.input_tokens == 11 and resp.output_tokens == 7
