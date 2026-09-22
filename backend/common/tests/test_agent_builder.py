from typing import Callable

from pydantic_ai import Agent
from pydantic_ai.models import Model, ModelRequestParameters
from pydantic_ai.settings import ModelSettings

from common.agent_builder import AgentBuilder
from common.settings import LLMClientSettings


def _build_agent(
    thinking: bool | None = None,
    instructions: str | Callable[[], str] | None = "Do the thing.",
    merge_system_messages: bool = False,
) -> Agent[None, str]:
    builder = AgentBuilder[None, str](type(None), str)
    return builder.build_agent(
        LLMClientSettings(thinking=thinking),
        instructions,
        merge_system_messages=merge_system_messages,
    )


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
    model = agent.model
    assert isinstance(model, Model)
    _, params = model.prepare_request(_model_settings(agent), ModelRequestParameters())
    return params


def test_thinking_enabled_reaches_the_request() -> None:
    params = _resolve_request_params(_build_agent(thinking=True))

    assert params.thinking is True


def test_thinking_disabled_reaches_the_request() -> None:
    params = _resolve_request_params(_build_agent(thinking=False))

    assert params.thinking is False


def test_thinking_unset_sends_no_reasoning_effort() -> None:
    agent = _build_agent(thinking=None)

    assert "thinking" not in _model_settings(agent)
    assert _resolve_request_params(agent).thinking is None


def test_callable_instructions_still_apply_merge_system_messages() -> None:
    """Regression guard: the callable branch used to pass ``merge_system_messages`` into
    the ``tool_timeout`` parameter, silently leaving the profile untouched."""
    agent = _build_agent(
        instructions=lambda: "Do the thing.", merge_system_messages=True
    )

    model = agent.model
    assert isinstance(model, Model)
    assert model.profile.get("openai_chat_supports_multiple_system_messages") is False
