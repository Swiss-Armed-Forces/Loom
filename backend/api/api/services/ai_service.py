"""Orchestrates AI context lifecycle for the AG-UI streaming endpoint."""

import json
import logging
from collections.abc import AsyncIterator, Sequence
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
    RunErrorEvent,
    RunFinishedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
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
    ModeId,
    ReasoningActivityEntry,
    ToolCallActivityEntry,
)
from common.ai_context.tool_models import ToolSource
from common.services.task_scheduling_service import TaskSchedulingService
from pydantic_ai.capabilities import Capability
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
    answer_text: str = ""
    activity: list[ReasoningActivityEntry | ToolCallActivityEntry] = field(
        default_factory=list
    )

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


def _extract_ask_user_question(tracker: _ActivityTracker) -> str:
    """Extract the question text from a pending ask_user tool call."""
    # pylint: disable=protected-access
    pending_names = tracker._pending_names
    pending_args = tracker._pending_args
    # pylint: enable=protected-access
    for tool_call_id, name in pending_names.items():
        if name != "ask_user":
            continue
        args_str = pending_args.get(tool_call_id, "")
        try:
            args = json.loads(args_str) if args_str else {}
        except json.JSONDecodeError:
            return ""
        return str(args.get("question", ""))
    return ""


async def _sanitise_agui_event_stream(
    stream: AsyncIterator[BaseEvent],
) -> AsyncIterator[BaseEvent]:
    """Ensure the AG-UI event stream satisfies the ``@ag-ui/client`` ``verifyEvents``
    state machine.

    Works around a known pydantic-ai bug (#3108) where the adapter can
    emit TEXT_MESSAGE_CONTENT after TEXT_MESSAGE_END without a new
    TEXT_MESSAGE_START.  This happens when a model interleaves text and
    thinking parts in a single response (text → thinking → text): the
    ``follows_text`` / ``followed_by_text`` flags on PartStartEvent /
    PartEndEvent can desynchronise, causing the adapter to skip the
    opening START event for the second text segment.

    The ``verifyEvents`` layer enforces strict pairing rules and rejects
    the entire run on any violation.  This wrapper patches the stream:

    - Injects a synthetic TEXT_MESSAGE_START before an orphaned
      TEXT_MESSAGE_CONTENT.
    - Before RUN_FINISHED, closes any text messages or tool calls
      that are still open.
    - Suppresses all events after a RUN_ERROR (the verify layer
      rejects any event once the error flag is set).

    A warning is logged for every synthetic event so the trigger can
    be identified in pod logs.

    Upstream references:
    - https://github.com/pydantic/pydantic-ai/issues/3108
      (reported, closed with a warning only — no event-ordering fix merged)
    - https://github.com/pydantic/pydantic-ai/pull/3206
      (attempted fix, closed without merging)
    """
    active_text_ids: set[str] = set()
    active_tool_call_ids: set[str] = set()
    errored = False

    async for event in stream:
        if errored:
            # verifyEvents rejects everything after RUN_ERROR — drop silently.
            continue

        match event:
            case TextMessageStartEvent(message_id=mid):
                active_text_ids.add(mid)
            case TextMessageContentEvent(message_id=mid) if mid not in active_text_ids:
                logger.warning(
                    "Orphaned TEXT_MESSAGE_CONTENT for message '%s' — "
                    "injecting synthetic TEXT_MESSAGE_START",
                    mid,
                )
                active_text_ids.add(mid)
                yield TextMessageStartEvent(message_id=mid)
            case TextMessageEndEvent(message_id=mid):
                active_text_ids.discard(mid)
            case ToolCallStartEvent(tool_call_id=tcid):
                active_tool_call_ids.add(tcid)
            case ToolCallEndEvent(tool_call_id=tcid):
                active_tool_call_ids.discard(tcid)
            case RunErrorEvent():
                errored = True
            case RunFinishedEvent():
                for orphan_id in list(active_text_ids):
                    logger.warning(
                        "Unclosed text message '%s' at RUN_FINISHED — "
                        "injecting synthetic TEXT_MESSAGE_END",
                        orphan_id,
                    )
                    yield TextMessageEndEvent(message_id=orphan_id)
                active_text_ids.clear()
                for tcid in list(active_tool_call_ids):
                    logger.warning(
                        "Unclosed tool call '%s' at RUN_FINISHED — "
                        "injecting synthetic TOOL_CALL_END",
                        tcid,
                    )
                    yield ToolCallEndEvent(tool_call_id=tcid)
                active_tool_call_ids.clear()

        yield event


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

    def set_mode(self, context_id: UUID, mode: ModeId) -> None:
        context = self.get_context(context_id)
        context.active_mode = mode
        self._ai_context_repository.save(context)

    async def run_agent_stream(
        self,
        context: AiContext,
        root_task_id: UUID,
        adapter: AGUIAdapter[AgentDeps],
        deps: AgentDeps,
        capabilities: Sequence[Capability[AgentDeps]] | None = None,
    ) -> AsyncIterator[BaseEvent]:
        """Run the agent and yield AG-UI events, then persist the question."""
        question = _extract_question(adapter.run_input.messages)
        logger.info("Running agent for context '%s'", context.id_)

        try:
            run_finished: RunFinishedEvent | None = None
            tracker = _ActivityTracker()

            async for event in _sanitise_agui_event_stream(
                adapter.run_stream(deps=deps, capabilities=capabilities)
            ):
                tracker.track(event)
                match event:
                    case TextMessageContentEvent(delta=delta):
                        tracker.answer_text += delta
                        yield event
                    case RunFinishedEvent():
                        run_finished = event
                    case _:
                        yield event

            activity = (
                _extract_activity_from_history(adapter.run_input.messages)
                + tracker.activity
            )

            # Skip citations when the run errored — the sanitiser already
            # yielded RUN_ERROR and suppressed further events, but citations
            # are appended here outside the sanitised stream.  The client's
            # verifyEvents would reject them after RUN_ERROR.
            citations: list[AiQuestionCitation] = []
            if run_finished is not None:
                citations = _collect_citations(deps.source_collector)
                for citation in citations:
                    yield CustomEvent(
                        name="citation",
                        value={
                            "file_id": str(citation.file_id),
                            "text": citation.text,
                        },
                    )
                yield run_finished

            if answer_text := (
                tracker.answer_text or _extract_ask_user_question(tracker)
            ):
                self._task_scheduling_service.dispatch_persist_question(
                    context_id=context.id_,
                    root_task_id=str(root_task_id),
                    question=AiQuestion(
                        question=question,
                        answer=answer_text,
                        citations=citations,
                        activity=activity,
                    ),
                )
        finally:
            self._task_scheduling_service.dispatch_persist_processing_done(
                context_id=context.id_,
                root_task_id=str(root_task_id),
            )
