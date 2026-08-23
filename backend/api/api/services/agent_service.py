"""Builds pydantic-ai Agent instances configured with LLM settings and tools."""

from datetime import datetime, timezone
from typing import Any, NamedTuple

from common.ai_context.ai_context_repository import AiContext
from common.settings import settings
from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.capabilities import Capability
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.profiles.openai import OpenAIModelProfile
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings
from pydantic_ai.tools import DeferredToolRequests

from api.services.tool_service import AgentDeps, ToolService


def _build_instructions() -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return (
        "You are an AI assistant helping users explore and understand "
        "their indexed documents. "
        f"The current date and time is {now}. "
        "Load capabilities as needed — their descriptions and "
        "instructions tell you what each provides and how to use them. "
        "Ask clarifying questions rather than assuming. "
        "You may use Markdown in your responses. "
        "Prefer plain prose for short answers."
    )


class PreparedAgent(NamedTuple):
    agent: Agent[AgentDeps, Any]
    deps: AgentDeps
    capabilities: list[Capability[AgentDeps]]


class AgentService:
    def __init__(self, tool_service: ToolService) -> None:
        self._tool_service = tool_service
        provider = OpenAIProvider(
            openai_client=AsyncOpenAI(
                base_url=str(settings.llm.agent.endpoint),
                api_key=settings.llm.agent.api_key,
            )
        )
        self._model = OpenAIChatModel(
            settings.llm.agent.model,
            provider=provider,
            profile=self._build_model_profile(),
        )
        self._model_settings = self._build_model_settings()
        self._agent: Agent[AgentDeps, str | DeferredToolRequests] = Agent(
            model=self._model,
            deps_type=AgentDeps,
            output_type=[str, DeferredToolRequests],
            instructions=_build_instructions,
            model_settings=self._model_settings,
        )

    @staticmethod
    def _build_model_profile() -> OpenAIModelProfile:
        profile = OpenAIModelProfile()
        if settings.llm.agent.merge_system_messages:
            # Backends that reject multiple leading system messages (vLLM/SGLang
            # serving Qwen) also reject system messages mid-conversation — e.g.
            # the tool-availability announcement injected after load_capability.
            profile["openai_chat_supports_multiple_system_messages"] = False
            profile["supports_inline_system_prompts"] = False
        return profile

    @staticmethod
    def _build_model_settings() -> ModelSettings:
        result: ModelSettings = {}
        if settings.llm.agent.temperature is not None:
            result["temperature"] = settings.llm.agent.temperature
        if settings.llm.agent.max_tokens is not None:
            result["max_tokens"] = settings.llm.agent.max_tokens
        if settings.llm.agent.extra_headers is not None:
            result["extra_headers"] = settings.llm.agent.extra_headers
        if settings.llm.agent.extra_body is not None:
            result["extra_body"] = settings.llm.agent.extra_body
        return result

    def build_agent(self, context: AiContext) -> PreparedAgent:
        return PreparedAgent(
            agent=self._agent,
            deps=AgentDeps(
                context=context,
                active_mode=context.active_mode,
            ),
            capabilities=self._tool_service.capabilities_for_mode(context.active_mode),
        )
