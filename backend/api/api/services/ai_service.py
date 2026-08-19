"""Orchestrates AI context lifecycle for the AG-UI streaming endpoint."""

import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from uuid import UUID

from ag_ui.core import (
    AssistantMessage,
    BaseEvent,
    CustomEvent,
    ReasoningEndEvent,
    ReasoningMessage,
    ReasoningMessageContentEvent,
    ReasoningStartEvent,
    RunFinishedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
    ToolCallArgsEvent,
    ToolCallResultEvent,
    ToolCallStartEvent,
    ToolMessage,
    UserMessage,
)
from common.ai_context.ai_context_repository import (
    AiContext,
    AiContextNotFoundException,
    AiContextRepository,
    AiQuestion,
    AiQuestionCitation,
    CapabilityId,
    ReasoningActivityEntry,
    ToolCallActivityEntry,
)
from common.ai_context.tool_models import ToolSource
from common.services.task_scheduling_service import TaskSchedulingService
from pydantic_ai.ui.ag_ui import AGUIAdapter

from api.services.tool_service import AgentDeps

logger = logging.getLogger(__name__)


def _extract_question(messages: list) -> str:
    """Extract the text of the last user message from AG-UI messages."""
    for msg in reversed(messages):
        if not isinstance(msg, UserMessage):
            continue
        content = msg.content
        if isinstance(content, str):
            return content
        return " ".join(part.text for part in content if hasattr(part, "text"))
    return ""


@dataclass
class _ActivityTracker:
    """Accumulates reasoning and tool call events into ordered activity + tool call
    lists."""

    _pending_names: dict[str, str] = field(default_factory=dict)
    _pending_args: dict[str, str] = field(default_factory=dict)
    _reasoning_buffer: str = ""
    activity: list[ReasoningActivityEntry | ToolCallActivityEntry] = field(
        default_factory=list
    )

    @property
    def has_pending_tool_calls(self) -> bool:
        """True when tool calls started but never received a result (frontend tools)."""
        return bool(self._pending_names)

    def track(self, event: BaseEvent) -> None:
        match event:
            case ReasoningStartEvent():
                self._reasoning_buffer = ""
            case ReasoningMessageContentEvent(delta=delta):
                self._reasoning_buffer += delta
            case ReasoningEndEvent():
                if self._reasoning_buffer:
                    self.activity.append(
                        ReasoningActivityEntry(text=self._reasoning_buffer)
                    )
                self._reasoning_buffer = ""
            case ToolCallStartEvent(
                tool_call_id=tool_call_id, tool_call_name=tool_call_name
            ):
                self._pending_names[tool_call_id] = tool_call_name
                self._pending_args[tool_call_id] = ""
            case ToolCallArgsEvent(tool_call_id=tool_call_id, delta=delta):
                self._pending_args[tool_call_id] += delta
            case ToolCallResultEvent(tool_call_id=tool_call_id, content=content):
                name = self._pending_names.pop(tool_call_id, tool_call_id)
                args_str = self._pending_args.pop(tool_call_id, "")
                try:
                    parsed_input: dict = json.loads(args_str) if args_str else {}
                except json.JSONDecodeError:
                    parsed_input = {"_raw": args_str}
                self.activity.append(
                    ToolCallActivityEntry(
                        tool_name=name,
                        input=parsed_input,
                        output=content,
                    )
                )


@dataclass
class _TextBuffer:
    """Accumulates the last text segment so only that segment is emitted.

    Storing two sentinel events plus the text string is cheaper than keeping one event
    object per streamed token.
    """

    start: TextMessageStartEvent | None = None
    end: TextMessageEndEvent | None = None
    text: str = ""

    def new_segment(self, start_event: TextMessageStartEvent) -> None:
        self.start = start_event
        self.end = None
        self.text = ""

    def final_events(self) -> list[BaseEvent]:
        """Compact [start, content?, end] list for the buffered segment."""
        if self.start is None:
            return []
        result: list[BaseEvent] = [self.start]
        if self.text:
            result.append(
                TextMessageContentEvent(
                    message_id=self.start.message_id, delta=self.text
                )
            )
        if self.end is not None:
            result.append(self.end)
        return result


def _collect_citations(source_collector: list[ToolSource]) -> list[AiQuestionCitation]:
    """Deduplicate sources by file_id and return ordered citations."""
    seen: set[UUID] = set()
    result: list[AiQuestionCitation] = []
    for source in source_collector:
        if source.file_id not in seen:
            seen.add(source.file_id)
            result.append(AiQuestionCitation(file_id=source.file_id, text=source.text))
    return result


