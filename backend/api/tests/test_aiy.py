from uuid import uuid4

from common.ai_context.ai_context_repository import AiContext
from common.dependencies import get_ai_scheduling_service
from common.services.query_builder import QueryParameters
from fastapi.testclient import TestClient

from api.routers.ai import ContextCreateResponse, ProcessQuestionQuery

ENDPOINT = "/v1/ai/"


def test_create_context(client: TestClient):

    query_parameters = QueryParameters(query_id="test")
    ai_context = AiContext(query=query_parameters)
    get_ai_scheduling_service().create_context.return_value = ai_context

    response = client.post(ENDPOINT, json=query_parameters.model_dump())
    response.raise_for_status()

    get_ai_scheduling_service().create_context.assert_called_once_with(
        query=query_parameters
    )
    create_context_response = ContextCreateResponse.model_validate(response.json())
    assert create_context_response == ContextCreateResponse(context_id=ai_context.id_)


def test_process_question(client: TestClient):

    context_id = uuid4()
    query = ProcessQuestionQuery(question="What are you doing?")

    get_ai_scheduling_service().process_ai_question.return_value = None

    response = client.post(
        f"{ENDPOINT}{context_id}/process_question", json=query.model_dump()
    )
    response.raise_for_status()

    get_ai_scheduling_service().process_ai_question.assert_called_once_with(
        context_id=context_id, question=query.question
    )
