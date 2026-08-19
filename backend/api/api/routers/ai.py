from datetime import datetime
from uuid import UUID, uuid4

from common.ai_context.ai_context_repository import AiQuestion, CapabilityId
from common.dependencies import get_root_task_information_repository
from common.task_object.root_task_information_repository import RootTaskInformation
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pydantic_ai.ui import SSE_CONTENT_TYPE
from pydantic_ai.ui.ag_ui import AGUIAdapter

from api.dependencies import get_agent_service, get_ai_service
from api.services.agent_service import AgentService
from api.services.ai_service import AiService

router = APIRouter()

_MAX_PAGE_SIZE = 100

default_ai_service = Depends(get_ai_service)
default_agent_service = Depends(get_agent_service)


class ContextCreateResponse(BaseModel):
    context_id: UUID


class ContextSummary(BaseModel):
    context_id: UUID
    created_at: datetime
    first_question: str | None
    question_count: int


class ListContextsResponse(BaseModel):
    contexts: list[ContextSummary]


class ContextHistoryResponse(BaseModel):
    created_at: datetime
    questions: list[AiQuestion]
    active_capabilities: list[CapabilityId]


class CapabilityUpdate(BaseModel):
    capability: CapabilityId
    active: bool


@router.get("")
def list_contexts(ai_service: AiService = default_ai_service) -> ListContextsResponse:
    contexts = ai_service.list_contexts()
    summaries = [
        ContextSummary(
            context_id=c.id_,
            created_at=c.created_at,
            first_question=c.questions[0].question if c.questions else None,
            question_count=len(c.questions),
        )
        for c in contexts
    ]
    return ListContextsResponse(contexts=summaries)


@router.get("/{context_id}/history")
def get_context_history(
    context_id: UUID,
    after: int | None = None,
    page_size: int | None = None,
    ai_service: AiService = default_ai_service,
) -> ContextHistoryResponse:
    context = ai_service.get_context(context_id)
    start = (after + 1) if after is not None else 0
    questions = context.questions[start:]
    if page_size is not None:
        questions = questions[: min(page_size, _MAX_PAGE_SIZE)]
    return ContextHistoryResponse(
        created_at=context.created_at,
        questions=questions,
        active_capabilities=context.active_capabilities,
    )


@router.patch("/{context_id}/capabilities")
def update_capabilities(
    context_id: UUID,
    update: CapabilityUpdate,
    ai_service: AiService = default_ai_service,
) -> None:
    """Enable or disable a capability for an AI context."""
    ai_service.update_capabilities(context_id, update.capability, update.active)


@router.delete("/{context_id}")
def delete_context(
    context_id: UUID,
    ai_service: AiService = default_ai_service,
) -> None:
    """Delete an AI context and its conversation history."""
    ai_service.delete_context(context_id)


@router.post("")
def create_context(
    ai_service: AiService = default_ai_service,
) -> ContextCreateResponse:
    context = ai_service.create_context()
    return ContextCreateResponse(context_id=context.id_)


@router.post("/{context_id}/run")
async def run_agent(
    context_id: UUID,
    request: Request,
    ai_service: AiService = default_ai_service,
    agent_service: AgentService = default_agent_service,
) -> StreamingResponse:
    context = ai_service.get_context(context_id)
    accept = request.headers.get("accept", SSE_CONTENT_TYPE)
    run_input = AGUIAdapter.build_run_input(await request.body())

    prepared = agent_service.build_agent(context)
    root_task_id = uuid4()
    get_root_task_information_repository().save(
        RootTaskInformation(root_task_id=root_task_id, object_id=context.id_)
    )

    adapter = AGUIAdapter(agent=prepared.agent, run_input=run_input, accept=accept)
    stream = ai_service.run_agent_stream(context, root_task_id, adapter, prepared.deps)
    return StreamingResponse(adapter.encode_stream(stream), media_type=accept)