def _extract_activity_from_history(
    messages: list,
) -> list[ReasoningActivityEntry | ToolCallActivityEntry]:
    """Extract reasoning and tool call activity from message history since the last user
    turn.

    Frontend tools execute on the client and their results are sent back in the next
    request as AssistantMessage/ToolMessage pairs.  Reasoning messages from prior runs
    are also included.  We collect both here so the full interleaved activity can be
    persisted alongside the answer that arrives in the follow-up request.
    """
    last_user_idx = max(
        (i for i, m in enumerate(messages) if isinstance(m, UserMessage)),
        default=-1,
    )
    since_last_user = messages[last_user_idx + 1 :]

    tool_outputs: dict[str, str] = {
        m.tool_call_id: m.content for m in since_last_user if isinstance(m, ToolMessage)
    }

    result: list[ReasoningActivityEntry | ToolCallActivityEntry] = []
    for msg in since_last_user:
        match msg:
            case ReasoningMessage(content=content) if content:
                result.append(ReasoningActivityEntry(text=content))
            case AssistantMessage(tool_calls=tool_calls) if tool_calls:
                for tc in tool_calls:
                    try:
                        parsed_args: dict = (
                            json.loads(tc.function.arguments)
                            if tc.function.arguments
                            else {}
                        )
                    except json.JSONDecodeError:
                        parsed_args = {"_raw": tc.function.arguments}
                    result.append(
                        ToolCallActivityEntry(
                            tool_name=tc.function.name,
                            input=parsed_args,
                            output=tool_outputs.get(tc.id, ""),
                        )
                    )
    return result


class AiService:
    def __init__(
        self,
        ai_context_repository: AiContextRepository,
        task_scheduling_service: TaskSchedulingService,
    ) -> None:
        self._ai_context_repository = ai_context_repository
        self._task_scheduling_service = task_scheduling_service

    def create_context(self) -> AiContext:
        context = AiContext()
        self._ai_context_repository.save(context)
        return context

    def list_contexts(self) -> list[AiContext]:
        return self._ai_context_repository.list_all()

    def delete_context(self, context_id: UUID) -> bool:
        return self._ai_context_repository.delete_by_id(context_id)

    def get_context(self, context_id: UUID) -> AiContext:
        context = self._ai_context_repository.get_by_id(context_id)
        if context is None:
            raise AiContextNotFoundException(f"Context not found: {context_id}")
        return context

    def update_capabilities(
        self, context_id: UUID, capability: CapabilityId, active: bool
    ) -> None:
        context = self.get_context(context_id)
        capabilities = set(context.active_capabilities)
        if active:
            capabilities.add(capability)
        else:
            capabilities.discard(capability)
        context.active_capabilities = list(capabilities)
        self._ai_context_repository.save(context)

    async def run_agent_stream(
        self,
        context: AiContext,
        root_task_id: UUID,
        adapter: AGUIAdapter[AgentDeps],
        deps: AgentDeps,
    ) -> AsyncIterator[BaseEvent]:
        """Run the agent and yield AG-UI events, then persist the question."""
        question = _extract_question(adapter.run_input.messages)
        logger.info("Running agent for context '%s'", context.id_)

        try:
            run_finished: RunFinishedEvent | None = None
            tracker = _ActivityTracker()
            text_buf = _TextBuffer()

            async for event in adapter.run_stream(
                deps=deps,
            ):
                tracker.track(event)
                match event:
                    case TextMessageStartEvent():
                        text_buf.new_segment(event)
                    case TextMessageContentEvent(delta=delta):
                        text_buf.text += delta
                    case TextMessageEndEvent():
                        text_buf.end = event
                    case RunFinishedEvent():
                        run_finished = event
                    case _:
                        yield event

            # Only emit text events for the final run — intermediate runs
            # (with pending frontend tool calls) stay silent so the frontend
            # never creates a bubble that would need to be removed.
            if not tracker.has_pending_tool_calls:
                for text_event in text_buf.final_events():
                    yield text_event

            activity = (
                _extract_activity_from_history(adapter.run_input.messages)
                + tracker.activity
            )

            citations = _collect_citations(deps.source_collector)
            for citation in citations:
                yield CustomEvent(
                    name="citation",
                    value={"file_id": str(citation.file_id), "text": citation.text},
                )

            if run_finished is not None:
                yield run_finished

            if text_buf.text and not tracker.has_pending_tool_calls:
                self._task_scheduling_service.dispatch_persist_question(
                    context_id=context.id_,
                    root_task_id=str(root_task_id),
                    question=AiQuestion(
                        question=question,
                        answer=text_buf.text,
                        citations=citations,
                        activity=activity,
                    ),
                )
        finally:
            self._task_scheduling_service.dispatch_persist_processing_done(
                context_id=context.id_,
                root_task_id=str(root_task_id),
            )
