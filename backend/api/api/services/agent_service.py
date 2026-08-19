"""Builds pydantic-ai Agent instances configured with LLM settings and tools."""

from typing import Any, NamedTuple

from common.ai_context.ai_context_repository import AiContext
from common.settings import settings
from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.profiles.openai import OpenAIModelProfile
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings
from pydantic_ai.tools import DeferredToolRequests

from api.services.tool_service import AgentDeps, ToolService


class PreparedAgent(NamedTuple):
    agent: Agent[AgentDeps, Any]
    deps: AgentDeps


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
            instructions=(
                "You are an AI assistant helping users explore and understand "
                "their indexed documents. "
                "Before answering, use your tools to retrieve relevant "
                "information rather than guessing. "
                "If the user refers to something they are looking at in the "
                "interface, check the UI state "
                "to understand their context. If a question is unclear or you "
                "need to know their preference, ask a clarifying question "
                "rather than assuming. "
                "Whenever the user wants to find or search for documents, "
                "call suggest_queries to generate a precise query string, "
                "then apply it — either via set_search_query to update the "
                "search view, or via execute_query in deep search mode. "
                "When a question requires deep understanding across many "
                "documents — such as cross-referencing, comparing findings, or "
                "building a comprehensive picture from multiple sources — "
                "request the 'research_mode' capability before attempting to "
                "answer. Tasks like summarising a single document do not "
                "require research mode. "
                "You may use Markdown in your responses: wrap code or "
                "structured text in ```triple backticks```, "
                "use **bold** for emphasis, bullet lists for enumerations, "
                "and headers sparingly. "
                "Prefer plain prose for short answers."
            ),
            model_settings=self._model_settings,
            capabilities=tool_service.capabilities,
        )

    @staticmethod
    def _build_model_profile() -> OpenAIModelProfile:
        profile = OpenAIModelProfile()
        if settings.llm.agent.merge_system_messages:
            profile["openai_chat_supports_multiple_system_messages"] = False
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
                active_capabilities=set(context.active_capabilities),
            ),
        )
