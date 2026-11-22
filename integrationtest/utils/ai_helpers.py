"""Shared helpers for AI integration tests."""

import json
from uuid import UUID, uuid4

import requests
from api.routers.ai import (
    ContextCreateResponse,
    ContextHiddenResponse,
    ContextHistoryResponse,
    ListContextsResponse,
)

from utils.consts import AI_ENDPOINT, REQUEST_TIMEOUT


def create_ai_context() -> ContextCreateResponse:
    response = requests.post(AI_ENDPOINT, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return ContextCreateResponse.model_validate(response.json())


def list_ai_contexts() -> ListContextsResponse:
    response = requests.get(AI_ENDPOINT, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return ListContextsResponse.model_validate(response.json())


def list_ai_context_ids() -> list[UUID]:
    return [context.context_id for context in list_ai_contexts().contexts]


def set_ai_context_hidden(ai_context_id: UUID, hidden: bool) -> ContextHiddenResponse:
    response = requests.patch(
        f"{AI_ENDPOINT}/{ai_context_id}/hidden",
        json={"hidden": hidden},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return ContextHiddenResponse.model_validate(response.json())


def get_ai_context_history(ai_context_id: UUID) -> ContextHistoryResponse:
    response = requests.get(
        f"{AI_ENDPOINT}/{ai_context_id}/history",
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return ContextHistoryResponse.model_validate(response.json())


def run_agent(ai_context_id: UUID, question: str) -> requests.Response:
    run_input = {
        "threadId": str(uuid4()),
        "runId": str(uuid4()),
        "messages": [
            {
                "id": str(uuid4()),
                "role": "user",
                "content": question,
            }
        ],
        "tools": [],
        "context": [],
        "state": {},
        "forwardedProps": {},
    }
    response = requests.post(
        f"{AI_ENDPOINT}/{ai_context_id}/run",
        json=run_input,
        headers={
            "content-type": "application/json",
            "accept": "text/event-stream",
        },
        timeout=REQUEST_TIMEOUT,
        stream=True,
    )
    response.raise_for_status()
    return response


def collect_sse_event_types(response: requests.Response) -> list[str]:
    """Iterate an SSE stream and collect the ``type`` field from every event."""
    event_types: list[str] = []
    for line in response.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data:"):
            continue
        data = json.loads(line[len("data:") :].strip())
        if "type" in data:
            event_types.append(data["type"])
    return event_types
