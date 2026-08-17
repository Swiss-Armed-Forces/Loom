"""Shared helpers for AI integration tests."""

from uuid import UUID, uuid4

import requests
from api.routers.ai import ContextCreateResponse

from utils.consts import AI_ENDPOINT, REQUEST_TIMEOUT


def create_ai_context() -> ContextCreateResponse:
    response = requests.post(AI_ENDPOINT, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return ContextCreateResponse.model_validate(response.json())


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
