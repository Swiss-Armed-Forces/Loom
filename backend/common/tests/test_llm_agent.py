import json
from typing import Any, Callable

import httpx
import httpx2
import pytest
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models import Model, ModelRequestParameters
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.system_one import SystemOneModel
from pydantic_ai.output import OutputSpec
from pydantic_ai.providers.system_one import SystemOneProvider
from pydantic_ai.settings import ModelSettings
from pydantic_ai.tools import DeferredToolRequests

from common.llm.agent import (
    _GENERAL_GUARDRAILS,
    _resolve_instructions,
    build_agent,
    build_system_one_agent,
)
from common.llm.return_types import Relevance, RerankResult
from common.settings import (
    LLMClientSettings,
    LLMProvider,
    LLMSuggestQueriesSettings,
    LLMSystemOneSettings,
)


class _StructuredOutput(BaseModel):
    """Stands in for `SummarizationResult` and its siblings.

    One field holding one string, which is the shape every structured client asks for.
    """

    text: str


def _stub_message(request_body: dict[str, Any]) -> dict[str, Any]:
    """Answer in whichever channel the request opened.

    A run answered in the wrong channel retries and then raises, burying the captured
    body under an exception, so the stub reads the request rather than guessing:
    `response_format` asks for the JSON in the message content, a `tools` list asks for
    a call to the output tool. The tool's name is taken off the request too -- what is
    under test is which channel was opened, not what pydantic-ai names its output tool.
    """
    if "response_format" in request_body:
        return {"role": "assistant", "content": '{"text": "ok"}'}

    if tools := request_body.get("tools"):
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call-stub",
                    "type": "function",
                    "function": {
                        "name": tools[0]["function"]["name"],
                        "arguments": '{"text": "ok"}',
                    },
                }
            ],
        }

    return {"role": "assistant", "content": "ok"}


def _chat_completion_stub(request_body: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": "chatcmpl-stub",
        "object": "chat.completion",
        "created": 0,
        "model": "stub",
        "choices": [
            {
                "index": 0,
                "message": _stub_message(request_body),
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }


def _build_agent(
    client_settings: LLMClientSettings | None = None,
    output_format: OutputSpec[Any] = str,
) -> Agent[None, Any]:
    return build_agent(
        type(None),
        output_format,
        client_settings or LLMClientSettings(),
        "Do the thing.",
    )


def _model(agent: Agent[None, Any]) -> Model:
    model = agent.model
    assert isinstance(model, Model)
    return model


def _model_settings(agent: Agent[None, Any]) -> ModelSettings:
    settings = agent.model_settings
    assert settings is not None and not callable(settings)
    return settings


def _resolve_request_params(agent: Agent[None, Any]) -> ModelRequestParameters:
    """Resolve what the model would actually put on the request.

    ``prepare_request`` is where pydantic-ai translates the unified ``thinking`` setting
    into request parameters — and where it silently drops it when the model profile does
    not advertise ``supports_thinking``.
    """
    _, params = _model(agent).prepare_request(
        _model_settings(agent), ModelRequestParameters()
    )
    return params


def _request_body(
    client_settings: LLMClientSettings,
    output_format: OutputSpec[Any] = str,
) -> dict[str, Any]:
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
        return httpx.Response(200, json=_chat_completion_stub(captured))

    agent = _build_agent(client_settings, output_format)
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
    """Static and dynamic instructions must produce the same layout -- system prompt
    first, then the caller's instructions, then the guardrails last."""
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
    """``thinking`` survives every family because of the profile layering.

    The gemma and gpt-oss family profiles set ``supports_thinking=False``. The provider
    merges the family *under* Loom's claim; the other order would make
    ``prepare_request`` strip ``thinking`` again for those two families.
    """
    params = _resolve_request_params(
        _build_agent(LLMClientSettings(thinking=True, model=model))
    )

    assert params.thinking is True


_PRODUCTION_MODEL = "qwen3.8:27b"
_DEVELOPMENT_MODEL = "qwen2.5:0.5b"


def test_a_small_model_gets_structured_output_as_a_grammar() -> None:
    """The whole point of deriving the mode in the provider.

    The output type goes in unmarked and the profile turns it into `response_format`,
    with no branch in `build_agent` and no setting behind it. Asserted on the wire
    because `default_structured_output_mode` only means anything if the schema's `auto`
    mode survives `build_agent` all the way to `prepare_request`.
    """
    body = _request_body(LLMClientSettings(model=_DEVELOPMENT_MODEL), _StructuredOutput)

    assert body["response_format"]["type"] == "json_schema"
    assert "tools" not in body


def test_the_production_model_gets_structured_output_as_a_tool() -> None:
    """The same unmarked type resolves the other way on weights that can carry a call.

    With the test above, this is the pair proving the profile alone decides: one output
    type, one `build_agent`, two modes decided by the model.
    """
    body = _request_body(LLMClientSettings(model=_PRODUCTION_MODEL), _StructuredOutput)

    assert "response_format" not in body
    assert len(body["tools"]) == 1


@pytest.mark.parametrize("model", [_DEVELOPMENT_MODEL, _PRODUCTION_MODEL])
def test_a_text_agent_is_untouched_by_the_parameter_floor(model: str) -> None:
    """A bare `str` builds a text schema, whose mode is never `auto`.

    No profile key can reach it, which is why `rag_hyde` and `rag_synthesize` need no
    special case however small the model they are pointed at.
    """
    body = _request_body(LLMClientSettings(model=model))

    assert "response_format" not in body
    assert "tools" not in body


def test_the_chat_agents_deferred_output_stays_text() -> None:
    """`[str, DeferredToolRequests]` builds a text schema on its own.

    No output marker is wrapped around it, so `build_agent` needs no special case for a
    `DeferredToolRequests` in the output list. The small model is deliberate -- it is
    the one that would flip if the resolution ever did reach this schema.
    """
    body = _request_body(
        LLMClientSettings(model=_DEVELOPMENT_MODEL), [str, DeferredToolRequests]
    )

    assert "response_format" not in body


_SYSTEM_ONE_INSTRUCTIONS = "How relevant is the text to the question?"


def _system_one_request_body(
    client_settings: LLMSystemOneSettings | None = None,
) -> dict[str, Any]:
    """The JSON body a built decision agent actually sends.

    Wire level for the same reason the chat helper above is: what reaches
    `POST /v1/systemone` is the only place the absent settings and the absent guardrail
    are observable, and `instructions` is assembled by pydantic-ai rather than stored
    as the string that was passed in.
    """
    captured: dict[str, Any] = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        captured.update(json.loads(request.content))
        questions = captured["questions"]
        return httpx2.Response(
            200,
            json={
                "model": "stub",
                "answers": {
                    name: {
                        "type": "score",
                        "score": 0.0,
                        "confidence": 1.0,
                        "probabilities": {
                            str(level): 1.0 if level == 0 else 0.0
                            for level in range(len(question["criteria"]))
                        },
                    }
                    for name, question in questions.items()
                },
                "usage": {"input_tokens": 1, "output_tokens": 1},
            },
        )

    agent = build_system_one_agent(
        RerankResult,
        client_settings or LLMSystemOneSettings(),
        _SYSTEM_ONE_INSTRUCTIONS,
    )
    assert isinstance(_model(agent), SystemOneModel)

    # `override` rather than reaching into the client the provider built: httpx2 exposes
    # no public seam for swapping a transport. What is under test travels on the agent
    # rather than on the model -- the questions come from the output type and the
    # instructions, and `temperature` from the agent's `model_settings` -- so a stand-in
    # model carries all of it. That the built model is a `SystemOneModel` pointed at the
    # configured endpoint is asserted above and in `test_llm_provider.py`.
    stub = SystemOneModel(
        "stub",
        provider=SystemOneProvider(
            base_url="http://decisions.invalid/v1/",
            api_key="stub",
            http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handler)),
        ),
    )
    with agent.override(model=stub):
        agent.run_sync("hello")

    return captured


