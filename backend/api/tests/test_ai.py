from uuid import uuid4

from ag_ui.core import RunFinishedEvent, TextMessageContentEvent
from common.ai_context.ai_context_repository import AiContext
from fastapi.testclient import TestClient

from api.dependencies import get_ai_service
from api.routers.ai import ContextCreateResponse

ENDPOINT = "/v1/ai"


def test_create_context(client: TestClient):

    ai_context = AiContext()
    get_ai_service().create_context.return_value = ai_context

    response = client.post(ENDPOINT)
    response.raise_for_status()

    get_ai_service().create_context.assert_called_once_with()
    create_context_response = ContextCreateResponse.model_validate(response.json())
    assert create_context_response == ContextCreateResponse(context_id=ai_context.id_)


def test_run_agent_streams_sse(client: TestClient):

    context_id = uuid4()
    ai_context = AiContext()
    ai_context.id_ = context_id
    get_ai_service().get_context.return_value = ai_context

    async def mock_stream(_ctx, _root_id, _adapter, _deps):  # type: ignore[override]
        yield TextMessageContentEvent(message_id="m1", delta="Hello world")
        yield RunFinishedEvent(thread_id="t1", run_id="r1")

    get_ai_service().run_agent_stream = mock_stream

    run_input = (
        b'{"threadId":"t1","runId":"r1","messages":[],'
        b'"tools":[],"context":[],"state":{},"forwardedProps":{}}'
    )
    response = client.post(
        f"{ENDPOINT}/{context_id}/run",
        content=run_input,
        headers={"content-type": "application/json", "accept": "text/event-stream"},
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    body = response.text
    assert "TEXT_MESSAGE_CONTENT" in body
    assert "Hello world" in body
    assert "RUN_FINISHED" in body
