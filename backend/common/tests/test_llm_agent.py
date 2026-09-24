import json
from typing import Any, Callable

import httpx
import pytest
from pydantic_ai import Agent
from pydantic_ai.models import Model, ModelRequestParameters
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.settings import ModelSettings

from common.llm.agent import _GENERAL_GUARDRAILS, _resolve_instructions, build_agent
from common.settings import (
    LLMClientSettings,
    LLMProvider,
    LLMSuggestQueriesSettings,
)

_CHAT_COMPLETION_STUB = {
    "id": "chatcmpl-stub",
    "object": "chat.completion",
    "created": 0,
    "model": "stub",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "ok"},
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
}


def _build_agent(client_settings: LLMClientSettings | None = None) -> Agent[None, str]:
    return build_agent(
        type(None), str, client_settings or LLMClientSettings(), "Do the thing."
    )


def _model(agent: Agent[None, str]) -> Model:
    model = agent.model
    assert isinstance(model, Model)
    return model


def _model_settings(agent: Agent[None, str]) -> ModelSettings:
    settings = agent.model_settings
    assert settings is not None and not callable(settings)
    return settings


def _resolve_request_params(agent: Agent[None, str]) -> ModelRequestParameters:
    """Resolve what the model would actually put on the request.

    ``prepare_request`` is where pydantic-ai translates the unified ``thinking`` setting
    into request parameters — and where it silently drops it when the model profile does
    not advertise ``supports_thinking``.
    """
    _, params = _model(agent).prepare_request(
        _model_settings(agent), ModelRequestParameters()
    )
    return params


def _request_body(client_settings: LLMClientSettings) -> dict[str, Any]:
    """The JSON body the built agent actually sends.

    One layer past ``prepare_request``: ``thinking`` only becomes ``reasoning_effort``
    inside ``OpenAIChatModel``, and the mapping is not an identity — ``False`` becomes
    the literal ``"none"``, not an omission.

    The transport is swapped on the client the provider already built, so everything the
    provider and profile decide is still exercised.
    """
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(200, json=_CHAT_COMPLETION_STUB)

    agent = _build_agent(client_settings)
    model = _model(agent)
    assert isinstance(model, OpenAIChatModel)
    model.client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    agent.run_sync("hello")

    return captured


def test_thinking_enabled_reaches_the_request() -> None:
    params = _resolve_request_params(_build_agent(LLMClientSettings(thinking=True)))

    assert params.thinking is True


def test_thinking_enabled_sends_reasoning_effort_medium() -> None:
    assert _request_body(LLMClientSettings(thinking=True))["reasoning_effort"] == (
        "medium"
    )


def test_thinking_disabled_sends_reasoning_effort_none() -> None:
    """Pydantic-ai maps `False` onto the literal `"none"`; pin it, it is not an
    omission.

    Every service Loom talks to has to accept that value for `thinking=False` to mean
    anything, which is why it is worth asserting on the wire rather than one layer up.
    """
    assert _request_body(LLMClientSettings(thinking=False))["reasoning_effort"] == (
        "none"
    )


def test_thinking_unset_sends_no_reasoning_effort() -> None:
    agent = _build_agent(LLMClientSettings(thinking=None))

    assert "thinking" not in _model_settings(agent)
    assert "reasoning_effort" not in _request_body(LLMClientSettings(thinking=None))


def test_suggest_queries_defaults_to_no_reasoning() -> None:
    """`suggest_queries` is off by default for a cost reason, so pin it.

    One invocation fans out `tool.suggest_queries.num_candidates` generations against an
    inference server that answers them one at a time. Asserted on the wire rather than on
    the literal: the default only means anything if `False` survives the profile layering
    and arrives as `reasoning_effort: "none"`.
    """
    assert _request_body(LLMSuggestQueriesSettings())["reasoning_effort"] == "none"


def test_hosted_openai_never_sends_reasoning_effort() -> None:
    """Only OpenAI's reasoning models accept `reasoning_effort`, and `OpenAIProvider`
    already knows which.

    Claiming support over it would send the field to a non-reasoning model and earn a
    400, so the setting stays inert there no matter what an operator configures.
    """
    body = _request_body(
        LLMClientSettings(provider=LLMProvider.OPENAI, thinking=True),
    )

    assert "reasoning_effort" not in body


@pytest.mark.parametrize(
    "instructions",
    [
        pytest.param("Do the thing.", id="static"),
        pytest.param(lambda: "Do the thing.", id="callable"),
    ],
)
def test_instructions_assemble_the_same_way(
    instructions: str | Callable[[], str],
) -> None:
    """Regression guard: the callable branch used to skip ``system_prompt`` entirely.

    Static and dynamic instructions must produce the same layout -- system prompt first,
    then the caller's instructions, then the guardrails last.
    """
    resolved = _resolve_instructions(
        LLMClientSettings(system_prompt="You are Loom."), instructions
    )()

    assert resolved.startswith("You are Loom.\n\nDo the thing.\n\n")
    assert resolved.endswith(_GENERAL_GUARDRAILS)


@pytest.mark.parametrize(
    "model",
    [
        "qwen3.5:9b",
        "llama3.3:70b",
        "gemma3:27b",
        "deepseek-r1:8b",
        "mistral-small",
        "mixtral:8x7b",
        "gpt-oss:20b",
    ],
)
def test_thinking_survives_every_family(model: str) -> None:
    """Regression guard for #307 via the profile layering.

    The gemma and gpt-oss family profiles set ``supports_thinking=False``. The provider
    merges the family *under* Loom's claim; the other order would make
    ``prepare_request`` strip ``thinking`` again for those two families.
    """
    params = _resolve_request_params(
        _build_agent(LLMClientSettings(thinking=True, model=model))
    )

    assert params.thinking is True