def test_a_system_one_agent_carries_only_the_request_settings() -> None:
    """The keys `POST /v1/systemone` takes, and nothing else.

    `max_tokens` and `thinking` describe generated text and a decision model writes
    none, so they are absent from `LLMSystemOneSettings` entirely. This pins that no
    later refactor reintroduces them by routing the chat builder's settings here.
    """
    agent = build_system_one_agent(
        RerankResult,
        LLMSystemOneSettings(
            temperature=0.2,
            extra_headers={"X-Tenant": "loom"},
            extra_body={"nucleus": 1},
        ),
        _SYSTEM_ONE_INSTRUCTIONS,
    )

    assert dict(_model_settings(agent)) == {
        "temperature": 0.2,
        "extra_headers": {"X-Tenant": "loom"},
        "extra_body": {"nucleus": 1},
    }


def test_an_unset_system_one_setting_is_not_sent() -> None:
    """None means "leave the service its own default", not "send a null"."""
    assert "temperature" not in _system_one_request_body()


def test_a_configured_temperature_reaches_the_request() -> None:
    body = _system_one_request_body(LLMSystemOneSettings(temperature=0.2))

    assert body["temperature"] == 0.2


def test_a_system_one_agent_gets_no_guardrails() -> None:
    """The one difference from `build_agent` that a refactor would undo silently.

    A model whose entire output is a choice among an enum's members has no instruction-
    following surface for a document to hijack, so the guardrail is deliberately absent
    rather than forgotten.
    """
    instructions = _system_one_request_body()["questions"]["rank"]["instructions"]

    assert _GENERAL_GUARDRAILS not in json.dumps(instructions)
    assert _SYSTEM_ONE_INSTRUCTIONS in json.dumps(instructions)


def test_the_output_type_is_the_prompt() -> None:
    """`Relevance`'s member docstrings are the whole rubric the service is given.

    Nothing in Loom writes the 0-5 scale out, so an edit to those docstrings is an edit
    to reranking -- and a member losing its docstring silently demotes the question from
    a scored rubric to a pick-one of bare digits.
    """
    question = _system_one_request_body()["questions"]["rank"]

    # A scored rubric, not a pick-one: pydantic-ai demotes the question to a choice of
    # bare digits the moment the levels stop being contiguous from zero or one of them
    # loses its description, and the answer is then arbitrary with nothing to show for
    # it on the wire but the missing descriptions.
    assert question["type"] == "score"
    assert len(question["criteria"]) == len(Relevance)
    assert (
        "completely irrelevant" in question["criteria"][Relevance.COMPLETELY_IRRELEVANT]
    )
    assert "very relevant" in question["criteria"][Relevance.VERY_RELEVANT]
