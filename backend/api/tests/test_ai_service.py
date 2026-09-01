"""Unit tests for the pure helper functions in api/services/ai_service.py."""

import asyncio
import json
from uuid import uuid4

from ag_ui.core import (
    AssistantMessage,
    BaseEvent,
    FunctionCall,
    ReasoningEndEvent,
    ReasoningMessage,
    ReasoningMessageContentEvent,
    ReasoningStartEvent,
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
    ToolCall,
    ToolCallArgsEvent,
    ToolCallResultEvent,
    ToolCallStartEvent,
    ToolMessage,
    UserMessage,
)
from common.ai_context.ai_context_repository import (
    AiQuestionCitation,
    ReasoningActivityEntry,
    ToolCallActivityEntry,
)
from common.ai_context.tool_models import ToolSource

from api.services.ai_service import (
    _ActivityTracker,
    _collect_citations,
    _extract_activity_from_history,
    _extract_question,
    _sanitise_agui_event_stream,
)

# ---------------------------------------------------------------------------
# _extract_question
# ---------------------------------------------------------------------------


def test_extract_question_empty_list():
    assert _extract_question([]) == ""


def test_extract_question_single_user_string():
    msg = UserMessage(id="u1", role="user", content="what is this?")
    assert _extract_question([msg]) == "what is this?"


def test_extract_question_last_user_message_wins():
    msg1 = UserMessage(id="u1", role="user", content="first")
    msg2 = UserMessage(id="u2", role="user", content="second")
    assert _extract_question([msg1, msg2]) == "second"


def test_extract_question_structured_content():
    msg = UserMessage.model_validate(
        {
            "id": "u1",
            "role": "user",
            "content": [
                {"type": "text", "text": "hello"},
                {"type": "text", "text": "world"},
            ],
        }
    )
    assert _extract_question([msg]) == "hello world"


# ---------------------------------------------------------------------------
# _ActivityTracker
# ---------------------------------------------------------------------------


def test_tracker_tool_call_lifecycle():
    tracker = _ActivityTracker()
    tc_id = "tc-1"

    tracker.track(ToolCallStartEvent(tool_call_id=tc_id, tool_call_name="search"))

    tracker.track(ToolCallArgsEvent(tool_call_id=tc_id, delta='{"q":'))
    tracker.track(ToolCallArgsEvent(tool_call_id=tc_id, delta='"hello"}'))

    tracker.track(
        ToolCallResultEvent(tool_call_id=tc_id, message_id="msg1", content="the result")
    )

    assert len(tracker.activity) == 1
    entry = tracker.activity[0]
    assert isinstance(entry, ToolCallActivityEntry)
    assert entry.tool_name == "search"
    assert entry.input == {"q": "hello"}
    assert entry.output == "the result"


def test_tracker_reasoning_lifecycle():
    tracker = _ActivityTracker()
    msg_id = "msg-r"

    tracker.track(ReasoningStartEvent(message_id=msg_id))
    tracker.track(ReasoningMessageContentEvent(message_id=msg_id, delta="I think "))
    tracker.track(ReasoningMessageContentEvent(message_id=msg_id, delta="therefore"))
    tracker.track(ReasoningEndEvent(message_id=msg_id))

    assert len(tracker.activity) == 1
    entry = tracker.activity[0]
    assert isinstance(entry, ReasoningActivityEntry)
    assert entry.text == "I think therefore"


def test_tracker_empty_reasoning_produces_no_entry():
    tracker = _ActivityTracker()
    msg_id = "msg-r"

    tracker.track(ReasoningStartEvent(message_id=msg_id))
    tracker.track(ReasoningEndEvent(message_id=msg_id))

    assert tracker.activity == []


def test_tracker_mixed_tool_and_reasoning():
    tracker = _ActivityTracker()

    tracker.track(ReasoningStartEvent(message_id="r1"))
    tracker.track(ReasoningMessageContentEvent(message_id="r1", delta="thought"))
    tracker.track(ReasoningEndEvent(message_id="r1"))

    tracker.track(ToolCallStartEvent(tool_call_id="tc1", tool_call_name="lookup"))
    tracker.track(ToolCallArgsEvent(tool_call_id="tc1", delta="{}"))
    tracker.track(
        ToolCallResultEvent(tool_call_id="tc1", message_id="msg2", content="found it")
    )

    assert len(tracker.activity) == 2
    assert isinstance(tracker.activity[0], ReasoningActivityEntry)
    assert isinstance(tracker.activity[1], ToolCallActivityEntry)


