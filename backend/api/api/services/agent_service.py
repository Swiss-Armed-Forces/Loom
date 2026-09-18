"""Builds pydantic-ai Agent instances configured with LLM settings and tools."""

from datetime import datetime, timezone
from typing import NamedTuple

from common.agent_builder import AgentBuilder
from common.ai_context.ai_context_repository import AiContext
from common.settings import settings
from pydantic_ai import Agent
from pydantic_ai.capabilities import Capability
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
    agent: Agent[AgentDeps, str | DeferredToolRequests]
    deps: AgentDeps
    capabilities: list[Capability[AgentDeps]]


class AgentService:
    def __init__(self, tool_service: ToolService) -> None:
        self._tool_service = tool_service
        self._agent: Agent[AgentDeps, str | DeferredToolRequests] = AgentBuilder(
            AgentDeps, [str, DeferredToolRequests]
        ).build_agent(
            settings.llm.agent,
            _build_instructions,
            settings.llm.agent.tool_timeout,
            settings.llm.agent.merge_system_messages,
        )

    def build_prepared_agent(self, context: AiContext) -> PreparedAgent:
        return PreparedAgent(
            agent=self._agent,
            deps=AgentDeps(
                context=context,
                active_mode=context.active_mode,
            ),
            capabilities=self._tool_service.capabilities_for_mode(context.active_mode),
        )
