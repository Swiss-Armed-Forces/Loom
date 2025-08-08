import logging
from typing import Annotated
from uuid import UUID

from common.ai_context.ai_scheduling_service import AiSchedulingService
from common.dependencies import get_ai_context_repository, get_ai_scheduling_service
from common.services.query_builder import QueryParameters
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

router = APIRouter()

logger = logging.getLogger(__name__)

default_ai_context_repository = Depends(get_ai_context_repository)
default_ai_scheduling_service = Depends(get_ai_scheduling_service)


class ContextCreateResponse(BaseModel):
    context_id: UUID = Field(min_length=1)


@router.post("/")
def create_context(
    query: Annotated[QueryParameters, Query()],
    ai_scheduling_service: AiSchedulingService = default_ai_scheduling_service,
) -> ContextCreateResponse:
    context = ai_scheduling_service.create_context(query=query)
    return ContextCreateResponse(context_id=context.id_)


class ProcessQuestionQuery(BaseModel):
    question: str = Field(min_length=1)


@router.post("/{context_id}/process_question")
def process_question(
    context_id: UUID,
    query: Annotated[ProcessQuestionQuery, Query()],
    ai_scheduling_service: AiSchedulingService = default_ai_scheduling_service,
):
    ai_scheduling_service.process_ai_question(
        context_id=context_id, question=query.question
    )