# ---------------------------------------------------------------------------
# _collect_citations
# ---------------------------------------------------------------------------


def test_collect_citations_empty():
    assert not _collect_citations([])


def test_collect_citations_unique_file_ids():
    fid1, fid2 = uuid4(), uuid4()
    sources = [
        ToolSource(file_id=fid1, text="snippet one"),
        ToolSource(file_id=fid2, text="snippet two"),
    ]
    result = _collect_citations(sources)
    assert len(result) == 2
    assert result[0] == AiQuestionCitation(file_id=fid1, text="snippet one")
    assert result[1] == AiQuestionCitation(file_id=fid2, text="snippet two")


def test_collect_citations_deduplicates_by_file_id():
    fid = uuid4()
    sources = [
        ToolSource(file_id=fid, text="first"),
        ToolSource(file_id=fid, text="second"),
    ]
    result = _collect_citations(sources)
    assert len(result) == 1
    assert result[0].file_id == fid
    assert result[0].text == "first"


def test_collect_citations_preserves_order():
    fids = [uuid4() for _ in range(3)]
    sources = [ToolSource(file_id=f, text=f"t{i}") for i, f in enumerate(fids)]
    result = _collect_citations(sources)
    assert [r.file_id for r in result] == fids


# ---------------------------------------------------------------------------
# _extract_activity_from_history
# ---------------------------------------------------------------------------


def test_extract_activity_from_history_empty():
    assert not _extract_activity_from_history([])


def test_extract_activity_messages_before_last_user_ignored():
    earlier_user = UserMessage(id="u0", role="user", content="earlier question")
    reasoning = ReasoningMessage(id="r0", role="reasoning", content="early thought")
    last_user = UserMessage(id="u1", role="user", content="current question")

    result = _extract_activity_from_history([earlier_user, reasoning, last_user])
    assert not result


def test_extract_activity_tool_calls_after_last_user():
    user = UserMessage(id="u1", role="user", content="find something")
    tc = ToolCall(
        id="tc1",
        function=FunctionCall(name="search", arguments=json.dumps({"q": "docs"})),
    )
    assistant = AssistantMessage(
        id="a1", role="assistant", content=None, tool_calls=[tc]
    )
    tool_msg = ToolMessage(
        id="t1", role="tool", content="found docs", tool_call_id="tc1"
    )

    result = _extract_activity_from_history([user, assistant, tool_msg])

    assert len(result) == 1
    entry = result[0]
    assert isinstance(entry, ToolCallActivityEntry)
    assert entry.tool_name == "search"
    assert entry.input == {"q": "docs"}
    assert entry.output == "found docs"


def test_extract_activity_reasoning_message_after_last_user():
    user = UserMessage(id="u1", role="user", content="question")
    reasoning = ReasoningMessage(
        id="r1", role="reasoning", content="some internal reasoning"
    )

    result = _extract_activity_from_history([user, reasoning])

    assert len(result) == 1
    assert isinstance(result[0], ReasoningActivityEntry)
    assert result[0].text == "some internal reasoning"


def test_extract_activity_mixed_reasoning_and_tool_calls():
    user = UserMessage(id="u1", role="user", content="question")
    reasoning = ReasoningMessage(id="r1", role="reasoning", content="thinking")
    tc = ToolCall(
        id="tc1",
        function=FunctionCall(name="lookup", arguments="{}"),
    )
    assistant = AssistantMessage(
        id="a1", role="assistant", content=None, tool_calls=[tc]
    )
    tool_msg = ToolMessage(id="t1", role="tool", content="result", tool_call_id="tc1")

    result = _extract_activity_from_history([user, reasoning, assistant, tool_msg])

    assert len(result) == 2
    assert isinstance(result[0], ReasoningActivityEntry)
    assert result[0].text == "thinking"
    assert isinstance(result[1], ToolCallActivityEntry)
    assert result[1].tool_name == "lookup"


# ---------------------------------------------------------------------------
# _sanitise_agui_event_stream
# ---------------------------------------------------------------------------


async def _to_list(stream):
    return [event async for event in stream]


async def _from_list(events):
    for event in events:
        yield event


def _run(events: list[BaseEvent]) -> list[BaseEvent]:
    """Feed *events* through the sanitiser and return the output list."""
    return asyncio.run(_to_list(_sanitise_agui_event_stream(_from_list(events))))


def _types(events: list[BaseEvent]) -> list[str]:
    return [e.type.value if hasattr(e.type, "value") else str(e.type) for e in events]


def test_sanitiser_passthrough_clean_stream():
    """A well-formed stream passes through unchanged."""
    events = [
        RunStartedEvent(thread_id="t", run_id="r"),
        TextMessageStartEvent(message_id="m1"),
        TextMessageContentEvent(message_id="m1", delta="hi"),
        TextMessageEndEvent(message_id="m1"),
        RunFinishedEvent(thread_id="t", run_id="r"),
    ]
    result = _run(events)
    assert _types(result) == _types(events)


def test_sanitiser_injects_start_for_orphaned_content():
    """Orphaned TEXT_MESSAGE_CONTENT gets a synthetic START injected."""
    events = [
        RunStartedEvent(thread_id="t", run_id="r"),
        TextMessageContentEvent(message_id="m1", delta="orphan"),
        TextMessageEndEvent(message_id="m1"),
        RunFinishedEvent(thread_id="t", run_id="r"),
    ]
    result = _run(events)
    types = _types(result)
    assert types[1] == "TEXT_MESSAGE_START"
    assert types[2] == "TEXT_MESSAGE_CONTENT"
    assert result[1].message_id == "m1"


def test_sanitiser_closes_unclosed_text_at_run_finished():
    """Unclosed text message gets a synthetic END before RUN_FINISHED."""
    events = [
        RunStartedEvent(thread_id="t", run_id="r"),
        TextMessageStartEvent(message_id="m1"),
        TextMessageContentEvent(message_id="m1", delta="hi"),
        # Missing TextMessageEndEvent
        RunFinishedEvent(thread_id="t", run_id="r"),
    ]
    result = _run(events)
    types = _types(result)
    assert types[-2] == "TEXT_MESSAGE_END"
    assert types[-1] == "RUN_FINISHED"
    assert result[-2].message_id == "m1"


def test_sanitiser_closes_unclosed_tool_call_at_run_finished():
    """Unclosed tool call gets a synthetic END before RUN_FINISHED."""
    events = [
        RunStartedEvent(thread_id="t", run_id="r"),
        ToolCallStartEvent(tool_call_id="tc1", tool_call_name="search"),
        # Missing ToolCallEndEvent
        RunFinishedEvent(thread_id="t", run_id="r"),
    ]
    result = _run(events)
    types = _types(result)
    assert types[-2] == "TOOL_CALL_END"
    assert types[-1] == "RUN_FINISHED"
    assert result[-2].tool_call_id == "tc1"


def test_sanitiser_suppresses_events_after_run_error():
    """All events after RUN_ERROR are dropped."""
    events = [
        RunStartedEvent(thread_id="t", run_id="r"),
        RunErrorEvent(message="boom"),
        TextMessageStartEvent(message_id="m1"),
        TextMessageContentEvent(message_id="m1", delta="should be dropped"),
        RunFinishedEvent(thread_id="t", run_id="r"),
    ]
    result = _run(events)
    types = _types(result)
    assert "TEXT_MESSAGE_START" not in types
    assert "TEXT_MESSAGE_CONTENT" not in types
    assert "RUN_FINISHED" not in types
    assert types == ["RUN_STARTED", "RUN_ERROR"]


def test_sanitiser_handles_full_orphan_scenario():
    """Simulate the pydantic-ai #3108 bug: text -> thinking -> orphaned text.

    The adapter emits END for text1, then reasoning, then CONTENT for text2 without a
    START — followed by RUN_FINISHED without an END.
    """
    events = [
        RunStartedEvent(thread_id="t", run_id="r"),
        TextMessageStartEvent(message_id="m1"),
        TextMessageContentEvent(message_id="m1", delta="hello"),
        TextMessageEndEvent(message_id="m1"),
        # Orphaned content (no START for m1 after its END)
        TextMessageContentEvent(message_id="m1", delta="world"),
        # No END for the re-opened m1
        RunFinishedEvent(thread_id="t", run_id="r"),
    ]
    result = _run(events)
    types = _types(result)

    # Should have: START, CONTENT, END, START(synthetic), CONTENT,
    #              END(synthetic), RUN_FINISHED
    assert types.count("TEXT_MESSAGE_START") == 2
    assert types.count("TEXT_MESSAGE_END") == 2
    assert types[-1] == "RUN_FINISHED"
